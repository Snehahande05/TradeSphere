import sqlite3
import os
from datetime import datetime

# Database File Path
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database", "tradesphere.db")

def get_db_connection():
    """
    Establishes and returns a connection to the SQLite database.
    Enforces foreign key constraints and sets Row factory for dictionary-like access.
    
    SYSTEM DESIGN VIVA COMMENT:
    Why SQLite is used:
    1. Simplicity & Serverless: No separate database server installation is needed (e.g., PostgreSQL/MySQL),
       making it extremely portable and easy to demonstrate during viva.
    2. ACID Compliance: SQLite supports full transactions (Atomic, Consistent, Isolated, Durable),
       which is critical for financial applications to prevent balance mismatch and race conditions.
    3. File-Based: All data is saved in a local file ("tradesphere.db"), making debugging and inspection direct.
    4. Row-level read access, table-level write locking: While it isn't suitable for high-concurrency systems,
       it's perfect for a single-threaded Python menu/CLI application.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Enforce foreign key constraints in SQLite
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def initialize_db():
    """
    Creates necessary tables and seeds the database with initial records.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        balance REAL NOT NULL CHECK(balance >= 0),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # 2. Stocks Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stocks (
        symbol TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        current_price REAL NOT NULL CHECK(current_price > 0)
    );
    """)
    
    # 3. Orders Table
    # status can be: PENDING, PARTIALLY_EXECUTED, EXECUTED, CANCELLED
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        symbol TEXT NOT NULL,
        order_type TEXT NOT NULL CHECK(order_type IN ('BUY', 'SELL')),
        quantity INTEGER NOT NULL CHECK(quantity > 0),
        price REAL NOT NULL CHECK(price > 0),
        status TEXT NOT NULL CHECK(status IN ('PENDING', 'PARTIALLY_EXECUTED', 'EXECUTED', 'CANCELLED')),
        remaining_quantity INTEGER NOT NULL CHECK(remaining_quantity >= 0),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (symbol) REFERENCES stocks(symbol)
    );
    """)
    
    # 4. Trades Table (Executed Matches)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        buyer_id INTEGER NOT NULL,
        seller_id INTEGER NOT NULL,
        buy_order_id INTEGER NOT NULL,
        sell_order_id INTEGER NOT NULL,
        symbol TEXT NOT NULL,
        quantity INTEGER NOT NULL CHECK(quantity > 0),
        price REAL NOT NULL CHECK(price > 0),
        executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (buyer_id) REFERENCES users(id),
        FOREIGN KEY (seller_id) REFERENCES users(id),
        FOREIGN KEY (buy_order_id) REFERENCES orders(id),
        FOREIGN KEY (sell_order_id) REFERENCES orders(id),
        FOREIGN KEY (symbol) REFERENCES stocks(symbol)
    );
    """)
    
    # 5. Portfolio Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS portfolio (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        symbol TEXT NOT NULL,
        quantity INTEGER NOT NULL CHECK(quantity >= 0),
        average_price REAL NOT NULL CHECK(average_price >= 0),
        UNIQUE(user_id, symbol),
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (symbol) REFERENCES stocks(symbol)
    );
    """)
    
    # 6. Audit Logs Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT NOT NULL,
        details TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # Lightweight migration for the web profile/settings page.
    # Existing SQLite databases from older versions will not have these columns.
    existing_user_cols = [row[1] for row in cursor.execute("PRAGMA table_info(users);").fetchall()]
    user_migrations = {
        "email": "ALTER TABLE users ADD COLUMN email TEXT;",
        "password": "ALTER TABLE users ADD COLUMN password TEXT DEFAULT 'demo123';",
        "last_login": "ALTER TABLE users ADD COLUMN last_login TIMESTAMP;",
        "trade_alerts": "ALTER TABLE users ADD COLUMN trade_alerts INTEGER DEFAULT 1;",
        "portfolio_updates": "ALTER TABLE users ADD COLUMN portfolio_updates INTEGER DEFAULT 1;",
        "theme_preference": "ALTER TABLE users ADD COLUMN theme_preference TEXT DEFAULT 'dark';"
    }
    for column, alter_sql in user_migrations.items():
        if column not in existing_user_cols:
            cursor.execute(alter_sql)

    conn.commit()
    
    # Check if database is already seeded
    cursor.execute("SELECT COUNT(*) FROM users;")
    if cursor.fetchone()[0] == 0:
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Seed Users
        users_data = [
            ("Sneha", 100000.0, "sneha@tradesphere.com", "demo123", now_str),
            ("Rahul", 100000.0, "rahul@tradesphere.com", "demo123", now_str),
            ("Priya", 100000.0, "priya@tradesphere.com", "demo123", now_str)
        ]
        cursor.executemany("INSERT INTO users (username, balance, email, password, last_login) VALUES (?, ?, ?, ?, ?);", users_data)
        
        # Seed Stocks
        stocks_data = [
            ("TCS", "Tata Consultancy Services", 3500.0),
            ("INFY", "Infosys Limited", 1500.0),
            ("RELIANCE", "Reliance Industries", 2500.0),
            ("HDFCBANK", "HDFC Bank Limited", 1600.0)
        ]
        cursor.executemany("INSERT INTO stocks (symbol, name, current_price) VALUES (?, ?, ?);", stocks_data)
        
        conn.commit()
        
        # Get Seeded User IDs
        cursor.execute("SELECT id, username FROM users;")
        users = {row["username"]: row["id"] for row in cursor.fetchall()}
        
        # Seed Initial Portfolio holdings so they can start selling right away!
        # Sneha: 10 TCS, 20 INFY
        # Rahul: 15 RELIANCE, 30 HDFCBANK
        # Priya: 5 TCS, 10 RELIANCE
        portfolio_data = [
            (users["Sneha"], "TCS", 10, 3500.0),
            (users["Sneha"], "INFY", 20, 1500.0),
            (users["Rahul"], "RELIANCE", 15, 2500.0),
            (users["Rahul"], "HDFCBANK", 30, 1600.0),
            (users["Priya"], "TCS", 5, 3500.0),
            (users["Priya"], "RELIANCE", 10, 2500.0)
        ]
        cursor.executemany("INSERT INTO portfolio (user_id, symbol, quantity, average_price) VALUES (?, ?, ?, ?);", portfolio_data)
        
        # Write Initial Audit Logs
        initial_logs = [
            ("SYSTEM_INIT", "Database tables initialized successfully.", now_str),
            ("USER_SEED", "Sample users created: Sneha (₹100,000), Rahul (₹100,000), Priya (₹100,000).", now_str),
            ("STOCK_SEED", "Sample stocks loaded: TCS, INFY, RELIANCE, HDFCBANK.", now_str),
            ("PORTFOLIO_SEED", "Initial portfolio holdings seeded for test trading.", now_str)
        ]
        cursor.executemany("INSERT INTO audit_logs (action, details, timestamp) VALUES (?, ?, ?);", initial_logs)
        
        conn.commit()

    # Backfill profile fields for databases created before the Profile Settings page.
    default_profiles = {
        "Sneha": "sneha@tradesphere.com",
        "Rahul": "rahul@tradesphere.com",
        "Priya": "priya@tradesphere.com"
    }
    for username, email in default_profiles.items():
        cursor.execute("""
            UPDATE users
            SET email = COALESCE(email, ?),
                password = COALESCE(password, 'demo123'),
                last_login = COALESCE(last_login, CURRENT_TIMESTAMP),
                trade_alerts = COALESCE(trade_alerts, 1),
                portfolio_updates = COALESCE(portfolio_updates, 1),
                theme_preference = COALESCE(theme_preference, 'dark')
            WHERE username = ?;
        """, (email, username))
    conn.commit()
        
    conn.close()

if __name__ == "__main__":
    # If run directly, initialize database.
    initialize_db()
    print("Database initialized successfully at:", DB_PATH)
