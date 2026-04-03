from flask import (
    Flask, render_template, session,
    redirect, url_for, request, jsonify, flash
)
import os
import re
import time
import hashlib
from datetime import datetime
import pyodbc
from uuid import uuid4
from werkzeug.utils import secure_filename
try:
    from deep_translator import GoogleTranslator
except Exception:
    GoogleTranslator = None

app = Flask(__name__)
app.secret_key = 'protocol-archive-2024'

DB_NAME = os.getenv('DB_NAME', 'ProtocolArchive')
DB_SERVER = os.getenv('DB_SERVER', r'SHIGITARU\SQLEXPRESS')
DB_CONNECTION_STRING = os.getenv(
    'DB_CONNECTION_STRING',
    f'DRIVER={{ODBC Driver 17 for SQL Server}};'
    f'SERVER={DB_SERVER};'
    f'DATABASE={DB_NAME};'
    'Trusted_Connection=yes;'
    'Encrypt=yes;'
    'TrustServerCertificate=yes;'
    'MARS_Connection=no;'
)
UPLOAD_DIR = os.path.join(app.root_path, 'static', 'products', 'uploads')
CAMPAIGN_UPLOAD_DIR = os.path.join(app.root_path, 'static', 'campaign', 'uploads')
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
AUTO_TRANSLATE_CACHE = {}


