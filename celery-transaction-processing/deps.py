import os
from typing import Final

from redis import Redis as Dragonfly, ConnectionPool as DragonflyConnectionPool
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker
from web3 import Web3

import utils


class _Constants:
    # Use Dragonfly as the default broker and the result backend for Celery.
    DEFAULT_DRAGONFLY_URL: Final[str] = 'redis://localhost:6380/0'
    DRAGONFLY_URL_ENV: Final[str] = 'DF_DRAGONFLY_URL'
    CELERY_BROKER_URL_ENV: Final[str] = 'DF_CELERY_BROKER_URL'
    CELERY_BACKEND_URL_ENV: Final[str] = 'DF_CELERY_BACKEND_URL'

    __dragonfly_url = DEFAULT_DRAGONFLY_URL
    if DRAGONFLY_URL_ENV in os.environ:
        __dragonfly_url = os.environ[DRAGONFLY_URL_ENV]

    __celery_broker_url = DEFAULT_DRAGONFLY_URL
    if CELERY_BROKER_URL_ENV in os.environ:
        __celery_broker_url = os.environ[CELERY_BROKER_URL_ENV]

    __celery_backend_url = DEFAULT_DRAGONFLY_URL
    if CELERY_BACKEND_URL_ENV in os.environ:
        __celery_backend_url = os.environ[CELERY_BACKEND_URL_ENV]

    @staticmethod
    def get_dragonfly_url() -> str:
        return _Constants.__dragonfly_url

    @staticmethod
    def get_celery_broker_url() -> str:
        return _Constants.__celery_broker_url

    @staticmethod
    def get_celery_backend_url() -> str:
        return _Constants.__celery_backend_url

    # Use SQLite as the default database.
    DEFAULT_DATABASE_URL: Final[str] = 'sqlite:///./data.db'
    DATABASE_URL_ENV: Final[str] = 'DF_DATABASE_URL'

    __database_url = DEFAULT_DATABASE_URL
    if DATABASE_URL_ENV in os.environ:
        __database_url = os.environ[DATABASE_URL_ENV]

    @staticmethod
    def get_database_url() -> str:
        return _Constants.__database_url

    # Web3 related constants.
    SYSTEM_ACCOUNT_PRIVATE_KEY_ENV: Final[str] = 'DF_SYSTEM_ACCOUNT_PRIVATE_KEY'
    WEB3_PROVIDER_URL_KEY: Final[str] = 'DF_WEB3_PROVIDER_URI'

    __system_account_private_key = ''
    if SYSTEM_ACCOUNT_PRIVATE_KEY_ENV in os.environ:
        __system_account_private_key = os.environ[SYSTEM_ACCOUNT_PRIVATE_KEY_ENV]
    else:
        raise ValueError(f'{SYSTEM_ACCOUNT_PRIVATE_KEY_ENV} environment variable is not set')

    __web3_provider_url = ''
    if WEB3_PROVIDER_URL_KEY in os.environ:
        __web3_provider_url = os.environ[WEB3_PROVIDER_URL_KEY]
    else:
        raise ValueError(f'{WEB3_PROVIDER_URL_KEY} environment variable is not set')

    @staticmethod
    def get_system_account_private_key() -> str:
        return _Constants.__system_account_private_key

    @staticmethod
    def get_web3_provider_url() -> str:
        return _Constants.__web3_provider_url


__constants_instance = _Constants()


def get_constants():
    return __constants_instance


class _Deps:
    # Database client/session.
    __engine = create_engine(
        get_constants().get_database_url(), connect_args={"check_same_thread": False}
    )
    __session_local = sessionmaker(autocommit=False, autoflush=False, bind=__engine)

    @staticmethod
    def get_db_session() -> Session:
        db = _Deps.__session_local()
        try:
            yield db
        finally:
            db.close()

    # Dragonfly client.
    __dragonfly_url = utils.parse_dragonfly_url(get_constants().get_dragonfly_url())
    __dragonfly_conn_pool = DragonflyConnectionPool(
        host=__dragonfly_url.host,
        port=__dragonfly_url.port,
        db=__dragonfly_url.db,
    )
    __dragonfly_client = Dragonfly(connection_pool=__dragonfly_conn_pool)

    @staticmethod
    def get_dragonfly() -> Dragonfly:
        return _Deps.__dragonfly_client

    # Web3 client.
    __web3_provider = Web3(Web3.HTTPProvider(get_constants().get_web3_provider_url()))

    @staticmethod
    def get_web3() -> Web3:
        return _Deps.__web3_provider


__deps_instance = _Deps()


def get_deps():
    return __deps_instance
