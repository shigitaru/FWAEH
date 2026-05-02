import logging
import threading

from psycopg2 import pool
from psycopg2.extras import NamedTupleCursor

from .config import settings

logger = logging.getLogger(__name__)

_pool_lock = threading.Lock()
_connection_pool = None


def _convert_placeholders(sql):
    out = []
    in_single = False
    i = 0
    while i < len(sql):
        ch = sql[i]
        if ch == "'":
            out.append(ch)
            if in_single and i + 1 < len(sql) and sql[i + 1] == "'":
                out.append(sql[i + 1])
                i += 2
                continue
            in_single = not in_single
        elif ch == '?' and not in_single:
            out.append('%s')
        else:
            out.append(ch)
        i += 1
    return ''.join(out)


def _adapt_postgres_sql(sql, params):
    return _convert_placeholders(sql), tuple(params or ())


class PostgresCursor:
    def __init__(self, cursor):
        self._cursor = cursor

    @property
    def description(self):
        return self._cursor.description

    def execute(self, sql, params=None):
        adapted_sql, adapted_params = _adapt_postgres_sql(sql, params)
        self._cursor.execute(adapted_sql, adapted_params)
        return self

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    def nextset(self):
        return False

    def __getattr__(self, name):
        return getattr(self._cursor, name)


class PostgresConnection:
    def __init__(self, connection):
        self._connection = connection

    def cursor(self):
        return PostgresCursor(self._connection.cursor(cursor_factory=NamedTupleCursor))

    def commit(self):
        return self._connection.commit()

    def rollback(self):
        return self._connection.rollback()

    def close(self):
        return self._connection.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def __getattr__(self, name):
        return getattr(self._connection, name)


class PooledPostgresConnection(PostgresConnection):
    """Returns the underlying connection to the pool on close()."""

    def __init__(self, raw_connection, pool_instance):
        super().__init__(raw_connection)
        self._pool = pool_instance
        self._returned = False

    def close(self):
        if self._returned:
            return
        self._returned = True
        conn = self._connection
        self._connection = None
        if conn is not None and self._pool is not None:
            try:
                self._pool.putconn(conn)
            except Exception:
                logger.exception('Failed to return connection to pool; closing underlying connection')
                try:
                    conn.close()
                except Exception:
                    logger.exception('Failed to close stray pooled connection')


def _get_or_create_pool():
    global _connection_pool
    if not settings.postgres_connection_string:
        raise RuntimeError('POSTGRES_CONNECTION_STRING or SUPABASE_DB_URL is required')
    if _connection_pool is not None:
        return _connection_pool
    with _pool_lock:
        if _connection_pool is None:
            _connection_pool = pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=15,
                dsn=settings.postgres_connection_string,
            )
    return _connection_pool


def get_db_connection():
    pl = _get_or_create_pool()
    raw = pl.getconn()
    return PooledPostgresConnection(raw, pl)
