"""Product catalog: DB queries with in-memory fallback."""
from db import get_db_connection

from constants import BRANDS, PRODUCTS, _resolve_brand_css

def _attach_related_data(products):
    if not products:
        return
    ids = [p['id'] for p in products]
    placeholders = ','.join('?' for _ in ids)
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            f'SELECT product_id, image_url FROM ProductImages WHERE product_id IN ({placeholders}) ORDER BY sort_order, id',
            ids
        )
        img_map = {}
        for row in cur.fetchall():
            img_map.setdefault(row.product_id, []).append(row.image_url)
        cur.execute(
            f'SELECT product_id, size_label FROM ProductSizes WHERE product_id IN ({placeholders}) ORDER BY id',
            ids
        )
        size_map = {}
        for row in cur.fetchall():
            size_map.setdefault(row.product_id, []).append(row.size_label)
    for p in products:
        p['images'] = img_map.get(p['id'], [p['image']])
        p['sizes'] = size_map.get(p['id'], p.get('sizes', []))

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
        return []


def find_product(product_id):
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                '''
                SELECT p.id, p.category, p.item_category, p.serial, b.name AS brand, p.name, p.price, p.max_days,
                       p.condition_score, p.material, p.origin, p.[condition], p.main_image
                FROM Products p
                JOIN Brands b ON b.id = p.brand_id
                WHERE p.id = ?
                ''',
                (product_id,)
            )
            row = cur.fetchone()
        if not row:
            return None
        product = {
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
        }
        _attach_related_data([product])
        return product
    except Exception:
        return next((p for p in PRODUCTS if p['id'] == product_id), None)

def filter_products(
    category=None,
    query=None,
    brand=None,
    item_category=None,
    min_condition=0,
    max_price=None,
    sort='id',
):
    sort = (sort or 'id').lower()
    if sort not in ('id', 'price_asc', 'price_desc'):
        sort = 'id'
    try:
        sql = '''
            SELECT p.id, p.category, p.item_category, p.serial, b.name AS brand, p.name, p.price, p.max_days,
                   p.condition_score, p.material, p.origin, p.[condition], p.main_image
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
            sql += ' AND (p.name LIKE ? OR p.serial LIKE ? OR b.name LIKE ? OR p.material LIKE ?)'
            q = f'%{query}%'
            params.extend([q, q, q, q])
        if min_condition > 0:
            sql += ' AND p.condition_score >= ?'
            params.append(min_condition)
        if max_price is not None and max_price > 0:
            sql += ' AND p.price <= ?'
            params.append(max_price)
        if sort == 'price_asc':
            sql += ' ORDER BY p.price ASC, p.id'
        elif sort == 'price_desc':
            sql += ' ORDER BY p.price DESC, p.id'
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
        _attach_related_data(results)
        return results
    except Exception:
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
            mat = (lambda p: (p.get('material') or '').lower())
            results = [
                p for p in results
                if q in p['name'].lower() or q in p['serial'].lower()
                or q in p['brand'].lower() or q in mat(p)
            ]
        if min_condition > 0:
            results = [p for p in results if p['condition_score'] >= min_condition]
        if max_price is not None and max_price > 0:
            results = [p for p in results if p['price'] <= max_price]
        if sort == 'price_asc':
            results.sort(key=lambda p: (p['price'], p['id']))
        elif sort == 'price_desc':
            results.sort(key=lambda p: (p['price'], p['id']), reverse=True)
        return results