TRANSLATIONS = {
    'en': {
        'enter': 'Enter',
        'collection': 'Collection',
        'couture': 'Couture',
        'campaign': 'Campaign',
        'about': 'About',
        'search': 'Search',
        'bag': 'Bag',
        'search_placeholder': 'Search by name, brand or code...',
        'shop_by_brand': 'Shop by brand',
        'all_brands': 'All brands',
        'no_results': 'No results for',
        'result_one': 'result',
        'result_few': 'results',
        'result_many': 'results',
        'filtered_by': 'Filtered by',
        'clear': 'Clear',
        'no_items': 'No items found',
        'size': 'Size',
        'card_sizes': 'Sizes',
        'rental_period': 'Rental period',
        'per_day': '/ day',
        'days_label': 'days',
        'max': 'max',
        'total': 'Total',
        'add_to_bag': 'Add to bag',
        'your_bag': 'Your bag',
        'period': 'Period',
        'remove': 'Remove',
        'clear_bag': 'Clear bag',
        'checkout': 'Proceed to checkout',
        'bag_empty': 'Your bag is empty',
        'browse': 'Browse collection',
        'material': 'Material',
        'made_in': 'Made in',
        'condition': 'Condition',
        'added': 'Added',
        'rental_service': 'Rental service',
        'rental_desc': 'We offer authenticated designer garments for short-term rental. Each piece is carefully inspected, cleaned, and prepared by our in-house atelier before delivery.',
        'duration': 'Duration',
        'duration_desc': 'Rental period is flexible per item. Late returns are charged at 150% of the daily rate.',
        'care': 'Care',
        'care_desc': 'All garments must be returned in the condition received. Do not wash or dry clean. Professional care is included in the rental price.',
        'contact': 'Contact',
        'couture_title': 'Couture Archive',
        'couture_subtitle': 'Restricted access — special handling required',
        'campaign_tagline': 'Editorial series',
        'campaign_intro': 'Silhouette, material, and light — a visual sequence shot for Protocol Archive.',
        'campaign_cta': 'Browse collection',
        'campaign_story_one': 'story',
        'campaign_story_many': 'stories',
        'campaign_open_story': 'Open',
        'campaign_story_back': 'Back to campaign',
        'campaign_no_stories': 'No stories yet.',
        'campaign_gallery': 'Gallery',
        'campaign_lightbox_close': 'Close',
        'campaign_image_zoom': 'View full size',
        'authenticated': 'All garments are authenticated',
        'min_condition': 'Minimum condition',
        'any_condition': 'Any',
        'admin': 'Admin',
        'admin_panel': 'Admin panel',
        'products': 'products',
        'create_product': 'Create product',
        'brand_placeholder': 'Brand (e.g. Rick Owens)',
        'name_placeholder': 'Name',
        'serial_placeholder': 'Serial (PA-XXXX)',
        'category_placeholder': 'Category: rtw/couture',
        'price_per_day_placeholder': 'Price per day',
        'max_days_placeholder': 'Max rental days',
        'condition_score_placeholder': 'Condition score 1-10',
        'material_placeholder': 'Material',
        'origin_placeholder': 'Origin (Italy, etc.)',
        'condition_label_placeholder': 'Condition label',
        'sizes_placeholder': 'Sizes (comma separated): EU 40, EU 41',
        'admin_required_fields': 'Admin: serial, brand, name and main image are required',
        'admin_product_created': 'Admin: product created',
        'admin_error_prefix': 'Admin error',
        'admin_main_image_upload': 'Main image (upload)',
        'admin_extra_images_upload': 'Extra images (upload, multiple)',
        'admin_drop_here': 'Drag files here or click to choose',
        'admin_required_main_image': 'Admin: add main image (upload)',
        'admin_no_images_uploaded': 'Admin: no valid images uploaded',
        'status_success': 'Success',
        'status_error': 'Error',
        'admin_brand_resolve_error': 'Admin: failed to resolve brand id',
        'admin_edit_product': 'Edit product',
        'admin_save_product': 'Save changes',
        'admin_cancel': 'Back to admin',
        'admin_product_updated': 'Admin: product updated',
        'admin_product_not_found': 'Admin: product not found',
        'admin_serial_exists': 'Admin: this serial is already used by another product',
        'admin_current_images': 'Current images (upload below to replace or add)',
        'admin_view_product': 'View on site',
        'admin_clear_extra_images': 'Remove all extra images (keep main only)',
        'admin_remove_images_hint': 'Check photos to remove, then Save changes',
        'admin_cannot_remove_last_image': 'You must keep at least one image',
        'admin_remove_photo': 'Remove',
        'category_rtw': 'RTW',
        'category_couture': 'Couture',
        'category_accessories': 'Accessories',
        'admin_edit_campaign': 'Edit campaign page',
        'admin_campaign_title': 'Campaign page',
        'admin_campaign_intro_en': 'Intro (English)',
        'admin_campaign_intro_ru': 'Intro (Russian)',
        'admin_campaign_tagline_en': 'Tagline (English)',
        'admin_campaign_tagline_ru': 'Tagline (Russian)',
        'admin_campaign_looks': 'Looks',
        'admin_campaign_ref': 'Label (e.g. Look 01)',
        'admin_campaign_location': 'Location',
        'admin_campaign_image': 'Image',
        'admin_campaign_add_row': 'Add look',
        'admin_campaign_save': 'Save campaign',
        'admin_campaign_save_header': 'Save page header',
        'admin_campaign_saved': 'Campaign saved',
        'admin_campaign_need_look': 'Add at least one look with an image',
        'admin_campaign_back': 'Back to products',
        'admin_campaign_replace_hint': 'Upload a file to replace the current image.',
        'admin_campaign_stories': 'Stories',
        'admin_new_story': 'New story',
        'admin_edit_story': 'Edit',
        'admin_story_headline_en': 'Title (English)',
        'admin_story_headline_ru': 'Title (Russian)',
        'admin_story_body_en': 'Description (English)',
        'admin_story_body_ru': 'Description (Russian)',
        'admin_story_credits_en': 'Credits / collaboration (English)',
        'admin_story_credits_ru': 'Credits / collaboration (Russian)',
        'admin_story_images': 'Photos',
        'admin_story_paste_hint': 'Paste images from clipboard (Ctrl+V) to add photos — no need to click «Add look» each time. Works when focus is not in a title or description field.',
        'admin_story_save': 'Save story',
        'admin_story_delete': 'Delete story',
        'admin_story_delete_confirm': 'Delete this story and all its photos?',
        'admin_story_created': 'Story created',
        'admin_story_updated': 'Story updated',
        'admin_story_deleted': 'Story deleted',
        'admin_story_need_headline': 'Title is required',
        'admin_story_need_image': 'Add at least one image',
        'admin_story_back_list': 'Campaign overview',
        'admin_campaign_settings_saved': 'Campaign header saved',
        'admin_campaign_header_section': 'Page header (intro & tagline)',
    },
    'ru': {
        'enter': 'Войти',
        'collection': 'Коллекция',
        'couture': 'Кутюр',
        'campaign': 'Кампания',
        'about': 'О нас',
        'search': 'Поиск',
        'bag': 'Корзина',
        'search_placeholder': 'Название, бренд или артикул...',
        'shop_by_brand': 'Бренды',
        'all_brands': 'Все бренды',
        'no_results': 'Нет результатов для',
        'result_one': 'результат',
        'result_few': 'результата',
        'result_many': 'результатов',
        'filtered_by': 'Фильтр',
        'clear': 'Сбросить',
        'no_items': 'Ничего не найдено',
        'size': 'Размер',
        'card_sizes': 'Размеры',
        'rental_period': 'Срок аренды',
        'per_day': '/ день',
        'days_label': 'дней',
        'max': 'макс',
        'total': 'Итого',
        'add_to_bag': 'В корзину',
        'your_bag': 'Ваша корзина',
        'period': 'Период',
        'remove': 'Удалить',
        'clear_bag': 'Очистить',
        'checkout': 'Оформить',
        'bag_empty': 'Корзина пуста',
        'browse': 'Смотреть коллекцию',
        'material': 'Материал',
        'made_in': 'Производство',
        'condition': 'Состояние',
        'added': 'Добавлено',
        'rental_service': 'Сервис аренды',
        'rental_desc': 'Мы предоставляем аутентифицированную дизайнерскую одежду для краткосрочной аренды. Каждая вещь проходит тщательную проверку и подготовку.',
        'duration': 'Сроки',
        'duration_desc': 'Срок аренды гибкий для каждой вещи. За просрочку взимается 150% от дневной ставки.',
        'care': 'Уход',
        'care_desc': 'Вещи должны быть возвращены в полученном состоянии. Не стирать. Профессиональный уход включён в стоимость.',
        'contact': 'Контакты',
        'couture_title': 'Архив кутюр',
        'couture_subtitle': 'Ограниченный доступ — требуется особое обращение',
        'campaign_tagline': 'Редакционная серия',
        'campaign_intro': 'Силуэт, материал и свет — визуальный ряд для Protocol Archive.',
        'campaign_cta': 'Перейти в коллекцию',
        'campaign_story_one': 'история',
        'campaign_story_few': 'истории',
        'campaign_story_many': 'историй',
        'campaign_open_story': 'Открыть',
        'campaign_story_back': 'Назад к кампании',
        'campaign_no_stories': 'Пока нет историй.',
        'campaign_gallery': 'Галерея',
        'campaign_lightbox_close': 'Закрыть',
        'campaign_image_zoom': 'Открыть в полном размере',
        'authenticated': 'Все вещи аутентифицированы',
        'min_condition': 'Минимальное состояние',
        'any_condition': 'Любое',
        'admin': 'Админ',
        'admin_panel': 'Панель администратора',
        'products': 'товаров',
        'create_product': 'Создать товар',
        'brand_placeholder': 'Бренд (например, Rick Owens)',
        'name_placeholder': 'Название',
        'serial_placeholder': 'Артикул (PA-XXXX)',
        'category_placeholder': 'Категория: rtw/couture',
        'price_per_day_placeholder': 'Цена за день',
        'max_days_placeholder': 'Максимум дней аренды',
        'condition_score_placeholder': 'Оценка состояния 1-10',
        'material_placeholder': 'Материал',
        'origin_placeholder': 'Страна происхождения (Italy и т.д.)',
        'condition_label_placeholder': 'Описание состояния',
        'sizes_placeholder': 'Размеры через запятую: EU 40, EU 41',
        'admin_required_fields': 'Админ: serial, brand, name и main image обязательны',
        'admin_product_created': 'Админ: товар добавлен',
        'admin_error_prefix': 'Ошибка админки',
        'admin_main_image_upload': 'Главное фото (загрузка)',
        'admin_extra_images_upload': 'Доп. фото (загрузка, несколько)',
        'admin_drop_here': 'Перетащите файлы сюда или нажмите для выбора',
        'admin_required_main_image': 'Админ: добавьте главное фото (загрузка)',
        'admin_no_images_uploaded': 'Админ: не загружено ни одного корректного изображения',
        'status_success': 'Успешно',
        'status_error': 'Ошибка',
        'admin_brand_resolve_error': 'Админ: не удалось получить id бренда',
        'admin_edit_product': 'Редактировать товар',
        'admin_save_product': 'Сохранить',
        'admin_cancel': 'Назад в админку',
        'admin_product_updated': 'Админ: товар обновлён',
        'admin_product_not_found': 'Админ: товар не найден',
        'admin_serial_exists': 'Админ: такой артикул уже у другого товара',
        'admin_current_images': 'Текущие фото (загрузите ниже, чтобы заменить или добавить)',
        'admin_view_product': 'Смотреть на сайте',
        'admin_clear_extra_images': 'Удалить все дополнительные фото (главное оставить)',
        'admin_remove_images_hint': 'Отметьте фото для удаления и нажмите «Сохранить»',
        'admin_cannot_remove_last_image': 'Нужно оставить хотя бы одно фото',
        'admin_remove_photo': 'Удалить',
        'category_rtw': 'RTW',
        'category_couture': 'Кутюр',
        'category_accessories': 'Аксессуары',
        'admin_edit_campaign': 'Редактировать кампанию',
        'admin_campaign_title': 'Страница «Кампания»',
        'admin_campaign_intro_en': 'Вступительный текст (English)',
        'admin_campaign_intro_ru': 'Вступительный текст (Русский)',
        'admin_campaign_tagline_en': 'Подзаголовок (English)',
        'admin_campaign_tagline_ru': 'Подзаголовок (Русский)',
        'admin_campaign_looks': 'Кадры',
        'admin_campaign_ref': 'Подпись (напр. Look 01)',
        'admin_campaign_location': 'Локация',
        'admin_campaign_image': 'Фото',
        'admin_campaign_add_row': 'Добавить кадр',
        'admin_campaign_save': 'Сохранить кампанию',
        'admin_campaign_save_header': 'Сохранить шапку страницы',
        'admin_campaign_saved': 'Кампания сохранена',
        'admin_campaign_need_look': 'Нужен хотя бы один кадр с изображением',
        'admin_campaign_back': 'К товарам',
        'admin_campaign_replace_hint': 'Загрузите файл, чтобы заменить изображение.',
        'admin_campaign_stories': 'Истории',
        'admin_new_story': 'Новая история',
        'admin_edit_story': 'Редактировать',
        'admin_story_headline_en': 'Заголовок (English)',
        'admin_story_headline_ru': 'Заголовок (Русский)',
        'admin_story_body_en': 'Описание (English)',
        'admin_story_body_ru': 'Описание (Русский)',
        'admin_story_credits_en': 'Коллаборация / титры (English)',
        'admin_story_credits_ru': 'Коллаборация / титры (Русский)',
        'admin_story_images': 'Фотографии',
        'admin_story_paste_hint': 'Вставьте фото из буфера (Ctrl+V) — строка добавится сама, без кнопки «Добавить кадр». Не вставляйте, когда курсор в заголовке или описании.',
        'admin_story_save': 'Сохранить историю',
        'admin_story_delete': 'Удалить историю',
        'admin_story_delete_confirm': 'Удалить эту историю и все её фото?',
        'admin_story_created': 'История создана',
        'admin_story_updated': 'История обновлена',
        'admin_story_deleted': 'История удалена',
        'admin_story_need_headline': 'Нужен заголовок',
        'admin_story_need_image': 'Добавьте хотя бы одно фото',
        'admin_story_back_list': 'К обзору кампании',
        'admin_campaign_settings_saved': 'Шапка кампании сохранена',
        'admin_campaign_header_section': 'Шапка страницы (интро и подзаголовок)',
    }
}

