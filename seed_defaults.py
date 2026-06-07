"""
Демо-каталог и кампания: единый источник для PostgreSQL seed-скрипта и fallback в app.py.
Редактируйте этот файл, чтобы «зашитые» товары и картинки кампании всегда
восстанавливались после пустой БД или запуска scripts/init_postgres_db.py.
"""
from __future__ import annotations

import json
import os
import re

from core.product_measurements import enrich_product_dict

                                                                                                   
_MEAS_DEMO_COAT = {
    "kind": "garment",
    "columns": ["S", "M", "L", "XL"],
    "rows": [
        {"en": "Length (cm)", "ru": "Длина (см)", "values": [108, 112, 116, 120]},
        {"en": "Chest (cm)", "ru": "Грудь (см)", "values": [52, 56, 60, 64]},
        {"en": "Shoulders (cm)", "ru": "Плечи (см)", "values": [46, 48, 50, 52]},
        {"en": "Sleeve (cm)", "ru": "Рукав (см)", "values": [62, 63, 64, 65]},
    ],
}
_MEAS_DEMO_BLAZER = {
    "kind": "garment",
    "columns": ["XS", "S", "M", "L", "XL"],
    "rows": [
        {"en": "Length (cm)", "ru": "Длина (см)", "values": [68, 70, 72, 74, 76]},
        {"en": "Chest (cm)", "ru": "Грудь (см)", "values": [48, 50, 52, 54, 56]},
        {"en": "Sleeve (cm)", "ru": "Рукав (см)", "values": [60, 61, 62, 63, 64]},
    ],
}
_MEAS_DEMO_BOMBER = {
    "kind": "garment",
    "columns": ["XL"],
    "rows": [
        {"en": "Length (cm)", "ru": "Длина (см)", "values": [72]},
        {"en": "Chest (cm)", "ru": "Грудь (см)", "values": [124]},
        {"en": "Sleeve (cm)", "ru": "Рукав (см)", "values": [68]},
        {"en": "Shoulders (cm)", "ru": "Плечи (см)", "values": [54]},
    ],
}
_MEAS_DEMO_HEELS = {
    "kind": "footwear",
    "rows": [
        {"eu": "39", "insole_cm": "25.0"},
        {"eu": "40", "insole_cm": "26.2"},
        {"eu": "41", "insole_cm": "26.9"},
    ],
}
_MEAS_DEMO_JEANS_XS = {
    "kind": "garment",
    "columns": ["XS"],
    "rows": [
        {"en": "Waist (cm)", "ru": "Талия (см)", "values": [38]},
        {"en": "Hip (cm)", "ru": "Бёдра (см)", "values": [52]},
        {"en": "Inseam (cm)", "ru": "Внутренний шов (см)", "values": [78]},
        {"en": "Length outseam (cm)", "ru": "Длина по боковому шву (см)", "values": [108]},
    ],
}
_MEAS_DEMO_BAG_OS = {
    "kind": "garment",
    "columns": ["OS"],
    "rows": [
        {"en": "Width (cm)", "ru": "Ширина (см)", "values": [28]},
        {"en": "Height (cm)", "ru": "Высота (см)", "values": [18]},
        {"en": "Depth (cm)", "ru": "Глубина (см)", "values": [8]},
        {"en": "Handle drop (cm)", "ru": "Плечевой ремень (см)", "values": [22]},
    ],
}
_MEAS_DEMO_JEWELRY_OS = {
    "kind": "garment",
    "columns": ["OS"],
    "rows": [
        {"en": "Piece width (cm)", "ru": "Ширина изделия (см)", "values": [6.2]},
        {"en": "Piece height (cm)", "ru": "Высота изделия (см)", "values": [1.1]},
    ],
}
_MEAS_DEMO_DRESS_XSM = {
    "kind": "garment",
    "columns": ["XS", "S", "M"],
    "rows": [
        {"en": "Length (cm)", "ru": "Длина (см)", "values": [118, 122, 126]},
        {"en": "Chest (cm)", "ru": "Грудь (см)", "values": [44, 46, 48]},
        {"en": "Waist (cm)", "ru": "Талия (см)", "values": [42, 44, 46]},
        {"en": "Sleeve (cm)", "ru": "Рукав (см)", "values": [58, 59, 60]},
    ],
}
_MEAS_DEMO_JACKET_SML = {
    "kind": "garment",
    "columns": ["S", "M", "L"],
    "rows": [
        {"en": "Length (cm)", "ru": "Длина (см)", "values": [70, 72, 74]},
        {"en": "Chest (cm)", "ru": "Грудь (см)", "values": [54, 58, 62]},
        {"en": "Sleeve (cm)", "ru": "Рукав (см)", "values": [64, 65, 66]},
        {"en": "Shoulders (cm)", "ru": "Плечи (см)", "values": [48, 50, 52]},
    ],
}
_MEAS_DEMO_GOWN_OS = {
    "kind": "garment",
    "columns": ["One size"],
    "rows": [
        {"en": "Length (cm)", "ru": "Длина (см)", "values": [165]},
        {"en": "Chest (cm)", "ru": "Грудь (см)", "values": [46]},
        {"en": "Waist (cm)", "ru": "Талия (см)", "values": [38]},
        {"en": "Hip (cm)", "ru": "Бёдра (см)", "values": [52]},
    ],
}

_ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC_PRODUCTS_DIR = os.path.join(_ROOT, "static", "products")
STATIC_CAMPAIGN_DIR = os.path.join(_ROOT, "static", "campaign")

                                                                                                                         
KISS_HEELS_SERIAL = "RO-0001"
KISS_HEELS_LEGACY_SERIAL = "PA-1206"
_KISS_HEELS_NAME = re.compile(r"^kiss-heels-(\d+)\.(png|jpg|jpeg|webp)$", re.I)
KISS_HEELS_REMOTE = (
    "https://images.unsplash.com/photo-1543163521-1bf539c55dd2?q=80&w=2069&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1460353581641-37baddab0fa2?q=80&w=2072&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1600185365928-3a27bccb6338?q=80&w=2025&auto=format&fit=crop",
)


def _kiss_heels_local_gallery_urls() -> list[str]:
    if not os.path.isdir(STATIC_PRODUCTS_DIR):
        return []
    found: list[tuple[int, str]] = []
    for name in os.listdir(STATIC_PRODUCTS_DIR):
        m = _KISS_HEELS_NAME.match(name)
        if m and os.path.isfile(os.path.join(STATIC_PRODUCTS_DIR, name)):
            found.append((int(m.group(1)), name))
    if not found:
        return []
    found.sort(key=lambda x: x[0])
    return [f"/static/products/{name}" for _, name in found]


def kiss_heels_gallery_urls() -> list[str]:
    local = _kiss_heels_local_gallery_urls()
    if local:
        return local
    return list(KISS_HEELS_REMOTE)


def sync_kiss_heels_product_images(cur) -> None:
    urls = kiss_heels_gallery_urls()
    if not urls:
        return
    for serial in (KISS_HEELS_SERIAL, KISS_HEELS_LEGACY_SERIAL):
        cur.execute("SELECT id FROM Products WHERE serial = ?", (serial,))
        row = cur.fetchone()
        if not row:
            continue
        pid = int(row[0])
        cur.execute("UPDATE Products SET main_image = ? WHERE id = ?", (urls[0], pid))
        cur.execute("DELETE FROM ProductImages WHERE product_id = ?", (pid,))
        for sort_order, url in enumerate(urls):
            cur.execute(
                "INSERT INTO ProductImages (product_id, image_url, sort_order) VALUES (?, ?, ?)",
                (pid, url, sort_order),
            )


                                                                                        
RAF_BOMBER_SERIAL = "RS-0001"
_RAF_BOMBER_NAME = re.compile(r"^raf-bomber-(\d+)\.(png|jpg|jpeg|webp)$", re.I)
RAF_BOMBER_REMOTE = (
    "https://images.unsplash.com/photo-1551028719-00167b16eac5?q=80&w=1975&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1591047139829-d91aecb6caea?q=80&w=1972&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1594938298603-c8148c4dae35?q=80&w=2080&auto=format&fit=crop",
)


