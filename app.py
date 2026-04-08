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
from werkzeug.security import generate_password_hash, check_password_hash
try:
    from deep_translator import GoogleTranslator
except Exception:
    GoogleTranslator = None

from seed_defaults import fallback_products_list

app = Flask(__name__)
app.secret_key = 'protocol-archive-2024'

_brand_coture_typo_fixed = False

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
        'collection': 'Items',
        'couture': 'Couture',
        'campaign': 'Campaign',
        'about': 'About',
        'search': 'Search',
        'menu': 'Menu',
        'menu_close': 'Close',
        'menu_help': 'Can we help you?',
        'account': 'Account',
        'aria_account': 'My account',
        'account_title': 'My account',
        'account_signed_in': 'Signed in as',
        'account_logout': 'Sign out',
        'account_login_title': 'Sign in',
        'account_register_title': 'Create an account',
        'acc_email': 'Email',
        'acc_password': 'Password',
        'acc_password_confirm': 'Confirm password',
        'acc_display_name': 'Name',
        'acc_submit_login': 'Sign in',
        'acc_submit_register': 'Register',
        'acc_err_email_invalid': 'Enter a valid email address.',
        'acc_err_password_short': 'Password must be at least 8 characters.',
        'acc_err_password_mismatch': 'Passwords do not match.',
        'acc_err_name': 'Enter your name.',
        'acc_err_email_used': 'This email is already registered.',
        'acc_err_credentials': 'Incorrect email or password.',
        'acc_ok_register': 'Account created. You are signed in.',
        'acc_ok_login': 'Welcome back.',
        'acc_db_unavailable': 'Account service is temporarily unavailable.',
        'acc_login_required': 'Please sign in to use this.',
        'acc_couture_members_only': 'Couture is available to signed-in members only.',
        'acc_couture_cart_login': 'Sign in to add couture pieces to your bag.',
        'acc_checkout_login_required': 'Sign in to complete rental checkout.',
        'acc_checkout_empty': 'Your bag is empty.',
        'acc_checkout_success': 'Rental request submitted. Added to your account history.',
        'acc_checkout_failed': 'Could not complete checkout right now. Try again later.',
        'account_history_title': 'Rental history',
        'account_history_empty': 'No completed rentals yet.',
        'account_history_order': 'Order',
        'account_history_date': 'Date',
        'account_history_status': 'Status',
        'account_history_items': 'items',
        'account_history_total': 'Total',
        'account_summary_title': 'Your rental summary',
        'account_summary_orders': 'Completed orders',
        'account_summary_items': 'Rented pieces',
        'account_summary_spent': 'Total spend',
        'account_summary_favorite_brand': 'Favorite brand',
        'account_summary_favorite_brand_none': 'No favorite yet',
        'account_quick_actions': 'Quick actions',
        'account_quick_action_bag': 'Open bag',
        'account_quick_action_wishlist': 'Open wishlist',
        'account_quick_action_collection': 'Browse collection',
        'order_status_confirmed': 'Confirmed',
        'members_title': 'Member area',
        'members_intro': 'Tools and access reserved for registered clients.',
        'members_tile_couture': 'Couture archive',
        'members_tile_couture_desc': 'Restricted looks and special handling.',
        'members_tile_wishlist': 'Wishlist',
        'members_tile_wishlist_desc': 'Saved pieces in one place.',
        'members_tile_cart': 'Your bag',
        'members_tile_cart_desc': 'Review items before checkout.',
        'members_tile_campaign': 'Campaign',
        'members_tile_campaign_desc': 'Editorial series and stories.',
        'members_tile_items': 'All items',
        'members_tile_items_desc': 'Full ready-to-wear selection.',
        'members_perks_title': 'Member benefits',
        'members_perk_1': 'Access to the couture archive and product pages.',
        'members_perk_2': 'Priority handling noted on rental requests.',
        'members_perk_3': 'Personal hub for bag, wishlist, and discovery.',
        'members_open': 'Member area',
        'bag': 'Bag',
        'search_placeholder': 'Search by name, brand or code...',
        'filters_title': 'Refine',
        'filters_search': 'Search',
        'filters_brand': 'Brand',
        'filters_brand_all': 'All brands',
        'filters_condition': 'Min. condition',
        'filters_sort': 'Sort',
        'sort_catalog': 'Catalog order',
        'sort_price_low': 'Price · low to high',
        'sort_price_high': 'Price · high to low',
        'filters_max_price': 'Max price / day',
        'filters_apply': 'Apply',
        'filters_reset': 'Reset',
        'refine_label': 'Refine',
        'refine_fab_aria': 'Open filters',
        'refine_drawer_close_aria': 'Close filters',
        'refine_drawer_title': 'Refine',
        'refine_acc_sort': 'Sort by',
        'refine_acc_brand': 'Brand',
        'refine_acc_search': 'Search',
        'refine_acc_condition': 'Condition',
        'refine_acc_item_category': 'Category',
        'filters_item_category_all': 'All categories',
        'refine_acc_price': 'Max price / day',
        'refine_show_results': 'Show results',
        'refine_clear_all': 'Clear all',
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
        'back_to_items': 'Back to items',
        'back_to_couture': 'Back to couture',
        'material': 'Material',
        'made_in': 'Made in',
        'condition': 'Condition',
        'item_category': 'Category',
        'added': 'Added',
        'added_to_bag_title': 'Added to your bag',
        'view_bag': 'View bag',
        'close': 'Close',
        'rental_service': 'Rental service',
        'rental_desc': 'We offer authenticated designer garments for short-term rental. Each piece is carefully inspected, cleaned, and prepared by our in-house atelier before delivery.',
        'duration': 'Duration',
        'duration_desc': 'Rental period is flexible per item. Late returns are charged at 150% of the daily rate.',
        'care': 'Care',
        'care_desc': 'All garments must be returned in the condition received. Do not wash or dry clean. Professional care is included in the rental price.',
        'about_lead': 'Authenticated designer archive for short-term rental with concierge-level handling.',
        'about_faq_title': 'FAQ',
        'about_faq_q1': 'How do I book a rental?',
        'about_faq_a1': 'Choose an item, select rental days, add it to bag, and complete checkout from your account.',
        'about_faq_q2': 'Do you offer size guidance?',
        'about_faq_a2': 'Yes. Product pages include available sizes, and our team can help with fit recommendations.',
        'about_faq_q3': 'What happens if I return late?',
        'about_faq_a3': 'Late returns are charged at 150% of the daily rate for each delayed day.',
        'about_faq_q4': 'Can I request a specific pickup or delivery window?',
        'about_faq_a4': 'Yes, you can leave a note in your request and our team confirms the final schedule.',
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
        'admin_item_category': 'Garment category',
        'admin_item_category_none': 'Not set',
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
        'admin_delete_product': 'Delete product',
        'admin_product_deleted': 'Product deleted',
        'admin_delete_product_confirm': 'Delete this product and all its photos? This cannot be undone.',
        'admin_serial_exists': 'Admin: this serial is already used by another product',
        'admin_current_images': 'Current images (upload below to replace or add)',
        'admin_view_product': 'View on site',
        'admin_clear_extra_images': 'Remove all extra images (keep main only)',
        'admin_remove_images_hint': 'Check photos to remove, then Save changes',
        'admin_drag_photos_hint': 'Drag photos by the handle to reorder. The first photo is the main image on the product page.',
        'admin_cannot_remove_last_image': 'You must keep at least one image',
        'admin_remove_photo': 'Remove',
        'admin_brands_title': 'Brands',
        'admin_brand_products_count': 'products',
        'admin_delete_brand': 'Delete brand',
        'admin_delete_brand_confirm': 'Delete this brand? This action cannot be undone.',
        'admin_brand_deleted': 'Brand deleted',
        'admin_brand_has_products': 'Cannot delete brand with linked products.',
        'admin_brand_not_found': 'Brand not found',
        'account_register_benefits_title': 'Enjoy a unique shopping experience with your personal account',
        'account_register_benefit_1': 'Check details and track status of your rentals and returns',
        'account_register_benefit_2': 'Create a wishlist to save your favorite pieces',
        'account_register_benefit_3': 'Manage private appointments and custom requests',
        'account_register_benefit_4': 'Receive tailored assistance from client service',
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
        'hero_title': 'Protocol Archive',
        'hero_cta': 'Discover items',
        'hero_service_line': 'Authenticated designer clothing rental',
        'hero_slogan': 'Curated pieces. Short-term wear. Archive precision.',
        'wishlist': 'Wishlist',
        'wishlist_empty': 'No saved pieces yet',
        'aria_wishlist_page': 'Wishlist',
        'aria_add_wishlist': 'Add to wishlist',
        'aria_remove_wishlist': 'Remove from wishlist',
        'aria_bag': 'Shopping bag',
    },
    'ru': {
        'enter': 'Войти',
        'collection': 'Вещи',
        'couture': 'Кутюр',
        'campaign': 'Кампания',
        'about': 'О нас',
        'search': 'Поиск',
        'menu': 'Меню',
        'menu_close': 'Закрыть',
        'menu_help': 'Нужна помощь?',
        'account': 'Аккаунт',
        'aria_account': 'Личный кабинет',
        'account_title': 'Личный кабинет',
        'account_signed_in': 'Вы вошли как',
        'account_logout': 'Выйти',
        'account_login_title': 'Вход',
        'account_register_title': 'Регистрация',
        'acc_email': 'Email',
        'acc_password': 'Пароль',
        'acc_password_confirm': 'Повторите пароль',
        'acc_display_name': 'Имя',
        'acc_submit_login': 'Войти',
        'acc_submit_register': 'Зарегистрироваться',
        'acc_err_email_invalid': 'Укажите корректный email.',
        'acc_err_password_short': 'Пароль не короче 8 символов.',
        'acc_err_password_mismatch': 'Пароли не совпадают.',
        'acc_err_name': 'Укажите имя.',
        'acc_err_email_used': 'Этот email уже зарегистрирован.',
        'acc_err_credentials': 'Неверный email или пароль.',
        'acc_ok_register': 'Аккаунт создан. Вы вошли.',
        'acc_ok_login': 'С возвращением.',
        'acc_db_unavailable': 'Сервис аккаунтов временно недоступен.',
        'acc_login_required': 'Войдите в аккаунт, чтобы пользоваться этим.',
        'acc_couture_members_only': 'Раздел кутюр доступен только зарегистрированным участникам.',
        'acc_couture_cart_login': 'Войдите, чтобы добавить кутюр в корзину.',
        'acc_checkout_login_required': 'Войдите, чтобы оформить аренду.',
        'acc_checkout_empty': 'Корзина пуста.',
        'acc_checkout_success': 'Заявка на аренду оформлена и добавлена в историю кабинета.',
        'acc_checkout_failed': 'Не удалось оформить аренду сейчас. Попробуйте позже.',
        'account_history_title': 'История аренд',
        'account_history_empty': 'Пока нет оформленных аренд.',
        'account_history_order': 'Заказ',
        'account_history_date': 'Дата',
        'account_history_status': 'Статус',
        'account_history_items': 'позиций',
        'account_history_total': 'Итого',
        'account_summary_title': 'Сводка по арендам',
        'account_summary_orders': 'Оформленных заказов',
        'account_summary_items': 'Арендованных вещей',
        'account_summary_spent': 'Суммарно',
        'account_summary_favorite_brand': 'Любимый бренд',
        'account_summary_favorite_brand_none': 'Пока нет',
        'account_quick_actions': 'Быстрые действия',
        'account_quick_action_bag': 'Открыть корзину',
        'account_quick_action_wishlist': 'Открыть избранное',
        'account_quick_action_collection': 'Смотреть каталог',
        'order_status_confirmed': 'Подтверждён',
        'members_title': 'Зона участника',
        'members_intro': 'Доступ и функции для зарегистрированных клиентов.',
        'members_tile_couture': 'Архив кутюр',
        'members_tile_couture_desc': 'Закрытая витрина и особое сопровождение.',
        'members_tile_wishlist': 'Избранное',
        'members_tile_wishlist_desc': 'Сохранённые вещи в одном месте.',
        'members_tile_cart': 'Корзина',
        'members_tile_cart_desc': 'Проверьте состав перед оформлением.',
        'members_tile_campaign': 'Кампания',
        'members_tile_campaign_desc': 'Редакционные серии и истории.',
        'members_tile_items': 'Все вещи',
        'members_tile_items_desc': 'Полная подборка ready-to-wear.',
        'members_perks_title': 'Возможности для участников',
        'members_perk_1': 'Доступ к архиву кутюр и карточкам изделий.',
        'members_perk_2': 'Приоритетная обработка заявок на аренду.',
        'members_perk_3': 'Личный центр: корзина, избранное и навигация.',
        'members_open': 'Зона участника',
        'bag': 'Корзина',
        'search_placeholder': 'Название, бренд или артикул...',
        'filters_title': 'Фильтры',
        'filters_search': 'Поиск',
        'filters_brand': 'Бренд',
        'filters_brand_all': 'Все бренды',
        'filters_condition': 'Мин. состояние',
        'filters_sort': 'Сортировка',
        'sort_catalog': 'Как в каталоге',
        'sort_price_low': 'Цена · по возрастанию',
        'sort_price_high': 'Цена · по убыванию',
        'filters_max_price': 'Макс. цена / день',
        'filters_apply': 'Применить',
        'filters_reset': 'Сбросить',
        'refine_label': 'Подбор',
        'refine_fab_aria': 'Открыть фильтры',
        'refine_drawer_close_aria': 'Закрыть фильтры',
        'refine_drawer_title': 'Подбор',
        'refine_acc_sort': 'Сортировка',
        'refine_acc_brand': 'Бренд',
        'refine_acc_search': 'Поиск',
        'refine_acc_condition': 'Состояние',
        'refine_acc_item_category': 'Категория',
        'filters_item_category_all': 'Все категории',
        'refine_acc_price': 'Макс. цена / день',
        'refine_show_results': 'Показать',
        'refine_clear_all': 'Сбросить всё',
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
        'back_to_items': 'Назад к вещам',
        'back_to_couture': 'Назад в кутюр',
        'material': 'Материал',
        'made_in': 'Производство',
        'condition': 'Состояние',
        'item_category': 'Категория',
        'added': 'Добавлено',
        'added_to_bag_title': 'Добавлено в корзину',
        'view_bag': 'Открыть корзину',
        'close': 'Закрыть',
        'rental_service': 'Сервис аренды',
        'rental_desc': 'Мы предоставляем аутентифицированную дизайнерскую одежду для краткосрочной аренды. Каждая вещь проходит тщательную проверку и подготовку.',
        'duration': 'Сроки',
        'duration_desc': 'Срок аренды гибкий для каждой вещи. За просрочку взимается 150% от дневной ставки.',
        'care': 'Уход',
        'care_desc': 'Вещи должны быть возвращены в полученном состоянии. Не стирать. Профессиональный уход включён в стоимость.',
        'about_lead': 'Аутентифицированный дизайнерский архив для краткосрочной аренды с персональным сопровождением.',
        'about_faq_title': 'FAQ',
        'about_faq_q1': 'Как оформить аренду?',
        'about_faq_a1': 'Выберите вещь, укажите срок аренды, добавьте в корзину и оформите заказ через аккаунт.',
        'about_faq_q2': 'Есть ли помощь с подбором размера?',
        'about_faq_a2': 'Да. На страницах товаров указаны доступные размеры, а команда поможет с рекомендацией по посадке.',
        'about_faq_q3': 'Что будет при позднем возврате?',
        'about_faq_a3': 'За каждый день просрочки начисляется 150% от дневной ставки аренды.',
        'about_faq_q4': 'Можно выбрать удобное окно доставки или самовывоза?',
        'about_faq_a4': 'Да, укажите пожелание в заявке, а команда подтвердит финальное время.',
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
        'admin_item_category': 'Категория вещи',
        'admin_item_category_none': 'Не задана',
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
        'admin_delete_product': 'Удалить товар',
        'admin_product_deleted': 'Товар удалён',
        'admin_delete_product_confirm': 'Удалить этот товар и все его фото? Действие нельзя отменить.',
        'admin_serial_exists': 'Админ: такой артикул уже у другого товара',
        'admin_current_images': 'Текущие фото (загрузите ниже, чтобы заменить или добавить)',
        'admin_view_product': 'Смотреть на сайте',
        'admin_clear_extra_images': 'Удалить все дополнительные фото (главное оставить)',
        'admin_remove_images_hint': 'Отметьте фото для удаления и нажмите «Сохранить»',
        'admin_drag_photos_hint': 'Перетаскивайте фото за ручку, чтобы поменять порядок. Первое фото — главное на карточке товара.',
        'admin_cannot_remove_last_image': 'Нужно оставить хотя бы одно фото',
        'admin_remove_photo': 'Удалить',
        'admin_brands_title': 'Бренды',
        'admin_brand_products_count': 'товаров',
        'admin_delete_brand': 'Удалить бренд',
        'admin_delete_brand_confirm': 'Удалить этот бренд? Действие нельзя отменить.',
        'admin_brand_deleted': 'Бренд удалён',
        'admin_brand_has_products': 'Нельзя удалить бренд, пока к нему привязаны товары.',
        'admin_brand_not_found': 'Бренд не найден',
        'account_register_benefits_title': 'Личный аккаунт открывает дополнительные возможности',
        'account_register_benefit_1': 'Проверяйте детали и отслеживайте статус аренд и возвратов',
        'account_register_benefit_2': 'Сохраняйте понравившиеся вещи в избранное',
        'account_register_benefit_3': 'Управляйте приватными заявками и особыми запросами',
        'account_register_benefit_4': 'Получайте персональную поддержку клиентского сервиса',
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
        'hero_title': 'Protocol Archive',
        'hero_cta': 'Смотреть вещи',
        'hero_service_line': 'Сервис аренды аутентичной дизайнерской одежды',
        'hero_slogan': 'Отобранные вещи. Краткий срок. Дух архива.',
        'wishlist': 'Избранное',
        'wishlist_empty': 'Пока нет сохранённых вещей',
        'aria_wishlist_page': 'Избранное',
        'aria_add_wishlist': 'Добавить в избранное',
        'aria_remove_wishlist': 'Убрать из избранного',
        'aria_bag': 'Корзина',
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
        'Steel': 'Сталь',
        'japanese organic denim': 'Японский органический деним',
    }
}

