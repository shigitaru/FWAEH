"""Collection listing request context (filters, brands, clear URL)."""
from flask import request, url_for

from .catalog import filter_products, get_brands
from .constants import CONDITION_LABELS, ITEM_CATEGORY_SLUGS


def _collection_listing_data(for_home=False):
    # Текстовый поиск только на /search; в «Подборе» каталога поля q нет
    brand = request.args.get('brand', '').strip()
    item_cat_arg = (request.args.get('item_category') or '').strip()
    active_item_category = item_cat_arg if item_cat_arg in ITEM_CATEGORY_SLUGS else ''
    min_cond = int(request.args.get('min_condition', 0))
    sort = (request.args.get('sort') or 'id').strip().lower()
    if sort not in ('id', 'price_asc', 'price_desc'):
        sort = 'id'
    max_price_raw = request.args.get('max_price', '').strip()
    max_price = None
    if max_price_raw.isdigit():
        v = int(max_price_raw)
        if v > 0:
            max_price = v
    products = filter_products(
        category='rtw',
        query=None,
        brand=brand or None,
        item_category=active_item_category or None,
        min_condition=min_cond,
        max_price=max_price,
        sort=sort,
    )
    clear_listing_url = url_for('home' if for_home else 'collection')
    has_filters = bool(
        brand or active_item_category or min_cond > 0 or max_price is not None or sort != 'id'
    )
    filter_count = sum(
        1
        for cond in (
            bool(brand),
            bool(active_item_category),
            min_cond > 0,
            max_price is not None,
            sort != 'id',
        )
        if cond
    )
    return {
        'products': products,
        'brands': get_brands(),
        'active_brand': brand,
        'active_item_category': active_item_category,
        'min_condition': min_cond,
        'active_sort': sort,
        'max_price_value': max_price_raw if max_price_raw.isdigit() else '',
        'has_active_filters': has_filters,
        'active_filter_count': filter_count,
        'condition_labels': CONDITION_LABELS,
        'clear_listing_url': clear_listing_url,
    }
