"""User persistence helpers for auth routes."""
from werkzeug.security import generate_password_hash

from repositories.user_repository import (
    fetch_user_by_email,
    increment_verification_attempt,
    insert_user,
    list_users_for_admin,
    mark_email_verified,
    set_admin_flag,
    set_user_verification_code,
    update_user_loyalty,
)

def _user_fetch_by_email(email_norm):
    return fetch_user_by_email(email_norm)


def _user_insert(email_norm, password_plain, display_name):
    return insert_user(email_norm, generate_password_hash(password_plain), display_name)


def _set_user_verification_code(user_id, code_hash, expires_at):
    set_user_verification_code(user_id, code_hash, expires_at)


def _increment_verification_attempt(user_id):
    increment_verification_attempt(user_id)


def _mark_email_verified(user_id):
    mark_email_verified(user_id)


def _list_users_for_admin(limit=200):
    return list_users_for_admin(limit)


def _set_admin_flag(user_id, is_admin):
    set_admin_flag(user_id, is_admin)


def _update_user_loyalty(user_id, level_code, orders_count, spend_amount):
    update_user_loyalty(user_id, level_code, orders_count, spend_amount)
