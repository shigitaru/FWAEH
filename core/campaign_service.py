"""Campaign page public data and admin/campaign DB helpers."""
import logging

from flask import request

from .db import get_db_connection
from .i18n import TRANSLATIONS, _campaign_bilingual_display, get_lang, t, _tv_has_cyrillic

from .media_uploads import _save_campaign_upload

logger = logging.getLogger(__name__)


def normalize_campaign_content_lang(raw):
    v = (raw or '').strip().lower()
    if v in ('en', 'ru', 'auto'):
        return v
    return 'auto'


def _effective_lang_for_auto(anchor_text):
    s = (anchor_text or '').strip()
    if not s:
        return 'en'
    return 'ru' if _tv_has_cyrillic(s) else 'en'


def bilingual_columns_from_primary(text, resolved_lang):
    """Одна заполненная колонка (en или ru); вторая пустая — публичный показ переводит через _campaign_bilingual_display."""
    s = (text or '').strip()
    if not s:
        return '', ''
    if resolved_lang == 'ru':
        return '', s
    return s, ''


def campaign_header_form_to_db_columns(intro, tagline, source_lang_raw):
    sl = normalize_campaign_content_lang(source_lang_raw)
    anchor = ' '.join(
        x for x in [(intro or '').strip(), (tagline or '').strip()] if x
    )
    eff = _effective_lang_for_auto(anchor) if sl == 'auto' else sl
    intro_en, intro_ru = bilingual_columns_from_primary(intro, eff)
    tagline_en, tagline_ru = bilingual_columns_from_primary(tagline, eff)
    return intro_en, intro_ru, tagline_en, tagline_ru


def campaign_story_form_to_db_columns(headline, body, credits, source_lang_raw):
    sl = normalize_campaign_content_lang(source_lang_raw)
    anchor = ' '.join(
        x
        for x in [(headline or '').strip(), (body or '').strip(), (credits or '').strip()]
        if x
    )
    eff = _effective_lang_for_auto(anchor) if sl == 'auto' else sl
    he, hr = bilingual_columns_from_primary(headline, eff)
    be, br = bilingual_columns_from_primary(body, eff)
    ce, cr = bilingual_columns_from_primary(credits, eff)
    return he, hr, be, br, ce, cr


def _admin_bilingual_pick(en_text, ru_text):
    e, r = (en_text or '').strip(), (ru_text or '').strip()
    if e and not r:
        return e, 'en'
    if r and not e:
        return r, 'ru'
    if e and r:
        if get_lang() == 'ru':
            return r, 'ru'
        return e, 'en'
    return '', 'en'


def get_members_area_hero_url_from_db():
    """
    URL изображения для зоны участника (меню + страница /members): CampaignSettings.members_area_hero_url.
    Пустое в БД — None; шаблоны не показывают блок с картинкой.
    """
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute('SELECT members_area_hero_url FROM CampaignSettings WHERE id=1')
            row = cur.fetchone()
        if not row:
            return None
        raw = getattr(row, 'members_area_hero_url', None)
        if raw is None and hasattr(row, '__getitem__'):
            try:
                raw = row[0]
            except (IndexError, TypeError):
                raw = None
        s = (raw or '').strip()
        return s if s else None
    except Exception:
        logger.exception('Failed to read members_area_hero_url')
        return None


