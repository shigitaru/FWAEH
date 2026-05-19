import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash, generate_password_hash

logger = logging.getLogger(__name__)


def register_auth_routes(app, deps):
    bp = Blueprint('auth', __name__)

    t = deps['t']
    get_current_user = deps['get_current_user']
    get_cart_count = deps['get_cart_count']
    fetch_user_rental_history = deps['_fetch_user_rental_history']
    ensure_app_users_table = deps['ensure_app_users_table']
    ensure_rental_orders_tables = deps['ensure_rental_orders_tables']
    user_fetch_by_email = deps['_user_fetch_by_email']
    user_insert = deps['_user_insert']
    set_user_verification_code = deps['_set_user_verification_code']
    increment_verification_attempt = deps['_increment_verification_attempt']
    mark_email_verified = deps['_mark_email_verified']
    send_verification_email = deps['_send_verification_email']
    email_delivery_disabled = deps.get('email_delivery_disabled', False)
    clear_user_session = deps['_clear_user_session']
    set_user_session_state = deps['_set_user_session_state']
    clear_user_session_state = deps['_clear_user_session_state']
    acc_email_re = deps['ACC_EMAIL_RE']
    demo_mode = deps['demo_mode']
    get_loyalty_level = deps['get_loyalty_level']
    next_loyalty_progress = deps['next_loyalty_progress']
    couture_min_level = deps['couture_min_level']
    get_order_review = deps['get_order_review']
    upsert_order_review = deps['upsert_order_review']
    try_cancel_user_order = deps['try_cancel_user_order']
    fetch_account_order_detail = deps['fetch_account_order_detail']
    fetch_order_status_for_user = deps['fetch_order_status_for_user']
    fetch_user_loyalty_counters = deps['fetch_user_loyalty_counters']
    upsert_demo_user = deps['upsert_demo_user']

    _PENDING_VERIFY_KEYS = (
        'pending_verify_user_id',
        'pending_verify_email',
        'pending_verify_display_name',
        'pending_verify_next_resend_at',
    )

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

    def _apply_user_session_from_row(row):
        auth_key = secrets.token_urlsafe(32)
        expires_at_utc = datetime.now(timezone.utc) + timedelta(days=1)
        set_user_session_state(
            int(row[0]),
            hashlib.sha256(auth_key.encode('utf-8')).hexdigest(),
            expires_at_utc.replace(tzinfo=None),
        )
        session['user_id'] = int(row[0])
        session['user_email'] = row[1]
        session['user_display_name'] = row[3]
        session['is_admin'] = bool(row[4]) if len(row) > 4 else False
        session['user_level_code'] = (row[9] if len(row) > 9 else 'bronze') or 'bronze'
        session['user_session_key'] = auth_key
        session['user_session_expires_at'] = expires_at_utc.isoformat()
        session.modified = True

    def _ensure_demo_user(role):
        specs = {
            'bronze': ('demo.bronze@protocol.local', 'Demo Bronze', 'bronze', 0, 0, 0),
            'gold': ('demo.gold@protocol.local', 'Demo Gold', 'gold', 0, 7, 900),
            'admin': ('demo.admin@protocol.local', 'Demo Admin', 'platinum', 1, 15, 2000),
        }
        spec = specs.get(role)
        if not spec:
            return None
        email, display_name, level_code, is_admin, orders_count, spend_amount = spec
        password_hash = generate_password_hash('demo-password')
        ensure_app_users_table()
        upsert_demo_user(email, password_hash, display_name, is_admin, level_code, orders_count, spend_amount)
        return user_fetch_by_email(email)

    @bp.route('/account', methods=['GET'])
    def account():
        history_orders = []
        history_stats = None
        user = get_current_user()
        if (
            not user
            and session.get('pending_verify_user_id')
            and session.get('pending_verify_email')
        ):
            return redirect(url_for('account_verify_page'))
        if user:
            try:
                history_orders, history_stats = fetch_user_rental_history(user['id'])
            except Exception:
                logger.exception('Failed to load account history for user %s', user.get('id'))
                history_orders, history_stats = [], None
        return render_template(
            'account.html',
            active_page='account',
            cart_count=get_cart_count(),
            history_orders=history_orders,
            history_stats=history_stats,
            demo_mode=demo_mode,
            t=t,
        )

    @bp.route('/account/verify', methods=['GET'])
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

    @bp.route('/account/verify/cancel', methods=['GET'])
    def account_verify_cancel():
        """Выход из шага кода без подтверждения почты — иначе /account снова редиректит сюда."""
        for k in _PENDING_VERIFY_KEYS:
            session.pop(k, None)
        session.modified = True
        flash(t('acc_verify_abandoned'), 'success')
        return redirect(url_for('account'))

    @bp.route('/account/login', methods=['POST'])
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
            logger.exception('Failed to load account user during login: %s', email)
            flash(t('acc_db_unavailable'), 'error')
            return redirect(url_for('account'))
        if not row or not check_password_hash(row[2], password):
            flash(t('acc_err_credentials'), 'error')
            return redirect(url_for('account'))
        if len(row) > 5 and not bool(row[5]):
            flash(t('acc_verify_before_login'), 'error')
            return redirect(url_for('account'))
        _apply_user_session_from_row(row)
        flash(t('acc_ok_login'), 'success')
        return redirect(url_for('account'))

    @bp.route('/account/demo-login', methods=['POST'])
    def account_demo_login():
        if not demo_mode:
            flash(t('demo_login_disabled'), 'error')
            return redirect(url_for('account'))
        role = (request.form.get('role') or '').strip().lower()
        row = _ensure_demo_user(role)
        if not row:
            flash(t('demo_login_invalid'), 'error')
            return redirect(url_for('account'))
        _apply_user_session_from_row(row)
        flash(t('demo_login_success'), 'success')
        return redirect(url_for('account'))

    @bp.route('/account/register', methods=['GET', 'POST'])
    def account_register():
        if request.method == 'GET':
            if get_current_user():
                return redirect(url_for('account'))
            if session.get('pending_verify_user_id') and session.get('pending_verify_email'):
                return redirect(url_for('account_verify_page'))
            return render_template(
                'account_register.html',
                active_page='account',
                cart_count=get_cart_count(),
                t=t,
            )
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password') or ''
        password2 = request.form.get('password_confirm') or ''
        display_name = (request.form.get('display_name') or '').strip()
        if not display_name:
            flash(t('acc_err_name'), 'error')
            return redirect(url_for('account_register'))
        if len(display_name) > 120:
            display_name = display_name[:120]
        if not acc_email_re.match(email):
            flash(t('acc_err_email_invalid'), 'error')
            return redirect(url_for('account_register'))
        if len(password) < 8:
            flash(t('acc_err_password_short'), 'error')
            return redirect(url_for('account_register'))
        if password != password2:
            flash(t('acc_err_password_mismatch'), 'error')
            return redirect(url_for('account_register'))
        try:
            ensure_app_users_table()
            existing = user_fetch_by_email(email)
            if existing:
                                                                               
                                                                     
                if len(existing) > 5 and not bool(existing[5]):
                    if email_delivery_disabled:
                        mark_email_verified(int(existing[0]))
                        row = user_fetch_by_email(email)
                        if row:
                            _apply_user_session_from_row(row)
                        flash(t('acc_ok_email_verified'), 'success')
                        return redirect(url_for('account'))
                    _issue_verification_code(email, existing[3] or display_name, int(existing[0]))
                    flash(t('acc_register_pending_exists_resent'), 'success')
                    return redirect(url_for('account_verify_page'))
                flash(t('acc_err_email_used'), 'error')
                return redirect(url_for('account'))
            new_id = user_insert(email, password, display_name)
            if email_delivery_disabled:
                mark_email_verified(new_id)
                row = user_fetch_by_email(email)
                if row:
                    _apply_user_session_from_row(row)
                flash(t('acc_ok_email_verified'), 'success')
                return redirect(url_for('account'))
            _issue_verification_code(email, display_name, new_id)
        except Exception as e:
            err = str(e).upper()
            if '23000' in str(e) or 'UNIQUE' in err or '2627' in str(e):
                flash(t('acc_err_email_used'), 'error')
                return redirect(url_for('account'))
                                                                                     
                                                                               
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
                or 'network is unreachable' in msg
            ):
                flash(f'{t("acc_mail_send_failed_prefix")}: {e}', 'error')
                return redirect(url_for('account_register'))
            flash(f'{t("acc_db_unavailable")}: {e}', 'error')
            return redirect(url_for('account_register'))
        flash(t('acc_code_sent_next_step'), 'success')
        return redirect(url_for('account_verify_page'))

    @bp.route('/account/verify-email', methods=['POST'])
    def account_verify_email():
        pending_user_id = session.get('pending_verify_user_id')
        pending_email = (session.get('pending_verify_email') or '').strip().lower()
        if not pending_user_id or not pending_email:
            flash(t('acc_register_start_first'), 'error')
            return redirect(url_for('account'))
        code = (request.form.get('code') or '').strip()
        if len(code) != 6 or not code.isdigit():
            flash(t('acc_verify_code_format'), 'error')
            return redirect(url_for('account_verify_page'))
        try:
            row = user_fetch_by_email(pending_email)
            if not row:
                for k in _PENDING_VERIFY_KEYS:
                    session.pop(k, None)
                session.modified = True
                flash(t('acc_verify_user_not_found'), 'error')
                return redirect(url_for('account'))
            expires_at = row[7] if len(row) > 7 else None
            attempts = int(row[8] or 0) if len(row) > 8 else 0
            expected_hash = row[6] if len(row) > 6 else None
            if attempts >= 5:
                flash(t('acc_verify_attempts_exceeded'), 'error')
                for k in _PENDING_VERIFY_KEYS:
                    session.pop(k, None)
                session.modified = True
                return redirect(url_for('account'))
            if not expires_at or expires_at < datetime.utcnow():
                flash(t('acc_verify_code_expired'), 'error')
                return redirect(url_for('account_verify_page'))
            actual_hash = _code_hash(pending_email, code)
            if not expected_hash or expected_hash != actual_hash:
                increment_verification_attempt(pending_user_id)
                flash(t('acc_verify_code_invalid'), 'error')
                return redirect(url_for('account_verify_page'))
            mark_email_verified(pending_user_id)
            _apply_user_session_from_row(row)
            for k in _PENDING_VERIFY_KEYS:
                session.pop(k, None)
            session.modified = True
            flash(t('acc_ok_email_verified'), 'success')
            return redirect(url_for('account'))
        except Exception:
            logger.exception('Failed to verify email for pending user %s', pending_user_id)
            flash(t('acc_db_unavailable'), 'error')
            return redirect(url_for('account_verify_page'))

    @bp.route('/account/resend-verification', methods=['POST'])
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
                    return redirect(url_for('account_verify_page'))
            except ValueError:
                logger.warning('Ignoring malformed pending_verify_next_resend_at: %s', next_resend_at)
        try:
            _issue_verification_code(pending_email, pending_name, pending_user_id)
            flash(t('acc_resend_sent'), 'success')
        except Exception:
            logger.exception('Failed to resend verification email for user %s', pending_user_id)
            flash(t('acc_resend_failed'), 'error')
        return redirect(url_for('account_verify_page'))

    @bp.route('/account/logout', methods=['POST'])
    def account_logout():
        current_uid = session.get('user_id')
        try:
            if current_uid is not None:
                clear_user_session_state(int(current_uid))
        except Exception:
            logger.exception('Failed to clear persistent session state for user %s', current_uid)
        clear_user_session()
        for k in ('is_admin', 'user_level_code'):
            session.pop(k, None)
        return redirect(url_for('account'))

    @bp.route('/account/order/<int:order_id>/cancel', methods=['POST'])
    def account_cancel_order(order_id):
        user_id = session.get('user_id')
        if not user_id:
            flash(t('acc_login_required'), 'error')
            return redirect(url_for('account'))
        try:
            ensure_rental_orders_tables()
            outcome = try_cancel_user_order(int(order_id), int(user_id))
            if outcome == 'not_found':
                flash(t('account_cancel_not_found'), 'error')
            elif outcome == 'not_allowed':
                flash(t('account_cancel_not_allowed'), 'error')
            else:
                flash(t('account_cancel_success'), 'success')
        except Exception:
            logger.exception('Failed to cancel order %s for user %s', order_id, user_id)
            flash(t('acc_db_unavailable'), 'error')
        return redirect(url_for('account'))

    @bp.route('/account/order/<int:order_id>', methods=['GET'])
    def account_order_detail(order_id):
        user_id = session.get('user_id')
        if not user_id:
            flash(t('acc_login_required'), 'error')
            return redirect(url_for('account'))
        try:
            ensure_rental_orders_tables()
            order = fetch_account_order_detail(order_id, user_id)
            if not order:
                flash(t('account_order_not_found'), 'error')
                return redirect(url_for('account'))
            order_review = get_order_review(order['id'], user_id)
            order_status_flow = ('created', 'confirmed', 'in_rent', 'returned')
            order_timeline_index = order_status_flow.index(order['status']) if order['status'] in order_status_flow else -1
            return render_template(
                'account_order.html',
                active_page='account',
                cart_count=get_cart_count(),
                order=order,
                order_review=order_review,
                order_status_flow=order_status_flow,
                order_timeline_index=order_timeline_index,
                t=t,
            )
        except Exception:
            logger.exception('Failed to load order %s for user %s', order_id, user_id)
            flash(t('acc_db_unavailable'), 'error')
            return redirect(url_for('account'))

    @bp.route('/account/order/<int:order_id>/review', methods=['POST'])
    def account_order_review(order_id):
        user_id = session.get('user_id')
        if not user_id:
            flash(t('acc_login_required'), 'error')
            return redirect(url_for('account'))
        try:
            rating = int(request.form.get('rating') or 0)
        except (TypeError, ValueError):
            rating = 0
        body = (request.form.get('body') or '').strip()
        if rating < 1 or rating > 5:
            flash(t('review_rating_required'), 'error')
            return redirect(url_for('account_order_detail', order_id=order_id) + '#order-review')
        try:
            ensure_rental_orders_tables()
            status = fetch_order_status_for_user(order_id, user_id)
            if status is None:
                flash(t('account_order_not_found'), 'error')
                return redirect(url_for('account'))
            if status != 'returned':
                flash(t('review_returned_only'), 'error')
                return redirect(url_for('account_order_detail', order_id=order_id) + '#order-review')
            upsert_order_review(order_id, user_id, rating, body)
            flash(t('review_saved_pending'), 'success')
            return redirect(url_for('account_order_detail', order_id=order_id) + '#order-review')
        except Exception:
            logger.exception('Failed to save review for order %s by user %s', order_id, user_id)
            flash(t('acc_db_unavailable'), 'error')
            return redirect(url_for('account_order_detail', order_id=order_id))

    @bp.route('/members')
    def members():
        user = get_current_user()
        if not user:
            flash(t('acc_members_members_only'), 'error')
            return redirect(url_for('account'))
        level_code = (session.get('user_level_code') or 'bronze').strip().lower()
        level = get_loyalty_level(level_code)
        orders_count = 0
        spend_amount = 0
        try:
            orders_count, spend_amount = fetch_user_loyalty_counters(user['id'])
        except Exception:
            logger.exception('Failed to load loyalty counters for user %s', user.get('id'))
            orders_count, spend_amount = 0, 0
        loyalty_progress = next_loyalty_progress(level_code, orders_count, spend_amount)
        return render_template(
            'members.html',
            active_page='members',
            cart_count=get_cart_count(),
            user_level_code=level_code,
            member_level=level,
            loyalty_progress=loyalty_progress,
            couture_min_level=couture_min_level,
            t=t,
        )

    app.register_blueprint(bp)