SPLASH_IMAGE = 'splash.jpg'

PRODUCTS = fallback_products_list()

BRANDS = [
    {'name': 'Maison Margiela', 'slug': 'Maison Margiela', 'css_class': 'brand-margiela'},
    {'name': 'Balenciaga', 'slug': 'Balenciaga', 'css_class': 'brand-balenciaga'},
    {'name': 'Balenciaga Couture', 'slug': 'Balenciaga Couture', 'css_class': 'brand-balenciaga'},
    {'name': 'Rick Owens', 'slug': 'Rick Owens', 'css_class': 'brand-rickowens'},
    {'name': 'YZY', 'slug': 'YZY', 'css_class': 'brand-yzy'},
    {'name': 'Raf Simons', 'slug': 'Raf Simons', 'css_class': 'brand-raf-simons'},
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

# Тип вещи для витрины (не путать с category rtw/couture в БД)
ITEM_CATEGORIES = [
    {'slug': 'bags', 'en': 'Bags', 'ru': 'Сумки'},
    {'slug': 'boots', 'en': 'Boots', 'ru': 'Ботинки'},
    {'slug': 'coats_jackets', 'en': 'Coats & jackets', 'ru': 'Пальто и куртки'},
    {'slug': 'dresses', 'en': 'Dresses', 'ru': 'Платья'},
    {'slug': 'flats', 'en': 'Flats', 'ru': 'Балетки'},
    {'slug': 'footwear', 'en': 'Footwear', 'ru': 'Обувь'},
    {'slug': 'heels', 'en': 'Heels', 'ru': 'Каблуки'},
    {'slug': 'jewelry', 'en': 'Jewelry', 'ru': 'Украшения'},
    {'slug': 'knitwear', 'en': 'Knitwear', 'ru': 'Трикотаж'},
    {'slug': 'pants_denim', 'en': 'Pants and denim', 'ru': 'Брюки и деним'},
    {'slug': 'pumps', 'en': 'Pumps', 'ru': 'Туфли'},
]
ITEM_CATEGORY_SLUGS = frozenset(c['slug'] for c in ITEM_CATEGORIES)


def normalize_item_category_slug(raw):
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    return s if s in ITEM_CATEGORY_SLUGS else None


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


def get_wishlist_ids():
    raw = session.get('wishlist') or []
    out = []
    for x in raw:
        try:
            out.append(int(x))
        except (TypeError, ValueError):
            continue
    return out


ACC_EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


def get_current_user():
    uid = session.get('user_id')
    if uid is None:
        return None
    try:
        uid_int = int(uid)
    except (TypeError, ValueError):
        return None
    return {
        'id': uid_int,
        'email': session.get('user_email') or '',
        'display_name': session.get('user_display_name') or '',
    }


def _clear_user_session():
    for k in ('user_id', 'user_email', 'user_display_name'):
        session.pop(k, None)
    session.modified = True


def ensure_app_users_table():
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            IF OBJECT_ID('AppUsers', 'U') IS NULL
            CREATE TABLE AppUsers (
                id INT IDENTITY(1,1) PRIMARY KEY,
                email NVARCHAR(255) NOT NULL UNIQUE,
                password_hash NVARCHAR(500) NOT NULL,
                display_name NVARCHAR(120) NOT NULL,
                created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
            );
            """
        )
        conn.commit()


def ensure_rental_orders_tables():
    ensure_app_users_table()
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            IF OBJECT_ID('RentalOrders', 'U') IS NULL
            CREATE TABLE RentalOrders (
                id INT IDENTITY(1,1) PRIMARY KEY,
                user_id INT NOT NULL,
                status NVARCHAR(30) NOT NULL DEFAULT N'confirmed',
                total_items INT NOT NULL,
                total_price INT NOT NULL,
                created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
                CONSTRAINT FK_RentalOrders_AppUsers FOREIGN KEY (user_id) REFERENCES AppUsers(id) ON DELETE CASCADE
            );
            """
        )
        cur.execute(
            """
            IF OBJECT_ID('RentalOrderItems', 'U') IS NULL
            CREATE TABLE RentalOrderItems (
                id INT IDENTITY(1,1) PRIMARY KEY,
                order_id INT NOT NULL,
                product_id INT NULL,
                serial NVARCHAR(50) NOT NULL,
                brand_name NVARCHAR(120) NOT NULL,
                product_name NVARCHAR(180) NOT NULL,
                size_label NVARCHAR(40) NULL,
                rental_days INT NOT NULL,
                price_per_day INT NOT NULL,
                line_total INT NOT NULL,
                image_url NVARCHAR(500) NULL,
                CONSTRAINT FK_RentalOrderItems_Order FOREIGN KEY (order_id) REFERENCES RentalOrders(id) ON DELETE CASCADE
            );
            """
        )
        conn.commit()


