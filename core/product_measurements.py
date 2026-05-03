"""Product flat measurements (garment grid) and footwear EU + insole cm — JSON in ProductMeasurements.payload_json."""
import json
import logging
import re
import threading
import time

logger = logging.getLogger(__name__)

_measurement_idle_lock = threading.Lock()
_measurement_idle_last_ts = 0.0
_MEASUREMENT_IDLE_MIN_SEC = 75.0

FOOTWEAR_ITEM_SLUGS = frozenset({'boots', 'flats', 'footwear', 'heels', 'pumps'})

# Примерные см по стельке для EU (для автозаполнения в бэкфилле)
_EU_INSOLE_CM = {
    35: '22.5', 36: '23.0', 37: '23.5', 38: '24.0', 39: '25.0', 40: '26.2',
    41: '26.9', 42: '27.5', 43: '28.2', 44: '28.9', 45: '29.6',
}


def is_footwear_item_category(slug):
    return str(slug or '').strip().lower() in FOOTWEAR_ITEM_SLUGS


def parse_measurements_payload(raw):
    """
    Accepts JSON string or dict.
    Garment: {"kind":"garment","columns":["S","M"],"rows":[{"en":"…","ru":"…","values":[1,2]}]}
    Footwear: {"kind":"footwear","rows":[{"eu":"40","insole_cm":"26.2"}]}
    """
    if raw is None:
        return None
    if isinstance(raw, dict):
        data = raw
    else:
        s = str(raw).strip()
        if not s:
            return None
        try:
            data = json.loads(s)
        except json.JSONDecodeError:
            logger.warning('Invalid measurements payload JSON')
            return None
    if not isinstance(data, dict):
        return None
    kind = str(data.get('kind') or '').strip().lower()
    if kind == 'footwear':
        rows = data.get('rows')
        if not isinstance(rows, list) or not rows:
            return None
        out_rows = []
        for r in rows:
            if not isinstance(r, dict):
                continue
            eu = str(r.get('eu') or '').strip()
            ins = str(r.get('insole_cm') or '').strip()
            if eu or ins:
                out_rows.append({'eu': eu, 'insole_cm': ins})
        if not out_rows:
            return None
        return {'kind': 'footwear', 'rows': out_rows}
    if kind == 'garment':
        cols = data.get('columns')
        rows = data.get('rows')
        if not isinstance(cols, list) or not cols or not isinstance(rows, list) or not rows:
            return None
        cols = [str(c).strip() for c in cols if str(c).strip()]
        out_rows = []
        for r in rows:
            if not isinstance(r, dict):
                continue
            vals = r.get('values')
            if not isinstance(vals, list):
                continue
            out_rows.append({
                'en': str(r.get('en') or '').strip(),
                'ru': str(r.get('ru') or '').strip(),
                'values': vals,
            })
        if not cols or not out_rows:
            return None
        return {'kind': 'garment', 'columns': cols, 'rows': out_rows}
    return None


def row_label(row, lang):
    lang = (lang or 'en').lower()
    if lang == 'ru':
        return row.get('ru') or row.get('en') or ''
    return row.get('en') or row.get('ru') or ''


def enrich_product_dict(d, measurements_json):
    """Mutates dict: measurements_json (str|None), measurements (parsed|None)."""
    mj = measurements_json
    if mj is not None and not isinstance(mj, str):
        try:
            mj = json.dumps(mj)
        except (TypeError, ValueError):
            mj = None
    d['measurements_json'] = mj
    d['measurements'] = parse_measurements_payload(mj)


def _garment_demo(columns, seed=0):
    """Таблица замеров одежды/аксессуаров: columns — подписи размеров из БД."""
    cols = [str(c).strip() for c in (columns or []) if str(c).strip()]
    if not cols:
        cols = ['OS']
    n = len(cols)
    base = 100 + (seed % 7) * 2

    def spread(start, step):
        out = []
        for i in range(n):
            out.append(start + i * step)
        return out

    return {
        'kind': 'garment',
        'columns': cols,
        'rows': [
            {'en': 'Length (cm)', 'ru': 'Длина (см)', 'values': spread(base, 2)},
            {'en': 'Chest / width (cm)', 'ru': 'Грудь / ширина (см)', 'values': spread(48 + (seed % 5), 2)},
            {'en': 'Sleeve / rise (cm)', 'ru': 'Рукав / шаговый шов (см)', 'values': spread(58 + (seed % 4), 1)},
        ],
    }


def _footwear_demo_from_sizes(size_labels):
    rows = []
    for raw in size_labels or []:
        s = str(raw).strip()
        m = re.search(r'(\d{2})', s)
        if not m:
            continue
        eu = int(m.group(1))
        if eu < 34 or eu > 46:
            continue
        ins = _EU_INSOLE_CM.get(eu, '')
        rows.append({'eu': str(eu), 'insole_cm': ins or '—'})
    if not rows:
        rows = [
            {'eu': '39', 'insole_cm': _EU_INSOLE_CM.get(39, '25.0')},
            {'eu': '40', 'insole_cm': _EU_INSOLE_CM.get(40, '26.2')},
            {'eu': '41', 'insole_cm': _EU_INSOLE_CM.get(41, '26.9')},
        ]
    return {'kind': 'footwear', 'rows': rows}


