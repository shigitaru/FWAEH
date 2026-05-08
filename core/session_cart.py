"""Cart, wishlist, and current user from Flask session."""
import hashlib
import re
from datetime import datetime, timezone

from flask import session

from core.db import get_db_connection
from services.rental_service import cart_item_period as rental_cart_item_period

def get_cart():
    cart = session.get('cart', [])
    changed = False
    normalized = []
    for item in cart:
        start, end, days = rental_cart_item_period(item)
        price_per_day = int(item.get('price_per_day', 0) or 0)
        total_price = price_per_day * days
        new_start = start.isoformat()
        new_end = end.isoformat()
        if (
            str(item.get('start_date') or '') != new_start
            or str(item.get('end_date') or '') != new_end
            or int(item.get('days', 0) or 0) != days
            or int(item.get('total_price', 0) or 0) != total_price
        ):
            changed = True
        item['start_date'] = new_start
        item['end_date'] = new_end
        item['days'] = days
        item['total_price'] = total_price
        normalized.append(item)
    if changed:
        session['cart'] = normalized
        session.modified = True
    return normalized

def get_cart_count():
    return len(get_cart())

def get_cart_total():
    return sum(item['total_price'] for item in get_cart())


def get_wishlist_ids():
    raw = session.get('wishlist') or []
    out = []
    for x in raw:
        try:
            out.append(int(x))
        except (TypeError, ValueError):
            continue
    return out


def get_current_user():
    uid = session.get('user_id')
    if uid is None:
        return None
    try:
        uid_int = int(uid)
    except (TypeError, ValueError):
        return None
    session_key = session.get('user_session_key')
    session_expires_at_raw = session.get('user_session_expires_at')
    if not session_key or not session_expires_at_raw:
        _clear_user_session()
        return None
    try:
        expires_at = datetime.fromisoformat(str(session_expires_at_raw))
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        _clear_user_session()
        return None
    if datetime.now(timezone.utc) >= expires_at:
        _clear_user_session()
        return None
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT session_key_hash, session_expires_at FROM AppUsers WHERE id = ?",
                (uid_int,),
            )
            row = cur.fetchone()
    except Exception:
        _clear_user_session()
        return None
    if not row:
        _clear_user_session()
        return None
    db_hash = row[0]
    db_expires_at = row[1]
    if not db_hash or not db_expires_at:
        _clear_user_session()
        return None
    if isinstance(db_expires_at, str):
        try:
            db_expires_at = datetime.fromisoformat(db_expires_at)
        except ValueError:
            _clear_user_session()
            return None
    if db_expires_at.tzinfo is None:
        db_expires_at = db_expires_at.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) >= db_expires_at:
        _clear_user_session()
        return None
    if hashlib.sha256(str(session_key).encode('utf-8')).hexdigest() != str(db_hash):
        _clear_user_session()
        return None
    return {
        'id': uid_int,
        'email': session.get('user_email') or '',
        'display_name': session.get('user_display_name') or '',
        'is_admin': bool(session.get('is_admin')),
        'level_code': (session.get('user_level_code') or 'bronze'),
    }


def _clear_user_session():
    for k in (
        'user_id',
        'user_email',
        'user_display_name',
        'is_admin',
        'user_level_code',
        'user_session_key',
        'user_session_expires_at',
    ):
        session.pop(k, None)
    session.modified = True


ACC_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')

