from core.db import get_db_connection


def fetch_user_by_email(email_norm):
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                id,
                email,
                password_hash,
                display_name,
                is_admin,
                is_email_verified,
                email_verification_code_hash,
                email_verification_expires_at,
                email_verification_attempts,
                level_code,
                lifetime_orders_count,
                lifetime_spend_amount
            FROM AppUsers
            WHERE email = ?
            """,
            (email_norm,),
        )
        return cur.fetchone()


def insert_user(email_norm, password_hash, display_name):
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO AppUsers (email, password_hash, display_name)
            VALUES (?, ?, ?)
            RETURNING id
            """,
            (email_norm, password_hash, display_name),
        )
        row = cur.fetchone()
        conn.commit()
        return int(row[0])


def set_user_verification_code(user_id, code_hash, expires_at):
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE AppUsers
            SET email_verification_code_hash = ?,
                email_verification_expires_at = ?,
                email_verification_attempts = 0
            WHERE id = ?
            """,
            (code_hash, expires_at, int(user_id)),
        )
        conn.commit()


def increment_verification_attempt(user_id):
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE AppUsers
            SET email_verification_attempts = COALESCE(email_verification_attempts, 0) + 1
            WHERE id = ?
            """,
            (int(user_id),),
        )
        conn.commit()


def mark_email_verified(user_id):
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE AppUsers
            SET is_email_verified = 1,
                email_verification_code_hash = NULL,
                email_verification_expires_at = NULL,
                email_verification_attempts = 0
            WHERE id = ?
            """,
            (int(user_id),),
        )
        conn.commit()


def list_users_for_admin(limit=200):
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, email, display_name, is_admin, is_email_verified, level_code, lifetime_orders_count, lifetime_spend_amount
            FROM AppUsers
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (int(limit),),
        )
        return cur.fetchall()


def set_admin_flag(user_id, is_admin):
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE AppUsers SET is_admin = ? WHERE id = ?",
            (1 if is_admin else 0, int(user_id)),
        )
        conn.commit()


def update_user_loyalty(user_id, level_code, orders_count, spend_amount):
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE AppUsers
            SET level_code = ?,
                lifetime_orders_count = ?,
                lifetime_spend_amount = ?
            WHERE id = ?
            """,
            (str(level_code), int(orders_count), int(spend_amount), int(user_id)),
        )
        conn.commit()
