from dataclasses import dataclass
from typing import Final
from urllib.parse import urlparse

from redis import Redis as Dragonfly

import models

CACHE_NORMAL_EXPIRATION_SECONDS: Final[int] = 60
CACHE_EMPTY_EXPIRATION_SECONDS: Final[int] = 30

# We use a lock to prevent concurrent transactions for the same user account.
LOCK_EXPIRATION_SECONDS: Final[int] = 10
LOCK_VALUE: Final[str] = "locked"

# This chain ID is for the Ethereum Sepolia testnet.
# Thus, the 'DF_WEB3_PROVIDER_URI' environment variable should be set to the Sepolia testnet,
# which looks like 'https://sepolia.infura.io/v3/7eaXXXXXXXXXX' if you are using Infura.
SEPOLIA_CHAIN_ID: Final[int] = 11155111

# We charge a fixed fee for each transaction.
# This fee should be enough to cover the blockchain transaction fee, so we can make a profit.
# Blockchain transaction fees are not fixed and can vary depending on the network congestion.
# We set the total transaction fee to 0.008 ETH, which is an estimation based on the Sepolia testnet.
# Note that 1 ETH = 10^18 Wei, so 0.008 ETH = 8000000000000000 Wei
TOTAL_TRANSACTION_FEE_IN_WEI: Final[int] = 8000000000000000


@dataclass
class TransactionRequest:
    user_account_id: int
    to_public_address: str
    transaction_amount_in_wei: int


@dataclass
class TransactionResponse:
    id: int
    transaction_hash: str
    from_public_address: str
    to_public_address: str
    transaction_amount_in_wei: int
    transaction_fee_total_in_wei: int
    transaction_fee_blockchain_in_wei: int
    status: str


def user_account_lock_key(user_account_id: int) -> str:
    return f"user_account_lock:{user_account_id}"


def txn_cache_key(txn_id: int) -> str:
    return f"user_account_transaction:{txn_id}"


def txn_to_response(txn: models.UserAccountTransaction) -> TransactionResponse:
    return TransactionResponse(
        id=txn.id,
        transaction_hash=txn.transaction_hash,
        from_public_address=txn.from_public_address,
        to_public_address=txn.to_public_address,
        transaction_amount_in_wei=txn.transaction_amount_in_wei,
        transaction_fee_total_in_wei=txn.transaction_fee_total_in_wei,
        transaction_fee_blockchain_in_wei=txn.transaction_fee_blockchain_in_wei,
        status=txn.status.name,
    )


def txn_to_dict(txn: models.UserAccountTransaction) -> dict:
    return {
        "id": txn.id,
        "transaction_hash": txn.transaction_hash,
        "from_public_address": txn.from_public_address,
        "to_public_address": txn.to_public_address,
        "transaction_amount_in_wei": txn.transaction_amount_in_wei,
        "transaction_fee_total_in_wei": txn.transaction_fee_total_in_wei,
        "transaction_fee_blockchain_in_wei": txn.transaction_fee_blockchain_in_wei,
        "status": txn.status.name,
    }


def txn_dict_to_response(txn: dict) -> TransactionResponse:
    return TransactionResponse(
        id=txn[b"id"],
        transaction_hash=txn[b"transaction_hash"],
        from_public_address=txn[b"from_public_address"],
        to_public_address=txn[b"to_public_address"],
        transaction_amount_in_wei=txn[b"transaction_amount_in_wei"],
        transaction_fee_total_in_wei=txn[b"transaction_fee_total_in_wei"],
        transaction_fee_blockchain_in_wei=txn[b"transaction_fee_blockchain_in_wei"],
        status=txn[b"status"],
    )


@dataclass
class DragonflyURLParsed:
    host: str
    port: int
    db: int


def parse_dragonfly_url(dragonfly_url) -> DragonflyURLParsed:
    result = urlparse(dragonfly_url)
    host = result.hostname
    port = result.port
    db = 0
    if result.path:
        try:
            db = int(result.path.strip('/'))
        except ValueError:
            raise ValueError("Invalid database index in URI")

    if port is None:
        port = 6379

    return DragonflyURLParsed(host=host, port=port, db=db)


def hset_and_expire(
        df: Dragonfly,
        key: str,
        mapping: dict,
        expiration: int,
):
    pipe = df.pipeline()
    pipe.hset(key, mapping=mapping)
    pipe.expire(key, expiration)
    pipe.execute()
