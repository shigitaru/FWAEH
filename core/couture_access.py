"""Couture viewing and rental access rules."""

from .constants import LOYALTY_LEVELS
from .loyalty import loyalty_level_rank

COUTURE_CATEGORY = 'couture'


def is_couture_product(product):
    return str((product or {}).get('category') or '').strip().lower() == COUTURE_CATEGORY


def couture_minimum_level():
    return next((lvl for lvl in LOYALTY_LEVELS if lvl.get('couture_access')), LOYALTY_LEVELS[-1])


def couture_level_context():
    level = couture_minimum_level()
    return {
        'tier': level.get('title') or level.get('code') or 'Gold',
        'orders': int(level.get('min_orders') or 0),
        'spend': int(level.get('min_spend') or 0),
    }


def user_can_rent_couture(user):
    if not user:
        return False
    if user.get('is_admin'):
        return True
    threshold = loyalty_level_rank(couture_minimum_level().get('code'))
    return loyalty_level_rank(user.get('level_code')) >= threshold


def can_rent_product(user, product):
    if not is_couture_product(product):
        return True
    return user_can_rent_couture(user)


def couture_gate_message_key(user, *, surface='product'):
    if surface == 'checkout':
        return 'acc_couture_loyalty_required'
    if not user:
        return 'acc_couture_cart_login' if surface == 'cart' else 'acc_couture_product_guest_hint'
    return 'acc_couture_cart_loyalty' if surface == 'cart' else 'acc_couture_product_tier_hint'


def format_couture_message(t, key):
    return t(key).format(**couture_level_context())
