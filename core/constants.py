"""Catalog constants, fallback products, brands, and item categories."""
from seed_defaults import fallback_products_list

ORDER_STATUS_FLOW = ('created', 'confirmed', 'in_rent', 'returned', 'cancelled')
ACTIVE_RENTAL_STATUSES = {'created', 'confirmed', 'in_rent'}

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

LOYALTY_LEVELS = (
    {
        'code': 'bronze',
        'title': 'Bronze',
        'min_orders': 0,
        'min_spend': 0,
        'discount_percent': 0,
        'priority_booking': False,
        'offline_events': False,
    },
    {
        'code': 'silver',
        'title': 'Silver',
        'min_orders': 3,
        'min_spend': 300,
        'discount_percent': 3,
        'priority_booking': True,
        'offline_events': False,
    },
    {
        'code': 'gold',
        'title': 'Gold',
        'min_orders': 7,
        'min_spend': 900,
        'discount_percent': 7,
        'priority_booking': True,
        'offline_events': True,
    },
    {
        'code': 'platinum',
        'title': 'Platinum',
        'min_orders': 15,
        'min_spend': 2000,
        'discount_percent': 10,
        'priority_booking': True,
        'offline_events': True,
    },
)
