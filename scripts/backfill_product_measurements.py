"""
Вручную проставить замеры (редко нужно): при обычном запуске приложения это уже делает ensure_postgres_schema + фоновая подстановка по запросам.

    python scripts/backfill_product_measurements.py
"""
import json
import os
import sys

_APP_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
if _APP_ROOT not in sys.path:
    sys.path.insert(0, _APP_ROOT)

from core.config import settings  # noqa: E402
from core.db import get_db_connection  # noqa: E402
from core.pg_schema import ensure_postgres_schema  # noqa: E402
from core.product_measurements import migrate_legacy_measurements_to_table, sync_missing_product_measurements  # noqa: E402


def main():
    if not settings.postgres_connection_string:
        raise SystemExit('Set POSTGRES_CONNECTION_STRING or SUPABASE_DB_URL first.')
    ensure_postgres_schema()
    with get_db_connection() as conn:
        cur = conn.cursor()
        legacy = migrate_legacy_measurements_to_table(cur)
        synced = sync_missing_product_measurements(cur)
        conn.commit()
    print(json.dumps({'legacy_migrated': legacy, 'synced_defaults': synced}, ensure_ascii=False))


if __name__ == '__main__':
    main()