# Словарь для перевода отдельных значений
VALUE_TRANSLATIONS = {
    'ru': {
        # Состояние
        'Excellent': 'Отличное',
        'Very good': 'Очень хорошее',
        'Good': 'Хорошее',
        'Good — light patina': 'Хорошее — лёгкая патина',
        'Pristine': 'Безупречное',
        'Perfect': 'Идеальное',
        'Museum grade': 'Музейный экземпляр',
        'Exhibition piece': 'Выставочный экземпляр',
        'Fragile': 'Хрупкое',
        # Материалы
        '100% Virgin Wool': '100% шерсть',
        'Wool Gabardine': 'Шерстяной габардин',
        'Calfskin Leather': 'Телячья кожа',
        '100% Mulberry Silk': '100% шёлк',
        'Recycled Nylon': 'Переработанный нейлон',
        'Cotton / Polyester': 'Хлопок / полиэстер',
        'Reclaimed vintage textiles': 'Винтажный текстиль',
        'Silk & Brass': 'Шёлк и латунь',
        # Страны
        'Italy': 'Италия',
        'italy': 'Италия',
        'Itally': 'Италия',
        'itally': 'Италия',
        'Japan': 'Япония',
        'japan': 'Япония',
        'France': 'Франция',
        'USA': 'США',
        'Usa': 'США',
        'United States': 'США',
        'UK': 'Великобритания',
        'United Kingdom': 'Великобритания',
        'China': 'Китай',
        'Germany': 'Германия',
        'Spain': 'Испания',
        'Portugal': 'Португалия',
        # Материалы (частые варианты из админки; регистр не важен — см. tv())
        'True Leather': 'Натуральная кожа',
        'Leather': 'Кожа',
    }
}

# ИСПРАВЛЕНО: Теперь используем локальный файл splash.jpg из папки static
SPLASH_IMAGE = '/static/splash.jpg'

PRODUCTS = [
    {
        'id': 1, 'category': 'rtw', 'serial': 'PA-0510',
        'brand': 'Maison Margiela', 'name': 'Oversized wool coat',
        'price': 180, 'max_days': 14, 'condition_score': 9,
        'material': '100% Virgin Wool', 'origin': 'Italy', 'condition': 'Excellent',
        'sizes': ['S', 'M', 'L', 'XL'],
        'image': 'https://images.unsplash.com/photo-1544022613-e87ca75a784a?q=80&w=1974&auto=format&fit=crop'
    },
    {
        'id': 2, 'category': 'rtw', 'serial': 'PA-0511',
        'brand': 'Balenciaga', 'name': 'Deconstructed blazer',
        'price': 150, 'max_days': 10, 'condition_score': 8,
        'material': 'Wool Gabardine', 'origin': 'Italy', 'condition': 'Very good',
        'sizes': ['XS', 'S', 'M', 'L', 'XL'],
        'image': 'https://images.unsplash.com/photo-1507679799987-c73779587ccf?q=80&w=2071&auto=format&fit=crop'
    },
    {
        'id': 3, 'category': 'rtw', 'serial': 'PA-1206',
        'brand': 'Rick Owens', 'name': 'Kiss Heels',
        'price': 95, 'max_days': 7, 'condition_score': 7,
        'material': 'Calfskin Leather', 'origin': 'Italy', 'condition': 'Good',
        'sizes': ['EU 40', 'EU 42', 'EU 43', 'EU 44'],
        'image': '/static/products/kiss-heels-1.png',
        'images': [
            '/static/products/kiss-heels-1.png',
            '/static/products/kiss-heels-2.png',
            '/static/products/kiss-heels-3.png',
        ]
    },
    {
        'id': 4, 'category': 'rtw', 'serial': 'PA-0512',
        'brand': 'Yohji Yamamoto', 'name': 'Silk shirt dress',
        'price': 200, 'max_days': 7, 'condition_score': 10,
        'material': '100% Mulberry Silk', 'origin': 'Japan', 'condition': 'Pristine',
        'sizes': ['XS', 'S', 'M'],
        'image': 'https://images.unsplash.com/photo-1539008835657-9e8e9680c956?q=80&w=1974&auto=format&fit=crop'
    },
    {
        'id': 5, 'category': 'rtw', 'serial': 'PA-0513',
        'brand': 'Vetements', 'name': 'Oversized bomber',
        'price': 120, 'max_days': 14, 'condition_score': 9,
        'material': 'Recycled Nylon', 'origin': 'Italy', 'condition': 'Excellent',
        'sizes': ['S', 'M', 'L'],
        'image': 'https://images.unsplash.com/photo-1550614000-4b95d4ed79cf?q=80&w=2000&auto=format&fit=crop'
    },
    {
        'id': 6, 'category': 'rtw', 'serial': 'PA-0556',
        'brand': 'Comme des Garçons', 'name': 'Layered jacket',
        'price': 90, 'max_days': 10, 'condition_score': 7,
        'material': 'Cotton / Polyester', 'origin': 'Japan', 'condition': 'Good',
        'sizes': ['S', 'M', 'L'],
        'image': 'https://images.unsplash.com/photo-1520639888713-7851133b1ed0?q=80&w=1974&auto=format&fit=crop'
    },
    {
        'id': 7, 'category': 'couture', 'serial': 'PA-C001',
        'brand': 'Maison Margiela', 'name': 'Artisanal recicla gown',
        'price': 900, 'max_days': 3, 'condition_score': 10,
        'material': 'Reclaimed vintage textiles', 'origin': 'France', 'condition': 'Museum grade',
        'sizes': ['One size'],
        'image': 'https://images.unsplash.com/photo-1566150905458-1bf1fc113f0d?q=80&w=2071&auto=format&fit=crop'
    },
    {
        'id': 8, 'category': 'couture', 'serial': 'PA-C002',
        'brand': 'Schiaparelli', 'name': 'Golden vein gown',
        'price': 1200, 'max_days': 3, 'condition_score': 10,
        'material': 'Silk & Brass', 'origin': 'France', 'condition': 'Exhibition piece',
        'sizes': ['One size'],
        'image': 'https://images.unsplash.com/photo-1595777457583-95e059d581b8?q=80&w=1983&auto=format&fit=crop'
    },
]

