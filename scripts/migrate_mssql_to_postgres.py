"""
Copy the local SQL Server database into Supabase/PostgreSQL.

Run from rental_app after creating the Supabase project and setting:
    DB_ENGINE=postgres
    POSTGRES_CONNECTION_STRING=...

The source stays your local SQL Server from DB_CONNECTION_STRING.
The target is reset by default. Set MIGRATION_RESET=0 to append instead.
"""
import os
import sys

import pyodbc

_APP_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if _APP_ROOT not in sys.path:
    sys.path.insert(0, _APP_ROOT)

from core.config import settings  # noqa: E402
from core.db import get_db_connection, using_postgres  # noqa: E402
from core.pg_schema import ensure_postgres_schema  # noqa: E402


RESET_TARGET = os.getenv("MIGRATION_RESET", "1").strip().lower() not in ("0", "false", "no")


TABLES = [
    ("Brands", ["id", "name", "slug", "css_class"]),
    (
        "Products",
        [
            "id",
            "brand_id",
            "category",
            "item_category",
            "serial",
            "name",
            "price",
            "max_days",
            "condition_score",
            "material",
            "origin",
            "condition",
            "main_image",
        ],
        ["id", "brand_id", "category", "item_category", "serial", "name", "price", "max_days", "condition_score", "material", "origin", "[condition]", "main_image"],
    ),
    ("ProductImages", ["id", "product_id", "image_url", "sort_order"]),
    ("ProductSizes", ["id", "product_id", "size_label"]),
    ("CampaignSettings", ["id", "intro_en", "intro_ru", "tagline_en", "tagline_ru"]),
    ("CampaignLooks", ["id", "sort_order", "image_url", "ref_text", "location_text"]),
    ("CampaignStories", ["id", "sort_order", "headline_en", "headline_ru", "body_en", "body_ru", "credits_en", "credits_ru"]),
    ("CampaignStoryImages", ["id", "story_id", "sort_order", "image_url"]),
    (
        "AppUsers",
        [
            "id",
            "email",
            "password_hash",
            "display_name",
            "is_admin",
            "is_email_verified",
            "email_verification_code_hash",
            "email_verification_expires_at",
            "email_verification_attempts",
            "level_code",
            "lifetime_orders_count",
            "lifetime_spend_amount",
            "created_at",
        ],
    ),
    ("RentalOrders", ["id", "user_id", "status", "pickup_code", "total_items", "total_price", "rental_start_date", "rental_end_date", "created_at"]),
    (
        "RentalOrderItems",
        [
            "id",
            "order_id",
            "product_id",
            "serial",
            "brand_name",
            "product_name",
            "size_label",
            "rental_days",
            "price_per_day",
            "line_total",
            "image_url",
            "rental_start_date",
            "rental_end_date",
        ],
    ),
    ("RentalOrderReviews", ["id", "order_id", "user_id", "rating", "body", "created_at", "updated_at"]),
]

DELETE_ORDER = [
    "RentalOrderReviews",
    "RentalOrderItems",
    "RentalOrders",
    "ProductImages",
    "ProductSizes",
    "Products",
    "Brands",
    "CampaignStoryImages",
    "CampaignStories",
    "CampaignLooks",
    "CampaignSettings",
    "AppUsers",
]

IDENTITY_TABLES = [
    "Brands",
    "Products",
    "ProductImages",
    "ProductSizes",
    "CampaignLooks",
    "CampaignStories",
    "CampaignStoryImages",
    "AppUsers",
    "RentalOrders",
    "RentalOrderItems",
    "RentalOrderReviews",
]


def _rows_from_mssql(source_cur, table_name, columns, source_columns=None):
    source_columns = source_columns or columns
    source_cur.execute(f"SELECT {', '.join(source_columns)} FROM {table_name} ORDER BY id")
    return [tuple(row) for row in source_cur.fetchall()]


def _insert_rows(target_cur, table_name, columns, rows):
    if not rows:
        return 0
    placeholders = ", ".join("?" for _ in columns)
    column_sql = ", ".join(columns)
    sql = f"INSERT INTO {table_name} ({column_sql}) VALUES ({placeholders})"
    for row in rows:
        normalized_row = tuple(int(value) if isinstance(value, bool) else value for value in row)
        target_cur.execute(sql, normalized_row)
    return len(rows)


def _reset_target(target_cur):
    for table in DELETE_ORDER:
        target_cur.execute(f"DELETE FROM {table}")


def _refresh_sequences(target_cur):
    for table in IDENTITY_TABLES:
        lower_table = table.lower()
        target_cur.execute(
            f"""
            SELECT setval(
                pg_get_serial_sequence('{lower_table}', 'id'),
                COALESCE((SELECT MAX(id) FROM {table}), 1),
                (SELECT MAX(id) FROM {table}) IS NOT NULL
            )
            """
        )


def main():
    if not using_postgres():
        raise SystemExit("Set DB_ENGINE=postgres before running this script.")
    if not settings.postgres_connection_string:
        raise SystemExit("Set POSTGRES_CONNECTION_STRING or SUPABASE_DB_URL first.")

    ensure_postgres_schema()
    with pyodbc.connect(settings.db_connection_string) as source_conn:
        source_cur = source_conn.cursor()
        with get_db_connection() as target_conn:
            target_cur = target_conn.cursor()
            if RESET_TARGET:
                _reset_target(target_cur)
            for table_spec in TABLES:
                table_name = table_spec[0]
                columns = table_spec[1]
                source_columns = table_spec[2] if len(table_spec) > 2 else None
                try:
                    rows = _rows_from_mssql(source_cur, table_name, columns, source_columns)
                except Exception as exc:
                    print(f"Skipped {table_name}: {exc}")
                    continue
                copied = _insert_rows(target_cur, table_name, columns, rows)
                print(f"Copied {copied} rows into {table_name}.")
            _refresh_sequences(target_cur)
            target_conn.commit()
    print("Migration complete.")


if __name__ == "__main__":
    main()
