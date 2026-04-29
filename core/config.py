import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    db_name: str
    db_server: str
    db_connection_string: str
    upload_dir: str
    campaign_upload_dir: str
    allowed_image_extensions: set[str]


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
    )


settings = load_settings()
