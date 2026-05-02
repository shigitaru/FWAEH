"""Product and campaign file uploads and admin image mutations."""
import logging
import os
from uuid import uuid4

import requests
from werkzeug.utils import secure_filename

from .config import settings
from .db import get_db_connection

UPLOAD_DIR = settings.upload_dir
CAMPAIGN_UPLOAD_DIR = settings.campaign_upload_dir
ALLOWED_IMAGE_EXTENSIONS = settings.allowed_image_extensions
ALLOWED_VIDEO_EXTENSIONS = settings.allowed_video_extensions
logger = logging.getLogger(__name__)

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
        logger.exception('Failed to fetch product images for product %s', product_id)
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
    return _save_uploaded_media(file_storage, folder='products')


def _save_uploaded_media(file_storage, folder='products'):
    if not file_storage or not file_storage.filename:
        return None
    original = secure_filename(file_storage.filename)
    _, ext = os.path.splitext(original.lower())
    if ext not in ALLOWED_IMAGE_EXTENSIONS and ext not in ALLOWED_VIDEO_EXTENSIONS:
        return None
    if settings.supabase_url and settings.supabase_service_role_key and settings.supabase_bucket:
        unique_name = f'{uuid4().hex}{ext}'
        object_path = f'protocol_archive/{folder}/{unique_name}'
        upload_url = f'{settings.supabase_url}/storage/v1/object/{settings.supabase_bucket}/{object_path}'
        body = file_storage.read()
        file_storage.stream.seek(0)
        content_type = file_storage.mimetype or ('video/mp4' if ext in ALLOWED_VIDEO_EXTENSIONS else 'image/jpeg')
        response = requests.post(
            upload_url,
            headers={
                'apikey': settings.supabase_service_role_key,
                'Authorization': f'Bearer {settings.supabase_service_role_key}',
                'Content-Type': content_type,
                'x-upsert': 'false',
            },
            data=body,
            timeout=30,
        )
        if response.ok:
            if settings.supabase_public_base_url:
                return f'{settings.supabase_public_base_url}/{settings.supabase_bucket}/{object_path}'
            return f'{settings.supabase_url}/storage/v1/object/public/{settings.supabase_bucket}/{object_path}'
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    filename = f'{uuid4().hex}{ext}'
    abs_path = os.path.join(UPLOAD_DIR, filename)
    file_storage.save(abs_path)
    return f'/static/products/uploads/{filename}'


def _save_campaign_upload(file_storage):
    if settings.supabase_url and settings.supabase_service_role_key and settings.supabase_bucket:
        return _save_uploaded_media(file_storage, folder='campaign')
    if not file_storage or not file_storage.filename:
        return None
    original = secure_filename(file_storage.filename)
    _, ext = os.path.splitext(original.lower())
    if ext not in ALLOWED_IMAGE_EXTENSIONS and ext not in ALLOWED_VIDEO_EXTENSIONS:
        return None
    os.makedirs(CAMPAIGN_UPLOAD_DIR, exist_ok=True)
    filename = f'{uuid4().hex}{ext}'
    abs_path = os.path.join(CAMPAIGN_UPLOAD_DIR, filename)
    file_storage.save(abs_path)
    return f'/static/campaign/uploads/{filename}'