def ensure_legacy_balenciaga_coture_brand_rename():
    """Переименовать бренд Balenciaga Coture → Balenciaga Couture в уже существующей БД."""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT OBJECT_ID('dbo.Brands', 'U')")
            if cur.fetchone()[0] is None:
                return
            cur.execute("SELECT 1 FROM Brands WHERE name = ?", ("Balenciaga Coture",))
            if not cur.fetchone():
                return
            cur.execute("SELECT 1 FROM Brands WHERE name = ?", ("Balenciaga Couture",))
            if cur.fetchone():
                return
            cur.execute(
                "UPDATE Brands SET name = ?, slug = ? WHERE name = ?",
                ("Balenciaga Couture", "Balenciaga Couture", "Balenciaga Coture"),
            )
            cur.execute("SELECT OBJECT_ID('dbo.RentalOrderItems', 'U')")
            if cur.fetchone()[0] is not None:
                cur.execute(
                    "UPDATE RentalOrderItems SET brand_name = ? WHERE brand_name = ?",
                    ("Balenciaga Couture", "Balenciaga Coture"),
                )
            conn.commit()
    except Exception:
        pass


@app.before_request
def _run_brand_coture_typo_fix_once():
    global _brand_coture_typo_fixed
    if _brand_coture_typo_fixed:
        return
    _brand_coture_typo_fixed = True
    ensure_legacy_balenciaga_coture_brand_rename()


