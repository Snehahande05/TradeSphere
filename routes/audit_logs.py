from flask import Blueprint, jsonify
from database import get_db_connection
from services import AuditLogService

audit_logs_bp = Blueprint('audit_logs', __name__, url_prefix='/api')

@audit_logs_bp.route('/audit-logs', methods=['GET'])
def get_audit_logs():
    conn = get_db_connection()
    logs = AuditLogService.get_audit_logs(conn, limit=100)
    conn.close()
    return jsonify(logs)
