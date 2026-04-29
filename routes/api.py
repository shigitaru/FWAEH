from datetime import date, timedelta

from flask import request, jsonify


def register_api_routes(app, deps):
    parse_iso_date = deps['_parse_iso_date']
    find_product = deps['find_product']
    is_product_available = deps['_is_product_available']

    @app.route('/api/calculate', methods=['POST'])
    def api_calculate():
        data = request.get_json()
        price = int(data.get('price', 0))
        days = int(data.get('days', 1))
        max_days = int(data.get('max_days', 30))
        days = min(max(days, 1), max_days)
        return jsonify({'total': price * days, 'days': days})

    @app.route('/api/product/<int:product_id>/availability', methods=['POST'])
    def api_product_availability(product_id):
        data = request.get_json(silent=True) or {}
        requested_start = parse_iso_date(data.get('start_date')) or date.today()
        days = int(data.get('days', 1) or 1)
        product = find_product(product_id)
        if not product:
            return jsonify({'ok': False, 'error': 'not_found'}), 404
        days = min(max(days, 1), int(product.get('max_days', 1) or 1))
        requested_end = requested_start + timedelta(days=days)
        available = is_product_available(product_id, requested_start, requested_end)
        return jsonify(
            {
                'ok': True,
                'available': bool(available),
                'start_date': requested_start.isoformat(),
                'end_date': requested_end.isoformat(),
                'days': days,
            }
        )
