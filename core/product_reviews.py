"""Order reviews: schema and read/write helpers."""
from .db import get_db_connection
from .pg_schema import ensure_postgres_schema


def ensure_order_reviews_table():
    ensure_postgres_schema()


def get_order_review(order_id, user_id):
    if not order_id or not user_id:
        return None
    ensure_order_reviews_table()
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, rating, body
            FROM RentalOrderReviews
            WHERE order_id = ? AND user_id = ?
            """,
            (int(order_id), int(user_id)),
        )
        row = cur.fetchone()
    if not row:
        return None
    return {'id': int(row[0]), 'rating': int(row[1] or 0), 'body': row[2] or ''}


def upsert_order_review(order_id, user_id, rating, body):
    ensure_order_reviews_table()
    rating = max(1, min(5, int(rating or 0)))
    body = (body or '').strip()[:1000]
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id
            FROM RentalOrderReviews
            WHERE order_id = ? AND user_id = ?
            """,
            (int(order_id), int(user_id)),
        )
        existing = cur.fetchone()
        if existing:
            cur.execute(
                """
                UPDATE RentalOrderReviews
                SET rating = ?, body = ?, updated_at = SYSUTCDATETIME()
                WHERE id = ?
                """,
                (rating, body, int(existing[0])),
            )
        else:
            cur.execute(
                """
                INSERT INTO RentalOrderReviews (order_id, user_id, rating, body)
                VALUES (?, ?, ?, ?)
                """,
                (int(order_id), int(user_id), rating, body),
            )
        conn.commit()
