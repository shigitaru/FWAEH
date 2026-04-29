from flask import request, session, redirect, url_for, render_template


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

    @app.route('/admin', methods=['GET', 'POST'])
    def admin_panel():
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
                if uploaded_main:
                    main_image = uploaded_main
                if not all([serial, brand_name, name, max_days_raw, condition_score_raw]):
                    session['admin_status'] = {'type': 'error', 'message': t('admin_required_fields')}
                    return redirect(url_for('admin_panel'))
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
                    return redirect(url_for('admin_panel'))
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
                            OUTPUT INSERTED.id
                            VALUES (?, ?, ?)
                            ''',
                            (brand_name, brand_name, '')
                        )
                        out_row = cur.fetchone()
                        brand_id = int(out_row[0]) if out_row and out_row[0] is not None else None
                    if not brand_id:
                        raise ValueError(t('admin_brand_resolve_error'))
                    cur.execute(
                        '''
                        INSERT INTO Products (brand_id, category, item_category, serial, name, price, max_days, condition_score, material, origin, [condition], main_image)
                        OUTPUT INSERTED.id
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    conn.commit()
                session['admin_status'] = {'type': 'success', 'message': t('admin_product_created')}
            except Exception as exc:
                session['admin_status'] = {'type': 'error', 'message': f'{t("admin_error_prefix")}: {exc}'}
            return redirect(url_for('admin_panel'))
        products = filter_products()
        orders_recent = fetch_recent_orders_admin()
        admin_status = session.pop('admin_status', None)
        return render_template(
            'admin.html',
            products=products,
            orders_recent=orders_recent,
            order_status_flow=order_status_flow,
            brands=get_brands(),
            brands_admin=get_admin_brands(),
            admin_status=admin_status,
            active_page='admin',
            cart_count=get_cart_count(),
            t=t,
            tv=tv
        )

    @app.route('/admin/order/<int:order_id>/status', methods=['POST'])
    def admin_update_order_status(order_id):
        next_status = (request.form.get('status') or '').strip().lower()
        if next_status not in order_status_flow:
            session['admin_status'] = {'type': 'error', 'message': t('admin_order_status_invalid')}
            return redirect(url_for('admin_panel'))
        try:
            ensure_rental_orders_tables()
            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute('SELECT id FROM RentalOrders WHERE id = ?', (order_id,))
                if not cur.fetchone():
                    session['admin_status'] = {'type': 'error', 'message': t('admin_order_not_found')}
                    return redirect(url_for('admin_panel'))
                cur.execute('UPDATE RentalOrders SET status = ? WHERE id = ?', (next_status, order_id))
                conn.commit()
            session['admin_status'] = {'type': 'success', 'message': t('admin_order_status_updated')}
        except Exception as exc:
            session['admin_status'] = {'type': 'error', 'message': f'{t("admin_error_prefix")}: {exc}'}
        return redirect(url_for('admin_panel'))

    @app.route('/admin/product/<int:product_id>/delete', methods=['POST'])
    def admin_delete_product(product_id):
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute('SELECT id FROM Products WHERE id = ?', (product_id,))
                if not cur.fetchone():
                    session['admin_status'] = {'type': 'error', 'message': t('admin_product_not_found')}
                    return redirect(url_for('admin_panel'))
                cur.execute('DELETE FROM Products WHERE id = ?', (product_id,))
                conn.commit()
            session['admin_status'] = {'type': 'success', 'message': t('admin_product_deleted')}
        except Exception as exc:
            session['admin_status'] = {'type': 'error', 'message': f'{t("admin_error_prefix")}: {exc}'}
        return redirect(url_for('admin_panel'))

    @app.route('/admin/brand/<int:brand_id>/delete', methods=['POST'])
    def admin_delete_brand(brand_id):
        try:
            with get_db_connection() as conn:
                cur = conn.cursor()
                cur.execute('SELECT id FROM Brands WHERE id = ?', (brand_id,))
                if not cur.fetchone():
                    session['admin_status'] = {'type': 'error', 'message': t('admin_brand_not_found')}
                    return redirect(url_for('admin_panel'))
                cur.execute('SELECT COUNT(*) FROM Products WHERE brand_id = ?', (brand_id,))
                linked_products = int(cur.fetchone()[0] or 0)
                if linked_products > 0:
                    session['admin_status'] = {'type': 'error', 'message': t('admin_brand_has_products')}
                    return redirect(url_for('admin_panel'))
                cur.execute('DELETE FROM Brands WHERE id = ?', (brand_id,))
                conn.commit()
            session['admin_status'] = {'type': 'success', 'message': t('admin_brand_deleted')}
        except Exception as exc:
            session['admin_status'] = {'type': 'error', 'message': f'{t("admin_error_prefix")}: {exc}'}
        return redirect(url_for('admin_panel'))

    @app.route('/admin/product/<int:product_id>/edit', methods=['GET', 'POST'])
    def admin_edit_product(product_id):
        product = find_product(product_id)
        if not product:
            session['admin_status'] = {'type': 'error', 'message': t('admin_product_not_found')}
            return redirect(url_for('admin_panel'))

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
                            OUTPUT INSERTED.id
                            VALUES (?, ?, ?)
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
                        condition_score=?, material=?, origin=?, [condition]=?, main_image=?
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
                    conn.commit()
                session['admin_status'] = {'type': 'success', 'message': t('admin_product_updated')}
            except Exception as exc:
                err = str(exc).lower()
                if 'unique' in err or '23000' in err or '2627' in err:
                    session['admin_status'] = {'type': 'error', 'message': t('admin_serial_exists')}
                else:
                    session['admin_status'] = {'type': 'error', 'message': f'{t("admin_error_prefix")}: {exc}'}
                return redirect(url_for('admin_edit_product', product_id=product_id))
            return redirect(url_for('admin_panel'))

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
        if request.method == 'POST':
            intro_en = request.form.get('intro_en', '').strip()
            intro_ru = request.form.get('intro_ru', '').strip()
            tagline_en = request.form.get('tagline_en', '').strip()
            tagline_ru = request.form.get('tagline_ru', '').strip()
            try:
                with get_db_connection() as conn:
                    cur = conn.cursor()
                    cur.execute('SELECT COUNT(*) FROM CampaignSettings WHERE id=1')
                    if cur.fetchone()[0]:
                        cur.execute(
                            'UPDATE CampaignSettings SET intro_en=?, intro_ru=?, tagline_en=?, tagline_ru=? WHERE id=1',
                            (intro_en, intro_ru, tagline_en, tagline_ru),
                        )
                    else:
                        cur.execute(
                            'INSERT INTO CampaignSettings (id, intro_en, intro_ru, tagline_en, tagline_ru) VALUES (1, ?, ?, ?, ?)',
                            (intro_en, intro_ru, tagline_en, tagline_ru),
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
