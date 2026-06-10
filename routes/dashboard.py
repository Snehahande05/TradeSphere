from flask import Blueprint, jsonify
from database import get_db_connection
from services import DashboardService

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api')

@dashboard_bp.route('/dashboard', methods=['GET'])
def get_dashboard():
    conn = get_db_connection()
    data = DashboardService.get_dashboard_data(conn)
    conn.close()
    return jsonify(data)
