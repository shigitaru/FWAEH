from datetime import datetime, date, timedelta


class RentalAvailabilityError(Exception):
    pass


class CoutureAccessError(Exception):
    """Cart contains couture items but the user's loyalty tier is too low."""


def parse_iso_date(raw_value):
    try:
        return datetime.strptime(str(raw_value or '').strip(), '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return None


def cart_item_period(item):
    start = parse_iso_date(item.get('start_date'))
    end = parse_iso_date(item.get('end_date'))
    days = int(item.get('days', 0) or 0)
    if start and end and end >= start:
        days = (end - start).days
        if days < 1:
            days = 1
            end = start + timedelta(days=1)
        return start, end, days
    if not start:
        start = date.today()
    if days < 1:
        days = 1
    end = start + timedelta(days=days)
    return start, end, days


def is_product_available(get_db_connection, active_statuses, product_id, start_date, end_date, *, exclude_order_id=None):
    if not product_id or not start_date or not end_date:
        return False
    statuses = tuple(active_statuses)
    placeholders = ','.join('?' for _ in statuses)
    sql = f"""
        SELECT 1
        FROM RentalOrderItems i
        INNER JOIN RentalOrders o ON o.id = i.order_id
        WHERE i.product_id = ?
          AND o.status IN ({placeholders})
          AND i.rental_start_date < ?
          AND i.rental_end_date > ?
    """
    params = [int(product_id), *statuses, end_date, start_date]
    if exclude_order_id is not None:
        sql += " AND o.id <> ?"
        params.append(int(exclude_order_id))
    sql += " LIMIT 1"
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, tuple(params))
        return cur.fetchone() is None