def _create_rental_order(user_id, cart_items):
    if not cart_items:
        return None
    ensure_rental_orders_tables()
    total_price = sum(int(i.get('total_price', 0) or 0) for i in cart_items)
    total_items = len(cart_items)
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO RentalOrders (user_id, status, total_items, total_price)
            OUTPUT INSERTED.id
            VALUES (?, N'confirmed', ?, ?)
            """,
            (int(user_id), total_items, total_price),
        )
        row = cur.fetchone()
        order_id = int(row[0]) if row and row[0] is not None else None
        if not order_id:
            conn.rollback()
            return None
        for item in cart_items:
            cur.execute(
                """
                INSERT INTO RentalOrderItems (
                    order_id, product_id, serial, brand_name, product_name, size_label,
                    rental_days, price_per_day, line_total, image_url
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    order_id,
                    int(item.get('product_id')) if item.get('product_id') is not None else None,
                    str(item.get('serial') or ''),
                    str(item.get('brand') or ''),
                    str(item.get('name') or ''),
                    (item.get('size') or '').strip() or None,
                    int(item.get('days', 0) or 0),
                    int(item.get('price_per_day', 0) or 0),
                    int(item.get('total_price', 0) or 0),
                    str(item.get('image') or ''),
                ),
            )
        conn.commit()
        return order_id


