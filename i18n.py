"""UI strings, value maps, and translation helpers (t, tc, tv)."""
import hashlib
import re
from flask import session

try:
    from deep_translator import GoogleTranslator
except Exception:
    GoogleTranslator = None

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
        'acc_checkout_unavailable': 'Some items are unavailable for selected dates. Update your bag and try again.',
        'account_history_title': 'Rental history',
        'account_history_empty': 'No completed rentals yet.',
        'account_history_order': 'Order',
        'account_history_date': 'Date',
        'account_history_status': 'Status',
        'account_history_period': 'Rental period',
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
        'order_status_created': 'Created',
        'order_status_confirmed': 'Confirmed',
        'order_status_in_rent': 'In rent',
        'order_status_returned': 'Returned',
        'order_status_cancelled': 'Cancelled',
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
        'rental_start_date': 'Start date',
        'rental_end_date': 'Return date',
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
        'admin_orders_title': 'Recent rental orders',
        'admin_order_user': 'Client',
        'admin_order_period': 'Period',
        'admin_order_status': 'Status',
        'admin_order_items': 'Items',
        'admin_order_update_status': 'Update status',
        'admin_order_status_updated': 'Order status updated',
        'admin_order_not_found': 'Order not found',
        'admin_order_status_invalid': 'Invalid order status',
        'admin_order_empty': 'No rental orders yet.',
        'product_available_for_dates': 'Available for selected dates',
        'product_unavailable_for_dates': 'Unavailable for selected dates',
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
        'lux_badge_new': 'New',
        'lux_hero_eyebrow': 'Authenticated designer clothing rental',
        'lux_hero_headline': 'The Wardrobe Your Evening Deserves',
        'lux_hero_lead': 'Pieces from our archive — authenticated, prepared to ship, and booked for the dates you choose.',
        'lux_start_badge': 'How it works',
        'lux_start_title': 'Choose it. Wear it. Return it.',
        'lux_start_copy': 'Browse the catalog, book your rental window, receive a garment ready to wear, then return it after your plans. Care and inspection are part of the service.',
        'lux_cap_badge': 'Capabilities',
        'lux_cap_title': 'Archive access. No friction.',
        'lux_chess1_title': 'Made to stand out. Ready to rent.',
        'lux_chess1_body': 'Each garment is photographed, inspected, prepared, and listed with clear rental terms before it reaches your bag.',
        'lux_chess1_cta': 'Browse pieces',
        'lux_chess2_title': 'Find the right piece, faster.',
        'lux_chess2_body': 'Filter by brand, category, condition, and price. Keep a shortlist in your wishlist, then finish the rental from your account.',
        'lux_chess2_cta': 'Open wishlist',
        'lux_why_badge': 'Why us',
        'lux_why_title': 'The difference is in the handling.',
        'lux_feat1_title': 'Days, not months',
        'lux_feat1_body': 'Book when your plans are set — the flow stays fast even close to the date.',
        'lux_feat2_title': 'Carefully curated',
        'lux_feat2_body': 'Garments chosen with an eye for silhouette, condition, and occasion.',
        'lux_feat3_title': 'Clear sizing',
        'lux_feat3_body': 'Sizes and details stay visible before you commit to a rental.',
        'lux_feat4_title': 'A secure workflow',
        'lux_feat4_body': 'Account, wishlist, bag, and checkout keep the entire rental in one place.',
        'lux_stats_sr': 'Archive at a glance',
        'lux_stat_pieces': 'Pieces in catalog',
        'lux_stat_brands': 'Brands represented',
        'lux_stat_condition': 'Condition on record',
        'lux_stat_days': 'Rental window (max. days)',
        'lux_test_badge': 'Client voices',
        'lux_test_title': 'What our clients say',
        'lux_test1': 'The dress arrived flawless. It felt borrowed from a private archive — not a typical rental rack.',
        'lux_test1_role': 'Client — Luminary',
        'lux_test2': 'Saved the look, picked the dates, and checked out in minutes. Unusually calm for fashion.',
        'lux_test2_role': 'Creative lead — Arcline',
        'lux_test3': 'The curation is the point: every piece could live in an editorial spread.',
        'lux_test3_role': 'Stylist — Helix',
        'lux_cta_title': 'Your next look starts here.',
        'lux_cta_copy': 'Open the catalog, choose a piece, and we will handle preparation and the hand-off.',
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
        'acc_checkout_unavailable': 'Часть вещей недоступна на выбранные даты. Обновите корзину и попробуйте снова.',
        'account_history_title': 'История аренд',
        'account_history_empty': 'Пока нет оформленных аренд.',
        'account_history_order': 'Заказ',
        'account_history_date': 'Дата',
        'account_history_status': 'Статус',
        'account_history_period': 'Период аренды',
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
        'order_status_created': 'Создан',
        'order_status_confirmed': 'Подтверждён',
        'order_status_in_rent': 'В аренде',
        'order_status_returned': 'Возвращён',
        'order_status_cancelled': 'Отменён',
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
        'rental_start_date': 'Дата начала',
        'rental_end_date': 'Дата возврата',
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
        'admin_orders_title': 'Последние заказы аренды',
        'admin_order_user': 'Клиент',
        'admin_order_period': 'Период',
        'admin_order_status': 'Статус',
        'admin_order_items': 'Позиции',
        'admin_order_update_status': 'Обновить статус',
        'admin_order_status_updated': 'Статус заказа обновлён',
        'admin_order_not_found': 'Заказ не найден',
        'admin_order_status_invalid': 'Некорректный статус заказа',
        'admin_order_empty': 'Пока нет заказов аренды.',
        'product_available_for_dates': 'Доступно на выбранные даты',
        'product_unavailable_for_dates': 'Недоступно на выбранные даты',
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
        'lux_badge_new': 'Новинка',
        'lux_hero_eyebrow': 'Аренда проверенной дизайнерской одежды',
        'lux_hero_headline': 'Гардероб, достойный вашего выхода',
        'lux_hero_lead': 'Вещи из архива — с проверкой подлинности, подготовкой к отправке и бронированием на выбранный срок.',
        'lux_start_badge': 'Как это устроено',
        'lux_start_title': 'Выберите. Наденьте. Верните.',
        'lux_start_copy': 'Найдите вещь в каталоге, забронируйте срок аренды, получите изделие в готовом виде и верните его после мероприятия. Уход и приёмка уже включены.',
        'lux_cap_badge': 'Возможности',
        'lux_cap_title': 'Доступ к архиву. Без лишних шагов.',
        'lux_chess1_title': 'Создано, чтобы впечатлять. Готово к аренде.',
        'lux_chess1_body': 'Каждая вещь снята, проверена, подготовлена и размещена с понятными условиями аренды до того, как окажется в корзине.',
        'lux_chess1_cta': 'Смотреть вещи',
        'lux_chess2_title': 'Быстрее находите то, что нужно.',
        'lux_chess2_body': 'Фильтры по бренду, категории, состоянию и цене. Сохраняйте избранное и завершайте аренду в личном кабинете.',
        'lux_chess2_cta': 'Открыть избранное',
        'lux_why_badge': 'Почему мы',
        'lux_why_title': 'Разница — в сервисе и аккуратности.',
        'lux_feat1_title': 'Дни, а не месяцы',
        'lux_feat1_body': 'Оформляйте аренду, когда планы уже ясны — процесс остаётся быстрым.',
        'lux_feat2_title': 'Тщательный отбор',
        'lux_feat2_body': 'Подбор по силуэту, состоянию и случаю — чтобы вещь попадала точно в момент.',
        'lux_feat3_title': 'Понятные размеры',
        'lux_feat3_body': 'Размеры и детали карточки на виду до принятия решения.',
        'lux_feat4_title': 'Прозрачный процесс',
        'lux_feat4_body': 'Аккаунт, избранное, корзина и оформление — весь цикл в одном месте.',
        'lux_stats_sr': 'Архив кратко',
        'lux_stat_pieces': 'Вещей в каталоге',
        'lux_stat_brands': 'Брендов в подборке',
        'lux_stat_condition': 'Контроль состояния',
        'lux_stat_days': 'Срок аренды (макс. дней)',
        'lux_test_badge': 'Отзывы',
        'lux_test_title': 'Что говорят клиенты',
        'lux_test1': 'Платье приехало безупречным. Ощущение частного архива, а не обычного проката.',
        'lux_test1_role': 'Клиент — Luminary',
        'lux_test2': 'Сохранил образ, выбрал даты и оформил за считанные минуты. Спокойно и без суеты.',
        'lux_test2_role': 'Креативный директор — Arcline',
        'lux_test3': 'Важен отбор: каждая вещь могла бы оказаться в редакционной съёмке.',
        'lux_test3_role': 'Стилист — Helix',
        'lux_cta_title': 'Следующий образ начинается здесь.',
        'lux_cta_copy': 'Откройте каталог, выберите вещь — подготовку и сопровождение мы возьмём на себя.',
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
