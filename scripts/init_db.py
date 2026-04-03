import pyodbc

DB_NAME = "ProtocolArchive"
SERVER = r"SHIGITARU\SQLEXPRESS"

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
        print("Tables are ready.")


if __name__ == "__main__":
    create_database()
    create_tables()
    print("Done.")
