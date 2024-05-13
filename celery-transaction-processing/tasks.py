from typing import Final

from celery import Celery
from celery.utils.log import get_task_logger

import eth
import models
from deps import get_constants

logger = get_task_logger(__name__)


class TaskRetryException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(message)


# Use Dragonfly as the broker and the result backend for Celery.
# Dragonfly is wire-protocol compatible with Redis.
# We can use the same Redis URL(s) as long as Dragonfly is running on the port specified.
app = Celery(
    'tasks',
    broker=get_constants().get_celery_broker_url(),
    backend=get_constants().get_celery_backend_url(),
)

TASK_MAX_RETRIES: Final[int] = 20
TASK_RETRY_DELAY: Final[int] = 100


# Define a Celery task to reconcile a transaction.
# We check the transaction status from the blockchain and update the database accordingly.
# The blockchain is just an example. Many finical systems have similar reconciliation or settlement processes.
#
# Maximum retry count is TASK_MAX_RETRIES, and the delay between retries is exponential.
# The retry delays are [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, ...] * TASK_RETRY_DELAY seconds.
# Thus, the first retry is after 100 seconds, the second retry is after 200 seconds, and so on.
@app.task(
    bind=True,
    autoretry_for=(TaskRetryException,),
    max_retries=TASK_MAX_RETRIES,
    retry_backoff=TASK_RETRY_DELAY,
    retry_jitter=False,
)
def reconcile_transaction(_self, tx_id: str):
    try:
        status_response = eth.get_transaction_status(tx_id)
        logger.info(status_response)
        if status_response.status == models.UserAccountTransactionStatus.PENDING:
            raise TaskRetryException('TransactionStatus=PENDING')
    finally:
        logger.info('transaction reconciliation attempted')
