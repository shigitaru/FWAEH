"""Rental order schema, checkout, and admin/history queries."""
from .db import get_db_connection
from repositories.user_repository import update_user_loyalty

from services.rental_service import RentalAvailabilityError

from .rental_wrappers import _cart_item_period, _is_product_available
from .constants import LOYALTY_LEVELS

def ensure_app_users_table():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            IF OBJECT_ID('AppUsers', 'U') IS NULL
            CREATE TABLE AppUsers (
                id INT IDENTITY(1,1) PRIMARY KEY,
                email NVARCHAR(255) NOT NULL UNIQUE,
                password_hash NVARCHAR(500) NOT NULL,
                display_name NVARCHAR(120) NOT NULL,
                is_admin BIT NOT NULL DEFAULT 0,
                is_email_verified BIT NOT NULL DEFAULT 0,
                email_verification_code_hash NVARCHAR(500) NULL,
                email_verification_expires_at DATETIME2 NULL,
                email_verification_attempts INT NOT NULL DEFAULT 0,
                level_code NVARCHAR(30) NOT NULL DEFAULT N'bronze',
                lifetime_orders_count INT NOT NULL DEFAULT 0,
                lifetime_spend_amount INT NOT NULL DEFAULT 0,
                created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
            );
            """
        )
        cur.execute("IF COL_LENGTH('dbo.AppUsers', 'is_admin') IS NULL ALTER TABLE dbo.AppUsers ADD is_admin BIT NOT NULL DEFAULT 0;")
        cur.execute("IF COL_LENGTH('dbo.AppUsers', 'is_email_verified') IS NULL ALTER TABLE dbo.AppUsers ADD is_email_verified BIT NOT NULL DEFAULT 0;")
        cur.execute("IF COL_LENGTH('dbo.AppUsers', 'email_verification_code_hash') IS NULL ALTER TABLE dbo.AppUsers ADD email_verification_code_hash NVARCHAR(500) NULL;")
        cur.execute("IF COL_LENGTH('dbo.AppUsers', 'email_verification_expires_at') IS NULL ALTER TABLE dbo.AppUsers ADD email_verification_expires_at DATETIME2 NULL;")
        cur.execute("IF COL_LENGTH('dbo.AppUsers', 'email_verification_attempts') IS NULL ALTER TABLE dbo.AppUsers ADD email_verification_attempts INT NOT NULL DEFAULT 0;")
        cur.execute("IF COL_LENGTH('dbo.AppUsers', 'level_code') IS NULL ALTER TABLE dbo.AppUsers ADD level_code NVARCHAR(30) NOT NULL DEFAULT N'bronze';")
        cur.execute("IF COL_LENGTH('dbo.AppUsers', 'lifetime_orders_count') IS NULL ALTER TABLE dbo.AppUsers ADD lifetime_orders_count INT NOT NULL DEFAULT 0;")
        cur.execute("IF COL_LENGTH('dbo.AppUsers', 'lifetime_spend_amount') IS NULL ALTER TABLE dbo.AppUsers ADD lifetime_spend_amount INT NOT NULL DEFAULT 0;")
        conn.commit()


def ensure_rental_orders_tables():
    ensure_app_users_table()
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            IF OBJECT_ID('RentalOrders', 'U') IS NULL
            CREATE TABLE RentalOrders (
                id INT IDENTITY(1,1) PRIMARY KEY,
                user_id INT NOT NULL,
                status NVARCHAR(30) NOT NULL DEFAULT N'created',
                pickup_code NVARCHAR(40) NULL,
                total_items INT NOT NULL,
                total_price INT NOT NULL,
                rental_start_date DATE NULL,
                rental_end_date DATE NULL,
                created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
                CONSTRAINT FK_RentalOrders_AppUsers FOREIGN KEY (user_id) REFERENCES AppUsers(id) ON DELETE CASCADE
            );
            """
        )
        cur.execute(
            """
            IF OBJECT_ID('RentalOrderItems', 'U') IS NULL
            CREATE TABLE RentalOrderItems (
                id INT IDENTITY(1,1) PRIMARY KEY,
                order_id INT NOT NULL,
                product_id INT NULL,
                serial NVARCHAR(50) NOT NULL,
                brand_name NVARCHAR(120) NOT NULL,
                product_name NVARCHAR(180) NOT NULL,
                size_label NVARCHAR(40) NULL,
                rental_days INT NOT NULL,
                price_per_day INT NOT NULL,
                line_total INT NOT NULL,
                image_url NVARCHAR(500) NULL,
                rental_start_date DATE NULL,
                rental_end_date DATE NULL,
                CONSTRAINT FK_RentalOrderItems_Order FOREIGN KEY (order_id) REFERENCES RentalOrders(id) ON DELETE CASCADE
            );
            """
        )
        cur.execute(
            """
            IF COL_LENGTH('dbo.RentalOrders', 'rental_start_date') IS NULL
                ALTER TABLE dbo.RentalOrders ADD rental_start_date DATE NULL;
            """
        )
        cur.execute(
            """
            IF COL_LENGTH('dbo.RentalOrders', 'pickup_code') IS NULL
                ALTER TABLE dbo.RentalOrders ADD pickup_code NVARCHAR(40) NULL;
            """
        )
        cur.execute(
            """
            IF COL_LENGTH('dbo.RentalOrders', 'rental_end_date') IS NULL
                ALTER TABLE dbo.RentalOrders ADD rental_end_date DATE NULL;
            """
        )
        cur.execute(
            """
            IF COL_LENGTH('dbo.RentalOrderItems', 'rental_start_date') IS NULL
                ALTER TABLE dbo.RentalOrderItems ADD rental_start_date DATE NULL;
            """
        )
        cur.execute(
            """
            IF COL_LENGTH('dbo.RentalOrderItems', 'rental_end_date') IS NULL
                ALTER TABLE dbo.RentalOrderItems ADD rental_end_date DATE NULL;
            """
        )
        cur.execute(
            """
            UPDATE RentalOrders
            SET status = N'created'
            WHERE status IS NULL OR LTRIM(RTRIM(status)) = N'';
            """
        )
        cur.execute(
            """
            ;WITH totals AS (
                SELECT order_id, COALESCE(SUM(line_total), 0) AS sum_total
                FROM RentalOrderItems
                GROUP BY order_id
            )
            UPDATE o
            SET o.total_price = t.sum_total
            FROM RentalOrders o
            INNER JOIN totals t ON t.order_id = o.id
            WHERE COALESCE(o.total_price, 0) = 0 AND t.sum_total > 0;
            """
        )
        conn.commit()


