from typing import Final

from eth_account import Account
from eth_account.signers.local import LocalAccount
from fastapi import FastAPI, Depends, HTTPException
from hexbytes import HexBytes
from redis import Redis as Dragonfly
from sqlalchemy.orm import Session
from web3 import Web3

import models
import utils
from deps import get_deps, get_constants

CACHE_NORMAL_EXPIRATION_SECONDS: Final[int] = 60
CACHE_EMPTY_EXPIRATION_SECONDS: Final[int] = 30

app = FastAPI()


@app.post("/transactions")
async def transaction(
        req: utils.TransactionRequest,
        db: Session = Depends(get_deps().get_db_session),
        df: Dragonfly = Depends(get_deps().get_dragonfly),
        w3: Web3 = Depends(get_deps().get_web3),
):
    # Read the user account from the database first.
    user_account = db.query(models.UserAccount) \
        .filter(models.UserAccount.id == req.user_account_id) \
        .first()
    if user_account is None:
        raise HTTPException(status_code=404, detail="User account not found")

    # Check if the user account has enough available balance.
    if user_account.available_balance_in_wei < req.transaction_amount_in_wei:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    # Construct a web3 transaction object without sending it.
    # Assume that the system account has enough balance to pay for the whole transaction.
    sys_account_private_key = get_constants().get_system_account_private_key()
    account: LocalAccount = Account.from_key(sys_account_private_key)
    txn_raw = {
        'chainId': 80002,  # Polygon Amoy Testnet
        'from': account.address,
        'to': HexBytes(req.to_public_address),
        'value': req.transaction_amount_in_wei,
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': 200000,
        'maxFeePerGas': 2000000000,
        'maxPriorityFeePerGas': 1000000000,
    }
    txn_signed = w3.eth.account.sign_transaction(txn_raw, sys_account_private_key)
    txn_hash_predicted = txn_signed.hash

    # Create a new transaction record and update the user account balance within a database transaction.
    txn = models.UserAccountTransaction(
        user_account_id=req.user_account_id,
        transaction_hash=txn_hash_predicted.hex(),
        from_public_address=account.address,
        to_public_address=req.to_public_address,
        transaction_amount_in_wei=req.transaction_amount_in_wei,
        transaction_fee_total_in_wei=0,
        transaction_fee_blockchain_in_wei=0,
        status=models.UserAccountTransactionStatus.PENDING,
    )
    db.add(txn)
    user_account.available_balance_in_wei -= req.transaction_amount_in_wei
    db.commit()
    db.refresh(txn)

    # Send the transaction to the blockchain.
    txn_hash_actual = w3.eth.send_raw_transaction(txn_signed.rawTransaction)
    if txn_hash_actual != txn_hash_predicted:
        print(f"Transaction hash mismatch! Predicted: {txn_hash_predicted.hex()}. Actual: {txn_hash_actual.hex()}")
        raise HTTPException(status_code=500, detail="Transaction hash mismatch")

    # Cache the transaction in Dragonfly.
    cache_key = utils.txn_cache_key(txn.id)
    df.hset(cache_key, mapping=utils.txn_to_dict(txn))
    df.expire(cache_key, CACHE_NORMAL_EXPIRATION_SECONDS)

    # Return the transaction response.
    return utils.txn_to_response(txn)


@app.get("/transactions/{txn_id}")
async def get_transaction(
        txn_id: int,
        db: Session = Depends(get_deps().get_db_session),
        df: Dragonfly = Depends(get_deps().get_dragonfly),
) -> utils.TransactionResponse:
    cache_key = utils.txn_cache_key(txn_id)

    # Try to read the transaction from Dragonfly first.
    cached_txn = df.hgetall(cache_key)

    # Empty cache value with only the ID.
    if len(cached_txn) == 1:
        raise HTTPException(status_code=404, detail="Transaction not found")
    # Cache hit.
    elif len(cached_txn) > 1:
        return utils.txn_dict_to_response(cached_txn)

    # Cache miss, read from the database.
    txn = db.query(models.UserAccountTransaction) \
        .filter(models.UserAccountTransaction.id == txn_id) \
        .first()

    # If the transaction is not found, cache an empty value with only the ID and return a 404.
    # Caching an empty value is important to prevent cache penetrations.
    if txn is None:
        df.hset(cache_key, mapping={"id": txn_id})
        df.expire(cache_key, CACHE_EMPTY_EXPIRATION_SECONDS)
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Cache the transaction in Dragonfly and return the response.
    df.hset(cache_key, mapping=utils.txn_to_dict(txn))
    df.expire(cache_key, CACHE_NORMAL_EXPIRATION_SECONDS)
    return utils.txn_to_response(txn)
