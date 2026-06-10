from dataclasses import dataclass

@dataclass
class User:
    id: int
    username: str
    balance: float
    created_at: str

@dataclass
class Stock:
    symbol: str
    name: str
    current_price: float

@dataclass
class Order:
    id: int
    user_id: int
    symbol: str
    order_type: str  # 'BUY' or 'SELL'
    quantity: int
    price: float
    status: str      # 'PENDING', 'PARTIALLY_EXECUTED', 'EXECUTED', 'CANCELLED'
    remaining_quantity: int
    created_at: str

@dataclass
class Trade:
    id: int
    buyer_id: int
    seller_id: int
    buy_order_id: int
    sell_order_id: int
    symbol: str
    quantity: int
    price: float
    executed_at: str

@dataclass
class PortfolioItem:
    id: int
    user_id: int
    symbol: str
    quantity: int
    average_price: float

@dataclass
class AuditLog:
    id: int
    action: str
    details: str
    timestamp: str
