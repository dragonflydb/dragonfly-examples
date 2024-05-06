import os

from celery import Celery

from eth import get_transaction_status

DRAGONFLY_URL_KEY = 'DRAGONFLY_URL'
dragonfly_url = 'redis://localhost:6380/0'

if DRAGONFLY_URL_KEY in os.environ:
    dragonfly_url = os.environ[DRAGONFLY_URL_KEY]

# Use Dragonfly as the broker and the result backend for Celery.
# Dragonfly is wire-protocol compatible with Redis.
# We can use the same Redis URL(s) as long as Dragonfly is running on the port specified.
app = Celery(
    'tasks',
    broker=dragonfly_url,
    backend=dragonfly_url,
)

TASK_MAX_RETRIES = 10
TASK_RETRY_DELAY = 10
TASK_RETRY_BACKOFF_MAX = 3600
NUM_OF_BLOCKS_TO_WAIT = 10


# Define a Celery task to reconcile a transaction.
# We check the transaction status from the blockchain and update the database accordingly.
# The blockchain is just an example. Many finical systems have similar reconciliation or settlement processes.
#
# Maximum retry count is 10, and the delay between retries is exponential.
# The retry delays are [1, 2, 4, 8, 16, 32, 64, ...] * 10 seconds up to 1 hour.
@app.task(
    max_retries=TASK_MAX_RETRIES,
    retry_backoff=TASK_RETRY_DELAY,
    retry_backoff_max=TASK_RETRY_BACKOFF_MAX,
)
def reconcile_transaction(tx_id: str):
    return get_transaction_status(tx_id)


@app.task
def process_transactions():
    return 'OK'
