"""Product flat measurements (garment grid) and footwear EU + insole cm — JSON in ProductMeasurements.payload_json."""
import json
import logging
import re

from flask import has_request_context

logger = logging.getLogger(__name__)


def _coerce_measurement_cell(raw):
    s = str(raw or '').strip()
    if not s:
        return ''
    try:
        if re.match(r'^-?\d+$', s):
            return int(s)
        if re.match(r'^-?\d+\.\d+$', s):
            return float(s)
    except ValueError:
        pass
    return s


def _garment_meas_row_indices(form):
    if not hasattr(form, 'keys'):
        return []
    ix = set()
    for k in form.keys():
        ks = str(k)
        m = re.match(r'^garment_meas_(\d+)_(?:label|en|ru)$', ks)
        if m:
            ix.add(int(m.group(1)))
    return sorted(ix)


def parse_measurements_from_admin_form(form, size_columns):
    kind = (form.get('measurements_kind') or 'none').strip().lower()
    if kind == 'none' or kind not in ('garment', 'footwear'):
        return None
    if kind == 'footwear':
        eus = form.getlist('footwear_meas_eu')
        tins = form.getlist('footwear_meas_insole')
        rows_out = []
        for eu, inch in zip(eus, tins):
            eu_s = str(eu or '').strip()
            inch_s = str(inch or '').strip()
            if eu_s or inch_s:
                rows_out.append({'eu': eu_s, 'insole_cm': inch_s})
        parsed = {'kind': 'footwear', 'rows': rows_out}
        out = parse_measurements_payload(parsed)
        return out
    cols = [str(x).strip() for x in (size_columns or []) if str(x).strip()]
    indices = _garment_meas_row_indices(form)
    rows_out = []
    ncols = len(cols)
    for i in indices:
        lab = str(form.get(f'garment_meas_{i}_label') or '').strip()
        if not lab:
            lab = str(form.get(f'garment_meas_{i}_ru') or '').strip() or str(
                form.get(f'garment_meas_{i}_en') or ''
            ).strip()
        vals = []
        nonempty = False
        for j in range(ncols):
            cell_raw = form.get(f'garment_meas_{i}_v_{j}')
            coerced = _coerce_measurement_cell(cell_raw)
            if coerced != '':
                nonempty = True
            vals.append(coerced if coerced != '' else '')
        while len(vals) < ncols:
            vals.append('')
        if len(vals) > ncols:
            vals = vals[:ncols]
        if lab or nonempty:
            rows_out.append({'label': lab, 'values': vals})
    parsed = {'kind': 'garment', 'columns': cols, 'rows': rows_out}
    return parse_measurements_payload(parsed)


def parse_measurements_payload(raw):
    """
    Accepts JSON string or dict.
    Garment: {"kind":"garment","columns":["S","M"],"rows":[{"label":"Длина (см)","values":[1,2]}]} (legacy: en/ru).
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
            lab = str(r.get('label') or '').strip()
            ru = str(r.get('ru') or '').strip()
            en = str(r.get('en') or '').strip()
            canonical = lab or ru or en
            has_val = any(str(v).strip() != '' for v in vals)
            if not canonical and not has_val:
                continue
            out_rows.append({'label': canonical, 'values': vals})
        if not cols or not out_rows:
            return None
        return {'kind': 'garment', 'columns': cols, 'rows': out_rows}
    return None


def row_label(row, lang):
    _ = lang
    return (
        row.get('parameter_display')
        or row.get('label')
        or row.get('ru')
        or row.get('en')
        or ''
    )


def _inject_garment_row_display(parsed):
    if not parsed or parsed.get('kind') != 'garment':
        return
    rows = parsed.get('rows')
    if not isinstance(rows, list):
        return
    if not has_request_context():
        return
    from .i18n import tv

    for row in rows:
        if not isinstance(row, dict):
            continue
        lab = row.get('label') or ''
        row['parameter_display'] = tv(lab)


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
    _inject_garment_row_display(d['measurements'])


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
    """Раньше заполнял демо-замеры; отключено — таблицы только из админки или legacy JSON."""
    return 0
