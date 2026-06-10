import sys
import os
import sqlite3

# Import database initialization
from database import initialize_db, get_db_connection
from services import OrderService, PortfolioService, AuditLogService, ValidationService

# Attempt to import tabulate and colorama, with graceful fallbacks
try:
    from tabulate import tabulate
    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False

try:
    import colorama
    from colorama import Fore, Style, Back
    colorama.init(autoreset=True)
    HAS_COLORAMA = True
except ImportError:
    HAS_COLORAMA = False
    # Define dummy colorama objects for fallback
    class DummyColor:
        def __getattr__(self, name):
            return ""
    Fore = DummyColor()
    Style = DummyColor()
    Back = DummyColor()

def format_table(data, headers, tablefmt="fancy_grid"):
    """
    Renders data in tabular format using tabulate, or fallbacks to plain text table.
    """
    if HAS_TABULATE:
        return tabulate(data, headers=headers, tablefmt=tablefmt)
    else:
        # Fallback text-based renderer
        if not data:
            return "No data found."
        col_widths = [len(str(h)) for h in headers]
        for row in data:
            for i, val in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(val)))
        
        separator = "+" + "+".join(["-" * (w + 2) for w in col_widths]) + "+"
        header_row = "|" + "|".join([f" {str(h).ljust(col_widths[i])} " for i, h in enumerate(headers)]) + "|"
        
        lines = [separator, header_row, separator]
        for row in data:
            row_str = "|" + "|".join([f" {str(val).ljust(col_widths[i])} " for i, val in enumerate(row)]) + "|"
            lines.append(row_str)
        lines.append(separator)
        return "\n".join(lines)

def print_banner():
    banner = f"""
{Fore.CYAN}{Style.BRIGHT}================================================================================
  ██████╗██████╗  █████╗ ██████╗ ███████╗███████╗██████╗  ██████╗███████╗
  ╚════██║██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔════╝██╔══██╗██╔════╝██╔════╝
   █████╔╝██████╔╝███████║██║  ██║█████╗  ███████╗██████╔╝██║     █████╗  
  ██╔═══╝ ██╔══██╗██╔══██║██║  ██║██╔══╝  ╚════██║██╔═══╝ ██║     ██╔══╝  
  ███████╗██║  ██║██║  ██║██████╔╝███████╗███████║██║     ╚██████╗███████╗
  ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚══════╝╚══════╝╚═╝      ╚═════╝╚══════╝
                     {Fore.YELLOW}{Style.BRIGHT}TradeSphere: Stock Trading Simulator
{Fore.CYAN}{Style.BRIGHT}================================================================================{Style.RESET_ALL}
    """
    print(banner)

def get_int_input(prompt, min_val=None):
    while True:
        try:
            val = input(prompt).strip()
            if not val:
                print(f"{Fore.RED}Input cannot be empty. Please enter an integer.{Style.RESET_ALL}")
                continue
            num = int(val)
            if min_val is not None and num < min_val:
                print(f"{Fore.RED}Value must be at least {min_val}. Try again.{Style.RESET_ALL}")
                continue
            return num
        except ValueError:
            print(f"{Fore.RED}Invalid input. Please enter a valid integer.{Style.RESET_ALL}")

def get_float_input(prompt, min_val=None):
    while True:
        try:
            val = input(prompt).strip()
            if not val:
                print(f"{Fore.RED}Input cannot be empty. Please enter a number.{Style.RESET_ALL}")
                continue
            num = float(val)
            if min_val is not None and num < min_val:
                print(f"{Fore.RED}Value must be at least {min_val}. Try again.{Style.RESET_ALL}")
                continue
            return num
        except ValueError:
            print(f"{Fore.RED}Invalid input. Please enter a valid decimal number.{Style.RESET_ALL}")

def display_menu():
    print(f"\n{Fore.GREEN}{Style.BRIGHT}--- MAIN MENU ---{Style.RESET_ALL}")
    print("1. View Users")
    print("2. View Stocks")
    print("3. Place Buy Order")
    print("4. Place Sell Order")
    print("5. View Order Book (Active Orders)")
    print("6. View Executed Trades")
    print("7. View User Portfolio & Balance")
    print("8. View System Audit Logs")
    print("9. Exit")
    print("-" * 17)

# --- CLI Action Handlers ---

