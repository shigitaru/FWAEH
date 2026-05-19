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
            SELECT id, rating, body, review_status
            FROM RentalOrderReviews
            WHERE order_id = ? AND user_id = ?
            """,
            (int(order_id), int(user_id)),
        )
        row = cur.fetchone()
    if not row:
        return None
    return {
        'id': int(row[0]),
        'rating': int(row[1] or 0),
        'body': row[2] or '',
        'review_status': (row[3] or 'pending').strip().lower(),
    }


def get_product_reviews(product_id, limit=24):
    """Published order reviews for orders that included this product."""
    pid = int(product_id)
    if pid <= 0:
        return []
    ensure_order_reviews_table()
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT r.id, r.rating, r.body, r.created_at, r.updated_at, u.display_name
            FROM RentalOrderReviews r
            INNER JOIN AppUsers u ON u.id = r.user_id
            WHERE EXISTS (
                SELECT 1
                FROM RentalOrderItems roi
                WHERE roi.order_id = r.order_id AND roi.product_id = ?
            )
            AND r.review_status = 'approved'
            ORDER BY COALESCE(r.updated_at, r.created_at) DESC, r.id DESC
            LIMIT ?
            """,
            (pid, int(limit)),
        )
        rows = cur.fetchall()
    out = []
    for row in rows:
        body = (row[2] or '').strip()
        rating = int(row[1] or 0)
        if rating < 1 and not body:
            continue
        out.append({
            'id': int(row[0]),
            'rating': max(1, min(5, rating)) if rating else 0,
            'body': body,
            'created_at': row[3],
            'updated_at': row[4],
            'display_name': row[5] or '',
        })
    return out


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
                SET rating = ?, body = ?, review_status = 'pending', approved_at = NULL, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (rating, body, int(existing[0])),
            )
        else:
            cur.execute(
                """
                INSERT INTO RentalOrderReviews (order_id, user_id, rating, body, review_status)
                VALUES (?, ?, ?, ?, 'pending')
                """,
                (int(order_id), int(user_id), rating, body),
            )
        conn.commit()


def list_pending_reviews_admin(limit=100):
    ensure_order_reviews_table()
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                r.id,
                r.order_id,
                r.rating,
                r.body,
                r.created_at,
                r.updated_at,
                u.display_name,
                u.email,
                STRING_AGG(roi.brand_name || ' - ' || roi.product_name, ', ' ORDER BY roi.id) AS product_names
            FROM RentalOrderReviews r
            INNER JOIN AppUsers u ON u.id = r.user_id
            LEFT JOIN RentalOrderItems roi ON roi.order_id = r.order_id
            WHERE r.review_status = 'pending'
            GROUP BY r.id, r.order_id, r.rating, r.body, r.created_at, r.updated_at, u.display_name, u.email
            ORDER BY COALESCE(r.updated_at, r.created_at) ASC, r.id ASC
            LIMIT ?
            """,
            (int(limit),),
        )
        rows = cur.fetchall()
    return [
        {
            'id': int(row[0]),
            'order_id': int(row[1]),
            'rating': int(row[2] or 0),
            'body': row[3] or '',
            'created_at': row[4],
            'updated_at': row[5],
            'display_name': row[6] or '',
            'email': row[7] or '',
            'product_names': row[8] or '',
        }
        for row in rows
    ]


def set_review_moderation_status(review_id, status):
    clean_status = (status or '').strip().lower()
    if clean_status not in ('approved', 'rejected'):
        raise ValueError('Invalid review status')
    ensure_order_reviews_table()
    approved_at_sql = 'CURRENT_TIMESTAMP' if clean_status == 'approved' else 'NULL'
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            f"""
            UPDATE RentalOrderReviews
            SET review_status = ?, approved_at = {approved_at_sql}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (clean_status, int(review_id)),
        )
        conn.commit()
        return cur.rowcount > 0
