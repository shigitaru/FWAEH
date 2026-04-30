import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from flask import render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash


def register_auth_routes(app, deps):
    t = deps['t']
    get_current_user = deps['get_current_user']
    get_cart_count = deps['get_cart_count']
    fetch_user_rental_history = deps['_fetch_user_rental_history']
    ensure_app_users_table = deps['ensure_app_users_table']
    ensure_rental_orders_tables = deps['ensure_rental_orders_tables']
    get_db_connection = deps['get_db_connection']
    user_fetch_by_email = deps['_user_fetch_by_email']
    user_insert = deps['_user_insert']
    set_user_verification_code = deps['_set_user_verification_code']
    increment_verification_attempt = deps['_increment_verification_attempt']
    mark_email_verified = deps['_mark_email_verified']
    send_verification_email = deps['_send_verification_email']
    clear_user_session = deps['_clear_user_session']
    acc_email_re = deps['ACC_EMAIL_RE']
    loyalty_levels = deps['LOYALTY_LEVELS']

    def _code_hash(email, code):
        return hashlib.sha256(f'{email.lower()}::{code}'.encode('utf-8')).hexdigest()

    def _issue_verification_code(email, display_name, user_id):
        code = f'{secrets.randbelow(1000000):06d}'
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        set_user_verification_code(user_id, _code_hash(email, code), expires_at.replace(tzinfo=None))
        send_verification_email(email, display_name, code)
        session['pending_verify_user_id'] = int(user_id)
        session['pending_verify_email'] = email
        session['pending_verify_display_name'] = display_name
        session['pending_verify_next_resend_at'] = (datetime.now(timezone.utc) + timedelta(seconds=30)).isoformat()
        session.modified = True

    @app.route('/account', methods=['GET'])
    def account():
        history_orders = []
        history_stats = None
        user = get_current_user()
        if user:
            try:
                history_orders, history_stats = fetch_user_rental_history(user['id'])
            except Exception:
                history_orders, history_stats = [], None
        return render_template(
            'account.html',
            active_page='account',
            cart_count=get_cart_count(),
            history_orders=history_orders,
            history_stats=history_stats,
            t=t,
        )

    @app.route('/account/verify', methods=['GET'])
    def account_verify_page():
        if not session.get('pending_verify_user_id') or not session.get('pending_verify_email'):
            flash(t('acc_verify_no_pending'), 'error')
            return redirect(url_for('account'))
        return render_template(
            'account_verify.html',
            active_page='account',
            cart_count=get_cart_count(),
            pending_email=session.get('pending_verify_email'),
            t=t,
        )

    @app.route('/account/login', methods=['POST'])
    def account_login():
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password') or ''
        if not email or not password:
            flash(t('acc_err_credentials'), 'error')
            return redirect(url_for('account'))
        try:
            ensure_app_users_table()
            row = user_fetch_by_email(email)
        except Exception:
            flash(t('acc_db_unavailable'), 'error')
            return redirect(url_for('account'))
        if not row or not check_password_hash(row[2], password):
            flash(t('acc_err_credentials'), 'error')
            return redirect(url_for('account'))
        if len(row) > 5 and not bool(row[5]):
            flash(t('acc_verify_before_login'), 'error')
            return redirect(url_for('account'))
        session['user_id'] = int(row[0])
        session['user_email'] = row[1]
        session['user_display_name'] = row[3]
        session['is_admin'] = bool(row[4]) if len(row) > 4 else False
        session['user_level_code'] = (row[9] if len(row) > 9 else 'bronze') or 'bronze'
        session.modified = True
        flash(t('acc_ok_login'), 'success')
        return redirect(url_for('account'))

    @app.route('/account/register', methods=['POST'])
    def account_register():
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password') or ''
        password2 = request.form.get('password_confirm') or ''
        display_name = (request.form.get('display_name') or '').strip()
        if not display_name:
            flash(t('acc_err_name'), 'error')
            return redirect(url_for('account'))
        if len(display_name) > 120:
            display_name = display_name[:120]
        if not acc_email_re.match(email):
            flash(t('acc_err_email_invalid'), 'error')
            return redirect(url_for('account'))
        if len(password) < 8:
            flash(t('acc_err_password_short'), 'error')
            return redirect(url_for('account'))
        if password != password2:
            flash(t('acc_err_password_mismatch'), 'error')
            return redirect(url_for('account'))
        try:
            ensure_app_users_table()
            existing = user_fetch_by_email(email)
            if existing:
                # If email exists but is not verified yet, allow resending code
                # instead of blocking user with "email already used".
                if len(existing) > 5 and not bool(existing[5]):
                    _issue_verification_code(email, existing[3] or display_name, int(existing[0]))
                    flash(t('acc_register_pending_exists_resent'), 'success')
                    return redirect(url_for('account_verify_page'))
                flash(t('acc_err_email_used'), 'error')
                return redirect(url_for('account'))
            new_id = user_insert(email, password, display_name)
            _issue_verification_code(email, display_name, new_id)
        except Exception as e:
            err = str(e).upper()
            if '23000' in str(e) or 'UNIQUE' in err or '2627' in str(e):
                flash(t('acc_err_email_used'), 'error')
                return redirect(url_for('account'))
            # Most common non-DB failure here is SMTP send failure after user insert.
            # Keep pending user and ask user to retry/resend after fixing SMTP.
            msg = str(e).lower()
            if (
                'smtp' in msg
                or 'auth' in msg
                or 'send' in msg
                or 'verification' in msg
                or 'timed out' in msg
                or 'getaddrinfo' in msg
                or 'name or service not known' in msg
                or 'connection' in msg
            ):
                flash(f'{t("acc_mail_send_failed_prefix")}: {e}', 'error')
                return redirect(url_for('account'))
            flash(f'{t("acc_db_unavailable")}: {e}', 'error')
            return redirect(url_for('account'))
        flash(t('acc_code_sent_next_step'), 'success')
        return redirect(url_for('account_verify_page'))

    @app.route('/account/verify-email', methods=['POST'])
    def account_verify_email():
        pending_user_id = session.get('pending_verify_user_id')
        pending_email = (session.get('pending_verify_email') or '').strip().lower()
        if not pending_user_id or not pending_email:
            flash(t('acc_register_start_first'), 'error')
            return redirect(url_for('account'))
        code = (request.form.get('code') or '').strip()
        if len(code) != 6 or not code.isdigit():
            flash(t('acc_verify_code_format'), 'error')
            return redirect(url_for('account'))
        try:
            row = user_fetch_by_email(pending_email)
            if not row:
                flash(t('acc_verify_user_not_found'), 'error')
                return redirect(url_for('account'))
            expires_at = row[7] if len(row) > 7 else None
            attempts = int(row[8] or 0) if len(row) > 8 else 0
            expected_hash = row[6] if len(row) > 6 else None
            if attempts >= 5:
                flash(t('acc_verify_attempts_exceeded'), 'error')
                return redirect(url_for('account'))
            if not expires_at or expires_at < datetime.utcnow():
                flash(t('acc_verify_code_expired'), 'error')
                return redirect(url_for('account'))
            actual_hash = _code_hash(pending_email, code)
            if not expected_hash or expected_hash != actual_hash:
                increment_verification_attempt(pending_user_id)
                flash(t('acc_verify_code_invalid'), 'error')
                return redirect(url_for('account'))
            mark_email_verified(pending_user_id)
            session['user_id'] = int(row[0])
            session['user_email'] = row[1]
            session['user_display_name'] = row[3]
            session['is_admin'] = bool(row[4]) if len(row) > 4 else False
            session['user_level_code'] = (row[9] if len(row) > 9 else 'bronze') or 'bronze'
            for k in ('pending_verify_user_id', 'pending_verify_email', 'pending_verify_display_name', 'pending_verify_next_resend_at'):
                session.pop(k, None)
            session.modified = True
            flash(t('acc_ok_email_verified'), 'success')
            return redirect(url_for('account'))
        except Exception:
            flash(t('acc_db_unavailable'), 'error')
            return redirect(url_for('account'))

    @app.route('/account/resend-verification', methods=['POST'])
    def account_resend_verification():
        pending_user_id = session.get('pending_verify_user_id')
        pending_email = (session.get('pending_verify_email') or '').strip().lower()
        pending_name = (session.get('pending_verify_display_name') or '').strip()
        next_resend_at = session.get('pending_verify_next_resend_at')
        if not pending_user_id or not pending_email:
            flash(t('acc_resend_no_pending'), 'error')
            return redirect(url_for('account'))
        if next_resend_at:
            try:
                if datetime.now(timezone.utc) < datetime.fromisoformat(next_resend_at):
                    flash(t('acc_resend_wait'), 'error')
                    return redirect(url_for('account'))
            except Exception:
                pass
        try:
            _issue_verification_code(pending_email, pending_name, pending_user_id)
            flash(t('acc_resend_sent'), 'success')
        except Exception:
            flash(t('acc_resend_failed'), 'error')
        return redirect(url_for('account_verify_page'))

    @app.route('/account/logout', methods=['POST'])
    def account_logout():
        clear_user_session()
        for k in ('is_admin', 'user_level_code'):
            session.pop(k, None)
        return redirect(url_for('account'))

    @app.route('/account/order/<int:order_id>/cancel', methods=['POST'])
    def account_cancel_order(order_id):
        user_id = session.get('user_id')
        if not user_id:
            flash(t('acc_login_required'), 'error')
            return redirect(url_for('account'))
        try:
            ensure_rental_orders_tables()
            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT id, status
                    FROM RentalOrders
                    WHERE id = ? AND user_id = ?
                    """,
                    (int(order_id), int(user_id)),
                )
                row = cur.fetchone()
                if not row:
                    flash(t('account_cancel_not_found'), 'error')
                    return redirect(url_for('account'))
                status = (row[1] or 'created').strip().lower()
                if status != 'created':
                    flash(t('account_cancel_not_allowed'), 'error')
                    return redirect(url_for('account'))
                cur.execute("UPDATE RentalOrders SET status = N'cancelled' WHERE id = ?", (int(order_id),))
                conn.commit()
            flash(t('account_cancel_success'), 'success')
        except Exception:
            flash(t('acc_db_unavailable'), 'error')
        return redirect(url_for('account'))

    @app.route('/account/order/<int:order_id>', methods=['GET'])
    def account_order_detail(order_id):
        user_id = session.get('user_id')
        if not user_id:
            flash(t('acc_login_required'), 'error')
            return redirect(url_for('account'))
        try:
            ensure_rental_orders_tables()
            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT id, status, total_items, total_price, rental_start_date, rental_end_date, created_at, pickup_code
                    FROM RentalOrders
                    WHERE id = ? AND user_id = ?
                    """,
                    (int(order_id), int(user_id)),
                )
                row = cur.fetchone()
                if not row:
                    flash(t('account_order_not_found'), 'error')
                    return redirect(url_for('account'))
                cur.execute(
                    """
                    SELECT serial, brand_name, product_name, size_label, rental_days, line_total, image_url
                    FROM RentalOrderItems
                    WHERE order_id = ?
                    ORDER BY id ASC
                    """,
                    (int(order_id),),
                )
                items = [
                    {
                        'serial': x[0] or '',
                        'brand_name': x[1] or '',
                        'product_name': x[2] or '',
                        'size_label': x[3] or '',
                        'rental_days': int(x[4] or 0),
                        'line_total': int(x[5] or 0),
                        'image_url': x[6] or '',
                    }
                    for x in cur.fetchall()
                ]
            order = {
                'id': int(row[0]),
                'status': (row[1] or 'created').strip().lower(),
                'total_items': int(row[2] or 0),
                'total_price': int(row[3] or 0),
                'rental_start_date': row[4],
                'rental_end_date': row[5],
                'created_at': row[6],
                'pickup_code': row[7] or '',
                'items': items,
            }
            return render_template(
                'account_order.html',
                active_page='account',
                cart_count=get_cart_count(),
                order=order,
                t=t,
            )
        except Exception:
            flash(t('acc_db_unavailable'), 'error')
            return redirect(url_for('account'))

    @app.route('/members')
    def members():
        if not get_current_user():
            flash(t('acc_login_required'), 'error')
            return redirect(url_for('account'))
        level_code = (session.get('user_level_code') or 'bronze').strip().lower()
        level = next((x for x in loyalty_levels if x['code'] == level_code), loyalty_levels[0])
        return render_template(
            'members.html',
            active_page='members',
            cart_count=get_cart_count(),
            user_level_code=level_code,
            member_level=level,
            t=t,
        )
