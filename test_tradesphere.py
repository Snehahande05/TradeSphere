import os
import sqlite3
from database import initialize_db, get_db_connection
from services import OrderService, PortfolioService, AuditLogService
from matching_engine import match_orders_for_stock

def test_flow():
    print("1. Initializing DB...")
    initialize_db()
    
    conn = get_db_connection()
    try:
        # Check seeded users
        users = conn.execute("SELECT * FROM users;").fetchall()
        print(f"   Seeded Users Count: {len(users)}")
        for u in users:
            print(f"   - User ID {u['id']}: {u['username']} (Balance: ₹{u['balance']})")
            
        # Check seeded stocks
        stocks = conn.execute("SELECT * FROM stocks;").fetchall()
        print(f"   Seeded Stocks Count: {len(stocks)}")
        for s in stocks:
            print(f"   - Stock: {s['symbol']} (LTP: ₹{s['current_price']})")
            
        # Check portfolios
        portfolios = conn.execute("SELECT * FROM portfolio;").fetchall()
        print(f"   Seeded Portfolio Rows: {len(portfolios)}")
        
        # Test Case: Match trade between Sneha (ID 1) and Rahul (ID 2)
        # Sneha places a SELL limit order for 5 TCS at ₹3,450
        print("\n2. Placing SELL order: Sneha sells 5 TCS @ ₹3,450...")
        sell_order_id, matches_count = OrderService.place_order(
            user_id=1, symbol="TCS", order_type="SELL", quantity=5, price=3450.0
        )
        print(f"   Sell Order ID: {sell_order_id}, Matches instantly executed: {matches_count}")
        
        # Rahul places a BUY limit order for 5 TCS at ₹3,460
        print("\n3. Placing BUY order: Rahul buys 5 TCS @ ₹3,460...")
        buy_order_id, matches_count = OrderService.place_order(
            user_id=2, symbol="TCS", order_type="BUY", quantity=5, price=3460.0
        )
        print(f"   Buy Order ID: {buy_order_id}, Matches instantly executed: {matches_count}")
        
        # Let's inspect trades
        trades = conn.execute("SELECT * FROM trades;").fetchall()
        print(f"\n4. Checking Executed Trades (Total: {len(trades)}):")
        for t in trades:
            print(f"   - Trade #{t['id']}: {t['quantity']} {t['symbol']} @ ₹{t['price']} (Buyer ID {t['buyer_id']}, Seller ID {t['seller_id']})")
            
        # Let's inspect updated portfolios
        sneha_portfolio = PortfolioService.get_user_portfolio(conn, 1)
        rahul_portfolio = PortfolioService.get_user_portfolio(conn, 2)
        
        print("\n5. Checking Updated Portfolio Holdings:")
        print("   Sneha Portfolio:")
        for item in sneha_portfolio:
            print(f"   - {item['quantity']} shares of {item['symbol']} (Avg Price: ₹{item['average_price']}, Market Price: ₹{item['current_price']})")
            
        print("   Rahul Portfolio:")
        for item in rahul_portfolio:
            print(f"   - {item['quantity']} shares of {item['symbol']} (Avg Price: ₹{item['average_price']}, Market Price: ₹{item['current_price']})")
            
        # Check balances
        sneha_bal = PortfolioService.get_user_balance(conn, 1)
        rahul_bal = PortfolioService.get_user_balance(conn, 2)
        print(f"\n6. Checking Updated Balances:")
        print(f"   - Sneha Cash Balance: ₹{sneha_bal:,.2f} (Should be ₹100,000 + 5 * 3,450 = ₹117,250.00)")
        print(f"   - Rahul Cash Balance: ₹{rahul_bal:,.2f} (Should be ₹100,000 - 5 * 3,450 = ₹82,750.00)")
        
        # Check audit logs
        logs = AuditLogService.get_audit_logs(conn, limit=5)
        print("\n7. Checking Recent Audit Logs:")
        for l in logs:
            print(f"   - [{l['action']}] {l['details']}")
            
        assert len(trades) == 1, "Should have executed 1 trade match!"
        assert sneha_bal == 117250.0, "Sneha balance calculation error!"
        assert rahul_bal == 82750.0, "Rahul balance calculation error!"
        print("\n✓ TradeSphere Test Suite completed successfully! Flow is fully correct and consistent.")
        
    finally:
        conn.close()
        # Clean up database file after test
        if os.path.exists("tradesphere.db"):
            os.remove("tradesphere.db")
            print("\nDatabase file cleaned up.")

if __name__ == "__main__":
    test_flow()
