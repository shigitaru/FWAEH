"""SMTP helpers for account verification emails."""
import smtplib
import socket
from email.message import EmailMessage

import requests

from .config import settings


class IPv4SMTP(smtplib.SMTP):
    def _get_socket(self, host, port, timeout):
        last_error = None
        for family, socktype, proto, _, sockaddr in socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM):
            sock = socket.socket(family, socktype, proto)
            sock.settimeout(timeout)
            try:
                sock.connect(sockaddr)
                return sock
            except OSError as exc:
                last_error = exc
                sock.close()
        detail = f': {last_error}' if last_error else ''
        raise OSError(f'Could not connect to SMTP host {host}:{port} over IPv4{detail}')


class IPv4SMTP_SSL(smtplib.SMTP_SSL):
    def _get_socket(self, host, port, timeout):
        last_error = None
        for family, socktype, proto, _, sockaddr in socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM):
            sock = socket.socket(family, socktype, proto)
            sock.settimeout(timeout)
            try:
                sock.connect(sockaddr)
                return self.context.wrap_socket(sock, server_hostname=host)
            except OSError as exc:
                last_error = exc
                sock.close()
        detail = f': {last_error}' if last_error else ''
        raise OSError(f'Could not connect to SMTP SSL host {host}:{port} over IPv4{detail}')


def _send_smtp_message(msg):
    smtp_cls = IPv4SMTP_SSL if int(settings.smtp_port or 0) == 465 else IPv4SMTP
    with smtp_cls(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
        if settings.smtp_use_tls and int(settings.smtp_port or 0) != 465:
            smtp.starttls()
        if settings.smtp_user and settings.smtp_pass:
            smtp.login(settings.smtp_user, settings.smtp_pass)
        smtp.send_message(msg)


def _send_resend_message(msg):
    sender = settings.resend_from or msg['From']
    if not sender:
        raise RuntimeError('RESEND_FROM or SMTP_FROM is required')
    response = requests.post(
        'https://api.resend.com/emails',
        headers={
            'Authorization': f'Bearer {settings.resend_api_key}',
            'Content-Type': 'application/json',
        },
        json={
            'from': sender,
            'to': [msg['To']],
            'subject': msg['Subject'],
            'text': msg.get_content(),
        },
        timeout=20,
    )
    if response.status_code >= 400:
        raise RuntimeError(f'Resend email failed: {response.status_code} {response.text}')


def _send_message(msg):
    if settings.resend_api_key:
        _send_resend_message(msg)
        return
    _send_smtp_message(msg)


def send_verification_email(email_to, display_name, code):
    if not settings.resend_api_key and (not settings.smtp_host or not settings.smtp_from):
        raise RuntimeError('Email delivery is not configured')
    msg = EmailMessage()
    msg['Subject'] = 'Protocol Archive - Email verification code'
    msg['From'] = settings.resend_from or settings.smtp_from
    msg['To'] = email_to
    msg.set_content(
        (
            f'Hello {display_name or "member"},\n\n'
            f'Your verification code: {code}\n'
            'This code will expire in 10 minutes.\n\n'
            'If you did not request registration, ignore this email.'
        )
    )
    _send_message(msg)


def send_rental_approved_email(email_to, display_name, product_names, pickup_code):
    if not settings.resend_api_key and (not settings.smtp_host or not settings.smtp_from):
        raise RuntimeError('Email delivery is not configured')
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
    msg['From'] = settings.resend_from or settings.smtp_from
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
    _send_message(msg)


