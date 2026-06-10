from flask import Blueprint, request, jsonify
from database import get_db_connection
from services import OrderService

orders_bp = Blueprint('orders', __name__, url_prefix='/api')

@orders_bp.route('/orders', methods=['GET'])
def get_orders():
    conn = get_db_connection()
    query = '''
        SELECT o.id, u.username AS user, o.user_id, o.symbol, o.order_type AS type,
               o.quantity, o.remaining_quantity AS remainingQty, o.price, o.status,
               o.created_at AS createdAt
        FROM orders o
        JOIN users u ON o.user_id = u.id
        ORDER BY o.created_at DESC;
    '''
    rows = conn.execute(query).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

@orders_bp.route('/orders', methods=['POST'])
def create_order():
    if not request.is_json:
        return jsonify({'success': False, 'message': 'Request body must be JSON.'}), 400

    data = request.get_json()
    try:
        user_id = int(data.get('user_id'))
        symbol = str(data.get('symbol', '')).strip().upper()
        order_type = str(data.get('order_type', '')).strip().upper()
        quantity = int(data.get('quantity'))
        price = float(data.get('price'))
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Invalid request fields. user_id, quantity, and price must be numeric.'}), 400

    if not symbol or order_type not in ('BUY', 'SELL'):
        return jsonify({'success': False, 'message': 'Invalid symbol or order_type. Use BUY or SELL.'}), 400

    try:
        order_id, matches_count = OrderService.place_order(user_id, symbol, order_type, quantity, price)
        return jsonify({
            'success': True,
            'message': 'Order placed successfully.',
            'order_id': order_id,
            'matches_executed': matches_count
        }), 201
    except ValueError as validation_error:
        return jsonify({'success': False, 'message': str(validation_error)}), 400
    except Exception as err:
        return jsonify({'success': False, 'message': str(err)}), 500
