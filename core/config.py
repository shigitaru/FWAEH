import os
from dataclasses import dataclass

from dotenv import load_dotenv

_ROOT_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(_ROOT_DIR, '.env'), override=True)


@dataclass(frozen=True)
class Settings:
    flask_secret_key: str
    flask_debug: bool
    postgres_connection_string: str
    upload_dir: str
    campaign_upload_dir: str
    allowed_image_extensions: set[str]
    allowed_video_extensions: set[str]
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_pass: str
    smtp_from: str
    smtp_use_tls: bool
    email_delivery_disabled: bool
    resend_api_key: str
    resend_from: str
    pickup_address: str
    supabase_url: str
    supabase_service_role_key: str
    supabase_bucket: str
    supabase_public_base_url: str
                                                                                                      
    collection_nav_tease_site_file: str
    campaign_nav_tease_site_file: str
    about_nav_tease_site_file: str
    demo_mode: bool


def load_settings() -> Settings:
    base_dir = os.path.dirname(__file__)
    postgres_connection_string = (
        os.getenv('POSTGRES_CONNECTION_STRING', '')
        or os.getenv('SUPABASE_DB_URL', '')
        or os.getenv('DATABASE_URL', '')
    ).strip()
    return Settings(
        flask_secret_key=os.getenv('FLASK_SECRET_KEY', 'protocol-archive-2024').strip() or 'protocol-archive-2024',
        flask_debug=os.getenv('FLASK_DEBUG', '1').strip().lower() in ('1', 'true', 'yes', 'on'),
        postgres_connection_string=postgres_connection_string,
        upload_dir=os.path.join(base_dir, 'static', 'products', 'uploads'),
        campaign_upload_dir=os.path.join(base_dir, 'static', 'campaign', 'uploads'),
        allowed_image_extensions={'.jpg', '.jpeg', '.png', '.webp', '.gif'},
        allowed_video_extensions={'.mp4', '.mov', '.webm', '.m4v'},
        smtp_host=os.getenv('SMTP_HOST', '').strip(),
        smtp_port=int(os.getenv('SMTP_PORT', '587') or 587),
        smtp_user=os.getenv('SMTP_USER', '').strip(),
        smtp_pass=os.getenv('SMTP_PASS', '').strip(),
        smtp_from=os.getenv('SMTP_FROM', '').strip(),
        smtp_use_tls=os.getenv('SMTP_USE_TLS', '1').strip().lower() not in ('0', 'false', 'no'),
        email_delivery_disabled=(
            os.getenv('EMAIL_DELIVERY_DISABLED', '')
            or os.getenv('DISABLE_EMAIL_DELIVERY', '')
        ).strip().lower() in ('1', 'true', 'yes', 'on'),
        resend_api_key=os.getenv('RESEND_API_KEY', '').strip(),
        resend_from=os.getenv('RESEND_FROM', '').strip(),
        pickup_address=os.getenv('PICKUP_ADDRESS', 'Москва, пункт выдачи Protocol Archive').strip(),
        supabase_url=os.getenv('SUPABASE_URL', '').strip().rstrip('/'),
        supabase_service_role_key=os.getenv('SUPABASE_SERVICE_ROLE_KEY', '').strip(),
        supabase_bucket=os.getenv('SUPABASE_BUCKET', 'media').strip(),
        supabase_public_base_url=os.getenv('SUPABASE_PUBLIC_BASE_URL', '').strip().rstrip('/'),
        collection_nav_tease_site_file=(
            os.getenv('COLLECTION_NAV_TEASE_SITE_FILE', '').strip()
            or os.getenv('ITEMS_NAV_TEASE_SITE_FILE', '').strip()
            or 'de1b395fd683996f64d13c9caf59e53a.jpg'
        ),
        campaign_nav_tease_site_file=(
            os.getenv('CAMPAIGN_NAV_TEASE_SITE_FILE', '').strip()
            or 'ef88a65170b81f7b6782159f2d40ad9c.jpg'
        ),
        about_nav_tease_site_file=(
            os.getenv('ABOUT_NAV_TEASE_SITE_FILE', '').strip()
            or 'image (1).jpeg'
        ),
        demo_mode=os.getenv('DEMO_MODE', '0').strip().lower() in ('1', 'true', 'yes', 'on'),
    )


settings = load_settings()
