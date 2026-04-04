import os
import sys
import pyodbc

_APP_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if _APP_ROOT not in sys.path:
    sys.path.insert(0, _APP_ROOT)

from seed_defaults import (  # noqa: E402
    DEFAULT_CAMPAIGN_SETTINGS,
    DEMO_PRODUCTS,
    campaign_stories_for_seed,
    resolve_demo_item_images,
    sync_balenciaga_graffiti_jeans_product_images,
    sync_bc_couture_bag_product_images,
    sync_kiss_heels_product_images,
    sync_raf_bomber_product_images,
    sync_yzy_grillz_product_images,
)

DB_NAME = os.getenv("DB_NAME", "ProtocolArchive")
SERVER = os.getenv("DB_SERVER", r"SHIGITARU\SQLEXPRESS")

# Сбросить витрину и кампанию к содержимому seed_defaults.py (удалит текущие товары/истории).
SEED_RESET_DEMO = os.getenv("SEED_RESET_DEMO", "").strip().lower() in ("1", "true", "yes")

MASTER_CONN_STR = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    f"SERVER={SERVER};"
    "DATABASE=master;"
    "Trusted_Connection=yes;"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
    "MARS_Connection=no;"
)

APP_CONN_STR = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    f"SERVER={SERVER};"
    f"DATABASE={DB_NAME};"
    "Trusted_Connection=yes;"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
    "MARS_Connection=no;"
)


def _ensure_brand_id(cur, brand_name):
    cur.execute("SELECT id FROM Brands WHERE name = ?", (brand_name,))
    row = cur.fetchone()
    if row:
        return int(row[0])
    cur.execute(
        """
        INSERT INTO Brands (name, slug, css_class)
        OUTPUT INSERTED.id
        VALUES (?, ?, ?)
        """,
        (brand_name, brand_name, ""),
    )
    out = cur.fetchone()
    return int(out[0]) if out and out[0] is not None else None


def _clear_product_rows(cur):
    cur.execute("DELETE FROM ProductImages")
    cur.execute("DELETE FROM ProductSizes")
    cur.execute("DELETE FROM Products")


def _clear_campaign_rows(cur):
    cur.execute("DELETE FROM CampaignStoryImages")
    cur.execute("DELETE FROM CampaignStories")
    cur.execute("DELETE FROM CampaignLooks")


def _insert_demo_products(cur, items=None):
    catalog = items if items is not None else DEMO_PRODUCTS
    for item in catalog:
        brand_id = _ensure_brand_id(cur, item["brand"])
        if not brand_id:
            continue
        main_image, gallery = resolve_demo_item_images(item)
        cur.execute(
            """
            INSERT INTO Products (
                brand_id, category, serial, name, price, max_days, condition_score,
                material, origin, [condition], main_image
            )
            OUTPUT INSERTED.id
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                brand_id,
                item["category"],
                item["serial"],
                item["name"],
                item["price"],
                item["max_days"],
                item["condition_score"],
                item.get("material"),
                item.get("origin"),
                item.get("condition"),
                main_image,
            ),
        )
        prod_row = cur.fetchone()
        product_id = int(prod_row[0]) if prod_row and prod_row[0] is not None else None
        if not product_id:
            continue
        for sort_order, url in enumerate(gallery):
            cur.execute(
                """
                INSERT INTO ProductImages (product_id, image_url, sort_order)
                VALUES (?, ?, ?)
                """,
                (product_id, url, sort_order),
            )
        for size_label in item.get("sizes") or []:
            cur.execute(
                "INSERT INTO ProductSizes (product_id, size_label) VALUES (?, ?)",
                (product_id, size_label),
            )


def _ensure_campaign_settings(cur, force_reset):
    d = DEFAULT_CAMPAIGN_SETTINGS
    cur.execute("SELECT COUNT(*) FROM CampaignSettings WHERE id = 1")
    if cur.fetchone()[0] == 0:
        cur.execute(
            """
            INSERT INTO CampaignSettings (id, intro_en, intro_ru, tagline_en, tagline_ru)
            VALUES (1, ?, ?, ?, ?)
            """,
            (d["intro_en"], d["intro_ru"], d["tagline_en"], d["tagline_ru"]),
        )
    elif force_reset:
        cur.execute(
            """
            UPDATE CampaignSettings
            SET intro_en = ?, intro_ru = ?, tagline_en = ?, tagline_ru = ?
            WHERE id = 1
            """,
            (d["intro_en"], d["intro_ru"], d["tagline_en"], d["tagline_ru"]),
        )


def _insert_campaign_from_defaults(cur):
    stories = sorted(campaign_stories_for_seed(), key=lambda x: x["sort_order"])
    for st in stories:
        cur.execute(
            """
            INSERT INTO CampaignStories (
                sort_order, headline_en, headline_ru, body_en, body_ru, credits_en, credits_ru
            )
            OUTPUT INSERTED.id
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                st["sort_order"],
                st["headline_en"],
                st["headline_ru"],
                st["body_en"],
                st["body_ru"],
                st["credits_en"],
                st["credits_ru"],
            ),
        )
        sid = int(cur.fetchone()[0])
        cover = st["images"][0]
        cur.execute(
            """
            INSERT INTO CampaignLooks (sort_order, image_url, ref_text, location_text)
            VALUES (?, ?, ?, ?)
            """,
            (
                st["sort_order"],
                cover,
                st["headline_en"][:120],
                (st["credits_en"] or "")[:120],
            ),
        )
        for idx, url in enumerate(st["images"]):
            cur.execute(
                """
                INSERT INTO CampaignStoryImages (story_id, sort_order, image_url)
                VALUES (?, ?, ?)
                """,
                (sid, idx, url),
            )