def _raf_bomber_local_gallery_urls() -> list[str]:
    if not os.path.isdir(STATIC_PRODUCTS_DIR):
        return []
    found: list[tuple[int, str]] = []
    for name in os.listdir(STATIC_PRODUCTS_DIR):
        m = _RAF_BOMBER_NAME.match(name)
        if m and os.path.isfile(os.path.join(STATIC_PRODUCTS_DIR, name)):
            found.append((int(m.group(1)), name))
    if not found:
        return []
    found.sort(key=lambda x: x[0])
    return [f"/static/products/{name}" for _, name in found]


def raf_bomber_gallery_urls() -> list[str]:
    local = _raf_bomber_local_gallery_urls()
    if local:
        return local
    return list(RAF_BOMBER_REMOTE)


def sync_raf_bomber_product_images(cur) -> None:
    urls = raf_bomber_gallery_urls()
    if not urls:
        return
    cur.execute("SELECT id FROM Products WHERE serial = ?", (RAF_BOMBER_SERIAL,))
    row = cur.fetchone()
    if not row:
        return
    pid = int(row[0])
    cur.execute("UPDATE Products SET main_image = ? WHERE id = ?", (urls[0], pid))
    cur.execute("DELETE FROM ProductImages WHERE product_id = ?", (pid,))
    for sort_order, url in enumerate(urls):
        cur.execute(
            "INSERT INTO ProductImages (product_id, image_url, sort_order) VALUES (?, ?, ?)",
            (pid, url, sort_order),
        )


                                                          
YZY_GRILLZ_SERIAL = "YZY-9999"
_YZY_NAME = re.compile(r"^yzy-(\d+)\.(png|jpg|jpeg|webp)$", re.I)
YZY_GRILLZ_REMOTE = (
    "https://images.unsplash.com/photo-1611591437281-460bfbe1220a?q=80&w=1974&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?q=80&w=1974&auto=format&fit=crop",
)


def _yzy_grillz_local_gallery_urls() -> list[str]:
    if not os.path.isdir(STATIC_PRODUCTS_DIR):
        return []
    found: list[tuple[int, str]] = []
    for name in os.listdir(STATIC_PRODUCTS_DIR):
        m = _YZY_NAME.match(name)
        if m and os.path.isfile(os.path.join(STATIC_PRODUCTS_DIR, name)):
            found.append((int(m.group(1)), name))
    if not found:
        return []
    found.sort(key=lambda x: x[0])
    return [f"/static/products/{name}" for _, name in found]


def yzy_grillz_gallery_urls() -> list[str]:
    local = _yzy_grillz_local_gallery_urls()
    if local:
        return local
    return list(YZY_GRILLZ_REMOTE)


def sync_yzy_grillz_product_images(cur) -> None:
    urls = yzy_grillz_gallery_urls()
    if not urls:
        return
    cur.execute("SELECT id FROM Products WHERE serial = ?", (YZY_GRILLZ_SERIAL,))
    row = cur.fetchone()
    if not row:
        return
    pid = int(row[0])
    cur.execute("UPDATE Products SET main_image = ? WHERE id = ?", (urls[0], pid))
    cur.execute("DELETE FROM ProductImages WHERE product_id = ?", (pid,))
    for sort_order, url in enumerate(urls):
        cur.execute(
            "INSERT INTO ProductImages (product_id, image_url, sort_order) VALUES (?, ?, ?)",
            (pid, url, sort_order),
        )


                                                                                                            
BAL_GRAFFITI_JEANS_SERIAL = "BAL-0001"
_BALENCIAGA_PRODUCT_NAME = re.compile(r"^balenciaga-(\d+)\.(png|jpg|jpeg|webp)$", re.I)
BAL_GRAFFITI_JEANS_REMOTE = (
    "https://images.unsplash.com/photo-1541099649105-f69ad21a3253?q=80&w=1974&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1582418702059-97ebafb35d09?q=80&w=1974&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1604176354204-9268737828e4?q=80&w=1974&auto=format&fit=crop",
)


def _balenciaga_graffiti_jeans_local_gallery_urls() -> list[str]:
    if not os.path.isdir(STATIC_PRODUCTS_DIR):
        return []
    found: list[tuple[int, str]] = []
    for name in os.listdir(STATIC_PRODUCTS_DIR):
        m = _BALENCIAGA_PRODUCT_NAME.match(name)
        if m and os.path.isfile(os.path.join(STATIC_PRODUCTS_DIR, name)):
            found.append((int(m.group(1)), name))
    if not found:
        return []
    found.sort(key=lambda x: x[0])
    return [f"/static/products/{name}" for _, name in found]


