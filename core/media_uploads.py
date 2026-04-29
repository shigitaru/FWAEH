"""Product and campaign file uploads and admin image mutations."""
import os
from uuid import uuid4

from werkzeug.utils import secure_filename

from .config import settings
from .db import get_db_connection

UPLOAD_DIR = settings.upload_dir
CAMPAIGN_UPLOAD_DIR = settings.campaign_upload_dir
ALLOWED_IMAGE_EXTENSIONS = settings.allowed_image_extensions

def _nullable_str(value):
    """Пустая строка → None для колонок БД (material, origin, condition), чтобы можно было «очистить» поле."""
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None


def _fetch_product_image_rows(product_id):
    """Строки ProductImages для админки (id + url), чтобы можно было удалить по id."""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                'SELECT id, image_url FROM ProductImages WHERE product_id=? ORDER BY sort_order, id',
                (product_id,),
            )
            return [{'id': r.id, 'url': r.image_url} for r in cur.fetchall()]
    except Exception:
        return []


def _apply_admin_product_image_changes(cur, product_id, remove_ids, ordered_ids, uploaded_main, extra_images):
    """Удаление отмеченных, порядок из формы (drag), новая главная при загрузке, доп. файлы в конец."""
    cur.execute(
        'SELECT id, image_url, sort_order FROM ProductImages WHERE product_id=? ORDER BY sort_order, id',
        (product_id,),
    )
    rows = cur.fetchall()
    remove_set = set(remove_ids or [])
    remaining = [r for r in rows if int(r.id) not in remove_set]
    if not remaining:
        raise ValueError('__LAST_IMAGE__')
    by_id = {int(r.id): r.image_url for r in remaining}

    id_order = []
    seen = set()
    for oid in ordered_ids or []:
        if oid in by_id and oid not in seen:
            id_order.append(oid)
            seen.add(oid)
    for r in sorted(remaining, key=lambda x: (x.sort_order, x.id)):
        rid = int(r.id)
        if rid not in seen:
            id_order.append(rid)
            seen.add(rid)

    urls = [by_id[i] for i in id_order]
    if uploaded_main:
        urls = [uploaded_main] + (urls[1:] if urls else [])
    for u in extra_images or []:
        urls.append(u)
    if not urls:
        raise ValueError('__LAST_IMAGE__')

    cur.execute('DELETE FROM ProductImages WHERE product_id=?', (product_id,))
    for i, u in enumerate(urls):
        cur.execute(
            'INSERT INTO ProductImages (product_id, image_url, sort_order) VALUES (?, ?, ?)',
            (product_id, u, i),
        )
    cur.execute('UPDATE Products SET main_image=? WHERE id=?', (urls[0], product_id))
    return urls[0]


def _save_uploaded_image(file_storage):
    if not file_storage or not file_storage.filename:
        return None
    original = secure_filename(file_storage.filename)
    _, ext = os.path.splitext(original.lower())
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return None
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    filename = f'{uuid4().hex}{ext}'
    abs_path = os.path.join(UPLOAD_DIR, filename)
    file_storage.save(abs_path)
    return f'/static/products/uploads/{filename}'


def _save_campaign_upload(file_storage):
    if not file_storage or not file_storage.filename:
        return None
    original = secure_filename(file_storage.filename)
    _, ext = os.path.splitext(original.lower())
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return None
    os.makedirs(CAMPAIGN_UPLOAD_DIR, exist_ok=True)
    filename = f'{uuid4().hex}{ext}'
    abs_path = os.path.join(CAMPAIGN_UPLOAD_DIR, filename)
    file_storage.save(abs_path)
    return f'/static/campaign/uploads/{filename}'

