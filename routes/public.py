import time
from datetime import date, timedelta

from flask import render_template, session, redirect, url_for, request, jsonify, flash


def register_public_routes(app, deps):
    t = deps['t']
    tv = deps['tv']
    tc = deps['tc']
    translations = deps['TRANSLATIONS']
    splash_image = deps['SPLASH_IMAGE']
    collection_listing_data = deps['_collection_listing_data']
    get_cart_count = deps['get_cart_count']
    get_cart_total = deps['get_cart_total']
    get_cart = deps['get_cart']
    get_current_user = deps['get_current_user']
    get_wishlist_ids = deps['get_wishlist_ids']
    filter_products = deps['filter_products']
    find_product = deps['find_product']
    parse_iso_date = deps['_parse_iso_date']
    is_product_available = deps['_is_product_available']
    create_rental_order = deps['_create_rental_order']
    rental_availability_error = deps['RentalAvailabilityError']
    get_brands = deps['get_brands']
    get_campaign_index_data = deps['get_campaign_index_data']
    get_campaign_story_detail = deps['get_campaign_story_detail']
    loyalty_levels = deps['LOYALTY_LEVELS']

    level_discounts = {
        str(level.get('code') or '').strip().lower(): int(level.get('discount_percent') or 0)
        for level in loyalty_levels
    }

    @app.route('/set-lang/<lang>')
    def set_lang(lang):
        if lang in translations:
            session['lang'] = lang
        return redirect(request.referrer or url_for('home'))

    @app.route('/')
    def home():
        kw = collection_listing_data(for_home=True)
        return render_template(
            'collection.html',
            show_hero=True,
            hero_image=url_for('static', filename=splash_image),
            active_page='collection',
            cart_count=get_cart_count(),
            t=t,
            tv=tv,
            **kw,
        )

    @app.route('/collection')
    def collection():
        kw = collection_listing_data(for_home=False)
        return render_template(
            'collection.html',
            show_hero=True,
            hero_image=url_for('static', filename=splash_image),
            active_page='collection',
            cart_count=get_cart_count(),
            t=t,
            tv=tv,
            **kw,
        )

    @app.route('/couture')
    def couture():
        if not get_current_user():
            flash(t('acc_couture_members_only'), 'error')
            return redirect(url_for('account'))
        products = filter_products(category='couture')
        return render_template('couture.html', products=products, active_page='couture', cart_count=get_cart_count(), t=t, tv=tv)

    @app.route('/product/<int:product_id>')
    def product_detail(product_id):
        product = find_product(product_id)
        if not product:
            return 'Not found', 404
        if product.get('category') == 'couture' and not get_current_user():
            flash(t('acc_couture_members_only'), 'error')
            return redirect(url_for('account'))
        days = int(request.args.get('days', 1))
        days = min(max(days, 1), product['max_days'])
        selected_start = parse_iso_date(request.args.get('start_date')) or date.today()
        selected_end = selected_start + timedelta(days=days)
        total = product['price'] * days
        available = is_product_available(product['id'], selected_start, selected_end)
        return render_template(
            'product.html',
            product=product,
            selected_days=days,
            selected_start_date=selected_start.isoformat(),
            selected_end_date=selected_end.isoformat(),
            selected_available=available,
            total_price=total,
            active_page='product',
            cart_count=get_cart_count(),
            t=t,
            tv=tv,
        )

    @app.route('/wishlist/toggle', methods=['POST'])
    def wishlist_toggle():
        if not request.is_json:
            return jsonify(ok=False, error='json'), 400
        payload = request.get_json(silent=True) or {}
        try:
            product_id = int(payload.get('product_id'))
        except (TypeError, ValueError):
            return jsonify(ok=False, error='bad_id'), 400
        if not find_product(product_id):
            return jsonify(ok=False, error='not_found'), 404
        ids = list(get_wishlist_ids())
        if product_id in ids:
            ids = [i for i in ids if i != product_id]
            in_wish = False
        else:
            ids.append(product_id)
            in_wish = True
        session['wishlist'] = ids
        session.modified = True
        return jsonify(ok=True, in_wishlist=in_wish, count=len(ids))

    @app.route('/wishlist')
    def wishlist_page():
        ids = get_wishlist_ids()
        products = []
        for pid in ids:
            p = find_product(pid)
            if p:
                products.append(p)
        return render_template(
            'wishlist.html',
            products=products,
            active_page='wishlist',
            cart_count=get_cart_count(),
            t=t,
            tv=tv,
        )

    def _cart_add_wants_json():
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return True
        return request.accept_mimetypes.best_match(['application/json', 'text/html']) == 'application/json'

    @app.route('/cart/add', methods=['POST'])
    def add_to_cart():
        product_id = int(request.form.get('product_id'))
        days = int(request.form.get('days', 1))
        size = request.form.get('size', '')
        start_date = parse_iso_date(request.form.get('start_date')) or date.today()
        product = find_product(product_id)
        if not product:
            if _cart_add_wants_json():
                return jsonify(ok=False, error='not_found'), 404
            return redirect(url_for('home'))
        if product.get('category') == 'couture' and not get_current_user():
            if _cart_add_wants_json():
                return jsonify(ok=False, error='login_required'), 403
            flash(t('acc_couture_cart_login'), 'error')
            return redirect(url_for('account'))
        days = min(max(days, 1), product['max_days'])
        end_date = start_date + timedelta(days=days)
        if not is_product_available(product['id'], start_date, end_date):
            if _cart_add_wants_json():
                return jsonify(ok=False, error='unavailable'), 409
            flash(t('product_unavailable_for_dates'), 'error')
            return redirect(url_for('product_detail', product_id=product_id, days=days, start_date=start_date.isoformat()))
        cart = get_cart()
        cart.append({
            'cart_id': int(time.time() * 1000),
            'product_id': product['id'],
            'serial': product['serial'],
            'brand': product['brand'],
            'name': product['name'],
            'price_per_day': product['price'],
            'days': days,
            'size': size,
            'total_price': product['price'] * days,
            'image': product['image'],
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
        })
        session['cart'] = cart
        if _cart_add_wants_json():
            return jsonify(ok=True, cart_count=len(cart), product_name=product['name'])
        flash(product['name'], 'cart_added')
        return redirect(url_for('product_detail', product_id=product_id, days=days, start_date=start_date.isoformat()))

    @app.route('/cart/remove/<int:cart_id>')
    def remove_from_cart(cart_id):
        cart = [i for i in get_cart() if i['cart_id'] != cart_id]
        session['cart'] = cart
        return redirect(url_for('cart'))

    @app.route('/cart')
    def cart():
        user = get_current_user()
        level_code = (user or {}).get('level_code', 'bronze')
        discount_percent = int(level_discounts.get((level_code or 'bronze').strip().lower(), 0))
        subtotal = int(get_cart_total() or 0)
        discount_amount = int(round(subtotal * discount_percent / 100.0))
        total = max(0, subtotal - discount_amount)
        return render_template(
            'cart.html',
            cart_items=get_cart(),
            subtotal=subtotal,
            discount_percent=discount_percent,
            discount_amount=discount_amount,
            total=total,
            active_page='cart',
            cart_count=get_cart_count(),
            t=t,
        )

    @app.route('/cart/clear')
    def clear_cart():
        session['cart'] = []
        return redirect(url_for('cart'))

    @app.route('/cart/checkout', methods=['POST'])
    def cart_checkout():
        user = get_current_user()
        if not user:
            flash(t('acc_checkout_login_required'), 'error')
            return redirect(url_for('account'))
        cart_items = get_cart()
        if not cart_items:
            flash(t('acc_checkout_empty'), 'error')
            return redirect(url_for('cart'))
        level_code = (user or {}).get('level_code', 'bronze')
        discount_percent = int(level_discounts.get((level_code or 'bronze').strip().lower(), 0))
        try:
            order_id = create_rental_order(user['id'], cart_items, discount_percent=discount_percent)
        except rental_availability_error:
            flash(t('acc_checkout_unavailable'), 'error')
            return redirect(url_for('cart'))
        except Exception:
            order_id = None
        if not order_id:
            flash(t('acc_checkout_failed'), 'error')
            return redirect(url_for('cart'))
        session['cart'] = []
        session.modified = True
        flash(t('acc_checkout_success'), 'success')
        return redirect(url_for('account'))

    @app.route('/search')
    def search():
        q = request.args.get('q', '').strip()
        if not q:
            results = []
        else:
            results = filter_products(
                category=None,
                query=q,
                brand=None,
                min_condition=0,
                max_price=None,
                sort='id',
            )
        return render_template(
            'search.html',
            brands=get_brands(),
            results=results,
            query=q,
            active_page='search',
            cart_count=get_cart_count(),
            t=t,
            tv=tv,
        )

    @app.route('/campaign')
    def campaign():
        data = get_campaign_index_data()
        return render_template(
            'campaign.html',
            stories=data['stories'],
            campaign_intro=data['campaign_intro'],
            campaign_tagline=data['campaign_tagline'],
            active_page='campaign',
            cart_count=get_cart_count(),
            t=t,
            tc=tc,
        )

    @app.route('/campaign/story/<int:story_id>')
    def campaign_story(story_id):
        story = get_campaign_story_detail(story_id)
        if not story:
            return 'Not found', 404
        return render_template(
            'campaign_story.html',
            story=story,
            active_page='campaign',
            cart_count=get_cart_count(),
            t=t,
        )

    @app.route('/about')
    def about():
        return render_template('about.html', active_page='about', cart_count=get_cart_count(), t=t)
