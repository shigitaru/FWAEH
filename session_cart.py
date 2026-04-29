"""Cart, wishlist, and current user from Flask session."""
import re
from flask import session
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
    return {
        'id': uid_int,
        'email': session.get('user_email') or '',
        'display_name': session.get('user_display_name') or '',
    }


def _clear_user_session():
    for k in ('user_id', 'user_email', 'user_display_name'):
        session.pop(k, None)
    session.modified = True


ACC_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')

