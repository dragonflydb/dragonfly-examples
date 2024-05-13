from dataclasses import dataclass
from typing import Final

import models

CACHE_NORMAL_EXPIRATION_SECONDS: Final[int] = 60
CACHE_EMPTY_EXPIRATION_SECONDS: Final[int] = 30

# We use a lock to prevent concurrent transactions for the same user account.
LOCK_EXPIRATION_SECONDS: Final[int] = 10
LOCK_VALUE: Final[str] = "locked"

# We charge a fixed fee for each transaction.
# This fee should be enough to cover the blockchain transaction fee.
TOTAL_TRANSACTION_FEE_IN_WEI: Final[int] = 50000000000000


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