def handle_view_users(conn):
    print(f"\n{Fore.BLUE}{Style.BRIGHT}=== TradeSphere Users ==={Style.RESET_ALL}")
    cursor = conn.execute("SELECT id, username, balance FROM users ORDER BY id ASC;")
    rows = cursor.fetchall()
    
    table_data = []
    for row in rows:
        user_id = row["id"]
        username = row["username"]
        cash_balance = row["balance"]
        
        # Calculate portfolio current market value
        portfolio = PortfolioService.get_user_portfolio(conn, user_id)
        portfolio_val = sum(item["current_value"] for item in portfolio)
        net_asset_value = cash_balance + portfolio_val
        
        table_data.append([
            user_id,
            username,
            f"₹{cash_balance:,.2f}",
            f"₹{portfolio_val:,.2f}",
            f"₹{net_asset_value:,.2f}"
        ])
        
    headers = ["User ID", "Username", "Cash Balance", "Portfolio Value", "Net Worth (NAV)"]
    print(format_table(table_data, headers))

def handle_view_stocks(conn):
    print(f"\n{Fore.BLUE}{Style.BRIGHT}=== Available Stocks ==={Style.RESET_ALL}")
    cursor = conn.execute("SELECT symbol, name, current_price FROM stocks ORDER BY symbol ASC;")
    rows = cursor.fetchall()
    
    table_data = []
    for row in rows:
        table_data.append([
            row["symbol"],
            row["name"],
            f"₹{row['current_price']:,.2f}"
        ])
        
    headers = ["Symbol", "Company Name", "LTP (Last Traded Price)"]
    print(format_table(table_data, headers))

def handle_place_order(conn, order_type):
    action_str = "BUY" if order_type == "BUY" else "SELL"
    color = Fore.GREEN if order_type == "BUY" else Fore.YELLOW
    
    print(f"\n{color}{Style.BRIGHT}=== Place {action_str} Order ==={Style.RESET_ALL}")
    
    # 1. Print Users for Selection
    cursor_users = conn.execute("SELECT id, username FROM users;")
    users = cursor_users.fetchall()
    print("Available Users:")
    for u in users:
        print(f"  [{u['id']}] {u['username']}")
    
    user_id = get_int_input("Enter User ID: ", min_val=1)
    
    # Check user exists
    user = conn.execute("SELECT username FROM users WHERE id = ?;", (user_id,)).fetchone()
    if not user:
        print(f"{Fore.RED}Error: User with ID {user_id} does not exist.{Style.RESET_ALL}")
        return
    username = user["username"]
    
    # 2. Print Stocks for Selection
    cursor_stocks = conn.execute("SELECT symbol, current_price FROM stocks;")
    stocks = cursor_stocks.fetchall()
    print("\nAvailable Stocks:")
    for s in stocks:
        print(f"  [{s['symbol']}] LTP: ₹{s['current_price']:,.2f}")
        
    symbol = input("Enter Stock Symbol: ").strip().upper()
    
    # Check stock exists
    stock = conn.execute("SELECT symbol FROM stocks WHERE symbol = ?;", (symbol,)).fetchone()
    if not stock:
        print(f"{Fore.RED}Error: Stock '{symbol}' does not exist.{Style.RESET_ALL}")
        return
        
    # Show available balance or holdings before order placement
    if order_type == "BUY":
        avail_bal = ValidationService.calculate_available_balance(conn, user_id)
        print(f"\nUser '{username}' Available Balance: ₹{avail_bal:,.2f}")
    else:
        avail_shares = ValidationService.calculate_available_shares(conn, user_id, symbol)
        print(f"\nUser '{username}' Available '{symbol}' Shares: {avail_shares}")

    # 3. Get Quantity and Price
    quantity = get_int_input("Enter Quantity: ", min_val=1)
    price = get_float_input("Enter Limit Price (₹): ", min_val=0.01)
    
    total_cost = quantity * price
    print(f"\nConfirming: {action_str} {quantity} {symbol} @ ₹{price:,.2f} per share (Total: ₹{total_cost:,.2f})")
    confirm = input("Confirm placement? (y/n): ").strip().lower()
    if confirm != 'y':
        print(f"{Fore.RED}Order placement cancelled.{Style.RESET_ALL}")
        return

    # 4. Place Order
    try:
        order_id, matches_count = OrderService.place_order(user_id, symbol, order_type, quantity, price)
        print(f"\n{Fore.GREEN}✓ Order #{order_id} placed successfully!{Style.RESET_ALL}")
        
        if matches_count > 0:
            print(f"{Fore.CYAN}{Style.BRIGHT}⚡ matching engine executed {matches_count} trade(s) for '{symbol}'!{Style.RESET_ALL}")
            # Show newly executed trades details
            trades = conn.execute(
                """
                SELECT t.id, bu.username as buyer, su.username as seller, t.quantity, t.price 
                FROM trades t
                JOIN users bu ON t.buyer_id = bu.id
                JOIN users su ON t.seller_id = su.id
                WHERE t.buy_order_id = ? OR t.sell_order_id = ?;
                """, (order_id, order_id)
            ).fetchall()
            if trades:
                print(f"{Fore.WHITE}{Style.BRIGHT}Trade Match Details:{Style.RESET_ALL}")
                for t in trades:
                    print(f"  - Trade #{t['id']}: {t['quantity']} shares @ ₹{t['price']:,.2f} between Buyer {t['buyer']} and Seller {t['seller']}")
        else:
            print(f"{Fore.WHITE}No immediate matching counter-order. Order placed in the book.{Style.RESET_ALL}")
            
    except ValueError as val_err:
        print(f"\n{Fore.RED}Validation Error: {str(val_err)}{Style.RESET_ALL}")
    except Exception as err:
        print(f"\n{Fore.RED}Error: {str(err)}{Style.RESET_ALL}")