BRANDS = [
    {'name': 'Maison Margiela', 'slug': 'Maison Margiela', 'css_class': 'brand-margiela'},
    {'name': 'Balenciaga', 'slug': 'Balenciaga', 'css_class': 'brand-balenciaga'},
    {'name': 'Rick Owens', 'slug': 'Rick Owens', 'css_class': 'brand-rickowens'},
    {'name': 'Yohji Yamamoto', 'slug': 'Yohji Yamamoto', 'css_class': 'brand-yohji'},
    {'name': 'Vetements', 'slug': 'Vetements', 'css_class': 'brand-vetements'},
    {'name': 'Comme des Garçons', 'slug': 'Comme des Garçons', 'css_class': 'brand-cdg'},
    {'name': 'Schiaparelli', 'slug': 'Schiaparelli', 'css_class': 'brand-schiaparelli'},
]

# Имя бренда (lower) → CSS-класс для тайла на Search; пополняется вместе с BRANDS / новыми брендами в style.css.
BRAND_CSS_BY_NAME = {b['name'].strip().lower(): b['css_class'] for b in BRANDS}
BRAND_CSS_BY_NAME.update({
    'gucci': 'brand-gucci',
    'yzy': 'brand-yzy',
    'raf simons': 'brand-raf-simons',
})


def _resolve_brand_css(name, db_css=None):
    """Класс шрифта для тайла бренда: приоритет — значение из БД, иначе словарь, иначе нейтральный fallback."""
    s = (db_css or '').strip()
    if s:
        return s
    key = (name or '').strip().lower()
    return BRAND_CSS_BY_NAME.get(key, 'brand-font-fallback')

CONDITION_LABELS = [
    {'score': 0, 'en': 'Any', 'ru': 'Любое'},
    {'score': 7, 'en': 'Good (7+)', 'ru': 'Хорошее (7+)'},
    {'score': 8, 'en': 'Very good (8+)', 'ru': 'Очень хорошее (8+)'},
    {'score': 9, 'en': 'Excellent (9+)', 'ru': 'Отличное (9+)'},
    {'score': 10, 'en': 'Pristine (10)', 'ru': 'Безупречное (10)'},
]


def get_lang():
    return session.get('lang', 'en')

def t(key):
    lang = get_lang()
    return TRANSLATIONS.get(lang, TRANSLATIONS['en']).get(key, key)

def tc(base_key, n):
    """Перевод с учетом количества (ru: 1/2-4/5+; en: one/many)."""
    try:
        n_int = int(n)
    except Exception:
        n_int = 0
    lang = get_lang()
    forms = TRANSLATIONS.get(lang, TRANSLATIONS['en'])
    if lang != 'ru':
        suffix = 'one' if n_int == 1 else 'many'
        return forms.get(f'{base_key}_{suffix}', forms.get(base_key, base_key))
    n_mod100 = n_int % 100
    n_mod10 = n_int % 10
    if 11 <= n_mod100 <= 14:
        suffix = 'many'
    elif n_mod10 == 1:
        suffix = 'one'
    elif 2 <= n_mod10 <= 4:
        suffix = 'few'
    else:
        suffix = 'many'
    return forms.get(f'{base_key}_{suffix}', forms.get(base_key, base_key))

def _tv_ru_value_to_en_key(s_try):
    """Соответствие русского значения из БД каноническому английскому ключу (обратно к VALUE_TRANSLATIONS)."""
    s_lower = s_try.lower()
    for en_key, ru_val in VALUE_TRANSLATIONS.get('ru', {}).items():
        if ru_val.lower() == s_lower:
            return en_key
    return None


def _tv_has_cyrillic(text):
    return bool(re.search(r'[\u0400-\u04FF]', text))


def _translate_for_display_cached(text, source_lang, target_lang):
    """Кэшированный перевод для публичного показа (Google через deep-translator)."""
    if not text or not str(text).strip():
        return None
    if not GoogleTranslator:
        return None
    key_src = hashlib.sha256(
        f'{source_lang}|{target_lang}|{text}'.encode('utf-8')
    ).hexdigest()
    cache_key = f'cmpdisp:{key_src}'
    if cache_key in AUTO_TRANSLATE_CACHE:
        return AUTO_TRANSLATE_CACHE[cache_key]
    try:
        out = GoogleTranslator(source=source_lang, target=target_lang).translate(text)
        if out:
            AUTO_TRANSLATE_CACHE[cache_key] = out.strip()
            return AUTO_TRANSLATE_CACHE[cache_key]
    except Exception:
        pass
    try:
        out = GoogleTranslator(source='auto', target=target_lang).translate(text)
        if out:
            AUTO_TRANSLATE_CACHE[cache_key] = out.strip()
            return AUTO_TRANSLATE_CACHE[cache_key]
    except Exception:
        pass
    return None


def _campaign_bilingual_display(en_text, ru_text, want_lang):
    """
    Текст для языка интерфейса: сначала колонка en/ru, иначе перевод с другой колонки.
    Так описание истории меняется при переключении EN/RU, даже если в админке заполнен один язык.
    """
    en_t = (en_text or '').strip()
    ru_t = (ru_text or '').strip()
    if want_lang == 'en':
        if en_t:
            return en_t
        if ru_t:
            return _translate_for_display_cached(ru_t, 'ru', 'en') or ru_t
        return ''
    if ru_t:
        return ru_t
    if en_t:
        return _translate_for_display_cached(en_t, 'en', 'ru') or en_t
    return ''