def _fetch_user_rental_history(user_id, limit=8):
    ensure_rental_orders_tables()
    orders = []
    stats = {
        'orders_count': 0,
        'items_count': 0,
        'total_spend': 0,
        'favorite_brand': '',
    }
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT TOP (?) id, status, total_items, total_price, created_at
            FROM RentalOrders
            WHERE user_id = ?
            ORDER BY created_at DESC, id DESC
            """,
            (int(limit), int(user_id)),
        )
        order_rows = cur.fetchall()
        if order_rows:
            order_ids = [int(r[0]) for r in order_rows]
            placeholders = ','.join('?' for _ in order_ids)
            cur.execute(
                f"""
                SELECT order_id, serial, brand_name, product_name, size_label, rental_days, line_total, image_url
                FROM RentalOrderItems
                WHERE order_id IN ({placeholders})
                ORDER BY order_id DESC, id ASC
                """,
                tuple(order_ids),
            )
            items_by_order = {}
            for row in cur.fetchall():
                oid = int(row[0])
                items_by_order.setdefault(oid, []).append({
                    'serial': row[1] or '',
                    'brand_name': row[2] or '',
                    'product_name': row[3] or '',
                    'size_label': row[4] or '',
                    'rental_days': int(row[5]) if row[5] is not None else 0,
                    'line_total': int(row[6]) if row[6] is not None else 0,
                    'image_url': row[7] or '',
                })
            for row in order_rows:
                oid = int(row[0])
                orders.append({
                    'id': oid,
                    'status': row[1] or 'confirmed',
                    'total_items': int(row[2]) if row[2] is not None else 0,
                    'total_price': int(row[3]) if row[3] is not None else 0,
                    'created_at': row[4],
                    'items': items_by_order.get(oid, []),
                })
        cur.execute(
            """
            SELECT
                COUNT(*) AS orders_count,
                COALESCE(SUM(total_items), 0) AS items_count,
                COALESCE(SUM(total_price), 0) AS total_spend
            FROM RentalOrders
            WHERE user_id = ?
            """,
            (int(user_id),),
        )
        base_stats = cur.fetchone()
        if base_stats:
            stats['orders_count'] = int(base_stats[0] or 0)
            stats['items_count'] = int(base_stats[1] or 0)
            stats['total_spend'] = int(base_stats[2] or 0)
        cur.execute(
            """
            SELECT TOP 1 brand_name, COUNT(*) AS c
            FROM RentalOrderItems i
            INNER JOIN RentalOrders o ON o.id = i.order_id
            WHERE o.user_id = ?
            GROUP BY brand_name
            ORDER BY c DESC, brand_name ASC
            """,
            (int(user_id),),
        )
        fav = cur.fetchone()
        if fav and fav[0]:
            stats['favorite_brand'] = str(fav[0])
    return orders, stats


def _user_fetch_by_email(email_norm):
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            'SELECT id, email, password_hash, display_name FROM AppUsers WHERE email = ?',
            (email_norm,),
        )
        return cur.fetchone()


def _user_insert(email_norm, password_plain, display_name):
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO AppUsers (email, password_hash, display_name)
            OUTPUT INSERTED.id
            VALUES (?, ?, ?)
            """,
            (email_norm, generate_password_hash(password_plain), display_name),
        )
        row = cur.fetchone()
        conn.commit()
        return int(row[0])


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


