import os
from dataclasses import dataclass

from eth_typing import HexStr
from web3 import Web3
from web3.types import TxReceipt

from models import UserAccountTransactionStatus

WEB3_PROVIDER_URL_KEY = 'WEB3_PROVIDER_URI'

if WEB3_PROVIDER_URL_KEY not in os.environ:
    raise ValueError(f'{WEB3_PROVIDER_URL_KEY} environment variable is not set')

w3 = Web3(Web3.HTTPProvider(os.environ[WEB3_PROVIDER_URL_KEY]))


@dataclass
class TransactionStatusResponse:
    tx_hash: str
    tx_block_number: int
    current_block_number: int
    status: UserAccountTransactionStatus


def get_transaction_status(
        tx_hash: str,
        number_of_blocks_to_wait: int = 10
) -> TransactionStatusResponse:
    receipt = w3.eth.get_transaction_receipt(HexStr(tx_hash))
    current_block_number = w3.eth.get_block_number()
    return TransactionStatusResponse(
        tx_hash=tx_hash,
        tx_block_number=receipt['blockNumber'],
        current_block_number=current_block_number,
        status=__calculate_transaction_status(receipt, current_block_number, number_of_blocks_to_wait)
    )


def __calculate_transaction_status(
        receipt: TxReceipt,
        current_block_number: int,
        number_of_blocks_to_wait: int
) -> UserAccountTransactionStatus:
    if receipt is None:
        return UserAccountTransactionStatus.PENDING
    elif receipt['status'] == 0:
        return UserAccountTransactionStatus.FAILED
    else:
        if receipt['blockNumber'] + number_of_blocks_to_wait <= current_block_number:
            return UserAccountTransactionStatus.SUCCESSFUL
        else:
            return UserAccountTransactionStatus.PENDING