def get_campaign_index_data():
    """Главная страница кампании: интро + список историй с обложкой."""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute('SELECT intro_en, intro_ru, tagline_en, tagline_ru FROM CampaignSettings WHERE id=1')
            srow = cur.fetchone()
            cur.execute(
                """
                SELECT s.id, s.sort_order, s.headline_en, s.headline_ru, s.credits_en, s.credits_ru,
                    (SELECT image_url FROM CampaignStoryImages i WHERE i.story_id = s.id ORDER BY i.sort_order, i.id LIMIT 1) AS cover_url,
                    (SELECT COUNT(*) FROM CampaignStoryImages i2 WHERE i2.story_id = s.id) AS img_count
                FROM CampaignStories s
                ORDER BY s.sort_order, s.id
                """
            )
            story_rows = cur.fetchall()
        lang = get_lang()
        if srow:
            intro = _campaign_bilingual_display(srow[0], srow[1], lang)
            tagline = _campaign_bilingual_display(srow[2], srow[3], lang)
        else:
            intro, tagline = '', ''
        if not intro.strip():
            intro = t('campaign_intro')
        if not tagline.strip():
            tagline = t('campaign_tagline')
        stories = []
        for r in story_rows:
            sid = int(r[0])
            h_en, h_ru = r[2], r[3]
            c_en, c_ru = r[4], r[5]
            cover = r[6] or ''
            img_count = int(r[7] or 0)
            stories.append(
                {
                    'id': sid,
                    'headline': _campaign_bilingual_display(h_en, h_ru, lang),
                    'credits': _campaign_bilingual_display(c_en, c_ru, lang),
                    'cover_url': cover,
                    'img_count': img_count,
                }
            )
        return {'campaign_intro': intro, 'campaign_tagline': tagline, 'stories': stories}
    except Exception:
        logger.exception('Failed to load campaign index data')
        return {'campaign_intro': t('campaign_intro'), 'campaign_tagline': t('campaign_tagline'), 'stories': []}


