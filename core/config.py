import os
from dataclasses import dataclass

from dotenv import load_dotenv

_ROOT_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(_ROOT_DIR, '.env'), override=True)


@dataclass(frozen=True)
class Settings:
    db_name: str
    db_server: str
    db_connection_string: str
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
    pickup_address: str
    supabase_url: str
    supabase_service_role_key: str
    supabase_bucket: str
    supabase_public_base_url: str


def load_settings() -> Settings:
    base_dir = os.path.dirname(__file__)
    db_name = os.getenv('DB_NAME', 'ProtocolArchive')
    db_server = os.getenv('DB_SERVER', r'SHIGITARU\SQLEXPRESS')
    db_connection_string = os.getenv(
        'DB_CONNECTION_STRING',
        f'DRIVER={{ODBC Driver 17 for SQL Server}};'
        f'SERVER={db_server};'
        f'DATABASE={db_name};'
        'Trusted_Connection=yes;'
        'Encrypt=yes;'
        'TrustServerCertificate=yes;'
        'MARS_Connection=no;'
    )
    return Settings(
        db_name=db_name,
        db_server=db_server,
        db_connection_string=db_connection_string,
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
        pickup_address=os.getenv('PICKUP_ADDRESS', 'Москва, пункт выдачи Protocol Archive').strip(),
        supabase_url=os.getenv('SUPABASE_URL', '').strip().rstrip('/'),
        supabase_service_role_key=os.getenv('SUPABASE_SERVICE_ROLE_KEY', '').strip(),
        supabase_bucket=os.getenv('SUPABASE_BUCKET', 'media').strip(),
        supabase_public_base_url=os.getenv('SUPABASE_PUBLIC_BASE_URL', '').strip().rstrip('/'),
    )


settings = load_settings()
