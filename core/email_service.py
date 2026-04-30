"""SMTP helpers for account verification emails."""
import smtplib
from email.message import EmailMessage

from .config import settings


def send_verification_email(email_to, display_name, code):
    if not settings.smtp_host or not settings.smtp_from:
        raise RuntimeError('SMTP is not configured')
    msg = EmailMessage()
    msg['Subject'] = 'Protocol Archive - Email verification code'
    msg['From'] = settings.smtp_from
    msg['To'] = email_to
    msg.set_content(
        (
            f'Hello {display_name or "member"},\n\n'
            f'Your verification code: {code}\n'
            'This code will expire in 10 minutes.\n\n'
            'If you did not request registration, ignore this email.'
        )
    )
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        if settings.smtp_user and settings.smtp_pass:
            smtp.login(settings.smtp_user, settings.smtp_pass)
        smtp.send_message(msg)


def send_rental_approved_email(email_to, display_name, product_name, pickup_code):
    if not settings.smtp_host or not settings.smtp_from:
        raise RuntimeError('SMTP is not configured')
    msg = EmailMessage()
    msg['Subject'] = 'Protocol Archive - Ваша заявка одобрена'
    msg['From'] = settings.smtp_from
    msg['To'] = email_to
    msg.set_content(
        (
            f'Здравствуйте, {display_name or "клиент"}!\n\n'
            f'Ваша заявка на аренду предмета "{product_name}" одобрена.\n'
            f'Приходите в пункт выдачи: {settings.pickup_address}\n'
            f'Код для получения: {pickup_code}\n\n'
            'Покажите этот код сотруднику пункта выдачи.'
        )
    )
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        if settings.smtp_user and settings.smtp_pass:
            smtp.login(settings.smtp_user, settings.smtp_pass)
        smtp.send_message(msg)
