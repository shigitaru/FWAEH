"""
Initialize the Supabase/PostgreSQL schema and optionally seed demo content.

Run after setting DB_ENGINE=postgres and POSTGRES_CONNECTION_STRING/SUPABASE_DB_URL:
    python scripts/init_postgres_db.py

Optional:
    SEED_RESET_DEMO=1 python scripts/init_postgres_db.py
"""
import os
import sys

_APP_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
if _APP_ROOT not in sys.path:
    sys.path.insert(0, _APP_ROOT)

from core.config import settings  # noqa: E402
from core.db import get_db_connection, using_postgres  # noqa: E402
from core.pg_schema import ensure_postgres_schema  # noqa: E402
from seed_defaults import (  # noqa: E402
    DEFAULT_CAMPAIGN_SETTINGS,
    campaign_stories_for_seed,
    resolve_demo_item_images,
    wired_demo_products,
)


RESET_DEMO = os.getenv("SEED_RESET_DEMO", "").strip().lower() in ("1", "true", "yes")


def _ensure_brand_id(cur, brand_name):
    cur.execute("SELECT id FROM Brands WHERE name = ?", (brand_name,))
    row = cur.fetchone()
    if row:
        return int(row[0])
    cur.execute(
        """
        INSERT INTO Brands (name, slug, css_class)
        VALUES (?, ?, ?)
        RETURNING id
        """,
        (brand_name, brand_name, ""),
    )
    return int(cur.fetchone()[0])


def _seed_products(cur):
    cur.execute("SELECT COUNT(*) FROM Products")
    if int(cur.fetchone()[0] or 0) > 0 and not RESET_DEMO:
        return
    if RESET_DEMO:
        cur.execute("DELETE FROM ProductImages")
        cur.execute("DELETE FROM ProductSizes")
        cur.execute("DELETE FROM Products")
    for item in wired_demo_products():
        brand_id = _ensure_brand_id(cur, item["brand"])
        main_image, gallery = resolve_demo_item_images(item)
        cur.execute(
            """
            INSERT INTO Products (
                brand_id, category, item_category, serial, name, price, max_days, condition_score,
                material, origin, condition, main_image
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (serial) DO NOTHING
            RETURNING id
            """,
            (
                brand_id,
                item["category"],
                item.get("item_category"),
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
        row = cur.fetchone()
        if row:
            product_id = int(row[0])
        else:
            cur.execute("SELECT id FROM Products WHERE serial = ?", (item["serial"],))
            product_id = int(cur.fetchone()[0])
        cur.execute("DELETE FROM ProductImages WHERE product_id = ?", (product_id,))
        cur.execute("DELETE FROM ProductSizes WHERE product_id = ?", (product_id,))
        for sort_order, url in enumerate(gallery):
            cur.execute(
                "INSERT INTO ProductImages (product_id, image_url, sort_order) VALUES (?, ?, ?)",
                (product_id, url, sort_order),
            )
        for size_label in item.get("sizes") or []:
            cur.execute(
                "INSERT INTO ProductSizes (product_id, size_label) VALUES (?, ?)",
                (product_id, size_label),
            )


def _seed_campaign(cur):
    d = DEFAULT_CAMPAIGN_SETTINGS
    cur.execute(
        """
        INSERT INTO CampaignSettings (id, intro_en, intro_ru, tagline_en, tagline_ru)
        VALUES (1, ?, ?, ?, ?)
        ON CONFLICT (id) DO UPDATE SET
            intro_en = EXCLUDED.intro_en,
            intro_ru = EXCLUDED.intro_ru,
            tagline_en = EXCLUDED.tagline_en,
            tagline_ru = EXCLUDED.tagline_ru
        """,
        (d["intro_en"], d["intro_ru"], d["tagline_en"], d["tagline_ru"]),
    )
    cur.execute("SELECT COUNT(*) FROM CampaignStories")
    if int(cur.fetchone()[0] or 0) > 0 and not RESET_DEMO:
        return
    if RESET_DEMO:
        cur.execute("DELETE FROM CampaignStoryImages")
        cur.execute("DELETE FROM CampaignStories")
        cur.execute("DELETE FROM CampaignLooks")
    for story in sorted(campaign_stories_for_seed(), key=lambda x: x["sort_order"]):
        cur.execute(
            """
            INSERT INTO CampaignStories (
                sort_order, headline_en, headline_ru, body_en, body_ru, credits_en, credits_ru
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            RETURNING id
            """,
            (
                story["sort_order"],
                story["headline_en"],
                story["headline_ru"],
                story["body_en"],
                story["body_ru"],
                story["credits_en"],
                story["credits_ru"],
            ),
        )
        story_id = int(cur.fetchone()[0])
        cover = story["images"][0]
        cur.execute(
            """
            INSERT INTO CampaignLooks (sort_order, image_url, ref_text, location_text)
            VALUES (?, ?, ?, ?)
            """,
            (story["sort_order"], cover, story["headline_en"][:120], (story["credits_en"] or "")[:120]),
        )
        for idx, url in enumerate(story["images"]):
            cur.execute(
                "INSERT INTO CampaignStoryImages (story_id, sort_order, image_url) VALUES (?, ?, ?)",
                (story_id, idx, url),
            )


def main():
    if not using_postgres():
        raise SystemExit("Set DB_ENGINE=postgres before running this script.")
    if not settings.postgres_connection_string:
        raise SystemExit("Set POSTGRES_CONNECTION_STRING or SUPABASE_DB_URL first.")
    ensure_postgres_schema()
    with get_db_connection() as conn:
        cur = conn.cursor()
        _seed_products(cur)
        _seed_campaign(cur)
        conn.commit()
    print("PostgreSQL schema initialized and demo content checked.")


if __name__ == "__main__":
    main()
