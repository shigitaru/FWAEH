"""User persistence helpers for auth routes."""
from werkzeug.security import generate_password_hash

from repositories.user_repository import fetch_user_by_email, insert_user

def _user_fetch_by_email(email_norm):
    return fetch_user_by_email(email_norm)


def _user_insert(email_norm, password_plain, display_name):
    return insert_user(email_norm, generate_password_hash(password_plain), display_name)
