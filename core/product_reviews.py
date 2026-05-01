"""Order reviews: schema and read/write helpers."""
from .db import get_db_connection


def ensure_order_reviews_table():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            IF OBJECT_ID('RentalOrderReviews', 'U') IS NULL
            CREATE TABLE RentalOrderReviews (
                id INT IDENTITY(1,1) PRIMARY KEY,
                order_id INT NOT NULL,
                user_id INT NOT NULL,
                rating INT NOT NULL,
                body NVARCHAR(1000) NULL,
                created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
                updated_at DATETIME2 NULL,
                CONSTRAINT FK_RentalOrderReviews_Order FOREIGN KEY (order_id) REFERENCES RentalOrders(id) ON DELETE CASCADE,
                CONSTRAINT FK_RentalOrderReviews_AppUsers FOREIGN KEY (user_id) REFERENCES AppUsers(id),
                CONSTRAINT UQ_RentalOrderReviews_OrderUser UNIQUE (order_id, user_id)
            );
            """
        )
        conn.commit()


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
