from typing import Final

from celery import Celery
from celery.utils.log import get_task_logger
from web3 import exceptions as web3_exceptions

import eth
import models
from deps import get_deps, get_constants

logger = get_task_logger(__name__)


class TaskRetryException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)


class TaskNotRetryException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)


# Celery app configuration.
# Use Dragonfly as the message broker and the result storage backend for Celery.
# Dragonfly is wire-protocol compatible with Redis.
# We can use the same Redis URL(s) as long as Dragonfly is running on the port specified.
app = Celery(
    'tasks',
    broker=get_constants().get_celery_broker_url(),
    backend=get_constants().get_celery_backend_url(),
)

TASK_MAX_RETRIES: Final[int] = 32
TASK_RETRY_BACKOFF: Final[int] = 100
TASK_RETRY_BACKOFF_MAX: Final[int] = 1600


# Define a Celery task to reconcile a transaction.
# We check the transaction status from the blockchain and update the database accordingly.
# The blockchain is just an example. Many finical systems have similar reconciliation or settlement processes.
#
# Maximum retry count is 32, and the delay between retries is exponential.
#
# The retry delays are [1, 2, 4, 8, 16, ...] x 100 seconds.
# So, the first retry is after 100 seconds, the second retry is after 200 seconds, and so on.
#
# The maximum backoff delay is set to 1600 seconds.
# Thus, the retry delays in this configuration are [100, 200, 400, 800, 1600, 1600, ...] seconds up to 32 retries.
@app.task(
    bind=True,
    autoretry_for=(TaskRetryException,),
    max_retries=TASK_MAX_RETRIES,
    retry_backoff=TASK_RETRY_BACKOFF,
    retry_backoff_max=TASK_RETRY_BACKOFF_MAX,
    retry_jitter=False,
)
def reconcile_transaction(_self, txn_id: str):
    db_gen = get_deps().get_db_session()
    db = next(db_gen)
    try:
        # Read the transaction and the user account from the database.
        # Stop if the transaction is already reconciled.
        txn = db.query(models.UserAccountTransaction).get(txn_id)
        if txn is None:
            raise TaskNotRetryException('TransactionNotFound')
        if txn.status != models.UserAccountTransactionStatus.PENDING:
            raise TaskNotRetryException('TransactionStatusNotPending')
        account = db.query(models.UserAccount).get(txn.user_account_id)

        # Check the transaction status from the blockchain.
        status_response = eth.get_transaction_status(txn.transaction_hash)
        logger.info(status_response)
        if status_response.status == models.UserAccountTransactionStatus.PENDING:
            raise TaskRetryException('TransactionStatus=PENDING')

        # Update the transaction status and the user account balance within a database transaction.
        if status_response.status == models.UserAccountTransactionStatus.SUCCESSFUL:
            total_amount_in_wei = txn.transaction_amount_in_wei + txn.transaction_fee_total_in_wei
            txn.status = status_response.status
            txn.transaction_fee_blockchain_in_wei = status_response.transaction_fee_blockchain_in_wei
            account.current_balance_in_wei -= total_amount_in_wei
            db.commit()
    except web3_exceptions.TransactionNotFound as e:
        logger.info(f'TransactionNotFoundOnChainYet: {e}')
        raise TaskRetryException('TransactionNotFoundOnChainYet')
    finally:
        logger.info('transaction reconciliation attempted')
