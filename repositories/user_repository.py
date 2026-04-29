from core.db import get_db_connection


def fetch_user_by_email(email_norm):
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            'SELECT id, email, password_hash, display_name FROM AppUsers WHERE email = ?',
            (email_norm,),
        )
        return cur.fetchone()


def insert_user(email_norm, password_hash, display_name):
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO AppUsers (email, password_hash, display_name)
            OUTPUT INSERTED.id
            VALUES (?, ?, ?)
            """,
            (email_norm, password_hash, display_name),
        )
        row = cur.fetchone()
        conn.commit()
        return int(row[0])