@app.route('/set-lang/<lang>')
def set_lang(lang):
    if lang in TRANSLATIONS:
        session['lang'] = lang
    return redirect(request.referrer or url_for('home'))

@app.route('/')
def home():
    kw = _collection_listing_data(for_home=True)
    return render_template(
        'collection.html',
        show_hero=True,
        hero_image=url_for('static', filename=SPLASH_IMAGE),
        active_page='collection',
        cart_count=get_cart_count(),
        t=t,
        tv=tv,
        **kw,
    )

@app.route('/collection')
def collection():
    kw = _collection_listing_data(for_home=False)
    return render_template(
        'collection.html',
        show_hero=True,
        hero_image=url_for('static', filename=SPLASH_IMAGE),
        active_page='collection',
        cart_count=get_cart_count(),
        t=t,
        tv=tv,
        **kw,
    )

@app.route('/couture')
def couture():
    if not get_current_user():
        flash(t('acc_couture_members_only'), 'error')
        return redirect(url_for('account'))
    products = filter_products(category='couture')
    return render_template('couture.html', products=products, active_page='couture', cart_count=get_cart_count(), t=t, tv=tv)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = find_product(product_id)
    if not product:
        return 'Not found', 404
    if product.get('category') == 'couture' and not get_current_user():
        flash(t('acc_couture_members_only'), 'error')
        return redirect(url_for('account'))
    days = int(request.args.get('days', 1))
    days = min(max(days, 1), product['max_days'])
    total = product['price'] * days
    return render_template('product.html', product=product, selected_days=days, total_price=total, active_page='product', cart_count=get_cart_count(), t=t, tv=tv)


@app.route('/wishlist/toggle', methods=['POST'])
def wishlist_toggle():
    if not request.is_json:
        return jsonify(ok=False, error='json'), 400
    payload = request.get_json(silent=True) or {}
    try:
        product_id = int(payload.get('product_id'))
    except (TypeError, ValueError):
        return jsonify(ok=False, error='bad_id'), 400
    if not find_product(product_id):
        return jsonify(ok=False, error='not_found'), 404
    ids = list(get_wishlist_ids())
    if product_id in ids:
        ids = [i for i in ids if i != product_id]
        in_wish = False
    else:
        ids.append(product_id)
        in_wish = True
    session['wishlist'] = ids
    session.modified = True
    return jsonify(ok=True, in_wishlist=in_wish, count=len(ids))


