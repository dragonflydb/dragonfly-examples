import os

from redis import ConnectionPool
from redis import Redis as Dragonfly


def connect_dragonfly() -> Dragonfly:
    """
    Connect to Dragonfly using the DF_URL environment variable if provided, else redis://localhost:6379/0
    Examples:
      export DF_URL=rediss://default:PASSKEY@DATASTORE.dragonflydb.cloud:6385
    """
    url = os.getenv("DF_URL", "redis://localhost:6379/0")
    pool = ConnectionPool.from_url(
        url,
        health_check_interval=30,
        socket_keepalive=True
    )
    return Dragonfly(connection_pool=pool, decode_responses=True)
