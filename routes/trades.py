from flask import Blueprint, jsonify
from database import get_db_connection

trades_bp = Blueprint('trades', __name__, url_prefix='/api')

@trades_bp.route('/trades', methods=['GET'])
def get_trades():
    conn = get_db_connection()
    query = '''
        SELECT t.id, bu.username AS buyerName, su.username AS sellerName,
               t.symbol, t.quantity, t.price, (t.quantity * t.price) AS tradeValue,
               t.executed_at AS executedAt
        FROM trades t
        JOIN users bu ON t.buyer_id = bu.id
        JOIN users su ON t.seller_id = su.id
        ORDER BY t.executed_at DESC;
    '''
    rows = conn.execute(query).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])
