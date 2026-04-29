import pyodbc

from config import settings


def get_db_connection():
    return pyodbc.connect(settings.db_connection_string)
