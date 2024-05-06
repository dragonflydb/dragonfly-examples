import os

from eth_typing import HexStr
from web3 import Web3

WEB3_PROVIDER_URL_KEY = 'WEB3_PROVIDER_URI'

if WEB3_PROVIDER_URL_KEY not in os.environ:
    raise ValueError(f'{WEB3_PROVIDER_URL_KEY} environment variable is not set')

w3 = Web3(Web3.HTTPProvider(os.environ[WEB3_PROVIDER_URL_KEY]))


def get_transaction_status(tx_hash: str):
    # Get the transaction receipt
    receipt = w3.eth.get_transaction_receipt(HexStr(tx_hash))
    if receipt is None:
        return 'TX_PENDING'
    elif receipt['status'] == 0:
        return 'TX_FAILED'
    else:
        return 'TX_OK'
