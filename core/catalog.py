"""Product catalog: DB queries with in-memory fallback."""
import logging

from .db import get_db_connection

from datetime import date, timedelta

from .constants import ACTIVE_RENTAL_STATUSES, BRANDS, PRODUCTS, _resolve_brand_css

logger = logging.getLogger(__name__)


def _search_rank(product, query):
    q = (query or '').strip().lower()
    if not q:
        return 99
    fields = {
        'serial': str(product.get('serial') or '').lower(),
        'name': str(product.get('name') or '').lower(),
        'brand': str(product.get('brand') or '').lower(),
        'material': str(product.get('material') or '').lower(),
        'origin': str(product.get('origin') or '').lower(),
        'condition': str(product.get('condition') or '').lower(),
        'item_category': str(product.get('item_category') or '').lower(),
    }
    if fields['serial'] == q:
        return 0
    if fields['name'] == q:
        return 1
    if fields['name'].startswith(q):
        return 2
    if fields['brand'] == q or fields['brand'].startswith(q):
        return 3
    if q in fields['serial']:
        return 4
    if q in fields['name']:
        return 5
    if q in fields['brand']:
        return 6
    if any(q in fields[key] for key in ('material', 'origin', 'condition', 'item_category')):
        return 7
    return 99

def _attach_related_data(products, conn=None):
    if not products:
        return
    ids = [p['id'] for p in products]
    placeholders = ','.join('?' for _ in ids)

    def _load(cur):
        cur.execute(
            f'SELECT product_id, image_url FROM ProductImages WHERE product_id IN ({placeholders}) ORDER BY sort_order, id',
            ids,
        )
        img_map = {}
        for row in cur.fetchall():
            img_map.setdefault(row.product_id, []).append(row.image_url)
        cur.execute(
            f'SELECT product_id, size_label FROM ProductSizes WHERE product_id IN ({placeholders}) ORDER BY id',
            ids,
        )
        size_map = {}
        for row in cur.fetchall():
            size_map.setdefault(row.product_id, []).append(row.size_label)
        return img_map, size_map

    if conn is not None:
        img_map, size_map = _load(conn.cursor())
    else:
        with get_db_connection() as c:
            img_map, size_map = _load(c.cursor())
    for p in products:
        p['images'] = img_map.get(p['id'], [p['image']])
        p['sizes'] = size_map.get(p['id'], p.get('sizes', []))


def _attach_availability_badges(products, selected_start=None, selected_end=None, conn=None):
    if not products:
        return
    today = date.today()
    selected_mode = bool(selected_start and selected_end)
    try:
        ids = [int(p['id']) for p in products]
        placeholders = ','.join('?' for _ in ids)
        statuses = tuple(ACTIVE_RENTAL_STATUSES)
        status_placeholders = ','.join('?' for _ in statuses)

        def _load_periods(cur):
            cur.execute(
                f"""
                SELECT i.product_id, i.rental_start_date, i.rental_end_date
                FROM RentalOrderItems i
                INNER JOIN RentalOrders o ON o.id = i.order_id
                WHERE i.product_id IN ({placeholders})
                  AND o.status IN ({status_placeholders})
                  AND i.rental_end_date > ?
                  AND i.rental_start_date < ?
                """,
                (*ids, *statuses, today, today + timedelta(days=14)),
            )
            periods = {}
            for row in cur.fetchall():
                periods.setdefault(int(row[0]), []).append((row[1], row[2]))
            return periods

        if conn is not None:
            periods = _load_periods(conn.cursor())
        else:
            with get_db_connection() as c:
                periods = _load_periods(c.cursor())
        for product in products:
            pid = int(product.get('id') or 0)
            rows = periods.get(pid, [])
            if selected_mode:
                unavailable = any(start < selected_end and end > selected_start for start, end in rows)
                product['availability_badge'] = 'unavailable_dates' if unavailable else 'available_now'
            elif any(start <= today and end > today for start, end in rows):
                product['availability_badge'] = 'booked_soon'
            elif rows:
                product['availability_badge'] = 'booked_soon'
            else:
                product['availability_badge'] = 'available_now'
    except Exception:
        logger.exception('Failed to attach availability badges')
        for product in products:
            product.setdefault('availability_badge', 'available_now')

