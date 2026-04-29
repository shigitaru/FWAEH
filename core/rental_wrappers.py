"""Thin wrappers around rental_service for DB availability checks."""
from .db import get_db_connection
from .constants import ACTIVE_RENTAL_STATUSES
from services.rental_service import (
    parse_iso_date as rental_parse_iso_date,
    cart_item_period as rental_cart_item_period,
    is_product_available as rental_is_product_available,
)

def _parse_iso_date(raw_value):
    return rental_parse_iso_date(raw_value)


def _cart_item_period(item):
    return rental_cart_item_period(item)


def _is_product_available(product_id, start_date, end_date, *, exclude_order_id=None, conn=None):
    try:
        return rental_is_product_available(
            get_db_connection, ACTIVE_RENTAL_STATUSES, product_id, start_date, end_date, exclude_order_id=exclude_order_id
        )
    except Exception:
        return True
