import sqlite3
from datetime import datetime
from database import get_db_connection
from models import User, Stock, Order, Trade, PortfolioItem, AuditLog

class AuditLogService:
    @staticmethod
    def log_action(conn, action, details):
        """
        Logs system events and financial transactions in the audit_logs table.
        """
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "INSERT INTO audit_logs (action, details, timestamp) VALUES (?, ?, ?);",
            (action, details, now_str)
        )

    @staticmethod
    def get_audit_logs(conn, limit=50):
        """
        Fetches the latest audit logs from the database.
        """
        cursor = conn.execute(
            "SELECT id, action, details, timestamp FROM audit_logs ORDER BY id DESC LIMIT ?;",
            (limit,)
        )
        return [dict(row) for row in cursor.fetchall()]


class ValidationService:
    @staticmethod
    def get_user(conn, user_id):
        """Helper to get user data."""
        row = conn.execute("SELECT * FROM users WHERE id = ?;", (user_id,)).fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_stock(conn, symbol):
        """Helper to get stock data."""
        row = conn.execute("SELECT * FROM stocks WHERE symbol = ?;", (symbol,)).fetchone()
        return dict(row) if row else None

    @staticmethod
    def calculate_available_balance(conn, user_id):
        """
        Calculates the available balance for a user after deducting funds locked
        in active PENDING/PARTIALLY_EXECUTED BUY orders.
        """
        # Fetch current absolute balance
        user = conn.execute("SELECT balance FROM users WHERE id = ?;", (user_id,)).fetchone()
        if not user:
            return 0.0
        
        balance = user["balance"]
        
        # Sum of locked balance in active buy orders
        locked_row = conn.execute(
            """
            SELECT SUM(remaining_quantity * price) as locked 
            FROM orders 
            WHERE user_id = ? AND order_type = 'BUY' AND status IN ('PENDING', 'PARTIALLY_EXECUTED');
            """,
            (user_id,)
        ).fetchone()
        
        locked_funds = locked_row["locked"] if locked_row["locked"] is not None else 0.0
        return balance - locked_funds

    @staticmethod
    def calculate_available_shares(conn, user_id, symbol):
        """
        Calculates available shares of a stock in a user's portfolio after deducting
        shares locked in active PENDING/PARTIALLY_EXECUTED SELL orders.
        """
        # Fetch current portfolio quantity
        portfolio_row = conn.execute(
            "SELECT quantity FROM portfolio WHERE user_id = ? AND symbol = ?;",
            (user_id, symbol)
        ).fetchone()
        
        portfolio_shares = portfolio_row["quantity"] if portfolio_row else 0
        
        # Sum of locked shares in active sell orders
        locked_row = conn.execute(
            """
            SELECT SUM(remaining_quantity) as locked 
            FROM orders 
            WHERE user_id = ? AND symbol = ? AND order_type = 'SELL' AND status IN ('PENDING', 'PARTIALLY_EXECUTED');
            """,
            (user_id, symbol)
        ).fetchone()
        
        locked_shares = locked_row["locked"] if locked_row["locked"] is not None else 0
        return portfolio_shares - locked_shares

    @classmethod
    def validate_order(cls, conn, user_id, symbol, order_type, quantity, price):
        """
        Performs thorough validation checks before order insertion.
        Raises ValueError if any check fails.
        """
        # 1. User must exist
        user = cls.get_user(conn, user_id)
        if not user:
            raise ValueError(f"Validation Failed: User with ID {user_id} does not exist.")

        # 2. Stock must exist
        stock = cls.get_stock(conn, symbol)
        if not stock:
            raise ValueError(f"Validation Failed: Stock '{symbol}' does not exist.")

        # 3. Quantity must be greater than 0
        if quantity <= 0:
            raise ValueError("Validation Failed: Quantity must be greater than 0.")

        # 4. Price must be greater than 0
        if price <= 0:
            raise ValueError("Validation Failed: Price must be greater than 0.")

        # 5. Financial validations based on buy/sell type
        if order_type == "BUY":
            req_funds = quantity * price
            avail_balance = cls.calculate_available_balance(conn, user_id)
            if avail_balance < req_funds:
                raise ValueError(
                    f"Validation Failed: Insufficient available balance. "
                    f"Required: ₹{req_funds:,.2f}, Available: ₹{avail_balance:,.2f} "
                    f"(includes funds locked in other active buy orders)."
                )
        elif order_type == "SELL":
            avail_shares = cls.calculate_available_shares(conn, user_id, symbol)
            if avail_shares < quantity:
                raise ValueError(
                    f"Validation Failed: Insufficient shares in portfolio. "
                    f"Required: {quantity} shares of {symbol}, Available: {avail_shares} shares "
                    f"(excludes shares locked in other active sell orders)."
                )
        return True


