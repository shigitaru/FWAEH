from datetime import datetime

from flask import Flask, request

from core.account_service import _user_fetch_by_email, _user_insert
from core.campaign_service import (
    _collect_story_image_urls_from_form,
    _fetch_campaign_settings_admin,
    _fetch_campaign_story_admin,
    _insert_campaign_story_return_id,
    _list_campaign_stories_admin,
    get_campaign_index_data,
    get_campaign_story_detail,
)
from core.catalog import filter_products, find_product, get_admin_brands, get_brands
from core.constants import (
    ITEM_CATEGORIES,
    ORDER_STATUS_FLOW,
    SPLASH_IMAGE,
    normalize_item_category_slug,
)
from core.db import get_db_connection
from core.i18n import TRANSLATIONS, get_lang, t, tc, tv
from core.listing import _collection_listing_data
from core.media_uploads import (
    _apply_admin_product_image_changes,
    _fetch_product_image_rows,
    _nullable_str,
    _save_campaign_upload,
    _save_uploaded_image,
)
from core.rental_orders import (
    _create_rental_order,
    _fetch_recent_orders_admin,
    _fetch_user_rental_history,
    ensure_app_users_table,
    ensure_legacy_balenciaga_coture_brand_rename,
    ensure_rental_orders_tables,
)
from routes.admin import register_admin_routes
from routes.api import register_api_routes
from routes.auth import register_auth_routes
from routes.public import register_public_routes
from services.rental_service import RentalAvailabilityError
from core.session_cart import (
    ACC_EMAIL_RE,
    _clear_user_session,
    get_cart,
    get_cart_count,
    get_cart_total,
    get_current_user,
    get_wishlist_ids,
)
from core.rental_wrappers import _is_product_available, _parse_iso_date

app = Flask(__name__)
app.secret_key = 'protocol-archive-2024'

_brand_coture_typo_fixed = False


@app.before_request
def _run_brand_coture_typo_fix_once():
    global _brand_coture_typo_fixed
    if _brand_coture_typo_fixed:
        return
    _brand_coture_typo_fixed = True
    ensure_legacy_balenciaga_coture_brand_rename()


register_auth_routes(
    app,
    {
        't': t,
        'get_current_user': get_current_user,
        'get_cart_count': get_cart_count,
        '_fetch_user_rental_history': _fetch_user_rental_history,
        'ensure_app_users_table': ensure_app_users_table,
        '_user_fetch_by_email': _user_fetch_by_email,
        '_user_insert': _user_insert,
        '_clear_user_session': _clear_user_session,
        'ACC_EMAIL_RE': ACC_EMAIL_RE,
    },
)

register_public_routes(
    app,
    {
        't': t,
        'tv': tv,
        'tc': tc,
        'TRANSLATIONS': TRANSLATIONS,
        'SPLASH_IMAGE': SPLASH_IMAGE,
        '_collection_listing_data': _collection_listing_data,
        'get_cart_count': get_cart_count,
        'get_cart_total': get_cart_total,
        'get_cart': get_cart,
        'get_current_user': get_current_user,
        'get_wishlist_ids': get_wishlist_ids,
        'filter_products': filter_products,
        'find_product': find_product,
        '_parse_iso_date': _parse_iso_date,
        '_is_product_available': _is_product_available,
        '_create_rental_order': _create_rental_order,
        'RentalAvailabilityError': RentalAvailabilityError,
        'get_brands': get_brands,
        'get_campaign_index_data': get_campaign_index_data,
        'get_campaign_story_detail': get_campaign_story_detail,
    },
)

register_api_routes(
    app,
    {
        '_parse_iso_date': _parse_iso_date,
        'find_product': find_product,
        '_is_product_available': _is_product_available,
    },
)

register_admin_routes(
    app,
    {
        't': t,
        'tv': tv,
        'ORDER_STATUS_FLOW': ORDER_STATUS_FLOW,
        'ensure_rental_orders_tables': ensure_rental_orders_tables,
        'get_db_connection': get_db_connection,
        'normalize_item_category_slug': normalize_item_category_slug,
        '_nullable_str': _nullable_str,
        '_save_uploaded_image': _save_uploaded_image,
        '_apply_admin_product_image_changes': _apply_admin_product_image_changes,
        'filter_products': filter_products,
        '_fetch_recent_orders_admin': _fetch_recent_orders_admin,
        'get_brands': get_brands,
        'get_admin_brands': get_admin_brands,
        'get_cart_count': get_cart_count,
        'find_product': find_product,
        '_fetch_product_image_rows': _fetch_product_image_rows,
        '_fetch_campaign_settings_admin': _fetch_campaign_settings_admin,
        '_list_campaign_stories_admin': _list_campaign_stories_admin,
        '_fetch_campaign_story_admin': _fetch_campaign_story_admin,
        '_collect_story_image_urls_from_form': _collect_story_image_urls_from_form,
        '_save_campaign_upload': _save_campaign_upload,
        '_insert_campaign_story_return_id': _insert_campaign_story_return_id,
    },
)


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

    path = (getattr(request, 'path', '') or '').lower()
    lux_theme = not path.startswith('/admin')
    admin_site = path.startswith('/admin')

    return {
        'current_year': datetime.now().year,
        'current_lang': lang,
        'tc': tc,
        'wishlist_ids': frozenset(wids),
        'wishlist_count': len(wids),
        'current_user': get_current_user(),
        'item_categories': ITEM_CATEGORIES,
        'item_category_label': item_category_label,
        'lux_theme': lux_theme,
        'admin_site': admin_site,
    }


if __name__ == '__main__':
    print('\n  Protocol Archive — http://127.0.0.1:5000\n')
    app.run(debug=True, port=5000)
