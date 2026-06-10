from flask import Blueprint, jsonify
from database import get_db_connection
from services import PortfolioService

portfolio_bp = Blueprint('portfolio', __name__, url_prefix='/api')

@portfolio_bp.route('/portfolio/<int:user_id>', methods=['GET'])
def get_portfolio(user_id):
    conn = get_db_connection()
    user_row = conn.execute('SELECT id, username, balance FROM users WHERE id = ?;', (user_id,)).fetchone()
    if not user_row:
        conn.close()
        return jsonify({'success': False, 'message': 'User not found'}), 404

    holdings = PortfolioService.get_user_portfolio(conn, user_id)
    balance = PortfolioService.get_user_balance(conn, user_id)
    total_value = sum(item['current_value'] for item in holdings)
    net_worth = balance + total_value
    conn.close()

    return jsonify({
        'success': True,
        'user_id': user_id,
        'username': user_row['username'],
        'balance': balance,
        'holdings': holdings,
        'total_value': total_value,
        'net_worth': net_worth
    })