def balenciaga_graffiti_jeans_gallery_urls() -> list[str]:
    local = _balenciaga_graffiti_jeans_local_gallery_urls()
    if local:
        return local
    return list(BAL_GRAFFITI_JEANS_REMOTE)


def sync_balenciaga_graffiti_jeans_product_images(cur) -> None:
    urls = balenciaga_graffiti_jeans_gallery_urls()
    if not urls:
        return
    cur.execute("SELECT id FROM Products WHERE serial = ?", (BAL_GRAFFITI_JEANS_SERIAL,))
    row = cur.fetchone()
    if not row:
        return
    pid = int(row[0])
    cur.execute("UPDATE Products SET main_image = ? WHERE id = ?", (urls[0], pid))
    cur.execute("DELETE FROM ProductImages WHERE product_id = ?", (pid,))
    for sort_order, url in enumerate(urls):
        cur.execute(
            "INSERT INTO ProductImages (product_id, image_url, sort_order) VALUES (?, ?, ?)",
            (pid, url, sort_order),
        )


                                                                                          
BC_COUTURE_BAG_SERIAL = "BC-0001"
_COUTUREBAG_NAME = re.compile(r"^couturebag(?:-(\d+))?\.(png|jpg|jpeg|webp)$", re.I)
BC_COUTURE_BAG_REMOTE = (
    "https://images.unsplash.com/photo-1584917865442-de89df76afd3?q=80&w=1974&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1566150905458-1bf1fc113f0d?q=80&w=2071&auto=format&fit=crop",
)


def _bc_couture_bag_local_gallery_urls() -> list[str]:
    if not os.path.isdir(STATIC_PRODUCTS_DIR):
        return []
    found: list[tuple[int, str]] = []
    for name in os.listdir(STATIC_PRODUCTS_DIR):
        m = _COUTUREBAG_NAME.match(name)
        if m and os.path.isfile(os.path.join(STATIC_PRODUCTS_DIR, name)):
            n = int(m.group(1)) if m.group(1) else 0
            found.append((n, name))
    if not found:
        return []
    found.sort(key=lambda x: x[0])
    return [f"/static/products/{name}" for _, name in found]


def bc_couture_bag_gallery_urls() -> list[str]:
    local = _bc_couture_bag_local_gallery_urls()
    if local:
        return local
    return list(BC_COUTURE_BAG_REMOTE)


def sync_bc_couture_bag_product_images(cur) -> None:
    urls = bc_couture_bag_gallery_urls()
    if not urls:
        return
    cur.execute("SELECT id FROM Products WHERE serial = ?", (BC_COUTURE_BAG_SERIAL,))
    row = cur.fetchone()
    if not row:
        return
    pid = int(row[0])
    cur.execute("UPDATE Products SET main_image = ? WHERE id = ?", (urls[0], pid))
    cur.execute("DELETE FROM ProductImages WHERE product_id = ?", (pid,))
    for sort_order, url in enumerate(urls):
        cur.execute(
            "INSERT INTO ProductImages (product_id, image_url, sort_order) VALUES (?, ?, ?)",
            (pid, url, sort_order),
        )


def resolve_demo_item_images(item: dict) -> tuple[str, list[str]]:
    serial = item.get("serial")
    if serial == KISS_HEELS_SERIAL:
        urls = kiss_heels_gallery_urls()
        return urls[0], urls
    if serial == RAF_BOMBER_SERIAL:
        urls = raf_bomber_gallery_urls()
        return urls[0], urls
    if serial == YZY_GRILLZ_SERIAL:
        urls = yzy_grillz_gallery_urls()
        return urls[0], urls
    if serial == BAL_GRAFFITI_JEANS_SERIAL:
        urls = balenciaga_graffiti_jeans_gallery_urls()
        return urls[0], urls
    if serial == BC_COUTURE_BAG_SERIAL:
        urls = bc_couture_bag_gallery_urls()
        return urls[0], urls
    main = item["image"]
    return main, item.get("images") or [main]


