from dataclasses import dataclass

import models


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


def txn_cache_key(transaction_id: int) -> str:
    return f"user_account_transaction:{transaction_id}"


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
        id=txn["id"],
        transaction_hash=txn["transaction_hash"],
        from_public_address=txn["from_public_address"],
        to_public_address=txn["to_public_address"],
        transaction_amount_in_wei=txn["transaction_amount_in_wei"],
        transaction_fee_total_in_wei=txn["transaction_fee_total_in_wei"],
        transaction_fee_blockchain_in_wei=txn["transaction_fee_blockchain_in_wei"],
        status=txn["status"],
    )
