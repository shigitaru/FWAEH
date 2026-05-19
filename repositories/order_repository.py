from datetime import datetime, timedelta, timezone

from core.db import get_db_connection

ORDER_CANCEL_WINDOW = timedelta(hours=1)


def _utc_now():
    return datetime.now(timezone.utc)


def _as_utc(dt):
    if dt is None:
        return None
    if getattr(dt, 'tzinfo', None) is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def order_cancel_allowed(status, created_at=None, confirmed_at=None):
    """
    User may cancel:
    - while status is 'created' (before admin confirmation), at any time;
    - while status is 'confirmed', within one hour of confirmation.
    """
    status = (status or 'created').strip().lower()
    if status == 'created':
        return True
    if status == 'confirmed':
        confirmed = _as_utc(confirmed_at)
        if confirmed is None:
            return False
        return _utc_now() - confirmed <= ORDER_CANCEL_WINDOW
    return False


def try_cancel_user_order(order_id, user_id):
    """
    Cancel an order for the owning user when order_cancel_allowed applies.
    Returns 'ok', 'not_found', or 'not_allowed'.
    """
    oid = int(order_id)
    uid = int(user_id)
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, status, created_at, confirmed_at
            FROM RentalOrders
            WHERE id = ? AND user_id = ?
            """,
            (oid, uid),
        )
        row = cur.fetchone()
        if not row:
            return 'not_found'
        status = (row[1] or 'created').strip().lower()
        if not order_cancel_allowed(status, row[2], row[3]):
            return 'not_allowed'
        cur.execute("UPDATE RentalOrders SET status = 'cancelled' WHERE id = ?", (oid,))
        conn.commit()
    return 'ok'


def fetch_account_order_detail(order_id, user_id):
    """Return order dict with items or None if not found."""
    oid = int(order_id)
    uid = int(user_id)
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, status, total_items, total_price, rental_start_date, rental_end_date, created_at, pickup_code, confirmed_at
            FROM RentalOrders
            WHERE id = ? AND user_id = ?
            """,
            (oid, uid),
        )
        row = cur.fetchone()
        if not row:
            return None
        cur.execute(
            """
            SELECT serial, brand_name, product_name, size_label, rental_days, line_total, image_url
            FROM RentalOrderItems
            WHERE order_id = ?
            ORDER BY id ASC
            """,
            (oid,),
        )
        items = [
            {
                'serial': x[0] or '',
                'brand_name': x[1] or '',
                'product_name': x[2] or '',
                'size_label': x[3] or '',
                'rental_days': int(x[4] or 0),
                'line_total': int(x[5] or 0),
                'image_url': x[6] or '',
            }
            for x in cur.fetchall()
        ]
    status = (row[1] or 'created').strip().lower()
    created_at = row[6]
    confirmed_at = row[8]
    return {
        'id': int(row[0]),
        'status': status,
        'total_items': int(row[2] or 0),
        'total_price': int(row[3] or 0),
        'rental_start_date': row[4],
        'rental_end_date': row[5],
        'created_at': created_at,
        'pickup_code': row[7] or '',
        'confirmed_at': confirmed_at,
        'items': items,
        'can_cancel': order_cancel_allowed(status, created_at, confirmed_at),
    }


def fetch_order_status_for_user(order_id, user_id):
    """Return normalized status string or None."""
    oid = int(order_id)
    uid = int(user_id)
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT status
            FROM RentalOrders
            WHERE id = ? AND user_id = ?
            """,
            (oid, uid),
        )
        row = cur.fetchone()
    if not row:
        return None
    return (row[0] or 'created').strip().lower()


def fetch_user_loyalty_counters(user_id):
    """Return (lifetime_orders_count, lifetime_spend_amount) or (0, 0)."""
    uid = int(user_id)
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT lifetime_orders_count, lifetime_spend_amount
            FROM AppUsers
            WHERE id = ?
            """,
            (uid,),
        )
        row = cur.fetchone()
    if not row:
        return 0, 0
    return int(row[0] or 0), int(row[1] or 0)
