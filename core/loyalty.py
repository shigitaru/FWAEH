"""Loyalty tier lookup, discounts, and progress rules."""

from .constants import LOYALTY_LEVELS

DEFAULT_LOYALTY_CODE = 'bronze'


def normalize_loyalty_code(level_code):
    return (level_code or DEFAULT_LOYALTY_CODE).strip().lower()


def get_loyalty_level(level_code):
    code = normalize_loyalty_code(level_code)
    return next((lvl for lvl in LOYALTY_LEVELS if lvl['code'] == code), LOYALTY_LEVELS[0])


def loyalty_level_rank(level_code):
    code = normalize_loyalty_code(level_code)
    for i, lvl in enumerate(LOYALTY_LEVELS):
        if lvl['code'] == code:
            return i
    return 0


def resolve_loyalty_level(orders_count, spend_amount):
    matched = LOYALTY_LEVELS[0]
    for level in LOYALTY_LEVELS:
        if orders_count >= level['min_orders'] and spend_amount >= level['min_spend']:
            matched = level
    return matched


def loyalty_discount_percent(level_code):
    return int(get_loyalty_level(level_code).get('discount_percent') or 0)


def cart_totals_for_level(subtotal, level_code):
    subtotal = int(subtotal or 0)
    discount_percent = loyalty_discount_percent(level_code)
    discount_amount = int(round(subtotal * discount_percent / 100.0))
    return {
        'subtotal': subtotal,
        'discount_percent': discount_percent,
        'discount_amount': discount_amount,
        'total': max(0, subtotal - discount_amount),
    }


def next_loyalty_progress(level_code, orders_count, spend_amount):
    current = get_loyalty_level(level_code)
    current_rank = loyalty_level_rank(current.get('code'))
    next_level = None
    for level in LOYALTY_LEVELS[current_rank + 1:]:
        next_level = level
        break
    orders_count = int(orders_count or 0)
    spend_amount = int(spend_amount or 0)
    if not next_level:
        return {
            'is_max': True,
            'current_level': current,
            'next_level': None,
            'orders_count': orders_count,
            'spend_amount': spend_amount,
            'remaining_orders': 0,
            'remaining_spend': 0,
            'percent': 100,
        }
    required_orders = int(next_level.get('min_orders') or 0)
    required_spend = int(next_level.get('min_spend') or 0)
    remaining_orders = max(0, required_orders - orders_count)
    remaining_spend = max(0, required_spend - spend_amount)
    order_progress = 1 if required_orders <= 0 else min(1, orders_count / float(required_orders))
    spend_progress = 1 if required_spend <= 0 else min(1, spend_amount / float(required_spend))
    return {
        'is_max': False,
        'current_level': current,
        'next_level': next_level,
        'orders_count': orders_count,
        'spend_amount': spend_amount,
        'remaining_orders': remaining_orders,
        'remaining_spend': remaining_spend,
        'percent': int(round(min(order_progress, spend_progress) * 100)),
    }