def ensure_legacy_balenciaga_coture_brand_rename():
    """Переименовать бренд Balenciaga Coture → Balenciaga Couture в уже существующей БД."""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT OBJECT_ID('dbo.Brands', 'U')")
            if cur.fetchone()[0] is None:
                return
            cur.execute("SELECT 1 FROM Brands WHERE name = ?", ("Balenciaga Coture",))
            if not cur.fetchone():
                return
            cur.execute("SELECT 1 FROM Brands WHERE name = ?", ("Balenciaga Couture",))
            if cur.fetchone():
                return
            cur.execute(
                "UPDATE Brands SET name = ?, slug = ? WHERE name = ?",
                ("Balenciaga Couture", "Balenciaga Couture", "Balenciaga Coture"),
            )
            cur.execute("SELECT OBJECT_ID('dbo.RentalOrderItems', 'U')")
            if cur.fetchone()[0] is not None:
                cur.execute(
                    "UPDATE RentalOrderItems SET brand_name = ? WHERE brand_name = ?",
                    ("Balenciaga Couture", "Balenciaga Coture"),
                )
            conn.commit()
    except Exception:
        pass


def _create_rental_order(user_id, cart_items, discount_percent=0):
    if not cart_items:
        return None
    ensure_rental_orders_tables()
    try:
        discount_percent = int(discount_percent or 0)
    except Exception:
        discount_percent = 0
    discount_percent = max(0, min(100, discount_percent))
    normalized_items = []
    unavailable = []
    for item in cart_items:
        start, end, days = _cart_item_period(item)
        product_id = int(item.get('product_id')) if item.get('product_id') is not None else None
        if not _is_product_available(product_id, start, end):
            unavailable.append(str(item.get('serial') or product_id or 'item'))
        normalized_items.append((item, start, end, days))
    if unavailable:
        raise RentalAvailabilityError(', '.join(unavailable))
    total_price = 0
    total_items = len(cart_items)
    rental_start = min(start for _, start, _, _ in normalized_items)
    rental_end = max(end for _, _, end, _ in normalized_items)
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO RentalOrders (user_id, status, total_items, total_price, rental_start_date, rental_end_date)
            OUTPUT INSERTED.id
            VALUES (?, N'created', ?, ?, ?, ?)
            """,
            (int(user_id), total_items, total_price, rental_start, rental_end),
        )
        row = cur.fetchone()
        order_id = int(row[0]) if row and row[0] is not None else None
        if not order_id:
            conn.rollback()
            return None
        for item, start, end, days in normalized_items:
            price_per_day = int(item.get('price_per_day', 0) or 0)
            line_total_raw = price_per_day * days
            line_total = int(round(line_total_raw * (100 - discount_percent) / 100.0))
            total_price += line_total
            cur.execute(
                """
                INSERT INTO RentalOrderItems (
                    order_id, product_id, serial, brand_name, product_name, size_label,
                    rental_days, price_per_day, line_total, image_url, rental_start_date, rental_end_date
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    order_id,
                    int(item.get('product_id')) if item.get('product_id') is not None else None,
                    str(item.get('serial') or ''),
                    str(item.get('brand') or ''),
                    str(item.get('name') or ''),
                    (item.get('size') or '').strip() or None,
                    days,
                    price_per_day,
                    line_total,
                    str(item.get('image') or ''),
                    start,
                    end,
                ),
            )
        cur.execute('UPDATE RentalOrders SET total_price = ? WHERE id = ?', (int(total_price), int(order_id)))
        conn.commit()
        return order_id


