from flask import request, session, redirect, url_for, render_template, flash
from werkzeug.security import check_password_hash
import secrets

from core.product_measurements import default_measurements_payload, parse_measurements_payload, upsert_product_measurement


def register_admin_routes(app, deps):
    t = deps['t']
    tv = deps['tv']
    order_status_flow = deps['ORDER_STATUS_FLOW']
    ensure_rental_orders_tables = deps['ensure_rental_orders_tables']
    get_db_connection = deps['get_db_connection']
    normalize_item_category_slug = deps['normalize_item_category_slug']
    nullable_str = deps['_nullable_str']
    save_uploaded_image = deps['_save_uploaded_image']
    apply_admin_product_image_changes = deps['_apply_admin_product_image_changes']
    filter_products = deps['filter_products']
    fetch_recent_orders_admin = deps['_fetch_recent_orders_admin']
    get_admin_dashboard_stats = deps['get_admin_dashboard_stats']
    get_brands = deps['get_brands']
    get_admin_brands = deps['get_admin_brands']
    get_cart_count = deps['get_cart_count']
    find_product = deps['find_product']
    fetch_product_image_rows = deps['_fetch_product_image_rows']
    fetch_campaign_settings_admin = deps['_fetch_campaign_settings_admin']
    list_campaign_stories_admin = deps['_list_campaign_stories_admin']
    fetch_campaign_story_admin = deps['_fetch_campaign_story_admin']
    collect_story_image_urls_from_form = deps['_collect_story_image_urls_from_form']
    save_campaign_upload = deps['_save_campaign_upload']
    insert_campaign_story_return_id = deps['_insert_campaign_story_return_id']
    list_users_for_admin = deps['_list_users_for_admin']
    set_admin_flag = deps['_set_admin_flag']
    update_user_loyalty = deps['_update_user_loyalty']
    loyalty_levels = deps['LOYALTY_LEVELS']
    recalculate_user_loyalty = deps['recalculate_user_loyalty']
    user_fetch_by_email = deps['_user_fetch_by_email']
    send_rental_approved_email = deps['_send_rental_approved_email']

    def _require_admin():
        if not session.get('user_id') or not bool(session.get('is_admin')):
            flash(t('admin_need_separate_login'), 'error')
            return redirect(url_for('admin_login'))
        return None

    @app.route('/admin/login', methods=['GET', 'POST'])
    def admin_login():
        if request.method == 'POST':
            email = (request.form.get('email') or '').strip().lower()
            password = request.form.get('password') or ''
            if not email or not password:
                flash(t('admin_login_fill_credentials'), 'error')
                return redirect(url_for('admin_login'))
            row = user_fetch_by_email(email)
            if not row or not check_password_hash(row[2], password):
                flash(t('admin_login_invalid'), 'error')
                return redirect(url_for('admin_login'))
            if not bool(row[4]):
                flash(t('admin_login_no_access'), 'error')
                return redirect(url_for('admin_login'))
            session['user_id'] = int(row[0])
            session['user_email'] = row[1]
            session['user_display_name'] = row[3]
            session['is_admin'] = bool(row[4])
            session['user_level_code'] = (row[9] if len(row) > 9 else 'bronze') or 'bronze'
            session.modified = True
            return redirect(url_for('admin_panel', section='products'))
        return render_template('admin_login.html', active_page='admin', cart_count=get_cart_count(), t=t)

    @app.route('/admin', methods=['GET', 'POST'])
    def admin_panel():
        denied = _require_admin()
        if denied:
            return denied
        section = (request.args.get('section') or 'products').strip().lower()
        inventory_query = (request.args.get('q') or '').strip()
        orders_status_filter = (request.args.get('order_status') or '').strip().lower()
        if request.method == 'POST':
            try:
                category = request.form.get('category', '').strip() or 'rtw'
                item_category = normalize_item_category_slug(request.form.get('item_category'))
                serial = request.form.get('serial', '').strip()
                brand_name = request.form.get('brand', '').strip()
                name = request.form.get('name', '').strip()
                price = int(request.form.get('price', '0'))
                max_days_raw = request.form.get('max_days', '').strip()
                condition_score_raw = request.form.get('condition_score', '').strip()
                material = nullable_str(request.form.get('material'))
                origin = nullable_str(request.form.get('origin'))
                condition = nullable_str(request.form.get('condition'))
                main_image = ''
                sizes_raw = request.form.get('sizes', '').strip()
                uploaded_main = save_uploaded_image(request.files.get('main_image_file'))
                uploaded_extra = request.files.getlist('extra_image_files')
                uploaded_unified = request.files.getlist('media_files')
                if uploaded_unified:
                    uploaded_main = save_uploaded_image(uploaded_unified[0]) or uploaded_main
                    for media_item in uploaded_unified[1:]:
                        uploaded_extra.append(media_item)
                if uploaded_main:
                    main_image = uploaded_main
                if not all([serial, brand_name, name, max_days_raw, condition_score_raw]):
                    session['admin_status'] = {'type': 'error', 'message': t('admin_required_fields')}
                    return redirect(url_for('admin_panel', section='products'))
                max_days = int(max_days_raw)
                condition_score = int(condition_score_raw)
                size_values = [s.strip() for s in sizes_raw.split(',') if s.strip()]
                extra_images = []
                for img in uploaded_extra:
                    saved = save_uploaded_image(img)
                    if saved:
                        extra_images.append(saved)
                if not main_image and extra_images:
                    main_image = extra_images.pop(0)
                if not main_image:
                    session['admin_status'] = {'type': 'error', 'message': t('admin_required_main_image')}
                    return redirect(url_for('admin_panel', section='products'))
                with get_db_connection() as conn:
                    cur = conn.cursor()
                    cur.execute('SELECT id FROM Brands WHERE name = ?', (brand_name,))
                    brand_row = cur.fetchone()
                    brand_id = None
                    if brand_row:
                        brand_id = int(brand_row[0])
                    else:
                        cur.execute(
                            '''
                            INSERT INTO Brands (name, slug, css_class)
                            VALUES (?, ?, ?)
                            RETURNING id
                            ''',
                            (brand_name, brand_name, '')
                        )
                        out_row = cur.fetchone()
                        brand_id = int(out_row[0]) if out_row and out_row[0] is not None else None
                    if not brand_id:
                        raise ValueError(t('admin_brand_resolve_error'))
                    cur.execute(
                        '''
                        INSERT INTO Products (brand_id, category, item_category, serial, name, price, max_days, condition_score, material, origin, condition, main_image)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        RETURNING id
                        ''',
                        (
                            brand_id,
                            category,
                            item_category,
                            serial,
                            name,
                            price,
                            max_days,
                            condition_score,
                            material,
                            origin,
                            condition,
                            main_image,
                        ),
                    )
                    prod_row = cur.fetchone()
                    product_id = int(prod_row[0]) if prod_row and prod_row[0] is not None else None
                    if not product_id:
                        raise ValueError('Admin: failed to create product id')
                    cur.execute(
                        'INSERT INTO ProductImages (product_id, image_url, sort_order) VALUES (?, ?, ?)',
                        (product_id, main_image, 0)
                    )
                    for idx, image_url in enumerate(extra_images, start=1):
                        cur.execute(
                            'INSERT INTO ProductImages (product_id, image_url, sort_order) VALUES (?, ?, ?)',
                            (product_id, image_url, idx)
                        )
                    for size_label in size_values:
                        cur.execute('INSERT INTO ProductSizes (product_id, size_label) VALUES (?, ?)', (product_id, size_label))
                    payload = default_measurements_payload(item_category, size_values, product_id=product_id)
                    if payload:
                        upsert_product_measurement(cur, product_id, payload)
                    conn.commit()
                session['admin_status'] = {'type': 'success', 'message': t('admin_product_created')}
            except Exception as exc:
                session['admin_status'] = {'type': 'error', 'message': f'{t("admin_error_prefix")}: {exc}'}
            return redirect(url_for('admin_panel', section='products'))
        products = filter_products(query=inventory_query) if inventory_query else filter_products()
        orders_recent = fetch_recent_orders_admin()
        if orders_status_filter in order_status_flow:
            orders_recent = [x for x in orders_recent if x.get('status') == orders_status_filter]
        else:
            orders_status_filter = ''
        admin_status = session.pop('admin_status', None)
        return render_template(
            'admin.html',
            products=products,
            orders_recent=orders_recent,
            admin_dashboard=get_admin_dashboard_stats(),
            admin_users=list_users_for_admin(),
            admin_section=section,
            order_status_flow=order_status_flow,
            loyalty_levels=loyalty_levels,
            brands=get_brands(),
            brands_admin=get_admin_brands(),
            inventory_query=inventory_query,
            orders_status_filter=orders_status_filter,
            admin_status=admin_status,
            active_page='admin',
            cart_count=get_cart_count(),
            t=t,
            tv=tv
        )

    @app.route('/admin/order/<int:order_id>/status', methods=['POST'])
    def admin_update_order_status(order_id):
        denied = _require_admin()
        if denied:
            return denied
        current_filter = (request.form.get('order_status_filter') or '').strip().lower()
        def _orders_redirect():
            if current_filter in order_status_flow:
                return redirect(url_for('admin_panel', section='orders', order_status=current_filter))
            return redirect(url_for('admin_panel', section='orders'))
        next_status = (request.form.get('status') or '').strip().lower()
        if next_status not in order_status_flow:
            session['admin_status'] = {'type': 'error', 'message': t('admin_order_status_invalid')}
            return _orders_redirect()
        try:
            ensure_rental_orders_tables()
            notification_error = None
            loyalty_recalc_user_id = None
            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT o.id, o.status, o.user_id, u.email, u.display_name
                    FROM RentalOrders o
                    INNER JOIN AppUsers u ON u.id = o.user_id
                    WHERE o.id = ?
                    """,
                    (order_id,),
                )
                order_row = cur.fetchone()
                if not order_row:
                    session['admin_status'] = {'type': 'error', 'message': t('admin_order_not_found')}
                    return _orders_redirect()
                prev_status = (order_row[1] or 'created').strip().lower()
                user_id = int(order_row[2])
                user_email = order_row[3] or ''
                user_name = order_row[4] or ''
                cur.execute('UPDATE RentalOrders SET status = ? WHERE id = ?', (next_status, order_id))
                pickup_code = None
                if next_status == 'confirmed' and prev_status != 'confirmed':
                    pickup_code = f'PA-{secrets.token_hex(3).upper()}'
                    cur.execute('UPDATE RentalOrders SET pickup_code = ? WHERE id = ?', (pickup_code, order_id))
                if next_status == 'returned' and prev_status != 'returned':
                    loyalty_recalc_user_id = user_id
                conn.commit()
            if loyalty_recalc_user_id is not None:
                recalculate_user_loyalty(loyalty_recalc_user_id)
            if next_status == 'confirmed' and user_email:
                try:
                    with get_db_connection() as conn:
                        cur = conn.cursor()
                        cur.execute(
                            """
                            SELECT product_name
                            FROM RentalOrderItems
                            WHERE order_id = ?
                            ORDER BY id ASC
                            """,
                            (order_id,),
                        )
                        item_names = [str(r[0] or '').strip() for r in cur.fetchall() if str(r[0] or '').strip()]
                    send_rental_approved_email(user_email, user_name, item_names or [f'заказ #{order_id}'], pickup_code or '—')
                except Exception as mail_exc:
                    notification_error = str(mail_exc)
            session['admin_status'] = {'type': 'success', 'message': t('admin_order_status_updated')}
            if notification_error:
                session['admin_status'] = {
                    'type': 'error',
                    'message': f'{t("admin_status_updated_but_email_failed")}: {notification_error}'
                }
        except Exception as exc:
            session['admin_status'] = {'type': 'error', 'message': f'{t("admin_error_prefix")}: {exc}'}
        return _orders_redirect()

    @app.route('/admin/product/<int:product_id>/delete', methods=['POST'])
    def admin_delete_product(product_id):
        denied = _require_admin()
        if denied:
            return denied
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute('SELECT id FROM Products WHERE id = ?', (product_id,))
                if not cur.fetchone():
                    session['admin_status'] = {'type': 'error', 'message': t('admin_product_not_found')}
                    return redirect(url_for('admin_panel', section='inventory'))
                cur.execute('DELETE FROM Products WHERE id = ?', (product_id,))
                conn.commit()
            session['admin_status'] = {'type': 'success', 'message': t('admin_product_deleted')}
        except Exception as exc:
            session['admin_status'] = {'type': 'error', 'message': f'{t("admin_error_prefix")}: {exc}'}
        return redirect(url_for('admin_panel', section='inventory'))

    @app.route('/admin/brand/<int:brand_id>/delete', methods=['POST'])
    def admin_delete_brand(brand_id):
        denied = _require_admin()
        if denied:
            return denied
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute('SELECT id FROM Brands WHERE id = ?', (brand_id,))
                if not cur.fetchone():
                    session['admin_status'] = {'type': 'error', 'message': t('admin_brand_not_found')}
                    return redirect(url_for('admin_panel', section='brands'))
                cur.execute('SELECT COUNT(*) FROM Products WHERE brand_id = ?', (brand_id,))
                linked_products = int(cur.fetchone()[0] or 0)
                if linked_products > 0:
                    session['admin_status'] = {'type': 'error', 'message': t('admin_brand_has_products')}
                    return redirect(url_for('admin_panel', section='brands'))
                cur.execute('DELETE FROM Brands WHERE id = ?', (brand_id,))
                conn.commit()
            session['admin_status'] = {'type': 'success', 'message': t('admin_brand_deleted')}
        except Exception as exc:
            session['admin_status'] = {'type': 'error', 'message': f'{t("admin_error_prefix")}: {exc}'}
        return redirect(url_for('admin_panel', section='brands'))

    @app.route('/admin/product/<int:product_id>/edit', methods=['GET', 'POST'])
    def admin_edit_product(product_id):
        denied = _require_admin()
        if denied:
            return denied
        product = find_product(product_id)
        if not product:
            session['admin_status'] = {'type': 'error', 'message': t('admin_product_not_found')}
            return redirect(url_for('admin_panel', section='inventory'))

        if request.method == 'POST':
            try:
                category = request.form.get('category', '').strip() or 'rtw'
                item_category = normalize_item_category_slug(request.form.get('item_category'))
                serial = request.form.get('serial', '').strip()
                brand_name = request.form.get('brand', '').strip()
                name = request.form.get('name', '').strip()
                price = int(request.form.get('price', '0'))
                max_days_raw = request.form.get('max_days', '').strip()
                condition_score_raw = request.form.get('condition_score', '').strip()
                material = nullable_str(request.form.get('material'))
                origin = nullable_str(request.form.get('origin'))
                condition = nullable_str(request.form.get('condition'))
                sizes_raw = request.form.get('sizes', '').strip()
                measurements_json_raw = (request.form.get('measurements_json') or '').strip()
                meas_parsed = None
                if measurements_json_raw:
                    meas_parsed = parse_measurements_payload(measurements_json_raw)
                    if meas_parsed is None:
                        session['admin_status'] = {'type': 'error', 'message': t('admin_measurements_invalid')}
                        return redirect(url_for('admin_edit_product', product_id=product_id))
                if not all([serial, brand_name, name, max_days_raw, condition_score_raw]):
                    session['admin_status'] = {'type': 'error', 'message': t('admin_required_fields')}
                    return redirect(url_for('admin_edit_product', product_id=product_id))
                max_days = int(max_days_raw)
                condition_score = int(condition_score_raw)
                size_values = [s.strip() for s in sizes_raw.split(',') if s.strip()]
                remove_ids = []
                for x in request.form.getlist('remove_image_id'):
                    try:
                        remove_ids.append(int(x))
                    except ValueError:
                        pass
                ordered_ids = []
                for x in request.form.getlist('image_order_id'):
                    try:
                        ordered_ids.append(int(x))
                    except ValueError:
                        pass
                uploaded_main = save_uploaded_image(request.files.get('main_image_file'))
                extra_images = []
                unified_media = request.files.getlist('media_files')
                if unified_media:
                    uploaded_main = save_uploaded_image(unified_media[0]) or uploaded_main
                    for media_item in unified_media[1:]:
                        saved = save_uploaded_image(media_item)
                        if saved:
                            extra_images.append(saved)
                for img in request.files.getlist('extra_image_files'):
                    saved = save_uploaded_image(img)
                    if saved:
                        extra_images.append(saved)
                with get_db_connection() as conn:
                    cur = conn.cursor()
                    try:
                        main_image = apply_admin_product_image_changes(
                            cur, product_id, remove_ids, ordered_ids, uploaded_main, extra_images
                        )
                    except ValueError as ve:
                        if str(ve) == '__LAST_IMAGE__':
                            session['admin_status'] = {'type': 'error', 'message': t('admin_cannot_remove_last_image')}
                            return redirect(url_for('admin_edit_product', product_id=product_id))
                        raise
                    if not main_image:
                        session['admin_status'] = {'type': 'error', 'message': t('admin_required_main_image')}
                        return redirect(url_for('admin_edit_product', product_id=product_id))
                    cur.execute('SELECT id FROM Brands WHERE name = ?', (brand_name,))
                    brand_row = cur.fetchone()
                    brand_id = None
                    if brand_row:
                        brand_id = int(brand_row[0])
                    else:
                        cur.execute(
                            '''
                            INSERT INTO Brands (name, slug, css_class)
                            VALUES (?, ?, ?)
                            RETURNING id
                            ''',
                            (brand_name, brand_name, '')
                        )
                        out_row = cur.fetchone()
                        brand_id = int(out_row[0]) if out_row and out_row[0] is not None else None
                    if not brand_id:
                        raise ValueError(t('admin_brand_resolve_error'))
                    cur.execute(
                        '''
                        UPDATE Products SET brand_id=?, category=?, item_category=?, serial=?, name=?, price=?, max_days=?,
                        condition_score=?, material=?, origin=?, condition=?, main_image=?
                        WHERE id=?
                        ''',
                        (
                            brand_id,
                            category,
                            item_category,
                            serial,
                            name,
                            price,
                            max_days,
                            condition_score,
                            material,
                            origin,
                            condition,
                            main_image,
                            product_id,
                        ),
                    )
                    cur.execute('DELETE FROM ProductSizes WHERE product_id=?', (product_id,))
                    for size_label in size_values:
                        cur.execute(
                            'INSERT INTO ProductSizes (product_id, size_label) VALUES (?, ?)',
                            (product_id, size_label),
                        )
                    upsert_product_measurement(cur, product_id, meas_parsed)
                    conn.commit()
                session['admin_status'] = {'type': 'success', 'message': t('admin_product_updated')}
            except Exception as exc:
                err = str(exc).lower()
                if 'unique' in err or '23000' in err or '2627' in err:
                    session['admin_status'] = {'type': 'error', 'message': t('admin_serial_exists')}
                else:
                    session['admin_status'] = {'type': 'error', 'message': f'{t("admin_error_prefix")}: {exc}'}
                return redirect(url_for('admin_edit_product', product_id=product_id))
            return redirect(url_for('admin_panel', section='inventory'))

        return render_template(
            'admin_edit.html',
            product=product,
            product_images=fetch_product_image_rows(product_id),
            brands=get_brands(),
            admin_status=session.pop('admin_status', None),
            active_page='admin',
            cart_count=get_cart_count(),
            t=t,
            tv=tv,
        )

    @app.route('/admin/campaign', methods=['GET', 'POST'])
    def admin_campaign():
        denied = _require_admin()
        if denied:
            return denied
        if request.method == 'POST':
            intro_en = request.form.get('intro_en', '').strip()
            intro_ru = request.form.get('intro_ru', '').strip()
            tagline_en = request.form.get('tagline_en', '').strip()
            tagline_ru = request.form.get('tagline_ru', '').strip()
            uploaded_hero = save_campaign_upload(request.files.get('members_area_hero_file'))
            members_area_hero_url = uploaded_hero if uploaded_hero else nullable_str(request.form.get('members_area_hero_url'))
            try:
                with get_db_connection() as conn:
                    cur = conn.cursor()
                    cur.execute('SELECT COUNT(*) FROM CampaignSettings WHERE id=1')
                    if cur.fetchone()[0]:
                        cur.execute(
                            '''UPDATE CampaignSettings SET intro_en=?, intro_ru=?, tagline_en=?, tagline_ru=?,
                               members_area_hero_url=? WHERE id=1''',
                            (intro_en, intro_ru, tagline_en, tagline_ru, members_area_hero_url),
                        )
                    else:
                        cur.execute(
                            '''INSERT INTO CampaignSettings (id, intro_en, intro_ru, tagline_en, tagline_ru, members_area_hero_url)
                               VALUES (1, ?, ?, ?, ?, ?)''',
                            (intro_en, intro_ru, tagline_en, tagline_ru, members_area_hero_url),
                        )
                    conn.commit()
                session['admin_status'] = {'type': 'success', 'message': t('admin_campaign_settings_saved')}
            except Exception as exc:
                session['admin_status'] = {'type': 'error', 'message': f'{t("admin_error_prefix")}: {exc}'}
            return redirect(url_for('admin_campaign'))
        settings_data = fetch_campaign_settings_admin()
        stories = list_campaign_stories_admin()
        admin_status = session.pop('admin_status', None)
        return render_template(
            'admin_campaign.html',
            settings=settings_data,
            stories=stories,
            admin_status=admin_status,
            active_page='admin',
            cart_count=get_cart_count(),
            t=t,
        )

    @app.route('/admin/campaign/story/new', methods=['GET', 'POST'])
    def admin_campaign_story_new():
        denied = _require_admin()
        if denied:
            return denied
        if request.method == 'POST':
            headline_en = request.form.get('headline_en', '').strip()
            headline_ru = request.form.get('headline_ru', '').strip()
            if not headline_en and not headline_ru:
                session['admin_status'] = {'type': 'error', 'message': t('admin_story_need_headline')}
                return redirect(url_for('admin_campaign_story_new'))
            urls = collect_story_image_urls_from_form()
            if not urls:
                session['admin_status'] = {'type': 'error', 'message': t('admin_story_need_image')}
                return redirect(url_for('admin_campaign_story_new'))
            body_en = request.form.get('body_en', '').strip()
            body_ru = request.form.get('body_ru', '').strip()
            credits_en = request.form.get('credits_en', '').strip()
            credits_ru = request.form.get('credits_ru', '').strip()
            try:
                with get_db_connection() as conn:
                    cur = conn.cursor()
                    cur.execute('SELECT COALESCE(MAX(sort_order), -1) + 1 FROM CampaignStories')
                    next_sort = int(cur.fetchone()[0])
                    sid = insert_campaign_story_return_id(
                        cur,
                        (
                            next_sort,
                            headline_en or headline_ru,
                            headline_ru or headline_en,
                            body_en,
                            body_ru,
                            credits_en,
                            credits_ru,
                        ),
                    )
                    for i, url in enumerate(urls):
                        cur.execute(
                            'INSERT INTO CampaignStoryImages (story_id, sort_order, image_url) VALUES (?, ?, ?)',
                            (sid, i, url),
                        )
                    conn.commit()
                session['admin_status'] = {'type': 'success', 'message': t('admin_story_created')}
                return redirect(url_for('admin_campaign_story_edit', story_id=sid))
            except Exception as exc:
                session['admin_status'] = {'type': 'error', 'message': f'{t("admin_error_prefix")}: {exc}'}
                return redirect(url_for('admin_campaign_story_new'))
        admin_status = session.pop('admin_status', None)
        return render_template(
            'admin_campaign_story.html',
            story=None,
            images=[],
            admin_status=admin_status,
            active_page='admin',
            cart_count=get_cart_count(),
            t=t,
        )

    @app.route('/admin/campaign/story/<int:story_id>', methods=['GET', 'POST'])
    def admin_campaign_story_edit(story_id):
        denied = _require_admin()
        if denied:
            return denied
        if request.method == 'POST':
            if request.form.get('delete_story'):
                try:
                    with get_db_connection() as conn:
                        cur = conn.cursor()
                        cur.execute('DELETE FROM CampaignStories WHERE id=?', (story_id,))
                        conn.commit()
                    session['admin_status'] = {'type': 'success', 'message': t('admin_story_deleted')}
                except Exception as exc:
                    session['admin_status'] = {'type': 'error', 'message': f'{t("admin_error_prefix")}: {exc}'}
                return redirect(url_for('admin_campaign'))
            headline_en = request.form.get('headline_en', '').strip()
            headline_ru = request.form.get('headline_ru', '').strip()
            if not headline_en and not headline_ru:
                session['admin_status'] = {'type': 'error', 'message': t('admin_story_need_headline')}
                return redirect(url_for('admin_campaign_story_edit', story_id=story_id))
            urls = collect_story_image_urls_from_form()
            if not urls:
                session['admin_status'] = {'type': 'error', 'message': t('admin_story_need_image')}
                return redirect(url_for('admin_campaign_story_edit', story_id=story_id))
            body_en = request.form.get('body_en', '').strip()
            body_ru = request.form.get('body_ru', '').strip()
            credits_en = request.form.get('credits_en', '').strip()
            credits_ru = request.form.get('credits_ru', '').strip()
            try:
                with get_db_connection() as conn:
                    cur = conn.cursor()
                    cur.execute(
                        """
                        UPDATE CampaignStories SET headline_en=?, headline_ru=?, body_en=?, body_ru=?, credits_en=?, credits_ru=?
                        WHERE id=?
                        """,
                        (
                            headline_en or headline_ru,
                            headline_ru or headline_en,
                            body_en,
                            body_ru,
                            credits_en,
                            credits_ru,
                            story_id,
                        ),
                    )
                    cur.execute('DELETE FROM CampaignStoryImages WHERE story_id=?', (story_id,))
                    for i, url in enumerate(urls):
                        cur.execute(
                            'INSERT INTO CampaignStoryImages (story_id, sort_order, image_url) VALUES (?, ?, ?)',
                            (story_id, i, url),
                        )
                    conn.commit()
                session['admin_status'] = {'type': 'success', 'message': t('admin_story_updated')}
            except Exception as exc:
                session['admin_status'] = {'type': 'error', 'message': f'{t("admin_error_prefix")}: {exc}'}
            return redirect(url_for('admin_campaign_story_edit', story_id=story_id))
        story, images = fetch_campaign_story_admin(story_id)
        if not story:
            session['admin_status'] = {'type': 'error', 'message': t('admin_product_not_found')}
            return redirect(url_for('admin_campaign'))
        admin_status = session.pop('admin_status', None)
        return render_template(
            'admin_campaign_story.html',
            story=story,
            images=images,
            admin_status=admin_status,
            active_page='admin',
            cart_count=get_cart_count(),
            t=t,
        )

    @app.route('/admin/users/<int:user_id>/set-admin', methods=['POST'])
    def admin_set_user_admin(user_id):
        denied = _require_admin()
        if denied:
            return denied
        is_admin_raw = str(request.form.get('is_admin') or '').strip().lower()
        make_admin = is_admin_raw in ('1', 'true', 'yes', 'on')
        try:
            current_uid = int(session.get('user_id') or 0)
            if current_uid and current_uid == int(user_id) and not make_admin:
                session['admin_status'] = {'type': 'error', 'message': t('admin_self_demote_forbidden')}
                return redirect(url_for('admin_panel', section='users'))
            set_admin_flag(user_id, make_admin)
            session['admin_status'] = {'type': 'success', 'message': t('admin_rights_updated')}
        except Exception as exc:
            session['admin_status'] = {'type': 'error', 'message': f'{t("admin_error_prefix")}: {exc}'}
        return redirect(url_for('admin_panel', section='users'))

    @app.route('/admin/users/<int:user_id>/level', methods=['POST'])
    def admin_set_user_level(user_id):
        denied = _require_admin()
        if denied:
            return denied
        level_code = (request.form.get('level_code') or '').strip().lower()
        allowed_codes = {str(level.get('code')).lower() for level in loyalty_levels}
        if level_code not in allowed_codes:
            session['admin_status'] = {'type': 'error', 'message': t('admin_user_level_invalid')}
            return redirect(url_for('admin_panel', section='users'))
        try:
            target = None
            for user in list_users_for_admin():
                if int(getattr(user, 'id', user[0]) or 0) == int(user_id):
                    target = user
                    break
            if not target:
                session['admin_status'] = {'type': 'error', 'message': t('admin_user_not_found')}
                return redirect(url_for('admin_panel', section='users'))
            update_user_loyalty(
                user_id,
                level_code,
                int(getattr(target, 'lifetime_orders_count', target[6]) or 0),
                int(getattr(target, 'lifetime_spend_amount', target[7]) or 0),
            )
            if int(session.get('user_id') or 0) == int(user_id):
                session['user_level_code'] = level_code
                session.modified = True
            session['admin_status'] = {'type': 'success', 'message': t('admin_user_level_updated')}
        except Exception as exc:
            session['admin_status'] = {'type': 'error', 'message': f'{t("admin_error_prefix")}: {exc}'}
        return redirect(url_for('admin_panel', section='users'))
