"""
Trading Types - Shared enums and dataclasses for execution layer
Part of Phase 4B: Broker Integration implementation
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class OrderType(Enum):
    """Order types for trade execution"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(Enum):
    """Order status tracking"""
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class TradeOrder:
    """Trade order data structure"""
    uid: str
    user_id: int
    symbol: str
    order_type: OrderType
    quantity: int
    price: float
    signal_id: Optional[str] = None
    stop_price: Optional[float] = None
    limit_price: Optional[float] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: int = 0
    filled_price: Optional[float] = None
    commission: float = 0.0
    created_at: datetime = None
    filled_at: Optional[datetime] = None
    notes: str = "" 