@app.route('/wishlist')
def wishlist_page():
    ids = get_wishlist_ids()
    products = []
    for pid in ids:
        p = find_product(pid)
        if p:
            products.append(p)
    return render_template(
        'wishlist.html',
        products=products,
        active_page='wishlist',
        cart_count=get_cart_count(),
        t=t,
        tv=tv,
    )


def _cart_add_wants_json():
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return True
    return request.accept_mimetypes.best_match(['application/json', 'text/html']) == 'application/json'


@app.route('/cart/add', methods=['POST'])
def add_to_cart():
    product_id = int(request.form.get('product_id'))
    days = int(request.form.get('days', 1))
    size = request.form.get('size', '')
    product = find_product(product_id)
    if not product:
        if _cart_add_wants_json():
            return jsonify(ok=False, error='not_found'), 404
        return redirect(url_for('home'))
    if product.get('category') == 'couture' and not get_current_user():
        if _cart_add_wants_json():
            return jsonify(ok=False, error='login_required'), 403
        flash(t('acc_couture_cart_login'), 'error')
        return redirect(url_for('account'))
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
    if _cart_add_wants_json():
        return jsonify(ok=True, cart_count=len(cart), product_name=product['name'])
    flash(product['name'], 'cart_added')
    return redirect(url_for('product_detail', product_id=product_id, days=days))

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


@app.route('/cart/checkout', methods=['POST'])
def cart_checkout():
    user = get_current_user()
    if not user:
        flash(t('acc_checkout_login_required'), 'error')
        return redirect(url_for('account'))
    cart_items = get_cart()
    if not cart_items:
        flash(t('acc_checkout_empty'), 'error')
        return redirect(url_for('cart'))
    try:
        order_id = _create_rental_order(user['id'], cart_items)
    except Exception:
        order_id = None
    if not order_id:
        flash(t('acc_checkout_failed'), 'error')
        return redirect(url_for('cart'))
    session['cart'] = []
    session.modified = True
    flash(t('acc_checkout_success'), 'success')
    return redirect(url_for('account'))


@app.route('/account', methods=['GET'])
def account():
    history_orders = []
    history_stats = None
    user = get_current_user()
    if user:
        try:
            history_orders, history_stats = _fetch_user_rental_history(user['id'])
        except Exception:
            history_orders, history_stats = [], None
    return render_template(
        'account.html',
        active_page='account',
        cart_count=get_cart_count(),
        history_orders=history_orders,
        history_stats=history_stats,
        t=t,
    )


@app.route('/account/login', methods=['POST'])
def account_login():
    email = (request.form.get('email') or '').strip().lower()
    password = request.form.get('password') or ''
    if not email or not password:
        flash(t('acc_err_credentials'), 'error')
        return redirect(url_for('account'))
    try:
        ensure_app_users_table()
        row = _user_fetch_by_email(email)
    except Exception:
        flash(t('acc_db_unavailable'), 'error')
        return redirect(url_for('account'))
    if not row or not check_password_hash(row[2], password):
        flash(t('acc_err_credentials'), 'error')
        return redirect(url_for('account'))
    session['user_id'] = int(row[0])
    session['user_email'] = row[1]
    session['user_display_name'] = row[3]
    session.modified = True
    flash(t('acc_ok_login'), 'success')
    return redirect(url_for('account'))


@app.route('/account/register', methods=['POST'])
def account_register():
    email = (request.form.get('email') or '').strip().lower()
    password = request.form.get('password') or ''
    password2 = request.form.get('password_confirm') or ''
    display_name = (request.form.get('display_name') or '').strip()
    if not display_name:
        flash(t('acc_err_name'), 'error')
        return redirect(url_for('account'))
    if len(display_name) > 120:
        display_name = display_name[:120]
    if not ACC_EMAIL_RE.match(email):
        flash(t('acc_err_email_invalid'), 'error')
        return redirect(url_for('account'))
    if len(password) < 8:
        flash(t('acc_err_password_short'), 'error')
        return redirect(url_for('account'))
    if password != password2:
        flash(t('acc_err_password_mismatch'), 'error')
        return redirect(url_for('account'))
    try:
        ensure_app_users_table()
        if _user_fetch_by_email(email):
            flash(t('acc_err_email_used'), 'error')
            return redirect(url_for('account'))
        new_id = _user_insert(email, password, display_name)
    except Exception as e:
        err = str(e).upper()
        if '23000' in str(e) or 'UNIQUE' in err or '2627' in str(e):
            flash(t('acc_err_email_used'), 'error')
            return redirect(url_for('account'))
        flash(t('acc_db_unavailable'), 'error')
        return redirect(url_for('account'))
    session['user_id'] = new_id
    session['user_email'] = email
    session['user_display_name'] = display_name
    session.modified = True
    flash(t('acc_ok_register'), 'success')
    return redirect(url_for('account'))


@app.route('/account/logout', methods=['POST'])
def account_logout():
    _clear_user_session()
    return redirect(url_for('account'))


@app.route('/members')
def members():
    if not get_current_user():
        flash(t('acc_login_required'), 'error')
        return redirect(url_for('account'))
    return render_template(
        'members.html',
        active_page='members',
        cart_count=get_cart_count(),
        t=t,
    )