def _fetch_user_rental_history(user_id, limit=8):
    ensure_rental_orders_tables()
    orders = []
    stats = {
        'orders_count': 0,
        'items_count': 0,
        'total_spend': 0,
        'favorite_brand': '',
    }
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT TOP (?) id, status, total_items, total_price, rental_start_date, rental_end_date, created_at
            FROM RentalOrders
            WHERE user_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (int(limit), int(user_id)),
        )
        order_rows = cur.fetchall()
        if order_rows:
            order_ids = [int(r[0]) for r in order_rows]
            placeholders = ','.join('?' for _ in order_ids)
            cur.execute(
                f"""
                SELECT order_id, serial, brand_name, product_name, size_label, rental_days, line_total, image_url, rental_start_date, rental_end_date
                FROM RentalOrderItems
                WHERE order_id IN ({placeholders})
                ORDER BY order_id DESC, id ASC
                """,
                tuple(order_ids),
            )
            items_by_order = {}
            for row in cur.fetchall():
                oid = int(row[0])
                items_by_order.setdefault(oid, []).append({
                    'serial': row[1] or '',
                    'brand_name': row[2] or '',
                    'product_name': row[3] or '',
                    'size_label': row[4] or '',
                    'rental_days': int(row[5]) if row[5] is not None else 0,
                    'line_total': int(row[6]) if row[6] is not None else 0,
                    'image_url': row[7] or '',
                    'rental_start_date': row[8],
                    'rental_end_date': row[9],
                })
            for row in order_rows:
                oid = int(row[0])
                orders.append({
                    'id': oid,
                    'status': (row[1] or 'created').strip().lower(),
                    'total_items': int(row[2]) if row[2] is not None else 0,
                    'total_price': int(row[3]) if row[3] is not None else 0,
                    'rental_start_date': row[4],
                    'rental_end_date': row[5],
                    'created_at': row[6],
                    'items': items_by_order.get(oid, []),
                })
        cur.execute(
            """
            SELECT
                COUNT(*) AS orders_count,
                COALESCE(SUM(total_items), 0) AS items_count,
                COALESCE(SUM(total_price), 0) AS total_spend
            FROM RentalOrders
            WHERE user_id = ?
            """,
            (int(user_id),),
        )
        base_stats = cur.fetchone()
        if base_stats:
            stats['orders_count'] = int(base_stats[0] or 0)
            stats['items_count'] = int(base_stats[1] or 0)
            stats['total_spend'] = int(base_stats[2] or 0)
        cur.execute(
            """
            SELECT TOP 1 brand_name, COUNT(*) AS c
            FROM RentalOrderItems i
            INNER JOIN RentalOrders o ON o.id = i.order_id
            WHERE o.user_id = ?
            GROUP BY brand_name
            ORDER BY c DESC, brand_name ASC
            """,
            (int(user_id),),
        )
        fav = cur.fetchone()
        if fav and fav[0]:
            stats['favorite_brand'] = str(fav[0])
    return orders, stats