def get_campaign_story_detail(story_id):
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT headline_en, headline_ru, body_en, body_ru, credits_en, credits_ru
                FROM CampaignStories WHERE id=?
                """,
                (story_id,),
            )
            srow = cur.fetchone()
            if not srow:
                return None
            cur.execute(
                'SELECT image_url FROM CampaignStoryImages WHERE story_id=? ORDER BY sort_order, id',
                (story_id,),
            )
            img_rows = cur.fetchall()
        lang = get_lang()
        h_en, h_ru = (srow[0] or ''), (srow[1] or '')
        b_en, b_ru = (srow[2] or ''), (srow[3] or '')
        c_en, c_ru = (srow[4] or ''), (srow[5] or '')
        return {
            'id': story_id,
            'headline': _campaign_bilingual_display(h_en, h_ru, lang),
            'body': _campaign_bilingual_display(b_en, b_ru, lang),
            'credits': _campaign_bilingual_display(c_en, c_ru, lang),
            'images': [{'src': r[0]} for r in img_rows],
        }
    except Exception:
        logger.exception('Failed to load campaign story detail %s', story_id)
        return None


def _fetch_campaign_settings_admin():
    d_en = TRANSLATIONS['en']
    d_ru = TRANSLATIONS['ru']
    defaults = {
        'intro_en': d_en.get('campaign_intro', ''),
        'intro_ru': d_ru.get('campaign_intro', ''),
        'tagline_en': d_en.get('campaign_tagline', ''),
        'tagline_ru': d_ru.get('campaign_tagline', ''),
        'members_area_hero_url': '',
    }
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                'SELECT intro_en, intro_ru, tagline_en, tagline_ru, members_area_hero_url FROM CampaignSettings WHERE id=1'
            )
            srow = cur.fetchone()
        if srow:
            hero = getattr(srow, 'members_area_hero_url', None)
            if hero is None:
                hero = (srow[4] if len(srow) > 4 else '') or ''
            intro_en = (srow.intro_en if hasattr(srow, 'intro_en') else (srow[0] or '')) or ''
            intro_ru = (srow.intro_ru if hasattr(srow, 'intro_ru') else (srow[1] or '')) or ''
            tagline_en = (srow.tagline_en if hasattr(srow, 'tagline_en') else (srow[2] or '')) or ''
            tagline_ru = (srow.tagline_ru if hasattr(srow, 'tagline_ru') else (srow[3] or '')) or ''
            intro_merged, _lang_intro = _admin_bilingual_pick(intro_en, intro_ru)
            tag_merged, _lang_tag = _admin_bilingual_pick(tagline_en, tagline_ru)
            return {
                'intro_en': intro_en,
                'intro_ru': intro_ru,
                'tagline_en': tagline_en,
                'tagline_ru': tagline_ru,
                'intro': intro_merged,
                'tagline': tag_merged,
                'members_area_hero_url': (hero or ''),
            }
        out = defaults.copy()
        intro_merged, _lang_intro = _admin_bilingual_pick(out['intro_en'], out['intro_ru'])
        tag_merged, _lang_tag = _admin_bilingual_pick(out['tagline_en'], out['tagline_ru'])
        out['intro'] = intro_merged
        out['tagline'] = tag_merged
        return out
    except Exception:
        logger.exception('Failed to load campaign settings for admin')
        out = defaults.copy()
        intro_merged, _lang_intro = _admin_bilingual_pick(out['intro_en'], out['intro_ru'])
        tag_merged, _lang_tag = _admin_bilingual_pick(out['tagline_en'], out['tagline_ru'])
        out['intro'] = intro_merged
        out['tagline'] = tag_merged
        return out


def _list_campaign_stories_admin():
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                'SELECT id, sort_order, headline_en, headline_ru FROM CampaignStories ORDER BY sort_order, id',
            )
            return [
                {
                    'id': int(r[0]),
                    'sort_order': int(r[1]),
                    'headline_en': r[2] or '',
                    'headline_ru': r[3] or '',
                }
                for r in cur.fetchall()
            ]
    except Exception:
        logger.exception('Failed to list campaign stories for admin')
        return []


def _fetch_campaign_story_admin(story_id):
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT id, sort_order, headline_en, headline_ru, body_en, body_ru, credits_en, credits_ru
                FROM CampaignStories WHERE id=?
                """,
                (story_id,),
            )
            srow = cur.fetchone()
            if not srow:
                return None, []
            cur.execute(
                'SELECT image_url FROM CampaignStoryImages WHERE story_id=? ORDER BY sort_order, id',
                (story_id,),
            )
            imgs = [{'url': r[0]} for r in cur.fetchall()]
        st = {
            'id': int(srow[0]),
            'sort_order': int(srow[1]),
            'headline_en': srow[2] or '',
            'headline_ru': srow[3] or '',
            'body_en': srow[4] or '',
            'body_ru': srow[5] or '',
            'credits_en': srow[6] or '',
            'credits_ru': srow[7] or '',
        }
        h, _lh = _admin_bilingual_pick(st['headline_en'], st['headline_ru'])
        b, _lb = _admin_bilingual_pick(st['body_en'], st['body_ru'])
        c, _lc = _admin_bilingual_pick(st['credits_en'], st['credits_ru'])
        st['form_headline'] = h
        st['form_body'] = b
        st['form_credits'] = c
        return (st, imgs)
    except Exception:
        logger.exception('Failed to fetch campaign story %s for admin', story_id)
        return None, []

def _insert_campaign_story_return_id(cur, params):
    cur.execute(
        """
        INSERT INTO CampaignStories (sort_order, headline_en, headline_ru, body_en, body_ru, credits_en, credits_ru)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        RETURNING id
        """,
        params,
    )
    row = cur.fetchone()
    if row is None or row[0] is None:
        raise RuntimeError('CampaignStories insert: could not read new id')
    return int(row[0])


def _collect_story_image_urls_from_form():
    existings = request.form.getlist('img_existing')
    files = request.files.getlist('img_file')
    n = max(len(existings), len(files), 1)
    urls = []
    for i in range(n):
        old = (existings[i].strip() if i < len(existings) else '') or ''
        fs = files[i] if i < len(files) else None
        new_u = _save_campaign_upload(fs)
        url = new_u or old
        if url:
            urls.append(url)
    return urls
