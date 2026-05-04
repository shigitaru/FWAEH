from datetime import date, timedelta

from flask import Blueprint, request, jsonify


def register_api_routes(app, deps):
    bp = Blueprint('api', __name__)

    parse_iso_date = deps['_parse_iso_date']
    find_product = deps['find_product']
    filter_products = deps['filter_products']
    get_brands = deps['get_brands']
    is_product_available = deps['_is_product_available']
    get_product_occupied_periods = deps['get_product_occupied_periods']
    get_current_user = deps['get_current_user']
    is_couture_product = deps['is_couture_product']

    def _next_available_period(product_id, requested_start, days, *, search_days=60):
        for offset in range(1, search_days + 1):
            candidate_start = requested_start + timedelta(days=offset)
            candidate_end = candidate_start + timedelta(days=days)
            if is_product_available(product_id, candidate_start, candidate_end):
                return candidate_start, candidate_end
        return None, None

    @bp.route('/api/calculate', methods=['POST'])
    def api_calculate():
        data = request.get_json()
        price = int(data.get('price', 0))
        days = int(data.get('days', 1))
        max_days = int(data.get('max_days', 30))
        days = min(max(days, 1), max_days)
        return jsonify({'total': price * days, 'days': days})

    @bp.route('/api/product/<int:product_id>/availability', methods=['POST'])
    def api_product_availability(product_id):
        data = request.get_json(silent=True) or {}
        requested_start = parse_iso_date(data.get('start_date')) or date.today()
        days = int(data.get('days', 1) or 1)
        product = find_product(product_id)
        if not product:
            return jsonify({'ok': False, 'error': 'not_found'}), 404
        if is_couture_product(product) and not get_current_user():
            return jsonify({'ok': False, 'error': 'login_required'}), 403
        days = min(max(days, 1), int(product.get('max_days', 1) or 1))
        requested_end = requested_start + timedelta(days=days)
        available = is_product_available(product_id, requested_start, requested_end)
        next_start = next_end = None
        if not available:
            next_start, next_end = _next_available_period(product_id, requested_start, days)
        return jsonify(
            {
                'ok': True,
                'available': bool(available),
                'start_date': requested_start.isoformat(),
                'end_date': requested_end.isoformat(),
                'days': days,
                'next_available': (
                    {
                        'start_date': next_start.isoformat(),
                        'end_date': next_end.isoformat(),
                    }
                    if next_start and next_end else None
                ),
            }
        )

    @bp.route('/api/product/<int:product_id>/occupancy', methods=['GET'])
    def api_product_occupancy(product_id):
        product = find_product(product_id)
        if not product:
            return jsonify({'ok': False, 'error': 'not_found'}), 404
        if is_couture_product(product) and not get_current_user():
            return jsonify({'ok': False, 'error': 'login_required'}), 403
        return jsonify(
            {
                'ok': True,
                'periods': get_product_occupied_periods(product_id, days_ahead=60),
            }
        )

    @bp.route('/api/search-suggestions', methods=['GET'])
    def api_search_suggestions():
        q = (request.args.get('q') or '').strip()
        if len(q) < 2:
            return jsonify({'ok': True, 'suggestions': []})
        ql = q.lower()
        suggestions = []
        seen = set()
        for brand in get_brands():
            name = brand.get('name') or ''
            if ql in name.lower():
                key = ('brand', name.lower())
                if key not in seen:
                    seen.add(key)
                    suggestions.append({'type': 'brand', 'label': name, 'url': f'/search?brand={brand.get("slug")}'})
            if len(suggestions) >= 3:
                break
        try:
            products = filter_products(query=q, sort='id')[:5]
        except Exception:
            products = []
        if not get_current_user():
            products = [p for p in products if not is_couture_product(p)]
        for product in products:
            key = ('product', int(product.get('id') or 0))
            if key in seen:
                continue
            seen.add(key)
            suggestions.append(
                {
                    'type': 'product',
                    'label': product.get('name') or '',
                    'meta': product.get('brand') or '',
                    'url': f'/product/{int(product.get("id") or 0)}',
                }
            )
            if len(suggestions) >= 6:
                break
        return jsonify({'ok': True, 'suggestions': suggestions})

    app.register_blueprint(bp)