def handle_view_order_book(conn):
    print(f"\n{Fore.BLUE}{Style.BRIGHT}=== TradeSphere Order Book (Active Orders) ==={Style.RESET_ALL}")
    orders = OrderService.get_order_book(conn)
    
    if not orders:
        print("No active pending orders in the book.")
        return
        
    table_data = []
    for o in orders:
        # Highlight order types
        type_str = f"{Fore.GREEN}BUY{Style.RESET_ALL}" if o["order_type"] == "BUY" else f"{Fore.YELLOW}SELL{Style.RESET_ALL}"
        table_data.append([
            o["id"],
            o["username"],
            o["symbol"],
            type_str,
            o["quantity"],
            o["remaining_quantity"],
            f"₹{o['price']:,.2f}",
            o["status"],
            o["created_at"]
        ])
        
    headers = ["Order ID", "User", "Stock", "Type", "Original Qty", "Remaining Qty", "Limit Price", "Status", "Timestamp"]
    print(format_table(table_data, headers))

def handle_view_trades(conn):
    print(f"\n{Fore.BLUE}{Style.BRIGHT}=== Executed Trades ==={Style.RESET_ALL}")
    trades = OrderService.get_trades(conn)
    
    if not trades:
        print("No trades executed yet in the system.")
        return
        
    table_data = []
    for t in trades:
        table_data.append([
            t["id"],
            t["buyer_name"],
            t["seller_name"],
            t["symbol"],
            t["quantity"],
            f"₹{t['price']:,.2f}",
            f"₹{t['trade_value']:,.2f}",
            t["executed_at"]
        ])
        
    headers = ["Trade ID", "Buyer", "Seller", "Symbol", "Qty", "Price", "Total Value", "Timestamp"]
    print(format_table(table_data, headers))

