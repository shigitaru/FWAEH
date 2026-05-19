from datetime import datetime
from urllib.parse import quote

from flask import request, url_for

from core.account_service import (
    _clear_user_session_state,
    _increment_verification_attempt,
    _list_users_for_admin,
    _mark_email_verified,
    _set_user_session_state,
    _set_admin_flag,
    _set_user_verification_code,
    _update_user_loyalty,
    _user_fetch_by_email,
    _user_insert,
)
from core.campaign_service import (
    _collect_story_image_urls_from_form,
    _fetch_campaign_settings_admin,
    _fetch_campaign_story_admin,
    _insert_campaign_story_return_id,
    _list_campaign_stories_admin,
    campaign_header_form_to_db_columns,
    campaign_story_form_to_db_columns,
    get_campaign_index_data,
    get_campaign_story_detail,
    get_members_area_hero_url_from_db,
)
from core.catalog import (
    BRAND_FONT_OPTIONS,
    filter_products,
    find_product,
    find_products_by_ids,
    get_admin_brands,
    get_brands,
    get_related_products,
)
from core.config import settings
from core.constants import (
    ITEM_CATEGORIES,
    LOYALTY_LEVELS,
    ORDER_STATUS_FLOW,
    SPLASH_IMAGE,
    normalize_item_category_slug,
)
from core.couture_access import (
    can_rent_product,
    couture_gate_message_key,
    couture_minimum_level,
    format_couture_message,
    is_couture_product,
)
from core.db import get_db_connection
from core.email_service import send_rental_approved_email, send_verification_email
from core.i18n import TRANSLATIONS, get_lang, t, tc, tv
from core.listing import _collection_listing_data
from core.loyalty import cart_totals_for_level, get_loyalty_level, next_loyalty_progress
from core.media_uploads import (
    _apply_admin_product_image_changes,
    _fetch_product_image_rows,
    _nullable_str,
    _save_campaign_upload,
    _save_uploaded_image,
)
from core.product_reviews import (
    get_order_review,
    get_product_reviews,
    list_pending_reviews_admin,
    set_review_moderation_status,
    upsert_order_review,
)
from core.rental_orders import (
    _create_rental_order,
    _fetch_recent_orders_admin,
    _fetch_user_rental_history,
    ensure_app_users_table,
    ensure_legacy_balenciaga_coture_brand_rename,
    ensure_rental_orders_tables,
    get_admin_dashboard_stats,
    get_product_occupied_periods,
    recalculate_user_loyalty,
)
from core.rental_wrappers import _is_product_available, _parse_iso_date
from core.session_cart import (
    ACC_EMAIL_RE,
    _clear_user_session,
    get_cart,
    get_cart_count,
    get_cart_total,
    get_current_user,
    get_wishlist_ids,
)
from repositories.order_repository import (
    fetch_account_order_detail,
    fetch_order_status_for_user,
    fetch_user_loyalty_counters,
    try_cancel_user_order,
)
from repositories.user_repository import upsert_demo_user
from routes.admin import register_admin_routes
from routes.api import register_api_routes
from routes.auth import register_auth_routes
from routes.public import register_public_routes
from services.rental_service import CoutureAccessError, RentalAvailabilityError

_brand_coture_typo_fixed = False


def register_startup_hooks(app):
    @app.before_request
    def _run_brand_coture_typo_fix_once():
        global _brand_coture_typo_fixed
        if _brand_coture_typo_fixed:
            return
        _brand_coture_typo_fixed = True
        ensure_legacy_balenciaga_coture_brand_rename()