def _user_fetch_by_email(email_norm):
    return fetch_user_by_email(email_norm)


def _user_insert(email_norm, password_plain, display_name):
    return insert_user(email_norm, generate_password_hash(password_plain), display_name)


def _fetch_recent_orders_admin(limit=80):
    ensure_rental_orders_tables()
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT TOP (?) o.id, o.status, o.total_items, o.total_price, o.rental_start_date, o.rental_end_date, o.created_at, u.email, o.pickup_code
            FROM RentalOrders o
            INNER JOIN AppUsers u ON u.id = o.user_id
            ORDER BY o.created_at DESC, o.id DESC
            """,
            (int(limit),),
        )
        rows = cur.fetchall()
        orders = [
            {
                'id': int(r[0]),
                'status': (r[1] or 'created').strip().lower(),
                'total_items': int(r[2] or 0),
                'total_price': int(r[3] or 0),
                'rental_start_date': r[4],
                'rental_end_date': r[5],
                'created_at': r[6],
                'user_email': r[7] or '',
                'pickup_code': r[8] or '',
                'items': [],
            }
            for r in rows
        ]
        if not orders:
            return orders
        order_ids = [o['id'] for o in orders]
        placeholders = ','.join('?' for _ in order_ids)
        cur.execute(
            f"""
            SELECT order_id, serial, brand_name, product_name, rental_days, size_label
            FROM RentalOrderItems
            WHERE order_id IN ({placeholders})
            ORDER BY order_id DESC, id ASC
            """,
            tuple(order_ids),
        )
        items_map = {}
        for item_row in cur.fetchall():
            oid = int(item_row[0])
            items_map.setdefault(oid, []).append(
                {
                    'serial': item_row[1] or '',
                    'brand_name': item_row[2] or '',
                    'product_name': item_row[3] or '',
                    'rental_days': int(item_row[4] or 0),
                    'size_label': item_row[5] or '',
                }
            )
        for order in orders:
            order['items'] = items_map.get(order['id'], [])
    return orders


def _resolve_loyalty_level(orders_count, spend_amount):
    matched = LOYALTY_LEVELS[0]
    for lvl in LOYALTY_LEVELS:
        if orders_count >= lvl['min_orders'] and spend_amount >= lvl['min_spend']:
            matched = lvl
    return matched


def recalculate_user_loyalty(user_id):
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT COUNT(*), COALESCE(SUM(total_price), 0)
            FROM RentalOrders
            WHERE user_id = ? AND status = N'returned'
            """,
            (int(user_id),),
        )
        row = cur.fetchone()
        orders_count = int(row[0] or 0) if row else 0
        spend_amount = int(row[1] or 0) if row else 0
    level = _resolve_loyalty_level(orders_count, spend_amount)
    update_user_loyalty(user_id, level['code'], orders_count, spend_amount)
    return {
        'level_code': level['code'],
        'level_title': level['title'],
        'discount_percent': int(level['discount_percent']),
        'priority_booking': bool(level['priority_booking']),
        'offline_events': bool(level['offline_events']),
        'orders_count': orders_count,
        'spend_amount': spend_amount,
    }
