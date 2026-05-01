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


def send_rental_approved_email(email_to, display_name, product_names, pickup_code):
    if not settings.smtp_host or not settings.smtp_from:
        raise RuntimeError('SMTP is not configured')
    if isinstance(product_names, (list, tuple)):
        names = [str(x).strip() for x in product_names if str(x or '').strip()]
    else:
        names = [str(product_names or '').strip()]
    names = [x for x in names if x]
    if not names:
        names = ['ваш заказ']
    items_text = '\n'.join(f'- {name}' for name in names)
    intro = 'Ваша заявка на аренду одобрена.' if len(names) > 1 else f'Ваша заявка на аренду предмета "{names[0]}" одобрена.'
    msg = EmailMessage()
    msg['Subject'] = 'Protocol Archive - Ваша заявка одобрена'
    msg['From'] = settings.smtp_from
    msg['To'] = email_to
    msg.set_content(
        (
            f'Здравствуйте, {display_name or "клиент"}!\n\n'
            f'{intro}\n'
            f'Состав аренды:\n{items_text}\n\n'
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