class PortfolioService:
    @staticmethod
    def get_user_balance(conn, user_id):
        """
        Fetches the user's current account balance.
        """
        row = conn.execute("SELECT balance FROM users WHERE id = ?;", (user_id,)).fetchone()
        return row["balance"] if row else 0.0

    @staticmethod
    def get_user_portfolio(conn, user_id):
        """
        Fetches user portfolio holdings, calculating current market value and P&L.
        """
        query = """
            SELECT 
                p.symbol,
                s.name as stock_name,
                p.quantity,
                p.average_price,
                s.current_price
            FROM portfolio p
            JOIN stocks s ON p.symbol = s.symbol
            WHERE p.user_id = ? AND p.quantity > 0;
        """
        cursor = conn.execute(query, (user_id,))
        portfolio_items = []
        for row in cursor.fetchall():
            qty = row["quantity"]
            avg_price = row["average_price"]
            curr_price = row["current_price"]
            
            total_cost = qty * avg_price
            current_value = qty * curr_price
            pnl = current_value - total_cost
            pnl_pct = (pnl / total_cost * 100) if total_cost > 0 else 0.0
            
            portfolio_items.append({
                "symbol": row["symbol"],
                "name": row["stock_name"],
                "quantity": qty,
                "average_price": avg_price,
                "current_price": curr_price,
                "total_cost": total_cost,
                "current_value": current_value,
                "pnl": pnl,
                "pnl_pct": pnl_pct
            })
        return portfolio_items