def default_measurements_payload(item_category, size_labels, *, product_id=0):
    """
    Демо-замеры для бэкфилла: по категории вещи и списку размеров из ProductSizes.
    Возвращает dict для JSON или None если нечего записать.
    """
    slug = str(item_category or '').strip().lower()
    sizes = [str(x).strip() for x in (size_labels or []) if str(x).strip()]
    if is_footwear_item_category(slug):
        data = _footwear_demo_from_sizes(sizes)
    else:
        data = _garment_demo(sizes, seed=int(product_id or 0))
    return data if parse_measurements_payload(data) else None


def upsert_product_measurement(cur, product_id, payload):
    """
    Записывает или обновляет строку в ProductMeasurements.
    payload: None / '' — удалить строку; dict или JSON-строка — сохранить (с валидацией).
    """
    pid = int(product_id)
    if payload is None:
        cur.execute('DELETE FROM ProductMeasurements WHERE product_id = ?', (pid,))
        return
    if isinstance(payload, str):
        s = payload.strip()
        if not s:
            cur.execute('DELETE FROM ProductMeasurements WHERE product_id = ?', (pid,))
            return
        parsed = parse_measurements_payload(s)
    elif isinstance(payload, dict):
        parsed = parse_measurements_payload(payload)
    else:
        parsed = None
    if not parsed:
        raise ValueError('invalid_measurements_json')
    js = json.dumps(parsed, ensure_ascii=False)
    cur.execute(
        """
        INSERT INTO ProductMeasurements (product_id, payload_json)
        VALUES (?, ?)
        ON CONFLICT (product_id) DO UPDATE SET payload_json = EXCLUDED.payload_json
        """,
        (pid, js),
    )


def migrate_legacy_measurements_to_table(cur):
    """Переносит непустой legacy Products.measurements_json в ProductMeasurements (по одному товару)."""
    cur.execute(
        """
        SELECT p.id, p.measurements_json
        FROM Products p
        WHERE p.measurements_json IS NOT NULL
          AND TRIM(COALESCE(p.measurements_json, '')) <> ''
          AND NOT EXISTS (SELECT 1 FROM ProductMeasurements m WHERE m.product_id = p.id)
        """
    )
    n = 0
    for row in cur.fetchall():
        pid = int(row.id)
        raw = getattr(row, 'measurements_json', None)
        if raw is None and isinstance(row, (list, tuple)) and len(row) > 1:
            raw = row[1]
        parsed = parse_measurements_payload(raw)
        if not parsed:
            continue
        upsert_product_measurement(cur, pid, parsed)
        n += 1
    if n:
        logger.info('Migrated legacy measurements to ProductMeasurements for %s products', n)
    return n


def sync_missing_product_measurements(cur):
    """
    Для товаров без строки в ProductMeasurements подставляет демо-замеры по размерам.
    Возвращает число вставленных/обновлённых строк.
    """
    cur.execute(
        """
        SELECT p.id, p.item_category
        FROM Products p
        WHERE NOT EXISTS (SELECT 1 FROM ProductMeasurements m WHERE m.product_id = p.id)
        ORDER BY p.id
        """
    )
    rows = cur.fetchall()
    updated = 0
    for row in rows:
        pid = int(row.id)
        ic = getattr(row, 'item_category', None)
        cur.execute(
            'SELECT size_label FROM ProductSizes WHERE product_id = ? ORDER BY id',
            (pid,),
        )
        sz_rows = cur.fetchall()
        sizes = []
        for sr in sz_rows:
            lbl = getattr(sr, 'size_label', None)
            if lbl is None and isinstance(sr, (list, tuple)) and sr:
                lbl = sr[0]
            if lbl:
                sizes.append(str(lbl).strip())
        payload = default_measurements_payload(ic, sizes, product_id=pid)
        if not payload:
            continue
        upsert_product_measurement(cur, pid, payload)
        updated += 1
    if updated:
        logger.info('Filled ProductMeasurements for %s products', updated)
    return updated


def idle_backfill_missing_measurements():
    """
    Дешёвая проверка + бэкапл: вызывается из Flask before_request (не каждый запрос).
    Нужна, когда после старта воркера в админке добавили товар без замеров.
    """
    global _measurement_idle_last_ts
    now = time.monotonic()
    with _measurement_idle_lock:
        if now - _measurement_idle_last_ts < _MEASUREMENT_IDLE_MIN_SEC:
            return 0
        _measurement_idle_last_ts = now
    try:
        from .db import get_db_connection

        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT 1 FROM Products p
                WHERE NOT EXISTS (SELECT 1 FROM ProductMeasurements m WHERE m.product_id = p.id)
                LIMIT 1
                """
            )
            if cur.fetchone() is None:
                return 0
            n = sync_missing_product_measurements(cur)
            conn.commit()
            return n
    except Exception:
        logger.exception('idle_backfill_missing_measurements failed')
        return 0