def _seed_demo_products(cur, force_reset, items=None):
    cur.execute("SELECT COUNT(*) AS c FROM Products")
    has_products = cur.fetchone()[0] > 0
    if has_products and not force_reset:
        return
    if force_reset:
        _clear_product_rows(cur)
        if has_products:
            print("Demo catalog reset from seed_defaults.py.")
    _insert_demo_products(cur, items)
    n = len(items) if items is not None else len(DEMO_PRODUCTS)
    print(f"Demo products seeded ({n} items).")


def _seed_campaign(cur, force_reset):
    cur.execute("SELECT COUNT(*) AS c FROM CampaignStories")
    story_count = cur.fetchone()[0]
    if force_reset:
        _clear_campaign_rows(cur)
        story_count = 0
    _ensure_campaign_settings(cur, force_reset)
    if story_count > 0:
        return
    _insert_campaign_from_defaults(cur)
    print("Campaign stories and images seeded.")


def apply_demo_seed(cur, *, reset=None, products=None):
    """
    Вставить демо-витрину и кампанию из seed_defaults.py.
    reset=None: брать флаг из переменной окружения SEED_RESET_DEMO.
    reset=True: очистить товары и кампанию и залить заново (как после потери БД).
    products: если задан — вставить только этот список (иначе полный DEMO_PRODUCTS).
    """
    force = SEED_RESET_DEMO if reset is None else bool(reset)
    _seed_demo_products(cur, force, items=products)
    sync_kiss_heels_product_images(cur)
    sync_raf_bomber_product_images(cur)
    sync_yzy_grillz_product_images(cur)
    sync_balenciaga_graffiti_jeans_product_images(cur)
    sync_bc_couture_bag_product_images(cur)
    _seed_campaign(cur, force)


def create_database():
    with pyodbc.connect(MASTER_CONN_STR, autocommit=True) as conn:
        cur = conn.cursor()
        cur.execute("SELECT DB_ID(?) AS db_id", DB_NAME)
        exists = cur.fetchone().db_id is not None
        if not exists:
            cur.execute(f"CREATE DATABASE [{DB_NAME}]")
            print(f"Created database: {DB_NAME}")
        else:
            print(f"Database already exists: {DB_NAME}")