class TradeExecutionService:
    @staticmethod
    def execute_trade(conn, buy_order_id, sell_order_id, symbol, quantity, price):
        """
        Executes a trade between matching buy and sell orders.
        This updates buyer & seller portfolios, account balances, order statuses,
        records the trade, and saves audit logs.
        
        MUST run inside a transaction block for data consistency!
        """
        # Fetch matching order details
        buy_order = conn.execute("SELECT * FROM orders WHERE id = ?;", (buy_order_id,)).fetchone()
        sell_order = conn.execute("SELECT * FROM orders WHERE id = ?;", (sell_order_id,)).fetchone()
        
        buyer_id = buy_order["user_id"]
        seller_id = sell_order["user_id"]
        
        buyer_name = conn.execute("SELECT username FROM users WHERE id = ?;", (buyer_id,)).fetchone()["username"]
        seller_name = conn.execute("SELECT username FROM users WHERE id = ?;", (seller_id,)).fetchone()["username"]
        
        trade_amount = quantity * price
        
        # 1. Update buyer's balance (deduct trade amount)
        conn.execute(
            "UPDATE users SET balance = balance - ? WHERE id = ?;",
            (trade_amount, buyer_id)
        )
        
        # 2. Update seller's balance (add trade amount)
        conn.execute(
            "UPDATE users SET balance = balance + ? WHERE id = ?;",
            (trade_amount, seller_id)
        )
        
        # 3. Update seller's portfolio: deduct the executed quantity
        sell_port = conn.execute(
            "SELECT quantity FROM portfolio WHERE user_id = ? AND symbol = ?;",
            (seller_id, symbol)
        ).fetchone()
        
        new_seller_qty = sell_port["quantity"] - quantity
        if new_seller_qty <= 0:
            conn.execute(
                "DELETE FROM portfolio WHERE user_id = ? AND symbol = ?;",
                (seller_id, symbol)
            )
        else:
            conn.execute(
                "UPDATE portfolio SET quantity = ? WHERE user_id = ? AND symbol = ?;",
                (new_seller_qty, seller_id, symbol)
            )

        # 4. Update buyer's portfolio: add quantity, recalculate average cost
        buy_port = conn.execute(
            "SELECT quantity, average_price FROM portfolio WHERE user_id = ? AND symbol = ?;",
            (buyer_id, symbol)
        ).fetchone()
        
        if not buy_port:
            # First time holding this stock
            conn.execute(
                "INSERT INTO portfolio (user_id, symbol, quantity, average_price) VALUES (?, ?, ?, ?);",
                (buyer_id, symbol, quantity, price)
            )
        else:
            old_qty = buy_port["quantity"]
            old_avg = buy_port["average_price"]
            new_buyer_qty = old_qty + quantity
            # Recalculate average price (Weighted Average Cost method)
            new_avg_price = ((old_qty * old_avg) + trade_amount) / new_buyer_qty
            
            conn.execute(
                "UPDATE portfolio SET quantity = ?, average_price = ? WHERE user_id = ? AND symbol = ?;",
                (new_buyer_qty, new_avg_price, buyer_id, symbol)
            )

        # 5. Insert trade record
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO trades (buyer_id, seller_id, buy_order_id, sell_order_id, symbol, quantity, price, executed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (buyer_id, seller_id, buy_order_id, sell_order_id, symbol, quantity, price, now_str)
        )
        trade_id = cursor.lastrowid
        
        # 6. Update orders' remaining quantities and status
        new_buy_rem = buy_order["remaining_quantity"] - quantity
        buy_status = "EXECUTED" if new_buy_rem == 0 else "PARTIALLY_EXECUTED"
        conn.execute(
            "UPDATE orders SET remaining_quantity = ?, status = ? WHERE id = ?;",
            (new_buy_rem, buy_status, buy_order_id)
        )
        
        new_sell_rem = sell_order["remaining_quantity"] - quantity
        sell_status = "EXECUTED" if new_sell_rem == 0 else "PARTIALLY_EXECUTED"
        conn.execute(
            "UPDATE orders SET remaining_quantity = ?, status = ? WHERE id = ?;",
            (new_sell_rem, sell_status, sell_order_id)
        )
        
        # 7. Update stock's current price in stocks table to reflect the last traded price (LTP)
        conn.execute(
            "UPDATE stocks SET current_price = ? WHERE symbol = ?;",
            (price, symbol)
        )
        
        # 8. Log audit entries
        AuditLogService.log_action(
            conn, 
            "TRADE_EXECUTION",
            f"Trade #{trade_id} executed: {quantity} shares of {symbol} at ₹{price:,.2f}. "
            f"Buyer: {buyer_name} (ID {buyer_id}), Seller: {seller_name} (ID {seller_id})."
        )
        AuditLogService.log_action(
            conn,
            "PORTFOLIO_UPDATE",
            f"Buyer {buyer_name} portfolio updated (+{quantity} {symbol}). "
            f"Seller {seller_name} portfolio updated (-{quantity} {symbol})."
        )
        AuditLogService.log_action(
            conn,
            "BALANCE_UPDATE",
            f"Transferred ₹{trade_amount:,.2f} from {buyer_name} (ID {buyer_id}) to {seller_name} (ID {seller_id})."
        )
        
        # Return details for execution confirmation / notification
        return {
            "trade_id": trade_id,
            "buyer_name": buyer_name,
            "seller_name": seller_name,
            "quantity": quantity,
            "price": price,
            "symbol": symbol,
            "amount": trade_amount
        }


