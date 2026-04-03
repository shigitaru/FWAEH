import os
import pyodbc

DB_NAME = os.getenv("DB_NAME", "ProtocolArchive")
SERVER = os.getenv("DB_SERVER", r"SHIGITARU\SQLEXPRESS")

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

        # Seed brand suggestions so admin has autocomplete immediately.
        default_brands = [
            'Rick Owens',
            'YZY',
            'Maison Margiela',
            'Balenciaga',
            'Vetements',
            'Gucci',
            'Raf Simons',
        ]
        for brand_name in default_brands:
            slug = brand_name
            cur.execute(
                """
                IF NOT EXISTS (SELECT 1 FROM Brands WHERE name = ?)
                    INSERT INTO Brands (name, slug, css_class) VALUES (?, ?, '')
                """,
                (brand_name, brand_name, slug),
            )

        cur.execute("SELECT COUNT(*) AS c FROM CampaignSettings WHERE id = 1")
        if cur.fetchone()[0] == 0:
            cur.execute(
                """
                INSERT INTO CampaignSettings (id, intro_en, intro_ru, tagline_en, tagline_ru)
                VALUES (1, ?, ?, ?, ?)
                """,
                (
                    "Silhouette, material, and light — a visual sequence shot for Protocol Archive.",
                    "Силуэт, материал и свет — визуальный ряд для Protocol Archive.",
                    "Editorial series",
                    "Редакционная серия",
                ),
            )
        cur.execute("SELECT COUNT(*) AS c FROM CampaignStories")
        if cur.fetchone()[0] == 0:
            cur.execute("SELECT COUNT(*) AS c FROM CampaignLooks")
            if cur.fetchone()[0] > 0:
                cur.execute(
                    "SELECT sort_order, image_url, ref_text, location_text FROM CampaignLooks ORDER BY sort_order, id"
                )
                for row in cur.fetchall():
                    so, url, ref_t, loc_t = row[0], row[1], row[2], row[3]
                    cur.execute(
                        """
                        INSERT INTO CampaignStories (sort_order, headline_en, headline_ru, body_en, body_ru, credits_en, credits_ru)
                        OUTPUT INSERTED.id
                        VALUES (?, ?, ?, N'', N'', ?, ?)
                        """,
                        (so, ref_t, ref_t, loc_t or "", loc_t or ""),
                    )
                    sid = cur.fetchone()[0]
                    cur.execute(
                        """
                        INSERT INTO CampaignStoryImages (story_id, sort_order, image_url)
                        VALUES (?, 0, ?)
                        """,
                        (sid, url),
                    )
            else:
                default_stories = [
                    (
                        0,
                        "Look 01",
                        "Look 01",
                        "Editorial session in Paris — silhouette, fabric, and light.",
                        "Редакционная съёмка в Париже — силуэт, ткань и свет.",
                        "Paris",
                        "Paris",
                        "https://images.unsplash.com/photo-1612336307429-8a898d10e223?q=80&w=2070&auto=format&fit=crop",
                    ),
                    (
                        1,
                        "Look 02",
                        "Look 02",
                        "Studio study — controlled lighting and form.",
                        "Студийный этюд — контроль света и формы.",
                        "Studio",
                        "Студия",
                        "https://images.unsplash.com/photo-1550614000-4b95d4ed79cf?q=80&w=2000&auto=format&fit=crop",
                    ),
                    (
                        2,
                        "Look 03",
                        "Look 03",
                        "Archive references — materials from the house collection.",
                        "Отсылки к архиву — материалы из домашней коллекции.",
                        "Archive",
                        "Архив",
                        "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?q=80&w=2070&auto=format&fit=crop",
                    ),
                ]
                for so, h_en, h_ru, b_en, b_ru, c_en, c_ru, url in default_stories:
                    cur.execute(
                        """
                        INSERT INTO CampaignStories (sort_order, headline_en, headline_ru, body_en, body_ru, credits_en, credits_ru)
                        OUTPUT INSERTED.id
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (so, h_en, h_ru, b_en, b_ru, c_en, c_ru),
                    )
                    sid = cur.fetchone()[0]
                    cur.execute(
                        "INSERT INTO CampaignStoryImages (story_id, sort_order, image_url) VALUES (?, 0, ?)",
                        (sid, url),
                    )

        print("Tables are ready.")


if __name__ == "__main__":
    create_database()
    create_tables()
    print("Done.")