def create_tables():
    with pyodbc.connect(APP_CONN_STR, autocommit=True) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            IF OBJECT_ID('Brands', 'U') IS NULL
            CREATE TABLE Brands (
                id INT IDENTITY(1,1) PRIMARY KEY,
                name NVARCHAR(120) NOT NULL UNIQUE,
                slug NVARCHAR(120) NOT NULL,
                css_class NVARCHAR(120) NULL
            );
            """
        )
        cur.execute(
            """
            IF OBJECT_ID('Products', 'U') IS NULL
            CREATE TABLE Products (
                id INT IDENTITY(1,1) PRIMARY KEY,
                brand_id INT NOT NULL,
                category NVARCHAR(40) NOT NULL,
                serial NVARCHAR(50) NOT NULL UNIQUE,
                name NVARCHAR(180) NOT NULL,
                price INT NOT NULL,
                max_days INT NOT NULL,
                condition_score INT NOT NULL,
                material NVARCHAR(120) NULL,
                origin NVARCHAR(120) NULL,
                [condition] NVARCHAR(180) NULL,
                main_image NVARCHAR(500) NOT NULL,
                created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),
                CONSTRAINT FK_Products_Brands FOREIGN KEY (brand_id) REFERENCES Brands(id)
            );
            """
        )
        cur.execute(
            """
            IF OBJECT_ID('ProductImages', 'U') IS NULL
            CREATE TABLE ProductImages (
                id INT IDENTITY(1,1) PRIMARY KEY,
                product_id INT NOT NULL,
                image_url NVARCHAR(500) NOT NULL,
                sort_order INT NOT NULL DEFAULT 0,
                CONSTRAINT FK_ProductImages_Products FOREIGN KEY (product_id) REFERENCES Products(id) ON DELETE CASCADE
            );
            """
        )
        cur.execute(
            """
            IF OBJECT_ID('ProductSizes', 'U') IS NULL
            CREATE TABLE ProductSizes (
                id INT IDENTITY(1,1) PRIMARY KEY,
                product_id INT NOT NULL,
                size_label NVARCHAR(40) NOT NULL,
                CONSTRAINT FK_ProductSizes_Products FOREIGN KEY (product_id) REFERENCES Products(id) ON DELETE CASCADE
            );
            """
        )
        cur.execute(
            """
            IF OBJECT_ID('CampaignSettings', 'U') IS NULL
            CREATE TABLE CampaignSettings (
                id INT NOT NULL PRIMARY KEY,
                intro_en NVARCHAR(2000) NULL,
                intro_ru NVARCHAR(2000) NULL,
                tagline_en NVARCHAR(500) NULL,
                tagline_ru NVARCHAR(500) NULL
            );
            """
        )
        cur.execute(
            """
            IF OBJECT_ID('CampaignLooks', 'U') IS NULL
            CREATE TABLE CampaignLooks (
                id INT IDENTITY(1,1) PRIMARY KEY,
                sort_order INT NOT NULL DEFAULT 0,
                image_url NVARCHAR(500) NOT NULL,
                ref_text NVARCHAR(120) NOT NULL,
                location_text NVARCHAR(120) NOT NULL
            );
            """
        )
        cur.execute(
            """
            IF OBJECT_ID('CampaignStories', 'U') IS NULL
            CREATE TABLE CampaignStories (
                id INT IDENTITY(1,1) PRIMARY KEY,
                sort_order INT NOT NULL DEFAULT 0,
                headline_en NVARCHAR(300) NOT NULL,
                headline_ru NVARCHAR(300) NOT NULL,
                body_en NVARCHAR(MAX) NULL,
                body_ru NVARCHAR(MAX) NULL,
                credits_en NVARCHAR(500) NULL,
                credits_ru NVARCHAR(500) NULL
            );
            """
        )
        cur.execute(
            """
            IF OBJECT_ID('CampaignStoryImages', 'U') IS NULL
            CREATE TABLE CampaignStoryImages (
                id INT IDENTITY(1,1) PRIMARY KEY,
                story_id INT NOT NULL,
                sort_order INT NOT NULL DEFAULT 0,
                image_url NVARCHAR(500) NOT NULL,
                CONSTRAINT FK_CampaignStoryImages_Story FOREIGN KEY (story_id) REFERENCES CampaignStories(id) ON DELETE CASCADE
            );
            """
        )
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

        default_brands = [
            "Rick Owens",
            "YZY",
            "Maison Margiela",
            "Balenciaga",
            "Balenciaga Coture",
            "Vetements",
            "Gucci",
            "Raf Simons",
            "Yohji Yamamoto",
            "Comme des Garçons",
            "Schiaparelli",
        ]
        for brand_name in default_brands:
            cur.execute(
                """
                IF NOT EXISTS (SELECT 1 FROM Brands WHERE name = ?)
                    INSERT INTO Brands (name, slug, css_class) VALUES (?, ?, N'')
                """,
                (brand_name, brand_name, brand_name),
            )

        apply_demo_seed(cur)

        print("Tables are ready.")


if __name__ == "__main__":
    create_database()
    create_tables()
    print("Done.")