def register_routes(app):
    register_auth_routes(
        app,
        {
            't': t,
            'get_current_user': get_current_user,
            'get_cart_count': get_cart_count,
            '_fetch_user_rental_history': _fetch_user_rental_history,
            'ensure_app_users_table': ensure_app_users_table,
            'ensure_rental_orders_tables': ensure_rental_orders_tables,
            '_user_fetch_by_email': _user_fetch_by_email,
            '_user_insert': _user_insert,
            '_set_user_verification_code': _set_user_verification_code,
            '_increment_verification_attempt': _increment_verification_attempt,
            '_mark_email_verified': _mark_email_verified,
            '_send_verification_email': send_verification_email,
            'email_delivery_disabled': settings.email_delivery_disabled,
            '_clear_user_session': _clear_user_session,
            '_set_user_session_state': _set_user_session_state,
            '_clear_user_session_state': _clear_user_session_state,
            'ACC_EMAIL_RE': ACC_EMAIL_RE,
            'demo_mode': settings.demo_mode,
            'get_loyalty_level': get_loyalty_level,
            'next_loyalty_progress': next_loyalty_progress,
            'couture_min_level': couture_minimum_level(),
            'get_order_review': get_order_review,
            'upsert_order_review': upsert_order_review,
            'try_cancel_user_order': try_cancel_user_order,
            'fetch_account_order_detail': fetch_account_order_detail,
            'fetch_order_status_for_user': fetch_order_status_for_user,
            'fetch_user_loyalty_counters': fetch_user_loyalty_counters,
            'upsert_demo_user': upsert_demo_user,
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
            'find_products_by_ids': find_products_by_ids,
            'get_related_products': get_related_products,
            'get_product_reviews': get_product_reviews,
            '_parse_iso_date': _parse_iso_date,
            '_is_product_available': _is_product_available,
            '_create_rental_order': _create_rental_order,
            'RentalAvailabilityError': RentalAvailabilityError,
            'CoutureAccessError': CoutureAccessError,
            'get_brands': get_brands,
            'get_campaign_index_data': get_campaign_index_data,
            'get_campaign_story_detail': get_campaign_story_detail,
            'cart_totals_for_level': cart_totals_for_level,
            'can_rent_product': can_rent_product,
            'couture_gate_message_key': couture_gate_message_key,
            'format_couture_message': format_couture_message,
        },
    )

    register_api_routes(
        app,
        {
            '_parse_iso_date': _parse_iso_date,
            'find_product': find_product,
            'filter_products': filter_products,
            'get_brands': get_brands,
            '_is_product_available': _is_product_available,
            'get_product_occupied_periods': get_product_occupied_periods,
            'get_current_user': get_current_user,
            'is_couture_product': is_couture_product,
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
            'get_admin_dashboard_stats': get_admin_dashboard_stats,
            'get_brands': get_brands,
            'get_admin_brands': get_admin_brands,
            'get_cart_count': get_cart_count,
            'find_product': find_product,
            '_fetch_product_image_rows': _fetch_product_image_rows,
            '_fetch_campaign_settings_admin': _fetch_campaign_settings_admin,
            '_list_campaign_stories_admin': _list_campaign_stories_admin,
            '_fetch_campaign_story_admin': _fetch_campaign_story_admin,
            'campaign_header_form_to_db_columns': campaign_header_form_to_db_columns,
            'campaign_story_form_to_db_columns': campaign_story_form_to_db_columns,
            '_collect_story_image_urls_from_form': _collect_story_image_urls_from_form,
            '_save_campaign_upload': _save_campaign_upload,
            '_insert_campaign_story_return_id': _insert_campaign_story_return_id,
            '_list_users_for_admin': _list_users_for_admin,
            '_set_admin_flag': _set_admin_flag,
            '_update_user_loyalty': _update_user_loyalty,
            '_set_user_session_state': _set_user_session_state,
            'LOYALTY_LEVELS': LOYALTY_LEVELS,
            'recalculate_user_loyalty': recalculate_user_loyalty,
            '_user_fetch_by_email': _user_fetch_by_email,
            '_send_rental_approved_email': send_rental_approved_email,
            'brand_font_options': BRAND_FONT_OPTIONS,
            'list_pending_reviews_admin': list_pending_reviews_admin,
            'set_review_moderation_status': set_review_moderation_status,
        },
    )


def register_template_context(app):
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
        has_supabase = bool(settings.supabase_url and settings.supabase_bucket)
        if has_supabase:
            base = settings.supabase_public_base_url or f'{settings.supabase_url}/storage/v1/object/public'
            site_media_base = f'{base}/{settings.supabase_bucket}/protocol_archive/site'
        else:
            site_media_base = '/static'
        hero_video_url = f'{site_media_base}/lux_start_local.mp4'
        how_hls_url = f'{site_media_base}/lux_how_local_hls/local.m3u8'
        showcase_image_1_url = f'{site_media_base}/1.png'
        showcase_image_2_url = f'{site_media_base}/2.png'
        couture_hero_url = f'{site_media_base}/couture-hero.jpg'
        members_area_hero_url = get_members_area_hero_url_from_db() or ''

        def _site_nav_tease_file_url(rel: str) -> str:
            name = rel.lstrip('/')
            if site_media_base.startswith(('http://', 'https://')):
                return f'{site_media_base}/{quote(name, safe="().-_~")}'
            return f'{site_media_base}/{name}'

        collection_file = getattr(
            settings,
            'collection_nav_tease_site_file',
            'de1b395fd683996f64d13c9caf59e53a.jpg',
        ).lstrip('/')
        campaign_file = getattr(
            settings,
            'campaign_nav_tease_site_file',
            'ef88a65170b81f7b6782159f2d40ad9c.jpg',
        ).lstrip('/')
        about_file = getattr(
            settings,
            'about_nav_tease_site_file',
            'image (1).jpeg',
        ).lstrip('/')

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
            'hero_video_url': hero_video_url,
            'how_hls_url': how_hls_url,
            'showcase_image_1_url': showcase_image_1_url,
            'showcase_image_2_url': showcase_image_2_url,
            'couture_hero_url': couture_hero_url,
            'members_area_hero_url': members_area_hero_url,
            'collection_nav_tease_img_url': _site_nav_tease_file_url(collection_file),
            'campaign_nav_tease_img_url': _site_nav_tease_file_url(campaign_file),
            'about_nav_tease_img_url': _site_nav_tease_file_url(about_file),
            'demo_mode': settings.demo_mode,
        }


def install_legacy_endpoint_aliases(app):
    endpoint_aliases = {}
    duplicate_aliases = set()
    for rule in app.url_map.iter_rules():
        endpoint = rule.endpoint
        if '.' not in endpoint:
            continue
        alias = endpoint.rsplit('.', 1)[-1]
        if alias in endpoint_aliases:
            duplicate_aliases.add(alias)
        else:
            endpoint_aliases[alias] = endpoint
    for alias in duplicate_aliases:
        endpoint_aliases.pop(alias, None)

    def _legacy_endpoint_handler(error, endpoint, values):
        mapped_endpoint = endpoint_aliases.get(endpoint)
        if not mapped_endpoint:
            return None
        return url_for(mapped_endpoint, **values)

    app.url_build_error_handlers.append(_legacy_endpoint_handler)
