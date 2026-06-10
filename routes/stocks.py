from flask import Blueprint, jsonify
from database import get_db_connection

stocks_bp = Blueprint('stocks', __name__, url_prefix='/api')

@stocks_bp.route('/stocks', methods=['GET'])
def get_stocks():
    conn = get_db_connection()
    rows = conn.execute('SELECT symbol, name, current_price AS currentPrice FROM stocks ORDER BY symbol ASC;').fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])