@app.route('/search')
def search():
    q = request.args.get('q', '').strip()
    if not q:
        results = []
    else:
        # Состояние вещи настраивается в фильтрах каталога, не на странице поиска
        results = filter_products(
            category=None,
            query=q,
            brand=None,
            min_condition=0,
            max_price=None,
            sort='id',
        )
    return render_template(
        'search.html',
        brands=get_brands(),
        results=results,
        query=q,
        active_page='search',
        cart_count=get_cart_count(),
        t=t,
        tv=tv,
    )

@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    if request.method == 'POST':
        try:
            category = request.form.get('category', '').strip() or 'rtw'
            item_category = normalize_item_category_slug(request.form.get('item_category'))
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
                    INSERT INTO Products (brand_id, category, item_category, serial, name, price, max_days, condition_score, material, origin, [condition], main_image)
                    OUTPUT INSERTED.id
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''',
                    (
                        brand_id,
                        category,
                        item_category,
                        serial,
                        name,
                        price,
                        max_days,
                        condition_score,
                        material,
                        origin,
                        condition,
                        main_image,
                    ),
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
        brands_admin=get_admin_brands(),
        admin_status=admin_status,
        active_page='admin',
        cart_count=get_cart_count(),
        t=t,
        tv=tv
    )


@app.route('/admin/product/<int:product_id>/delete', methods=['POST'])
def admin_delete_product(product_id):
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute('SELECT id FROM Products WHERE id = ?', (product_id,))
            if not cur.fetchone():
                session['admin_status'] = {'type': 'error', 'message': t('admin_product_not_found')}
                return redirect(url_for('admin_panel'))
            cur.execute('DELETE FROM Products WHERE id = ?', (product_id,))
            conn.commit()
        session['admin_status'] = {'type': 'success', 'message': t('admin_product_deleted')}
    except Exception as exc:
        session['admin_status'] = {'type': 'error', 'message': f'{t("admin_error_prefix")}: {exc}'}
    return redirect(url_for('admin_panel'))


@app.route('/admin/brand/<int:brand_id>/delete', methods=['POST'])
def admin_delete_brand(brand_id):
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute('SELECT id FROM Brands WHERE id = ?', (brand_id,))
            if not cur.fetchone():
                session['admin_status'] = {'type': 'error', 'message': t('admin_brand_not_found')}
                return redirect(url_for('admin_panel'))
            cur.execute('SELECT COUNT(*) FROM Products WHERE brand_id = ?', (brand_id,))
            linked_products = int(cur.fetchone()[0] or 0)
            if linked_products > 0:
                session['admin_status'] = {'type': 'error', 'message': t('admin_brand_has_products')}
                return redirect(url_for('admin_panel'))
            cur.execute('DELETE FROM Brands WHERE id = ?', (brand_id,))
            conn.commit()
        session['admin_status'] = {'type': 'success', 'message': t('admin_brand_deleted')}
    except Exception as exc:
        session['admin_status'] = {'type': 'error', 'message': f'{t("admin_error_prefix")}: {exc}'}
    return redirect(url_for('admin_panel'))


@app.route('/admin/product/<int:product_id>/edit', methods=['GET', 'POST'])
def admin_edit_product(product_id):
    product = find_product(product_id)
    if not product:
        session['admin_status'] = {'type': 'error', 'message': t('admin_product_not_found')}
        return redirect(url_for('admin_panel'))

    if request.method == 'POST':
        try:
            category = request.form.get('category', '').strip() or 'rtw'
            item_category = normalize_item_category_slug(request.form.get('item_category'))
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
            ordered_ids = []
            for x in request.form.getlist('image_order_id'):
                try:
                    ordered_ids.append(int(x))
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
                try:
                    main_image = _apply_admin_product_image_changes(
                        cur, product_id, remove_ids, ordered_ids, uploaded_main, extra_images
                    )
                except ValueError as ve:
                    if str(ve) == '__LAST_IMAGE__':
                        session['admin_status'] = {'type': 'error', 'message': t('admin_cannot_remove_last_image')}
                        return redirect(url_for('admin_edit_product', product_id=product_id))
                    raise
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
                    UPDATE Products SET brand_id=?, category=?, item_category=?, serial=?, name=?, price=?, max_days=?,
                    condition_score=?, material=?, origin=?, [condition]=?, main_image=?
                    WHERE id=?
                    ''',
                    (
                        brand_id,
                        category,
                        item_category,
                        serial,
                        name,
                        price,
                        max_days,
                        condition_score,
                        material,
                        origin,
                        condition,
                        main_image,
                        product_id,
                    ),
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
    wids = get_wishlist_ids()
    lang = get_lang()

    def item_category_label(slug):
        if not slug:
            return ''
        for c in ITEM_CATEGORIES:
            if c['slug'] == slug:
                return c.get(lang) or c['en']
        return str(slug)

    return {
        'current_year': datetime.now().year,
        'current_lang': lang,
        'tc': tc,
        'wishlist_ids': frozenset(wids),
        'wishlist_count': len(wids),
        'current_user': get_current_user(),
        'item_categories': ITEM_CATEGORIES,
        'item_category_label': item_category_label,
    }


if __name__ == '__main__':
    print('\n  Protocol Archive — http://127.0.0.1:5000\n')
    app.run(debug=True, port=5000)