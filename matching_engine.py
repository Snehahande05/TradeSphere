import sqlite3

def match_orders_for_stock(conn, symbol):
    """
    Finds and executes matching BUY and SELL orders for a specific stock symbol.
    Uses Price-Time Priority (FIFO) matching rules.
    
    HOW IT WORKS:
    1. Fetch the highest price buy order (priority to higher price, then older order).
    2. Fetch the lowest price sell order (priority to lower price, then older order).
    3. Check if buy_price >= sell_price:
       - If YES: Match!
         - Determine quantity to execute: min(buy_remaining, sell_remaining).
         - Determine execution price (Passive Order Pricing):
           - The order with the older created_at timestamp sets the price.
         - Call TradeExecutionService.execute_trade to persist balance, portfolio,
           and order changes atomically in a transaction.
         - Repeat the process (loop again) since orders might still match or be partially filled.
       - If NO or no orders found: Break (book is in equilibrium, no matches possible).
       
    SYSTEM DESIGN VIVA COMMENTS:
    
    1. How the Matching Engine Works:
       - Price-Time Priority: Orders are queued and prioritized first by price (highest bid for buyers, 
         lowest ask for sellers) and second by time (earlier orders get executed first).
       - Continuous Matching: Runs automatically whenever a new limit order is placed on that stock symbol.
       - Partial Matching: If one order's quantity is larger than the other, the smaller order is fully 
         filled, while the larger order is partially filled and remains active with updated remaining quantity.
         
    2. How Consistency is Maintained:
       - Database Transactions (ACID): The entire matching loop and trade execution operate within SQLite 
         transactions. If any step fails (e.g., database constraint check or syntax error), the database 
         is rolled back to the state before the match attempt. This prevents partial state updates 
         (like deducting money from the buyer but failing to credit the seller).
       - Available Balance & Share Lock: Instead of physically debiting balances during order placement 
         (which is hard to refund on cancellation), we calculate 'available_balance' and 'available_shares' 
         dynamically. Any active buy/sell orders lock these funds/shares, ensuring no double-spending.
         
    3. How Scalability Can Be Improved in Real-World Systems:
       - In-Memory Order Books: Relational database queries for every match are too slow for real-world exchanges. 
         Production engines store order books in-memory (e.g., using Red-Black Trees, Heaps, or Double-Ended Queues) 
         for microsecond matching speeds, then dump trades to a database asynchronously.
       - Actor Model & Sharding: Scale horizontally by partitioning/sharding order matching by stock symbol. 
         For example, Engine-1 matches only TCS, Engine-2 matches INFY. Each symbol matching queue runs 
         single-threaded to eliminate lock contention, utilizing architectures like the LMAX Disruptor pattern.
       - Message Queues: Use distributed streaming platforms like Apache Kafka or RabbitMQ to ingest, queue, 
         and sequence incoming orders before they hit the matching engine, ensuring zero data loss and orderly execution.
    """
    # Import inside function to prevent circular imports
    from services import TradeExecutionService, AuditLogService
    
    matches_executed = 0
    
    while True:
        # 1. Fetch highest-priced BUY order that is PENDING or PARTIALLY_EXECUTED
        # Order by price DESC (highest bid), then created_at ASC (first in time)
        buy_order = conn.execute(
            """
            SELECT * FROM orders 
            WHERE symbol = ? AND order_type = 'BUY' AND status IN ('PENDING', 'PARTIALLY_EXECUTED')
            ORDER BY price DESC, created_at ASC 
            LIMIT 1;
            """,
            (symbol,)
        ).fetchone()

        # 2. Fetch lowest-priced SELL order that is PENDING or PARTIALLY_EXECUTED
        # Order by price ASC (lowest ask), then created_at ASC (first in time)
        sell_order = conn.execute(
            """
            SELECT * FROM orders 
            WHERE symbol = ? AND order_type = 'SELL' AND status IN ('PENDING', 'PARTIALLY_EXECUTED')
            ORDER BY price ASC, created_at ASC 
            LIMIT 1;
            """,
            (symbol,)
        ).fetchone()

        # If either side of the book is empty, no matching can happen
        if not buy_order or not sell_order:
            break

        # 3. Check matching condition (cross-matching limit check)
        if buy_order["price"] >= sell_order["price"]:
            # Match quantity is the minimum of the remaining quantities
            match_qty = min(buy_order["remaining_quantity"], sell_order["remaining_quantity"])
            
            # Determine execution price based on passive order priority (the order placed first)
            if buy_order["created_at"] < sell_order["created_at"]:
                exec_price = buy_order["price"]
            else:
                exec_price = sell_order["price"]

            # Execute the trade atomically
            TradeExecutionService.execute_trade(
                conn, 
                buy_order_id=buy_order["id"], 
                sell_order_id=sell_order["id"], 
                symbol=symbol, 
                quantity=match_qty, 
                price=exec_price
            )
            matches_executed += 1
        else:
            # Buy price is less than sell price, no matches possible
            break

    return matches_executed