DEMO_PRODUCTS: list[dict] = [
    {
        "category": "rtw",
        "item_category": "coats_jackets",
        "serial": "PA-0510",
        "brand": "Maison Margiela",
        "name": "Oversized wool coat",
        "price": 505,
        "max_days": 14,
        "condition_score": 9,
        "material": "100% Virgin Wool",
        "origin": "Italy",
        "condition": "Excellent",
        "sizes": ["S", "M", "L", "XL"],
        "image": "https://images.unsplash.com/photo-1544022613-e87ca75a784a?q=80&w=1974&auto=format&fit=crop",
        "measurements": _MEAS_DEMO_COAT,
    },
    {
        "category": "rtw",
        "item_category": "coats_jackets",
        "serial": "PA-0511",
        "brand": "Balenciaga",
        "name": "Deconstructed blazer",
        "price": 421,
        "max_days": 10,
        "condition_score": 8,
        "material": "Wool Gabardine",
        "origin": "Italy",
        "condition": "Very good",
        "sizes": ["XS", "S", "M", "L", "XL"],
        "image": "https://images.unsplash.com/photo-1507679799987-c73779587ccf?q=80&w=2071&auto=format&fit=crop",
        "measurements": _MEAS_DEMO_BLAZER,
    },
    {
        "category": "rtw",
        "item_category": "heels",
        "serial": "RO-0001",
        "brand": "Rick Owens",
        "name": "Kiss Heels",
        "price": 196,
        "max_days": 12,
        "condition_score": 9,
        "material": "True Leather",
        "origin": "Italy",
        "condition": "Good",
        "sizes": ["EU 40"],
        "image": "/static/products/kiss-heels-1.png",
        "images": [],
        "measurements": _MEAS_DEMO_HEELS,
    },
    {
        "category": "rtw",
        "item_category": "coats_jackets",
        "serial": "RS-0001",
        "brand": "Raf Simons",
        "name": "AW01 Raf Simons Riot Riot Camouflage Patched Bomber Jacket",
        "price": 982,
        "max_days": 3,
        "condition_score": 8,
        "material": "Canvas",
        "origin": "USA",
        "condition": "Good",
        "sizes": ["XL"],
        "image": "/static/products/raf-bomber-1.png",
        "images": [],
        "measurements": _MEAS_DEMO_BOMBER,
    },
    {
        "category": "rtw",
        "item_category": "jewelry",
        "serial": "YZY-9999",
        "brand": "YZY",
        "name": "Yeezy Grillz",
        "price": 56,
        "max_days": 30,
        "condition_score": 10,
        "material": "Steel",
        "origin": "USA",
        "condition": "Perfect",
        "sizes": [],
        "image": "/static/products/yzy-1.jpg",
        "images": [],
        "measurements": _MEAS_DEMO_JEWELRY_OS,
    },
    {
        "category": "rtw",
        "item_category": "pants_denim",
        "serial": "BAL-0001",
        "brand": "Balenciaga",
        "name": "SS23 Graffiti Jeans Baggy",
        "price": 224,
        "max_days": 10,
        "condition_score": 9,
        "material": "japanese organic denim, light wash",
        "origin": "Itally",
        "condition": "Perfect",
        "sizes": ["XS"],
        "image": "/static/products/balenciaga-1.jpg",
        "images": [],
        "measurements": _MEAS_DEMO_JEANS_XS,
    },
    {
        "category": "couture",
        "item_category": "bags",
        "serial": "BC-0001",
        "brand": "Balenciaga Couture",
        "name": "Getaria One Handle Bag",
        "price": 393,
        "max_days": 5,
        "condition_score": 10,
        "material": "Black calfskin leather",
        "origin": "Itally",
        "condition": "Perfect",
        "sizes": [],
        "image": "/static/products/couturebag.jpg",
        "images": [],
        "measurements": _MEAS_DEMO_BAG_OS,
    },
    {
        "category": "rtw",
        "item_category": "dresses",
        "serial": "PA-0512",
        "brand": "Yohji Yamamoto",
        "name": "Silk shirt dress",
        "price": 561,
        "max_days": 7,
        "condition_score": 10,
        "material": "100% Mulberry Silk",
        "origin": "Japan",
        "condition": "Pristine",
        "sizes": ["XS", "S", "M"],
        "image": "https://images.unsplash.com/photo-1539008835657-9e8e9680c956?q=80&w=1974&auto=format&fit=crop",
        "measurements": _MEAS_DEMO_DRESS_XSM,
    },
    {
        "category": "rtw",
        "item_category": "coats_jackets",
        "serial": "PA-0513",
        "brand": "Vetements",
        "name": "Oversized bomber",
        "price": 337,
        "max_days": 14,
        "condition_score": 9,
        "material": "Recycled Nylon",
        "origin": "Italy",
        "condition": "Excellent",
        "sizes": ["S", "M", "L"],
        "image": "https://images.unsplash.com/photo-1550614000-4b95d4ed79cf?q=80&w=2000&auto=format&fit=crop",
        "measurements": _MEAS_DEMO_JACKET_SML,
    },
    {
        "category": "rtw",
        "item_category": "coats_jackets",
        "serial": "PA-0556",
        "brand": "Comme des Garçons",
        "name": "Layered jacket",
        "price": 253,
        "max_days": 10,
        "condition_score": 7,
        "material": "Cotton / Polyester",
        "origin": "Japan",
        "condition": "Good",
        "sizes": ["S", "M", "L"],
        "image": "https://images.unsplash.com/photo-1520639888713-7851133b1ed0?q=80&w=1974&auto=format&fit=crop",
        "measurements": _MEAS_DEMO_JACKET_SML,
    },
    {
        "category": "couture",
        "item_category": "dresses",
        "serial": "PA-C001",
        "brand": "Maison Margiela",
        "name": "Artisanal recicla gown",
        "price": 2525,
        "max_days": 3,
        "condition_score": 10,
        "material": "Reclaimed vintage textiles",
        "origin": "France",
        "condition": "Museum grade",
        "sizes": ["One size"],
        "image": "https://images.unsplash.com/photo-1566150905458-1bf1fc113f0d?q=80&w=2071&auto=format&fit=crop",
        "measurements": _MEAS_DEMO_GOWN_OS,
    },
    {
        "category": "couture",
        "item_category": "dresses",
        "serial": "PA-C002",
        "brand": "Schiaparelli",
        "name": "Golden vein gown",
        "price": 3367,
        "max_days": 3,
        "condition_score": 10,
        "material": "Silk & Brass",
        "origin": "France",
        "condition": "Exhibition piece",
        "sizes": ["One size"],
        "image": "https://images.unsplash.com/photo-1595777457583-95e059d581b8?q=80&w=1983&auto=format&fit=crop",
        "measurements": _MEAS_DEMO_GOWN_OS,
    },
]

                                                                   
DEMO_WIRED_PRODUCT_SERIALS = ("RO-0001", "RS-0001", "YZY-9999", "BAL-0001", "BC-0001")


