import os
from flask import Flask, render_template
from routes.users import users_bp
from routes.stocks import stocks_bp
from routes.orders import orders_bp
from routes.trades import trades_bp
from routes.portfolio import portfolio_bp
from routes.audit_logs import audit_logs_bp
from routes.dashboard import dashboard_bp
from database import initialize_db


def create_app():
    # Ensure SQLite tables and seed data exist before APIs are used.
    initialize_db()

    app = Flask(__name__, static_folder='static', template_folder='templates')

    # Register API blueprints
    app.register_blueprint(users_bp)
    app.register_blueprint(stocks_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(trades_bp)
    app.register_blueprint(portfolio_bp)
    app.register_blueprint(audit_logs_bp)
    app.register_blueprint(dashboard_bp)

    @app.route('/')
    def index():
        return render_template('index.html')

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