def tv(value):
    """Перевод значений (материал, состояние, страна). Учитывает регистр и пробелы."""
    if value is None:
        return ''
    s = str(value).strip()
    if not s:
        return ''
    lang = get_lang()
    s_norm = s.replace('\u2014', '-').replace('\u2013', '-')

    if lang == 'en':
        en = _tv_ru_value_to_en_key(s) or _tv_ru_value_to_en_key(s_norm)
        if en is not None:
            return en
        s_stripped = re.sub(r'\s*\(\d+\s*/\s*\d+\)\s*$', '', s).strip()
        if s_stripped != s:
            en = _tv_ru_value_to_en_key(s_stripped)
            if en is not None:
                return en
        if GoogleTranslator and _tv_has_cyrillic(s):
            cache_key = f'en::{s}'
            if cache_key in AUTO_TRANSLATE_CACHE:
                return AUTO_TRANSLATE_CACHE[cache_key]
            try:
                auto_value = GoogleTranslator(source='ru', target='en').translate(s)
                if auto_value:
                    AUTO_TRANSLATE_CACHE[cache_key] = auto_value
                    return auto_value
            except Exception:
                pass
        return s

    ru_map = VALUE_TRANSLATIONS.get(lang, {})
    if s in ru_map:
        return ru_map[s]
    if s_norm != s and s_norm in ru_map:
        return ru_map[s_norm]
    s_lower = s.lower()
    for key, translated in ru_map.items():
        if key.lower() == s_lower:
            return translated
    if s_norm.lower() != s_lower:
        for key, translated in ru_map.items():
            if key.lower() == s_norm.lower():
                return translated
    # Fallback: automatic translation for unknown values.
    if lang == 'ru' and GoogleTranslator:
        cache_key = f'ru::{s}'
        if cache_key in AUTO_TRANSLATE_CACHE:
            return AUTO_TRANSLATE_CACHE[cache_key]
        try:
            auto_value = GoogleTranslator(source='en', target='ru').translate(s)
            if auto_value:
                AUTO_TRANSLATE_CACHE[cache_key] = auto_value
                return auto_value
        except Exception:
            pass
    return value

def get_cart():
    return session.get('cart', [])

def get_cart_count():
    return len(get_cart())

def get_cart_total():
    return sum(item['total_price'] for item in get_cart())


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


def _rebuild_product_images_after_removal(cur, product_id, remove_ids):
    """Удаляет выбранные фото из ProductImages, перенумеровывает sort_order, обновляет main_image в Products."""
    if not remove_ids:
        return
    cur.execute(
        'SELECT id, image_url FROM ProductImages WHERE product_id=? ORDER BY sort_order, id',
        (product_id,),
    )
    rows = cur.fetchall()
    remove_set = set(remove_ids)
    kept = [r for r in rows if r.id not in remove_set]
    if not kept:
        raise ValueError('__LAST_IMAGE__')
    cur.execute('DELETE FROM ProductImages WHERE product_id=?', (product_id,))
    for i, r in enumerate(kept):
        cur.execute(
            'INSERT INTO ProductImages (product_id, image_url, sort_order) VALUES (?, ?, ?)',
            (product_id, r.image_url, i),
        )
    cur.execute('UPDATE Products SET main_image=? WHERE id=?', (kept[0].image_url, product_id))


def get_db_connection():
    return pyodbc.connect(DB_CONNECTION_STRING)

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
                    (SELECT TOP 1 image_url FROM CampaignStoryImages i WHERE i.story_id = s.id ORDER BY i.sort_order, i.id) AS cover_url,
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
            # Индексы: надёжнее чем r.id у pyodbc/драйвера ODBC
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
        return None


def _fetch_campaign_settings_admin():
    d_en = TRANSLATIONS['en']
    d_ru = TRANSLATIONS['ru']
    defaults = {
        'intro_en': d_en.get('campaign_intro', ''),
        'intro_ru': d_ru.get('campaign_intro', ''),
        'tagline_en': d_en.get('campaign_tagline', ''),
        'tagline_ru': d_ru.get('campaign_tagline', ''),
    }
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute('SELECT intro_en, intro_ru, tagline_en, tagline_ru FROM CampaignSettings WHERE id=1')
            srow = cur.fetchone()
        if srow:
            return {
                'intro_en': (srow[0] or ''),
                'intro_ru': (srow[1] or ''),
                'tagline_en': (srow[2] or ''),
                'tagline_ru': (srow[3] or ''),
            }
        return defaults.copy()
    except Exception:
        return defaults.copy()


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
        return (
            {
                'id': int(srow[0]),
                'sort_order': int(srow[1]),
                'headline_en': srow[2] or '',
                'headline_ru': srow[3] or '',
                'body_en': srow[4] or '',
                'body_ru': srow[5] or '',
                'credits_en': srow[6] or '',
                'credits_ru': srow[7] or '',
            },
            imgs,
        )
    except Exception:
        return None, []


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