def wired_demo_products() -> list[dict]:
    by_serial = {p["serial"]: p for p in DEMO_PRODUCTS}
    missing = [s for s in DEMO_WIRED_PRODUCT_SERIALS if s not in by_serial]
    if missing:
        raise KeyError(f"DEMO_PRODUCTS missing serials: {missing}")
    return [by_serial[s] for s in DEMO_WIRED_PRODUCT_SERIALS]


DEFAULT_CAMPAIGN_SETTINGS = {
    "intro_en": "Silhouette, material, and light — a visual sequence shot for Protocol Archive.",
    "intro_ru": "Силуэт, материал и свет — визуальный ряд для Protocol Archive.",
    "tagline_en": "Editorial series",
    "tagline_ru": "Редакционная серия",
    "members_area_hero_url": (
        "https://zxpcxfcmqfgzufcuvyyw.supabase.co/storage/v1/object/public/media/"
        "protocol_archive/site/14a650ccb04209cfc3e5e793782643f8.jpg"
    ),
}

_CAMPAIGN_IMAGE_NAME = re.compile(r"^campaign-(\d+)\.(png|jpg|jpeg|webp)$", re.I)


def campaign_local_image_urls() -> list[str]:
    """Файлы campaign-1.jpg, campaign-02.png, … в static/campaign — по возрастанию номера."""
    if not os.path.isdir(STATIC_CAMPAIGN_DIR):
        return []
    found: list[tuple[int, str]] = []
    for name in os.listdir(STATIC_CAMPAIGN_DIR):
        m = _CAMPAIGN_IMAGE_NAME.match(name)
        path = os.path.join(STATIC_CAMPAIGN_DIR, name)
        if m and os.path.isfile(path):
            found.append((int(m.group(1)), name))
    if not found:
        return []
    found.sort(key=lambda x: x[0])
    return [f"/static/campaign/{name}" for _, name in found]


                                                                                                 
