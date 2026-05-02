import pyodbc
import re

try:
    import psycopg2
    from psycopg2.extras import NamedTupleCursor
except ImportError:  # Local SQL Server mode does not need psycopg2.
    psycopg2 = None
    NamedTupleCursor = None

from .config import settings


def using_postgres():
    return settings.db_engine in ('postgres', 'postgresql', 'supabase')


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
    params = tuple(params or ())
    sql = sql.replace('[condition]', 'condition')
    sql = re.sub(r"\bN'", "'", sql)
    sql = re.sub(r'LTRIM\s*\(\s*RTRIM\s*\((.*?)\)\s*\)', r'TRIM(\1)', sql, flags=re.I | re.S)
    sql = re.sub(r'SYSUTCDATETIME\s*\(\s*\)', 'CURRENT_TIMESTAMP', sql, flags=re.I)

    top_param = re.search(r'^\s*SELECT\s+TOP\s*\(\s*\?\s*\)\s+', sql, flags=re.I)
    if top_param:
        sql = re.sub(r'^\s*SELECT\s+TOP\s*\(\s*\?\s*\)\s+', 'SELECT ', sql, count=1, flags=re.I)
        if params:
            params = tuple(params[1:]) + (params[0],)
        sql = sql.rstrip().rstrip(';') + ' LIMIT ?'
    else:
        top_literal = re.search(r'^\s*SELECT\s+TOP\s+(\d+)\s+', sql, flags=re.I)
        if top_literal:
            limit = top_literal.group(1)
            sql = re.sub(r'^\s*SELECT\s+TOP\s+\d+\s+', 'SELECT ', sql, count=1, flags=re.I)
            sql = sql.rstrip().rstrip(';') + f' LIMIT {limit}'

    if re.search(r'OUTPUT\s+INSERTED\.id', sql, flags=re.I):
        sql = re.sub(r'\s*OUTPUT\s+INSERTED\.id\s*', ' ', sql, flags=re.I)
        sql = sql.rstrip().rstrip(';') + ' RETURNING id'

    return _convert_placeholders(sql), params


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


def get_db_connection():
    if using_postgres():
        if psycopg2 is None:
            raise RuntimeError('psycopg2-binary is required when DB_ENGINE=postgres')
        if not settings.postgres_connection_string:
            raise RuntimeError('POSTGRES_CONNECTION_STRING or SUPABASE_DB_URL is required when DB_ENGINE=postgres')
        return PostgresConnection(psycopg2.connect(settings.postgres_connection_string))
    return pyodbc.connect(settings.db_connection_string)