class OrderService:
    @staticmethod
    def place_order(user_id, symbol, order_type, quantity, price):
        """
        High-level service API to place an order.
        Validates, inserts, logs, and triggers matching.
        """
        conn = get_db_connection()
        try:
            with conn: # Standard context manager handles transactions automatically (COMMIT on success, ROLLBACK on error)
                # 1. Run validations
                ValidationService.validate_order(conn, user_id, symbol, order_type, quantity, price)
                
                # 2. Insert order
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO orders (user_id, symbol, order_type, quantity, price, status, remaining_quantity)
                    VALUES (?, ?, ?, ?, ?, 'PENDING', ?);
                    """,
                    (user_id, symbol, order_type, quantity, price, quantity)
                )
                order_id = cursor.lastrowid
                
                # 3. Log audit event
                user_name = conn.execute("SELECT username FROM users WHERE id = ?;", (user_id,)).fetchone()["username"]
                AuditLogService.log_action(
                    conn,
                    "ORDER_PLACEMENT",
                    f"User {user_name} (ID {user_id}) placed {order_type} order #{order_id}: "
                    f"{quantity} shares of {symbol} at ₹{price:,.2f} per share."
                )
                
            # 4. Trigger Matching Engine (we run it in a separate transaction loop after placing the order)
            from matching_engine import match_orders_for_stock
            # Open a new connection or pass current one
            with conn:
                matches_count = match_orders_for_stock(conn, symbol)
                
            return order_id, matches_count
            
        except sqlite3.Error as db_err:
            raise RuntimeError(f"Database error during order placement: {str(db_err)}")
        finally:
            conn.close()

    @staticmethod
    def get_order_book(conn):
        """
        Retrieves all active orders (PENDING / PARTIALLY_EXECUTED).
        """
        query = """
            SELECT 
                o.id,
                u.username,
                o.symbol,
                o.order_type,
                o.quantity,
                o.remaining_quantity,
                o.price,
                o.status,
                o.created_at
            FROM orders o
            JOIN users u ON o.user_id = u.id
            WHERE o.status IN ('PENDING', 'PARTIALLY_EXECUTED')
            ORDER BY o.created_at DESC;
        """
        cursor = conn.execute(query)
        return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_trades(conn):
        """
        Retrieves executed trades.
        """
        query = """
            SELECT 
                t.id,
                bu.username as buyer_name,
                su.username as seller_name,
                t.symbol,
                t.quantity,
                t.price,
                (t.quantity * t.price) as trade_value,
                t.executed_at
            FROM trades t
            JOIN users bu ON t.buyer_id = bu.id
            JOIN users su ON t.seller_id = su.id
            ORDER BY t.executed_at DESC;
        """
        cursor = conn.execute(query)
        return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_all_orders(conn):
        """
        Retrieves all orders from the book, regardless of status.
        """
        query = """
            SELECT o.id, u.username AS user, o.user_id, o.symbol, o.order_type AS type,
                   o.quantity, o.remaining_quantity AS remainingQty, o.price, o.status,
                   o.created_at AS createdAt
            FROM orders o
            JOIN users u ON o.user_id = u.id
            ORDER BY o.created_at DESC;
        """
        rows = conn.execute(query).fetchall()
        return [dict(row) for row in rows]


class DashboardService:
    @staticmethod
    def get_dashboard_data(conn):
        total_users = conn.execute('SELECT COUNT(*) FROM users;').fetchone()[0]
        total_orders = conn.execute('SELECT COUNT(*) FROM orders;').fetchone()[0]
        total_trades = conn.execute('SELECT COUNT(*) FROM trades;').fetchone()[0]
        portfolio_value_row = conn.execute(
            'SELECT SUM(p.quantity * s.current_price) AS portfolio_value FROM portfolio p JOIN stocks s ON p.symbol = s.symbol;'
        ).fetchone()
        portfolio_value = portfolio_value_row['portfolio_value'] if portfolio_value_row and portfolio_value_row['portfolio_value'] is not None else 0.0
        return {
            'total_users': total_users,
            'total_orders': total_orders,
            'total_trades': total_trades,
            'portfolio_value': portfolio_value
        }
