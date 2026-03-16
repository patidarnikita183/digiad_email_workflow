import os

from dotenv import load_dotenv
import psycopg2
from psycopg2.pool import SimpleConnectionPool


load_dotenv()


def get_db_config():
    """
    Central place for all DB connection settings.
    """
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "5432"),
        "dbname": os.getenv("DB_NAME", "digiAd"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", "12345"),
        # Keep a short connect timeout so workers never hang forever
        "connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", "5")),
    }


class PooledConnection:
    """
    Lightweight wrapper around a psycopg2 pooled connection.

    It mimics the regular connection API but when `.close()` is called,
    it returns the connection to the pool instead of actually closing it.
    This lets existing worker code keep using `conn = get_db_connection()`
    and `conn.close()` without any changes.
    """

    def __init__(self, pool: SimpleConnectionPool):
        self._pool = pool
        self._conn = pool.getconn()
        self._returned = False

    def close(self):
        if not self._returned:
            self._pool.putconn(self._conn)
            self._returned = True

    # Delegate everything else to the underlying connection
    def __getattr__(self, item):
        return getattr(self._conn, item)


# Global connection pool for the app / workers
_DB_POOL = SimpleConnectionPool(
    minconn=int(os.getenv("DB_MIN_CONNECTIONS", "1")),
    maxconn=int(os.getenv("DB_MAX_CONNECTIONS", "10")),
    **get_db_config(),
)


def get_db_connection():
    """
    Returns a connection-like object backed by the global pool.

    Call `.close()` on it as usual — the wrapper will return it to the pool.
    """
    return PooledConnection(_DB_POOL)

