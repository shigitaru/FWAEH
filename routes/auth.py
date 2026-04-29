from flask import render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash


def register_auth_routes(app, deps):
    t = deps['t']
    get_current_user = deps['get_current_user']
    get_cart_count = deps['get_cart_count']
    fetch_user_rental_history = deps['_fetch_user_rental_history']
    ensure_app_users_table = deps['ensure_app_users_table']
    user_fetch_by_email = deps['_user_fetch_by_email']
    user_insert = deps['_user_insert']
    clear_user_session = deps['_clear_user_session']
    acc_email_re = deps['ACC_EMAIL_RE']

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
        session['user_id'] = int(row[0])
        session['user_email'] = row[1]
        session['user_display_name'] = row[3]
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
            if user_fetch_by_email(email):
                flash(t('acc_err_email_used'), 'error')
                return redirect(url_for('account'))
            new_id = user_insert(email, password, display_name)
        except Exception as e:
            err = str(e).upper()
            if '23000' in str(e) or 'UNIQUE' in err or '2627' in str(e):
                flash(t('acc_err_email_used'), 'error')
                return redirect(url_for('account'))
            flash(t('acc_db_unavailable'), 'error')
            return redirect(url_for('account'))
        session['user_id'] = new_id
        session['user_email'] = email
        session['user_display_name'] = display_name
        session.modified = True
        flash(t('acc_ok_register'), 'success')
        return redirect(url_for('account'))

    @app.route('/account/logout', methods=['POST'])
    def account_logout():
        clear_user_session()
        return redirect(url_for('account'))

    @app.route('/members')
    def members():
        if not get_current_user():
            flash(t('acc_login_required'), 'error')
            return redirect(url_for('account'))
        return render_template(
            'members.html',
            active_page='members',
            cart_count=get_cart_count(),
            t=t,
        )
