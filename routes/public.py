import time
from datetime import date, timedelta

from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify, flash


def register_public_routes(app, deps):
    bp = Blueprint('public', __name__)

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
    find_products_by_ids = deps['find_products_by_ids']
    get_related_products = deps['get_related_products']
    parse_iso_date = deps['_parse_iso_date']
    is_product_available = deps['_is_product_available']
    create_rental_order = deps['_create_rental_order']
    rental_availability_error = deps['RentalAvailabilityError']
    get_brands = deps['get_brands']
    get_campaign_index_data = deps['get_campaign_index_data']
    get_campaign_story_detail = deps['get_campaign_story_detail']
    CoutureAccessError = deps['CoutureAccessError']
    cart_totals_for_level = deps['cart_totals_for_level']
    can_rent_product = deps['can_rent_product']
    couture_gate_message_key = deps['couture_gate_message_key']
    format_couture_message = deps['format_couture_message']

    @bp.route('/set-lang/<lang>')
    def set_lang(lang):
        if lang in translations:
            session['lang'] = lang
        return redirect(request.referrer or url_for('home'))

    @bp.route('/')
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

    @bp.route('/collection')
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

    @bp.route('/couture')
    def couture():
        if not get_current_user():
            flash(t('acc_couture_members_only'), 'error')
            return redirect(url_for('account'))
        products = filter_products(category='couture')
        return render_template('couture.html', products=products, active_page='couture', cart_count=get_cart_count(), t=t, tv=tv)

    @bp.route('/product/<int:product_id>')
    def product_detail(product_id):
        product = find_product(product_id)
        if not product:
            return 'Not found', 404
        if str(product.get('category') or '').strip().lower() == 'couture' and not get_current_user():
            flash(t('acc_couture_members_only'), 'error')
            return redirect(url_for('account'))
        user = get_current_user()
        can_rent = can_rent_product(user, product)
        couture_rent_notice = ''
        if not can_rent:
            key = couture_gate_message_key(user, surface='product')
            couture_rent_notice = format_couture_message(t, key)
        days = int(request.args.get('days', 1))
        days = min(max(days, 1), product['max_days'])
        selected_start = parse_iso_date(request.args.get('start_date')) or date.today()
        selected_end = selected_start + timedelta(days=days)
        total = product['price'] * days
        available = is_product_available(product['id'], selected_start, selected_end)
        related_products = get_related_products(product, limit=4)
        return render_template(
            'product.html',
            product=product,
            selected_days=days,
            selected_start_date=selected_start.isoformat(),
            selected_end_date=selected_end.isoformat(),
            selected_available=available,
            total_price=total,
            can_rent_product=can_rent,
            couture_rent_notice=couture_rent_notice,
            related_products=related_products,
            active_page='product',
            cart_count=get_cart_count(),
            t=t,
            tv=tv,
        )

    @bp.route('/wishlist/toggle', methods=['POST'])
    def wishlist_toggle():
        if not request.is_json:
            return jsonify(ok=False, error='json'), 400
        payload = request.get_json(silent=True) or {}
        try:
            product_id = int(payload.get('product_id'))
        except (TypeError, ValueError):
            return jsonify(ok=False, error='bad_id'), 400
        product = find_product(product_id)
        if not product:
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

    @bp.route('/wishlist')
    def wishlist_page():
        ids = get_wishlist_ids()
        by_id = find_products_by_ids(ids)
        products = [by_id[i] for i in ids if i in by_id]
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

    @bp.route('/cart/add', methods=['POST'])
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
        user = get_current_user()
        if not can_rent_product(user, product):
            if _cart_add_wants_json():
                error = 'login_required' if not user else 'loyalty_required'
                return jsonify(ok=False, error=error), 403
            key = couture_gate_message_key(user, surface='cart')
            flash(format_couture_message(t, key), 'error')
            if not user:
                return redirect(url_for('account'))
            return redirect(url_for('product_detail', product_id=product_id))
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

    @bp.route('/cart/remove/<int:cart_id>')
    def remove_from_cart(cart_id):
        cart = [i for i in get_cart() if i['cart_id'] != cart_id]
        session['cart'] = cart
        return redirect(url_for('cart'))

    @bp.route('/cart')
    def cart():
        user = get_current_user()
        level_code = (user or {}).get('level_code', 'bronze')
        totals = cart_totals_for_level(get_cart_total(), level_code)
        return render_template(
            'cart.html',
            cart_items=get_cart(),
            subtotal=totals['subtotal'],
            discount_percent=totals['discount_percent'],
            discount_amount=totals['discount_amount'],
            total=totals['total'],
            active_page='cart',
            cart_count=get_cart_count(),
            t=t,
        )

    @bp.route('/cart/clear')
    def clear_cart():
        session['cart'] = []
        return redirect(url_for('cart'))

    @bp.route('/cart/checkout', methods=['POST'])
    def cart_checkout():
        user = get_current_user()
        if not user:
            flash(t('acc_checkout_login_required'), 'error')
            return redirect(url_for('account'))
        cart_items = get_cart()
        if not cart_items:
            flash(t('acc_checkout_empty'), 'error')
            return redirect(url_for('cart'))
        if request.form.get('accept_terms') != '1':
            flash(t('cart_terms_required'), 'error')
            return redirect(url_for('cart'))
        level_code = (user or {}).get('level_code', 'bronze')
        totals = cart_totals_for_level(get_cart_total(), level_code)
        try:
            order_id = create_rental_order(user['id'], cart_items, discount_percent=totals['discount_percent'])
        except rental_availability_error:
            flash(t('acc_checkout_unavailable'), 'error')
            return redirect(url_for('cart'))
        except CoutureAccessError:
            key = couture_gate_message_key(user, surface='checkout')
            flash(format_couture_message(t, key), 'error')
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

    @bp.route('/search')
    def search():
        q = request.args.get('q', '').strip()
        category = (request.args.get('category') or '').strip().lower()
        if category not in ('rtw', 'couture'):
            category = ''
        brand = (request.args.get('brand') or '').strip()
        item_category = (request.args.get('item_category') or '').strip()
        sort = (request.args.get('sort') or 'id').strip().lower()
        if sort not in ('id', 'price_asc', 'price_desc'):
            sort = 'id'
        max_price_raw = (request.args.get('max_price') or '').strip()
        max_price = None
        if max_price_raw.isdigit():
            max_price = int(max_price_raw)
        search_started = bool(q or category or brand or item_category or max_price is not None or sort != 'id')
        user = get_current_user()
        if category == 'couture' and not user:
            flash(t('acc_couture_members_only'), 'error')
            return redirect(url_for('account'))
        if not search_started:
            results = []
        else:
            results = filter_products(
                category=category or None,
                query=q or None,
                brand=brand or None,
                item_category=item_category or None,
                min_condition=0,
                max_price=max_price,
                sort=sort,
            )
        if not user:
            results = [p for p in results if str(p.get('category') or '').strip().lower() != 'couture']
        return render_template(
            'search.html',
            brands=get_brands(),
            results=results,
            query=q,
            active_category=category,
            active_brand=brand,
            active_item_category=item_category,
            active_sort=sort,
            max_price_value=max_price_raw if max_price_raw.isdigit() else '',
            search_started=search_started,
            active_page='search',
            cart_count=get_cart_count(),
            t=t,
            tv=tv,
        )

    @bp.route('/campaign')
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

    @bp.route('/campaign/story/<int:story_id>')
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

    @bp.route('/about')
    def about():
        return render_template('about.html', active_page='about', cart_count=get_cart_count(), t=t)

    app.register_blueprint(bp)
