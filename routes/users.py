from flask import Blueprint, jsonify, request
from database import get_db_connection

users_bp = Blueprint('users', __name__, url_prefix='/api')

@users_bp.route('/users', methods=['GET'])
def get_users():
    conn = get_db_connection()
    rows = conn.execute('\n        SELECT id, username, email, balance, last_login, trade_alerts, portfolio_updates, theme_preference\n        FROM users\n        ORDER BY id ASC;\n    ').fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

@users_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    conn = get_db_connection()
    row = conn.execute('\n        SELECT id, username, email, balance, last_login, trade_alerts, portfolio_updates, theme_preference\n        FROM users\n        WHERE id = ?;\n    ', (user_id,)).fetchone()
    conn.close()
    if not row:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    return jsonify(dict(row))

@users_bp.route('/profile/<int:user_id>', methods=['GET'])
def get_profile(user_id):
    conn = get_db_connection()
    row = conn.execute('\n        SELECT id, username, email, balance, created_at, last_login,\n               trade_alerts, portfolio_updates, theme_preference\n        FROM users\n        WHERE id = ?;\n    ', (user_id,)).fetchone()
    conn.close()
    if not row:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    return jsonify(dict(row))

@users_bp.route('/profile/<int:user_id>', methods=['PUT'])
def update_profile(user_id):
    data = request.get_json() or {}
    email = (data.get('email') or '').strip()
    trade_alerts = 1 if data.get('trade_alerts', True) else 0
    portfolio_updates = 1 if data.get('portfolio_updates', True) else 0
    theme_preference = data.get('theme_preference', 'dark')

    if theme_preference not in ('dark', 'light'):
        theme_preference = 'dark'

    if not email or '@' not in email:
        return jsonify({'success': False, 'message': 'Please enter a valid email address.'}), 400

    conn = get_db_connection()
    user = conn.execute('SELECT id FROM users WHERE id = ?;', (user_id,)).fetchone()
    if not user:
        conn.close()
        return jsonify({'success': False, 'message': 'User not found'}), 404

    conn.execute('\n        UPDATE users\n        SET email = ?, trade_alerts = ?, portfolio_updates = ?, theme_preference = ?\n        WHERE id = ?;\n    ', (email, trade_alerts, portfolio_updates, theme_preference, user_id))
    conn.execute('INSERT INTO audit_logs (action, details) VALUES (?, ?);',
                 ('PROFILE_UPDATE', f'User ID {user_id} updated profile settings.'))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Profile updated successfully.'})

@users_bp.route('/change-password', methods=['POST'])
def change_password():
    data = request.get_json() or {}
    user_id = data.get('user_id')
    current_password = data.get('current_password') or ''
    new_password = data.get('new_password') or ''
    confirm_password = data.get('confirm_password') or ''

    if not user_id:
        return jsonify({'success': False, 'message': 'User ID is required.'}), 400
    if len(new_password) < 6:
        return jsonify({'success': False, 'message': 'New password must be at least 6 characters long.'}), 400
    if new_password != confirm_password:
        return jsonify({'success': False, 'message': 'New password and confirm password do not match.'}), 400

    conn = get_db_connection()
    user = conn.execute('SELECT id, password FROM users WHERE id = ?;', (user_id,)).fetchone()
    if not user:
        conn.close()
        return jsonify({'success': False, 'message': 'User not found.'}), 404

    saved_password = user['password'] or 'demo123'
    if current_password != saved_password:
        conn.close()
        return jsonify({'success': False, 'message': 'Current password is incorrect.'}), 400

    conn.execute('UPDATE users SET password = ? WHERE id = ?;', (new_password, user_id))
    conn.execute('INSERT INTO audit_logs (action, details) VALUES (?, ?);',
                 ('PASSWORD_CHANGE', f'Password changed for User ID {user_id}.'))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Password changed successfully.'})