CAMPAIGN_STORIES_REMOTE_FALLBACK: list[dict] = [
    {
        "sort_order": 0,
        "headline_en": "Look 01",
        "headline_ru": "Look 01",
        "body_en": "Editorial session in Paris — silhouette, fabric, and light.",
        "body_ru": "Редакционная съёмка в Париже — силуэт, ткань и свет.",
        "credits_en": "Paris",
        "credits_ru": "Paris",
        "images": [
            "https://images.unsplash.com/photo-1612336307429-8a898d10e223?q=80&w=2070&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?q=80&w=2070&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?q=80&w=2000&auto=format&fit=crop",
        ],
    },
    {
        "sort_order": 1,
        "headline_en": "Look 02",
        "headline_ru": "Look 02",
        "body_en": "Studio study — controlled lighting and form.",
        "body_ru": "Студийный этюд — контроль света и формы.",
        "credits_en": "Studio",
        "credits_ru": "Студия",
        "images": [
            "https://images.unsplash.com/photo-1550614000-4b95d4ed79cf?q=80&w=2000&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1469334031218-e382a71b716b?q=80&w=1970&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1509631179647-0177331693ae?q=80&w=1976&auto=format&fit=crop",
        ],
    },
    {
        "sort_order": 2,
        "headline_en": "Look 03",
        "headline_ru": "Look 03",
        "body_en": "Archive references — materials from the house collection.",
        "body_ru": "Отсылки к архиву — материалы из домашней коллекции.",
        "credits_en": "Archive",
        "credits_ru": "Архив",
        "images": [
            "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?q=80&w=2070&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1539008835657-9e8e9680c956?q=80&w=1974&auto=format&fit=crop",
            "https://images.unsplash.com/photo-1595777457583-95e059d581b8?q=80&w=1983&auto=format&fit=crop",
        ],
    },
]


def campaign_stories_for_seed() -> list[dict]:
    """
    Истории для сида: при наличии файлов в static/campaign — одна история, все кадры в одной галерее
    (первый файл — обложка на странице кампании). Иначе — CAMPAIGN_STORIES_REMOTE_FALLBACK.
    """
    urls = campaign_local_image_urls()
    if not urls:
        return list(CAMPAIGN_STORIES_REMOTE_FALLBACK)
    return [
        {
            "sort_order": 0,
            "headline_en": "Campaign",
            "headline_ru": "Кампания",
            "body_en": "Full editorial sequence — studio portraits, silhouettes, and light.",
            "body_ru": "Полная редакционная серия — студийные портреты, силуэты и свет.",
            "credits_en": "Campaign",
            "credits_ru": "Кампания",
            "images": list(urls),
        }
    ]


def fallback_products_list() -> list[dict]:
    """Список как PRODUCTS в app.py при недоступной БД (id 1..n по порядку)."""
    out: list[dict] = []
    for i, item in enumerate(DEMO_PRODUCTS, start=1):
        main, gallery = resolve_demo_item_images(item)
        mj = None
        if item.get("measurements") is not None:
            mj = json.dumps(item["measurements"], ensure_ascii=False)
        row = {
            "id": i,
            "category": item["category"],
            "item_category": item.get("item_category"),
            "serial": item["serial"],
            "brand": item["brand"],
            "name": item["name"],
            "price": item["price"],
            "max_days": item["max_days"],
            "condition_score": item["condition_score"],
            "material": item["material"],
            "origin": item["origin"],
            "condition": item["condition"],
            "sizes": list(item.get("sizes") or []),
            "image": main,
            "images": gallery,
            "measurements_json": mj,
        }
        enrich_product_dict(row, mj)
        out.append(row)
    return out