def find_product(product_id):
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                '''
                SELECT p.id, p.category, p.serial, b.name AS brand, p.name, p.price, p.max_days,
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

def filter_products(category=None, query=None, brand=None, min_condition=0):
    try:
        sql = '''
            SELECT p.id, p.category, p.serial, b.name AS brand, p.name, p.price, p.max_days,
                   p.condition_score, p.material, p.origin, p.[condition], p.main_image
            FROM Products p
            JOIN Brands b ON b.id = p.brand_id
            WHERE 1=1
        '''
        params = []
        if category:
            sql += ' AND p.category = ?'
            params.append(category)
        if brand:
            sql += ' AND b.name LIKE ?'
            params.append(f'%{brand}%')
        if query:
            sql += ' AND (p.name LIKE ? OR p.serial LIKE ? OR b.name LIKE ?)'
            q = f'%{query}%'
            params.extend([q, q, q])
        if min_condition > 0:
            sql += ' AND p.condition_score >= ?'
            params.append(min_condition)
        sql += ' ORDER BY p.id'
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            rows = cur.fetchall()
        results = [{
            'id': row.id,
            'category': row.category,
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
        if brand:
            results = [p for p in results if brand.lower() in p['brand'].lower()]
        if query:
            q = query.lower()
            results = [p for p in results if q in p['name'].lower() or q in p['serial'].lower() or q in p['brand'].lower()]
        if min_condition > 0:
            results = [p for p in results if p['condition_score'] >= min_condition]
        return results


@app.route('/set-lang/<lang>')
def set_lang(lang):
    if lang in TRANSLATIONS:
        session['lang'] = lang
    return redirect(request.referrer or url_for('collection'))

@app.route('/')
def splash():
    # Передаем URL локального изображения в шаблон
    return render_template('splash.html', splash_image=SPLASH_IMAGE, t=t)

@app.route('/collection')
def collection():
    q = request.args.get('q', '')
    brand = request.args.get('brand', '')
    min_cond = int(request.args.get('min_condition', 0))
    products = filter_products(category='rtw', query=q, brand=brand, min_condition=min_cond)
    return render_template('collection.html', products=products, active_brand=brand, search_query=q, active_page='collection', cart_count=get_cart_count(), t=t, tv=tv, min_condition=min_cond, condition_labels=CONDITION_LABELS)

@app.route('/couture')
def couture():
    products = filter_products(category='couture')
    return render_template('couture.html', products=products, active_page='couture', cart_count=get_cart_count(), t=t, tv=tv)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = find_product(product_id)
    if not product:
        return 'Not found', 404
    days = int(request.args.get('days', 1))
    days = min(max(days, 1), product['max_days'])
    total = product['price'] * days
    return render_template('product.html', product=product, selected_days=days, total_price=total, active_page='product', cart_count=get_cart_count(), t=t, tv=tv)

@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    product_id = int(request.form.get('product_id'))
    days = int(request.form.get('days', 1))
    size = request.form.get('size', '')
    product = find_product(product_id)
    if not product:
        return redirect(url_for('collection'))
    days = min(max(days, 1), product['max_days'])
    cart = get_cart()
    cart.append({
        'cart_id': int(time.time() * 1000),
        'product_id': product['id'],
        'serial': product['serial'],
        'brand': product['brand'],
        'name': product['name'],
        'price_per_day': product['price'],
        'days': days,
        'size': size,
        'total_price': product['price'] * days,
        'image': product['image'],
    })
    session['cart'] = cart
    flash(f'{t("added")} — {product["name"]}')
    return redirect(url_for('cart'))

@app.route('/cart/remove/<int:cart_id>')
def remove_from_cart(cart_id):
    cart = [i for i in get_cart() if i['cart_id'] != cart_id]
    session['cart'] = cart
    return redirect(url_for('cart'))

@app.route('/cart')
def cart():
    return render_template('cart.html', cart_items=get_cart(), total=get_cart_total(), active_page='cart', cart_count=get_cart_count(), t=t)

@app.route('/cart/clear')
def clear_cart():
    session['cart'] = []
    return redirect(url_for('cart'))

@app.route('/search')
def search():
    q = request.args.get('q', '')
    min_cond = int(request.args.get('min_condition', 0))
    results = filter_products(query=q, min_condition=min_cond) if q else []
    return render_template('search.html', brands=get_brands(), results=results, query=q, active_page='search', cart_count=get_cart_count(), t=t, tv=tv, min_condition=min_cond, condition_labels=CONDITION_LABELS)

@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if request.method == 'POST':
        try:
            category = request.form.get('category', '').strip() or 'rtw'
            serial = request.form.get('serial', '').strip()
            brand_name = request.form.get('brand', '').strip()
            name = request.form.get('name', '').strip()
            price = int(request.form.get('price', '0'))
            max_days_raw = request.form.get('max_days', '').strip()
            condition_score_raw = request.form.get('condition_score', '').strip()
            material = _nullable_str(request.form.get('material'))
            origin = _nullable_str(request.form.get('origin'))
            condition = _nullable_str(request.form.get('condition'))
            main_image = ''
            sizes_raw = request.form.get('sizes', '').strip()
            uploaded_main = _save_uploaded_image(request.files.get('main_image_file'))
            uploaded_extra = request.files.getlist('extra_image_files')
            if uploaded_main:
                main_image = uploaded_main
            if not all([serial, brand_name, name, max_days_raw, condition_score_raw]):
                session['admin_status'] = {'type': 'error', 'message': t('admin_required_fields')}
                return redirect(url_for('admin_panel'))
            max_days = int(max_days_raw)
            condition_score = int(condition_score_raw)
            size_values = [s.strip() for s in sizes_raw.split(',') if s.strip()]
            extra_images = []
            for img in uploaded_extra:
                saved = _save_uploaded_image(img)
                if saved:
                    extra_images.append(saved)
            if not main_image and extra_images:
                main_image = extra_images.pop(0)
            if not main_image:
                session['admin_status'] = {'type': 'error', 'message': t('admin_required_main_image')}
                return redirect(url_for('admin_panel'))
            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute('SELECT id FROM Brands WHERE name = ?', (brand_name,))
                brand_row = cur.fetchone()
                brand_id = None
                if brand_row:
                    brand_id = int(brand_row[0])
                else:
                    cur.execute(
                        '''
                        INSERT INTO Brands (name, slug, css_class)
                        OUTPUT INSERTED.id
                        VALUES (?, ?, ?)
                        ''',
                        (brand_name, brand_name, '')
                    )
                    out_row = cur.fetchone()
                    brand_id = int(out_row[0]) if out_row and out_row[0] is not None else None
                if not brand_id:
                    raise ValueError(t('admin_brand_resolve_error'))
                cur.execute(
                    '''
                    INSERT INTO Products (brand_id, category, serial, name, price, max_days, condition_score, material, origin, [condition], main_image)
                    OUTPUT INSERTED.id
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''',
                    (brand_id, category, serial, name, price, max_days, condition_score, material, origin, condition, main_image)
                )
                prod_row = cur.fetchone()
                product_id = int(prod_row[0]) if prod_row and prod_row[0] is not None else None
                if not product_id:
                    raise ValueError('Admin: failed to create product id')
                cur.execute(
                    'INSERT INTO ProductImages (product_id, image_url, sort_order) VALUES (?, ?, ?)',
                    (product_id, main_image, 0)
                )
                for idx, image_url in enumerate(extra_images, start=1):
                    cur.execute(
                        'INSERT INTO ProductImages (product_id, image_url, sort_order) VALUES (?, ?, ?)',
                        (product_id, image_url, idx)
                    )
                for size_label in size_values:
                    cur.execute('INSERT INTO ProductSizes (product_id, size_label) VALUES (?, ?)', (product_id, size_label))
                conn.commit()
            session['admin_status'] = {'type': 'success', 'message': t('admin_product_created')}
        except Exception as exc:
            session['admin_status'] = {'type': 'error', 'message': f'{t("admin_error_prefix")}: {exc}'}
        return redirect(url_for('admin_panel'))
    products = filter_products()
    admin_status = session.pop('admin_status', None)
    return render_template(
        'admin.html',
        products=products,
        brands=get_brands(),
        admin_status=admin_status,
        active_page='admin',
        cart_count=get_cart_count(),
        t=t,
        tv=tv
    )


@app.route('/admin/product/<int:product_id>/edit', methods=['GET', 'POST'])
def admin_edit_product(product_id):
    product = find_product(product_id)
    if not product:
        session['admin_status'] = {'type': 'error', 'message': t('admin_product_not_found')}
        return redirect(url_for('admin_panel'))

    if request.method == 'POST':
        try:
            category = request.form.get('category', '').strip() or 'rtw'
            serial = request.form.get('serial', '').strip()
            brand_name = request.form.get('brand', '').strip()
            name = request.form.get('name', '').strip()
            price = int(request.form.get('price', '0'))
            max_days_raw = request.form.get('max_days', '').strip()
            condition_score_raw = request.form.get('condition_score', '').strip()
            material = _nullable_str(request.form.get('material'))
            origin = _nullable_str(request.form.get('origin'))
            condition = _nullable_str(request.form.get('condition'))
            sizes_raw = request.form.get('sizes', '').strip()
            if not all([serial, brand_name, name, max_days_raw, condition_score_raw]):
                session['admin_status'] = {'type': 'error', 'message': t('admin_required_fields')}
                return redirect(url_for('admin_edit_product', product_id=product_id))
            max_days = int(max_days_raw)
            condition_score = int(condition_score_raw)
            size_values = [s.strip() for s in sizes_raw.split(',') if s.strip()]
            remove_ids = []
            for x in request.form.getlist('remove_image_id'):
                try:
                    remove_ids.append(int(x))
                except ValueError:
                    pass
            uploaded_main = _save_uploaded_image(request.files.get('main_image_file'))
            extra_images = []
            for img in request.files.getlist('extra_image_files'):
                saved = _save_uploaded_image(img)
                if saved:
                    extra_images.append(saved)
            with get_db_connection() as conn:
                cur = conn.cursor()
                if remove_ids:
                    try:
                        _rebuild_product_images_after_removal(cur, product_id, remove_ids)
                    except ValueError as ve:
                        if str(ve) == '__LAST_IMAGE__':
                            session['admin_status'] = {'type': 'error', 'message': t('admin_cannot_remove_last_image')}
                            return redirect(url_for('admin_edit_product', product_id=product_id))
                        raise
                cur.execute('SELECT main_image FROM Products WHERE id=?', (product_id,))
                er = cur.fetchone()
                existing_main = er[0] if er and er[0] is not None else product['image']
                main_image = uploaded_main or existing_main
                if not main_image:
                    session['admin_status'] = {'type': 'error', 'message': t('admin_required_main_image')}
                    return redirect(url_for('admin_edit_product', product_id=product_id))
                cur.execute('SELECT id FROM Brands WHERE name = ?', (brand_name,))
                brand_row = cur.fetchone()
                brand_id = None
                if brand_row:
                    brand_id = int(brand_row[0])
                else:
                    cur.execute(
                        '''
                        INSERT INTO Brands (name, slug, css_class)
                        OUTPUT INSERTED.id
                        VALUES (?, ?, ?)
                        ''',
                        (brand_name, brand_name, '')
                    )
                    out_row = cur.fetchone()
                    brand_id = int(out_row[0]) if out_row and out_row[0] is not None else None
                if not brand_id:
                    raise ValueError(t('admin_brand_resolve_error'))
                cur.execute(
                    '''
                    UPDATE Products SET brand_id=?, category=?, serial=?, name=?, price=?, max_days=?,
                    condition_score=?, material=?, origin=?, [condition]=?, main_image=?
                    WHERE id=?
                    ''',
                    (
                        brand_id, category, serial, name, price, max_days, condition_score,
                        material, origin, condition, main_image, product_id,
                    ),
                )
                cur.execute(
                    'SELECT id FROM ProductImages WHERE product_id=? AND sort_order=0',
                    (product_id,),
                )
                if cur.fetchone():
                    cur.execute(
                        'UPDATE ProductImages SET image_url=? WHERE product_id=? AND sort_order=0',
                        (main_image, product_id),
                    )
                else:
                    cur.execute(
                        'INSERT INTO ProductImages (product_id, image_url, sort_order) VALUES (?, ?, ?)',
                        (product_id, main_image, 0),
                    )
                cur.execute(
                    'SELECT COALESCE(MAX(sort_order), 0) FROM ProductImages WHERE product_id=?',
                    (product_id,),
                )
                max_sort_row = cur.fetchone()
                max_sort = int(max_sort_row[0]) if max_sort_row and max_sort_row[0] is not None else 0
                for url in extra_images:
                    max_sort += 1
                    cur.execute(
                        'INSERT INTO ProductImages (product_id, image_url, sort_order) VALUES (?, ?, ?)',
                        (product_id, url, max_sort),
                    )
                cur.execute('DELETE FROM ProductSizes WHERE product_id=?', (product_id,))
                for size_label in size_values:
                    cur.execute(
                        'INSERT INTO ProductSizes (product_id, size_label) VALUES (?, ?)',
                        (product_id, size_label),
                    )
                conn.commit()
            session['admin_status'] = {'type': 'success', 'message': t('admin_product_updated')}
        except Exception as exc:
            err = str(exc).lower()
            if 'unique' in err or '23000' in err or '2627' in err:
                session['admin_status'] = {'type': 'error', 'message': t('admin_serial_exists')}
            else:
                session['admin_status'] = {'type': 'error', 'message': f'{t("admin_error_prefix")}: {exc}'}
            return redirect(url_for('admin_edit_product', product_id=product_id))
        return redirect(url_for('admin_panel'))

    return render_template(
        'admin_edit.html',
        product=product,
        product_images=_fetch_product_image_rows(product_id),
        brands=get_brands(),
        admin_status=session.pop('admin_status', None),
        active_page='admin',
        cart_count=get_cart_count(),
        t=t,
        tv=tv,
    )


def _insert_campaign_story_return_id(cur, params):
    """
    Вставка CampaignStories и получение id. SCOPE_IDENTITY() должен быть в том же T-SQL batch,
    что и INSERT: отдельный execute() в pyodbc — это новый batch, и SCOPE_IDENTITY() даёт NULL.
    """
    cur.execute(
        """
        INSERT INTO CampaignStories (sort_order, headline_en, headline_ru, body_en, body_ru, credits_en, credits_ru)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        SELECT CAST(SCOPE_IDENTITY() AS INT);
        """,
        params,
    )
    sid = None
    while True:
        if cur.description:
            row = cur.fetchone()
            if row is not None and row[0] is not None:
                sid = int(row[0])
                break
        if not cur.nextset():
            break
    if sid is None:
        raise RuntimeError('CampaignStories insert: could not read new id')
    return sid


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


@app.route('/admin/campaign', methods=['GET', 'POST'])
def admin_campaign():
    if request.method == 'POST':
        intro_en = request.form.get('intro_en', '').strip()
        intro_ru = request.form.get('intro_ru', '').strip()
        tagline_en = request.form.get('tagline_en', '').strip()
        tagline_ru = request.form.get('tagline_ru', '').strip()
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute('SELECT COUNT(*) FROM CampaignSettings WHERE id=1')
                if cur.fetchone()[0]:
                    cur.execute(
                        'UPDATE CampaignSettings SET intro_en=?, intro_ru=?, tagline_en=?, tagline_ru=? WHERE id=1',
                        (intro_en, intro_ru, tagline_en, tagline_ru),
                    )
                else:
                    cur.execute(
                        'INSERT INTO CampaignSettings (id, intro_en, intro_ru, tagline_en, tagline_ru) VALUES (1, ?, ?, ?, ?)',
                        (intro_en, intro_ru, tagline_en, tagline_ru),
                    )
                conn.commit()
            session['admin_status'] = {'type': 'success', 'message': t('admin_campaign_settings_saved')}
        except Exception as exc:
            session['admin_status'] = {'type': 'error', 'message': f'{t("admin_error_prefix")}: {exc}'}
        return redirect(url_for('admin_campaign'))
    settings = _fetch_campaign_settings_admin()
    stories = _list_campaign_stories_admin()
    admin_status = session.pop('admin_status', None)
    return render_template(
        'admin_campaign.html',
        settings=settings,
        stories=stories,
        admin_status=admin_status,
        active_page='admin',
        cart_count=get_cart_count(),
        t=t,
    )


@app.route('/admin/campaign/story/new', methods=['GET', 'POST'])
def admin_campaign_story_new():
    if request.method == 'POST':
        headline_en = request.form.get('headline_en', '').strip()
        headline_ru = request.form.get('headline_ru', '').strip()
        if not headline_en and not headline_ru:
            session['admin_status'] = {'type': 'error', 'message': t('admin_story_need_headline')}
            return redirect(url_for('admin_campaign_story_new'))
        urls = _collect_story_image_urls_from_form()
        if not urls:
            session['admin_status'] = {'type': 'error', 'message': t('admin_story_need_image')}
            return redirect(url_for('admin_campaign_story_new'))
        body_en = request.form.get('body_en', '').strip()
        body_ru = request.form.get('body_ru', '').strip()
        credits_en = request.form.get('credits_en', '').strip()
        credits_ru = request.form.get('credits_ru', '').strip()
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute('SELECT COALESCE(MAX(sort_order), -1) + 1 FROM CampaignStories')
                next_sort = int(cur.fetchone()[0])
                sid = _insert_campaign_story_return_id(
                    cur,
                    (
                        next_sort,
                        headline_en or headline_ru,
                        headline_ru or headline_en,
                        body_en,
                        body_ru,
                        credits_en,
                        credits_ru,
                    ),
                )
                for i, url in enumerate(urls):
                    cur.execute(
                        'INSERT INTO CampaignStoryImages (story_id, sort_order, image_url) VALUES (?, ?, ?)',
                        (sid, i, url),
                    )
                conn.commit()
            session['admin_status'] = {'type': 'success', 'message': t('admin_story_created')}
            return redirect(url_for('admin_campaign_story_edit', story_id=sid))
        except Exception as exc:
            session['admin_status'] = {'type': 'error', 'message': f'{t("admin_error_prefix")}: {exc}'}
            return redirect(url_for('admin_campaign_story_new'))
    admin_status = session.pop('admin_status', None)
    return render_template(
        'admin_campaign_story.html',
        story=None,
        images=[],
        admin_status=admin_status,
        active_page='admin',
        cart_count=get_cart_count(),
        t=t,
    )


@app.route('/admin/campaign/story/<int:story_id>', methods=['GET', 'POST'])
def admin_campaign_story_edit(story_id):
    if request.method == 'POST':
        if request.form.get('delete_story'):
            try:
                with get_db_connection() as conn:
                    cur = conn.cursor()
                    cur.execute('DELETE FROM CampaignStories WHERE id=?', (story_id,))
                    conn.commit()
                session['admin_status'] = {'type': 'success', 'message': t('admin_story_deleted')}
            except Exception as exc:
                session['admin_status'] = {'type': 'error', 'message': f'{t("admin_error_prefix")}: {exc}'}
            return redirect(url_for('admin_campaign'))
        headline_en = request.form.get('headline_en', '').strip()
        headline_ru = request.form.get('headline_ru', '').strip()
        if not headline_en and not headline_ru:
            session['admin_status'] = {'type': 'error', 'message': t('admin_story_need_headline')}
            return redirect(url_for('admin_campaign_story_edit', story_id=story_id))
        urls = _collect_story_image_urls_from_form()
        if not urls:
            session['admin_status'] = {'type': 'error', 'message': t('admin_story_need_image')}
            return redirect(url_for('admin_campaign_story_edit', story_id=story_id))
        body_en = request.form.get('body_en', '').strip()
        body_ru = request.form.get('body_ru', '').strip()
        credits_en = request.form.get('credits_en', '').strip()
        credits_ru = request.form.get('credits_ru', '').strip()
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    UPDATE CampaignStories SET headline_en=?, headline_ru=?, body_en=?, body_ru=?, credits_en=?, credits_ru=?
                    WHERE id=?
                    """,
                    (
                        headline_en or headline_ru,
                        headline_ru or headline_en,
                        body_en,
                        body_ru,
                        credits_en,
                        credits_ru,
                        story_id,
                    ),
                )
                cur.execute('DELETE FROM CampaignStoryImages WHERE story_id=?', (story_id,))
                for i, url in enumerate(urls):
                    cur.execute(
                        'INSERT INTO CampaignStoryImages (story_id, sort_order, image_url) VALUES (?, ?, ?)',
                        (story_id, i, url),
                    )
                conn.commit()
            session['admin_status'] = {'type': 'success', 'message': t('admin_story_updated')}
        except Exception as exc:
            session['admin_status'] = {'type': 'error', 'message': f'{t("admin_error_prefix")}: {exc}'}
        return redirect(url_for('admin_campaign_story_edit', story_id=story_id))
    story, images = _fetch_campaign_story_admin(story_id)
    if not story:
        session['admin_status'] = {'type': 'error', 'message': t('admin_product_not_found')}
        return redirect(url_for('admin_campaign'))
    admin_status = session.pop('admin_status', None)
    return render_template(
        'admin_campaign_story.html',
        story=story,
        images=images,
        admin_status=admin_status,
        active_page='admin',
        cart_count=get_cart_count(),
        t=t,
    )


@app.route('/campaign')
def campaign():
    data = get_campaign_index_data()
    return render_template(
        'campaign.html',
        stories=data['stories'],
        campaign_intro=data['campaign_intro'],
        campaign_tagline=data['campaign_tagline'],
        active_page='campaign',
        cart_count=get_cart_count(),
        t=t,
        tc=tc,
    )


@app.route('/campaign/story/<int:story_id>')
def campaign_story(story_id):
    story = get_campaign_story_detail(story_id)
    if not story:
        return 'Not found', 404
    return render_template(
        'campaign_story.html',
        story=story,
        active_page='campaign',
        cart_count=get_cart_count(),
        t=t,
    )

@app.route('/about')
def about():
    return render_template('about.html', active_page='about', cart_count=get_cart_count(), t=t)

@app.route('/api/calculate', methods=['POST'])
def api_calculate():
    data = request.get_json()
    price = int(data.get('price', 0))
    days = int(data.get('days', 1))
    max_days = int(data.get('max_days', 30))
    days = min(max(days, 1), max_days)
    return jsonify({'total': price * days, 'days': days})

@app.context_processor
def inject_globals():
    return {'current_year': datetime.now().year, 'current_lang': get_lang(), 'tc': tc}


if __name__ == '__main__':
    print('\n  Protocol Archive — http://127.0.0.1:5000\n')
    app.run(debug=True, port=5000)