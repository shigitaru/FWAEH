"""Collection listing request context (filters, brands, clear URL)."""
from datetime import date, timedelta

from flask import request, url_for

from .catalog import filter_products, get_brands
from .constants import CONDITION_LABELS, ITEM_CATEGORY_SLUGS


def _parse_brand_slugs():
    rows = get_brands()
    by_key = {}
    for b in rows:
        slug = (b.get('slug') or '').strip()
        if not slug:
            continue
        by_key[slug.lower()] = slug
    chunks = []
    for raw in request.args.getlist('brand'):
        s = (raw or '').strip()
        if not s:
            continue
        if ',' in s:
            chunks.extend(part.strip() for part in s.split(',') if part.strip())
        else:
            chunks.append(s)
    out = []
    seen = set()
    for token in chunks:
        canon = by_key.get(token.strip().lower())
        if canon and canon not in seen:
            seen.add(canon)
            out.append(canon)
    return out


def _parse_item_category_slugs():
    chunks = []
    for raw in request.args.getlist('item_category'):
        s = (raw or '').strip()
        if not s:
            continue
        if ',' in s:
            chunks.extend(part.strip() for part in s.split(',') if part.strip())
        else:
            chunks.append(s)
    out = []
    seen = set()
    for slug in chunks:
        if slug not in ITEM_CATEGORY_SLUGS or slug in seen:
            continue
        seen.add(slug)
        out.append(slug)
    return out


def _collection_listing_data(for_home=False):
    # Текстовый поиск только на /search; в «Подборе» каталога поля q нет
    active_brands = _parse_brand_slugs()
    active_item_categories = _parse_item_category_slugs()
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
    available_start_raw = (request.args.get('available_start') or '').strip()
    available_days_raw = (request.args.get('available_days') or '').strip()
    available_start = None
    available_days = 0
    try:
        if available_start_raw:
            available_start = date.fromisoformat(available_start_raw)
    except Exception:
        available_start = None
    if available_days_raw.isdigit():
        available_days = max(1, min(30, int(available_days_raw)))
    available_end = available_start + timedelta(days=available_days) if available_start and available_days else None
    brands_for_query = active_brands if active_brands else None
    item_categories_for_query = active_item_categories if active_item_categories else None
    products = filter_products(
        category='rtw',
        query=None,
        brand=brands_for_query,
        item_category=item_categories_for_query,
        min_condition=min_cond,
        max_price=max_price,
        sort=sort,
        available_start=available_start,
        available_end=available_end,
    )
    clear_listing_url = url_for('home' if for_home else 'collection')
    has_filters = bool(
        active_brands
        or active_item_categories
        or min_cond > 0
        or max_price is not None
        or sort != 'id'
        or bool(available_start and available_days)
    )
    filter_count = sum(
        1
        for cond in (
            bool(active_brands),
            bool(active_item_categories),
            min_cond > 0,
            max_price is not None,
            sort != 'id',
            bool(available_start and available_days),
        )
        if cond
    )
    return {
        'products': products,
        'brands': get_brands(),
        'active_brands': active_brands,
        'active_brand': active_brands[0] if len(active_brands) == 1 else '',
        'active_item_categories': active_item_categories,
        'active_item_category': active_item_categories[0] if len(active_item_categories) == 1 else '',
        'min_condition': min_cond,
        'active_sort': sort,
        'max_price_value': max_price_raw if max_price_raw.isdigit() else '',
        'available_start_value': available_start.isoformat() if available_start else '',
        'available_days_value': str(available_days) if available_days else '',
        'has_active_filters': has_filters,
        'active_filter_count': filter_count,
        'condition_labels': CONDITION_LABELS,
        'clear_listing_url': clear_listing_url,
    }
