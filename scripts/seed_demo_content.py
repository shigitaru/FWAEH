"""
Восстановить витрину и страницу кампании из seed_defaults.py без удаления БД.

Запуск из папки rental_app:
    python scripts/seed_demo_content.py

Очищает текущие товары (и связанные фото/размеры) и все истории кампании,
затем вставляет только «вшитые» товары (Kiss Heels, Raf bomber, YZY grillz,
Balenciaga jeans, Getaria couture bag) и кампанию по умолчанию. Пользователей (AppUsers) не трогает.
"""
import os
import sys

_APP_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
for p in (_APP_ROOT, _SCRIPTS_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

import pyodbc  # noqa: E402

import init_db  # noqa: E402
from seed_defaults import wired_demo_products  # noqa: E402


def main():
    with pyodbc.connect(init_db.APP_CONN_STR, autocommit=True) as conn:
        cur = conn.cursor()
        init_db.apply_demo_seed(cur, reset=True, products=wired_demo_products())
    print("Demo catalog (wired products) and campaign restored from seed_defaults.py.")


if __name__ == "__main__":
    main()