def get_brands():
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute('SELECT name, slug, css_class FROM Brands ORDER BY name')
            rows = cur.fetchall()
        out = []
        for r in rows:
            name = r.name
            raw_slug = getattr(r, 'slug', None)
            slug = (raw_slug or '').strip() or name
            db_css = getattr(r, 'css_class', None)
            out.append({
                'name': name,
                'slug': slug,
                'css_class': _resolve_brand_css(name, db_css),
            })
        return out
    except Exception:
        logger.exception('Failed to load brands from database; using fallback brands')
        return [dict(b, css_class=_resolve_brand_css(b['name'], b.get('css_class'))) for b in BRANDS]


def get_admin_brands():
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT b.id, b.name, b.slug, b.css_class, COUNT(p.id) AS products_count
                FROM Brands b
                LEFT JOIN Products p ON p.brand_id = b.id
                GROUP BY b.id, b.name, b.slug, b.css_class
                ORDER BY b.name
                """
            )
            rows = cur.fetchall()
        out = []
        for r in rows:
            name = r.name
            raw_slug = getattr(r, 'slug', None)
            slug = (raw_slug or '').strip() or name
            db_css = getattr(r, 'css_class', None)
            out.append({
                'id': int(r.id),
                'name': name,
                'slug': slug,
                'css_class': _resolve_brand_css(name, db_css),
                'products_count': int(r.products_count or 0),
            })
        return out
    except Exception:
        logger.exception('Failed to load admin brands')
        return []


def find_products_by_ids(product_ids):
    """Load multiple catalog rows in one round trip; returns dict[id -> product]."""
    ids = []
    for x in product_ids:
        if x is None:
            continue
        try:
            ids.append(int(x))
        except (TypeError, ValueError):
            continue
    ids = list(dict.fromkeys(ids))
    if not ids:
        return {}
    placeholders = ','.join('?' for _ in ids)
    sql = f'''
                SELECT p.id, p.category, p.item_category, p.serial, b.name AS brand, p.name, p.price, p.max_days,
                       p.condition_score, p.material, p.origin, p.condition, p.main_image
                FROM Products p
                JOIN Brands b ON b.id = p.brand_id
                WHERE p.id IN ({placeholders})
                '''
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, ids)
            rows = cur.fetchall()
            products = []
            for row in rows:
                products.append({
                    'id': row.id,
                    'category': row.category,
                    'item_category': getattr(row, 'item_category', None),
                    'serial': row.serial,
                    'brand': row.brand,
                    'name': row.name,
                    'price': row.price,
                    'max_days': row.max_days,
                    'condition_score': row.condition_score,
                    'material': row.material,
                    'origin': row.origin,
                    'condition': row.condition,
                    'image': row.main_image,
                })
            _attach_related_data(products, conn=conn)
            return {p['id']: p for p in products}
    except Exception:
        logger.exception('Failed to batch-load products from database; using fallback catalog')
        qs = []
        for pid in ids:
            p = next((x for x in PRODUCTS if x['id'] == pid), None)
            if p:
                qs.append(dict(p))
        _attach_related_data(qs)
        return {p['id']: p for p in qs}


def find_product(product_id):
    try:
        pid = int(product_id)
    except (TypeError, ValueError):
        return None
    found = find_products_by_ids([pid])
    if pid in found:
        return found[pid]
    return next((p for p in PRODUCTS if p['id'] == pid), None)

def filter_products(
    category=None,
    query=None,
    brand=None,
    item_category=None,
    min_condition=0,
    max_price=None,
    sort='id',
    available_start=None,
    available_end=None,
):
    sort = (sort or 'id').lower()
    if sort not in ('id', 'price_asc', 'price_desc'):
        sort = 'id'
    try:
        sql = '''
            SELECT p.id, p.category, p.item_category, p.serial, b.name AS brand, p.name, p.price, p.max_days,
                   p.condition_score, p.material, p.origin, p.condition, p.main_image
            FROM Products p
            JOIN Brands b ON b.id = p.brand_id
            WHERE 1=1
        '''
        params = []
        if category:
            sql += ' AND p.category = ?'
            params.append(category)
        if item_category:
            sql += ' AND p.item_category = ?'
            params.append(item_category)
        if brand:
            sql += ' AND (LOWER(LTRIM(RTRIM(b.slug))) = LOWER(?) OR b.name LIKE ?)'
            btrim = brand.strip()
            params.append(btrim)
            params.append(f'%{btrim}%')
        if query:
            sql += ' AND (p.name LIKE ? OR p.serial LIKE ? OR b.name LIKE ? OR p.material LIKE ? OR p.origin LIKE ? OR p.condition LIKE ? OR p.item_category LIKE ?)'
            q = f'%{query}%'
            params.extend([q, q, q, q, q, q, q])
        if min_condition > 0:
            sql += ' AND p.condition_score >= ?'
            params.append(min_condition)
        if max_price is not None and max_price > 0:
            sql += ' AND p.price <= ?'
            params.append(max_price)
        if available_start and available_end:
            statuses = tuple(ACTIVE_RENTAL_STATUSES)
            placeholders = ','.join('?' for _ in statuses)
            sql += f"""
                AND NOT EXISTS (
                    SELECT 1
                    FROM RentalOrderItems roi
                    INNER JOIN RentalOrders ro ON ro.id = roi.order_id
                    WHERE roi.product_id = p.id
                      AND ro.status IN ({placeholders})
                      AND roi.rental_start_date < ?
                      AND roi.rental_end_date > ?
                )
            """
            params.extend([*statuses, available_end, available_start])
        if sort == 'price_asc':
            sql += ' ORDER BY p.price ASC, p.id'
        elif sort == 'price_desc':
            sql += ' ORDER BY p.price DESC, p.id'
        elif query:
            sql += '''
                ORDER BY CASE
                    WHEN LOWER(p.serial) = LOWER(?) THEN 0
                    WHEN LOWER(p.name) = LOWER(?) THEN 1
                    WHEN LOWER(p.name) LIKE LOWER(?) THEN 2
                    WHEN LOWER(b.name) = LOWER(?) OR LOWER(b.name) LIKE LOWER(?) THEN 3
                    WHEN LOWER(p.serial) LIKE LOWER(?) THEN 4
                    WHEN LOWER(p.name) LIKE LOWER(?) THEN 5
                    WHEN LOWER(b.name) LIKE LOWER(?) THEN 6
                    ELSE 7
                END,
                p.id
            '''
            qraw = query.strip()
            params.extend([qraw, qraw, f'{qraw}%', qraw, f'{qraw}%', f'%{qraw}%', f'%{qraw}%', f'%{qraw}%'])
        else:
            sql += ' ORDER BY p.id'
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
            results = [{
                'id': row.id,
                'category': row.category,
                'item_category': getattr(row, 'item_category', None),
                'serial': row.serial,
                'brand': row.brand,
                'name': row.name,
                'price': row.price,
                'max_days': row.max_days,
                'condition_score': row.condition_score,
                'material': row.material,
                'origin': row.origin,
                'condition': row.condition,
                'image': row.main_image,
            } for row in rows]
            _attach_related_data(results, conn=conn)
            _attach_availability_badges(results, available_start, available_end, conn=conn)
        return results
    except Exception:
        logger.exception('Failed to filter products from database; using fallback catalog')
        results = PRODUCTS.copy()
        if category:
            results = [p for p in results if p['category'] == category]
        if item_category:
            results = [p for p in results if (p.get('item_category') or '') == item_category]
        if brand:
            bl = brand.strip().lower()
            results = [
                p for p in results
                if bl == p['brand'].lower() or bl in p['brand'].lower()
            ]
        if query:
            q = query.lower()
            text = (
                lambda p: ' '.join(
                    str(p.get(k) or '').lower()
                    for k in ('name', 'serial', 'brand', 'material', 'origin', 'condition', 'item_category')
                )
            )
            results = [
                p for p in results
                if q in text(p)
            ]
        if min_condition > 0:
            results = [p for p in results if p['condition_score'] >= min_condition]
        if max_price is not None and max_price > 0:
            results = [p for p in results if p['price'] <= max_price]
        if sort == 'price_asc':
            results.sort(key=lambda p: (p['price'], p['id']))
        elif sort == 'price_desc':
            results.sort(key=lambda p: (p['price'], p['id']), reverse=True)
        elif query:
            results.sort(key=lambda p: (_search_rank(p, query), p['id']))
        _attach_availability_badges(results, available_start, available_end)
        return results


def get_related_products(product, limit=4):
    if not product:
        return []
    pid = int(product.get('id') or 0)
    category = product.get('category') or ''
    brand = (product.get('brand') or '').strip()
    item_category = (product.get('item_category') or '').strip()
    price = int(product.get('price') or 0)
    price_band = max(50, int(price * 0.25)) if price else 0
    lim = int(limit or 4)
    candidate_cap = max(lim * 6, 24)

    def score(p):
        s = 0
        if (p.get('brand') or '').strip().lower() == brand.lower():
            s += 4
        if item_category and (p.get('item_category') or '') == item_category:
            s += 3
        p_price = int(p.get('price') or 0)
        if price and abs(p_price - price) <= price_band:
            s += 1
        return s

    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                '''
                SELECT p.id, p.category, p.item_category, p.serial, b.name AS brand, p.name, p.price, p.max_days,
                       p.condition_score, p.material, p.origin, p.condition, p.main_image
                FROM Products p
                JOIN Brands b ON b.id = p.brand_id
                WHERE p.category = ? AND p.id <> ?
                ORDER BY (
                    (CASE WHEN LOWER(TRIM(b.name)) = LOWER(?) THEN 4 ELSE 0 END)
                  + (CASE WHEN ? <> '' AND COALESCE(p.item_category, '') = ? THEN 3 ELSE 0 END)
                  + (CASE WHEN ? > 0 AND ABS(p.price - ?) <= ? THEN 1 ELSE 0 END)
                ) DESC,
                p.id
                LIMIT ?
                ''',
                (
                    category,
                    pid,
                    brand,
                    item_category,
                    item_category,
                    price,
                    price,
                    price_band,
                    candidate_cap,
                ),
            )
            rows = cur.fetchall()
            candidates = [{
                'id': row.id,
                'category': row.category,
                'item_category': getattr(row, 'item_category', None),
                'serial': row.serial,
                'brand': row.brand,
                'name': row.name,
                'price': row.price,
                'max_days': row.max_days,
                'condition_score': row.condition_score,
                'material': row.material,
                'origin': row.origin,
                'condition': row.condition,
                'image': row.main_image,
            } for row in rows]
            _attach_related_data(candidates, conn=conn)
    except Exception:
        logger.exception('Failed to load related products from database; using fallback catalog')
        candidates = [dict(p) for p in PRODUCTS if p.get('category') == category and int(p.get('id') or 0) != pid]
        _attach_related_data(candidates)

    ranked = [(score(p), p) for p in candidates if int(p.get('id') or 0) != pid]
    ranked.sort(key=lambda pair: (-pair[0], int(pair[1].get('id') or 0)))
    return [p for s, p in ranked if s > 0][:lim]