def handle_view_portfolio(conn):
    print(f"\n{Fore.BLUE}{Style.BRIGHT}=== View User Portfolio holdings ==={Style.RESET_ALL}")
    # Print Users
    cursor_users = conn.execute("SELECT id, username FROM users;")
    users = cursor_users.fetchall()
    for u in users:
        print(f"  [{u['id']}] {u['username']}")
        
    user_id = get_int_input("Enter User ID: ", min_val=1)
    
    # Check user exists
    user = conn.execute("SELECT username FROM users WHERE id = ?;", (user_id,)).fetchone()
    if not user:
        print(f"{Fore.RED}Error: User with ID {user_id} does not exist.{Style.RESET_ALL}")
        return
    username = user["username"]
    
    balance = PortfolioService.get_user_balance(conn, user_id)
    portfolio = PortfolioService.get_user_portfolio(conn, user_id)
    
    print(f"\n{Fore.GREEN}{Style.BRIGHT}--- Account Summary for {username} ---{Style.RESET_ALL}")
    print(f"Available Cash Balance: ₹{balance:,.2f}")
    
    if not portfolio:
        print(f"No stock holdings in portfolio. (Net Worth: ₹{balance:,.2f})")
        return
        
    table_data = []
    total_cost = 0.0
    total_value = 0.0
    
    for item in portfolio:
        total_cost += item["total_cost"]
        total_value += item["current_value"]
        
        # Color profit/loss
        pnl = item["pnl"]
        pnl_pct = item["pnl_pct"]
        if pnl > 0:
            pnl_str = f"{Fore.GREEN}+₹{pnl:,.2f}{Style.RESET_ALL}"
            pnl_pct_str = f"{Fore.GREEN}+{pnl_pct:.2f}%{Style.RESET_ALL}"
        elif pnl < 0:
            pnl_str = f"{Fore.RED}-₹{abs(pnl):,.2f}{Style.RESET_ALL}"
            pnl_pct_str = f"{Fore.RED}{pnl_pct:.2f}%{Style.RESET_ALL}"
        else:
            pnl_str = f"₹{pnl:,.2f}"
            pnl_pct_str = f"{pnl_pct:.2f}%"
            
        table_data.append([
            item["symbol"],
            item["name"],
            item["quantity"],
            f"₹{item['average_price']:,.2f}",
            f"₹{item['current_price']:,.2f}",
            f"₹{item['total_cost']:,.2f}",
            f"₹{item['current_value']:,.2f}",
            pnl_str,
            pnl_pct_str
        ])
        
    headers = ["Stock", "Name", "Qty", "Avg Cost", "Market Price", "Total Cost", "Market Value", "P&L", "P&L %"]
    print(format_table(table_data, headers))
    
    net_pnl = total_value - total_cost
    net_pnl_pct = (net_pnl / total_cost * 100) if total_cost > 0 else 0.0
    net_worth = balance + total_value
    
    if net_pnl > 0:
        net_pnl_str = f"{Fore.GREEN}+₹{net_pnl:,.2f} (+{net_pnl_pct:.2f}%){Style.RESET_ALL}"
    elif net_pnl < 0:
        net_pnl_str = f"{Fore.RED}-₹{abs(net_pnl):,.2f} ({net_pnl_pct:.2f}%){Style.RESET_ALL}"
    else:
        net_pnl_str = f"₹{net_pnl:,.2f} ({net_pnl_pct:.2f}%)"
        
    print(f"\nPortfolio Cost Basis:  ₹{total_cost:,.2f}")
    print(f"Portfolio Market Val:  ₹{total_value:,.2f}")
    print(f"Unrealized P&L:        {net_pnl_str}")
    print(f"Total Net Worth (NAV): {Fore.CYAN}{Style.BRIGHT}₹{net_worth:,.2f}{Style.RESET_ALL}")

def handle_view_audit_logs(conn):
    print(f"\n{Fore.BLUE}{Style.BRIGHT}=== System Audit Logs (Recent 30) ==={Style.RESET_ALL}")
    logs = AuditLogService.get_audit_logs(conn, limit=30)
    
    if not logs:
        print("No audit logs recorded.")
        return
        
    table_data = []
    for log in logs:
        # Highlight action type slightly
        action = log["action"]
        if action == "TRADE_EXECUTION":
            action_styled = f"{Fore.CYAN}{action}{Style.RESET_ALL}"
        elif "ORDER" in action:
            action_styled = f"{Fore.YELLOW}{action}{Style.RESET_ALL}"
        elif "BALANCE" in action or "PORTFOLIO" in action:
            action_styled = f"{Fore.GREEN}{action}{Style.RESET_ALL}"
        else:
            action_styled = action
            
        table_data.append([
            log["id"],
            action_styled,
            log["details"],
            log["timestamp"]
        ])
        
    headers = ["Log ID", "Action", "Description / Details", "Timestamp"]
    print(format_table(table_data, headers))


def main():
    # 1. Initialize SQLite Database (and seed if empty)
    initialize_db()
    
    conn = get_db_connection()
    
    try:
        while True:
            print_banner()
            display_menu()
            choice = input("Enter choice (1-9): ").strip()
            
            if choice == "1":
                handle_view_users(conn)
            elif choice == "2":
                handle_view_stocks(conn)
            elif choice == "3":
                handle_place_order(conn, "BUY")
            elif choice == "4":
                handle_place_order(conn, "SELL")
            elif choice == "5":
                handle_view_order_book(conn)
            elif choice == "6":
                handle_view_trades(conn)
            elif choice == "7":
                handle_view_portfolio(conn)
            elif choice == "8":
                handle_view_audit_logs(conn)
            elif choice == "9":
                print(f"\n{Fore.GREEN}Thank you for using TradeSphere! Exiting...{Style.RESET_ALL}")
                break
            else:
                print(f"{Fore.RED}Invalid choice! Please choose a number between 1 and 9.{Style.RESET_ALL}")
                
            input(f"\n{Fore.WHITE}{Style.DIM}Press Enter to return to main menu...{Style.RESET_ALL}")
            # Clear terminal console for neatness
            os.system('cls' if os.name == 'nt' else 'clear')
            
    except KeyboardInterrupt:
        print(f"\n\n{Fore.GREEN}System interrupted. Exiting TradeSphere...{Style.RESET_ALL}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()
