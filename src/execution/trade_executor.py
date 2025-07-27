"""
Trade Executor - Handles trade execution, order management, and broker integration
Part of Phase 4: Execution Layer implementation
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from ..utils.database_manager import DatabaseManager
from ..strategy.trading_engine import TradingSignal, SignalType
from ..profile.profile_manager import ProfileManager
from .alpaca_broker import AlpacaBroker
from .trading_types import TradeOrder, OrderType, OrderStatus





class MockBroker:
    """Mock broker interface for testing and development"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.commission_rate = 0.005  # 0.5% commission
        self.min_commission = 1.0  # $1 minimum commission
        
    def place_order(self, order: TradeOrder) -> bool:
        """Place an order with the mock broker"""
        try:
            # Simulate order processing
            self.logger.info(f"Placing order: {order.symbol} {order.order_type.value} {order.quantity} @ {order.price}")
            
            # Simulate market conditions
            if order.order_type == OrderType.MARKET:
                # Market orders are filled immediately
                order.status = OrderStatus.FILLED
                order.filled_quantity = order.quantity
                order.filled_price = order.price
                order.filled_at = datetime.now()
                order.commission = max(self.min_commission, order.price * order.quantity * self.commission_rate)
                
            elif order.order_type == OrderType.LIMIT:
                # Limit orders are filled if price is favorable
                if order.price <= order.limit_price:
                    order.status = OrderStatus.FILLED
                    order.filled_quantity = order.quantity
                    order.filled_price = order.limit_price
                    order.filled_at = datetime.now()
                    order.commission = max(self.min_commission, order.limit_price * order.quantity * self.commission_rate)
                else:
                    order.status = OrderStatus.PENDING
                    
            self.logger.info(f"Order {order.uid} status: {order.status.value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error placing order: {e}")
            order.status = OrderStatus.REJECTED
            return False
    
    def cancel_order(self, order_uid: str) -> bool:
        """Cancel an existing order"""
        self.logger.info(f"Cancelling order: {order_uid}")
        return True
    
    def get_order_status(self, order_uid: str) -> Optional[OrderStatus]:
        """Get current order status"""
        # Mock implementation - in real system would query broker
        return OrderStatus.FILLED


class TradeExecutor:
    """
    Trade execution engine that handles order placement and management
    """
    
    def __init__(self, db_manager: DatabaseManager, profile_manager: ProfileManager):
        self.db_manager = db_manager
        self.profile_manager = profile_manager
        self.broker = None  # Will be initialized based on configuration
        self.logger = logging.getLogger(__name__)
        
        # Execution state
        self.pending_orders: Dict[str, TradeOrder] = {}
        self.execution_enabled = False
        self.paper_trading = True  # Default to paper trading
        
        self.logger.info("Trade Executor initialized")
    
    def enable_execution(self, enabled: bool = True, paper_trading: bool = True, use_alpaca: bool = True) -> None:
        """Enable or disable trade execution"""
        self.execution_enabled = enabled
        self.paper_trading = paper_trading
        
        # Initialize broker based on configuration
        if enabled and self.broker is None:
            self._initialize_broker(use_alpaca)
        
        self.logger.info(f"Trade execution {'enabled' if enabled else 'disabled'} (paper_trading={paper_trading}, alpaca={use_alpaca})")
    
    def _initialize_broker(self, use_alpaca: bool = True) -> None:
        """Initialize the appropriate broker interface"""
        try:
            if use_alpaca:
                # Import config here to avoid circular imports
                from config.config import ALPACA_API_KEY, ALPACA_SECRET_KEY, ALPACA_BASE_URL
                
                if not ALPACA_API_KEY or not ALPACA_SECRET_KEY:
                    self.logger.warning("Alpaca API credentials not found, falling back to MockBroker")
                    self.broker = MockBroker()
                    return
                
                self.broker = AlpacaBroker(
                    api_key=ALPACA_API_KEY,
                    secret_key=ALPACA_SECRET_KEY,
                    base_url=ALPACA_BASE_URL,
                    paper_trading=self.paper_trading
                )
                
                if not self.broker.is_connected():
                    self.logger.warning("Failed to connect to Alpaca, falling back to MockBroker")
                    self.broker = MockBroker()
                else:
                    self.logger.info("Successfully connected to Alpaca API")
            else:
                self.broker = MockBroker()
                self.logger.info("Using MockBroker for testing")
                
        except Exception as e:
            self.logger.error(f"Error initializing broker: {e}")
            self.broker = MockBroker()
            self.logger.info("Falling back to MockBroker")
    
    def execute_signal(self, signal: TradingSignal, user_id: int) -> Optional[TradeOrder]:
        """
        Execute a trading signal by creating and placing an order
        """
        if not self.execution_enabled:
            self.logger.warning("Trade execution is disabled")
            return None
        
        if self.broker is None:
            self.logger.error("Broker not initialized")
            return None
        
        try:
            # Validate signal
            if not self._validate_signal(signal, user_id):
                self.logger.warning(f"Signal validation failed for {signal.symbol}")
                return None
            
            # Calculate position size based on risk management
            quantity = self._calculate_position_size(signal, user_id)
            if quantity <= 0:
                self.logger.warning(f"Invalid position size calculated for {signal.symbol}")
                return None
            
            # Create trade order
            order = self._create_order(signal, user_id, quantity)
            if not order:
                self.logger.error(f"Failed to create order for {signal.symbol}")
                return None
            
            # Place order with broker
            if self.broker.place_order(order):
                # Store order in database
                self._store_order(order)
                self.pending_orders[order.uid] = order
                
                self.logger.info(f"Order executed: {order.symbol} {order.order_type.value} {order.quantity} @ {order.price}")
                return order
            else:
                self.logger.error(f"Failed to place order for {signal.symbol}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error executing signal: {e}")
            return None
    
    def _validate_signal(self, signal: TradingSignal, user_id: int) -> bool:
        """Validate trading signal before execution"""
        try:
            # Check if signal is actionable
            if signal.signal_type not in [SignalType.BUY, SignalType.SELL, SignalType.STRONG_BUY, SignalType.STRONG_SELL]:
                self.logger.warning(f"Non-actionable signal type: {signal.signal_type}")
                return False
            
            # Check signal confidence
            if signal.confidence < 0.6:  # Minimum 60% confidence
                self.logger.warning(f"Low confidence signal: {signal.confidence}")
                return False
            
            # Check if user has sufficient funds (for buy signals)
            if signal.signal_type in [SignalType.BUY, SignalType.STRONG_BUY]:
                user_profile = self.profile_manager.get_user_profile(user_id)
                if not user_profile:
                    self.logger.error(f"User profile not found for user {user_id}")
                    return False
                
                # Check available funds (simplified)
                # In real implementation, would check actual account balance
                required_amount = signal.price * 100  # Assume minimum 100 shares
                if user_profile.get('max_position_pct', 0.1) * 10000 < required_amount:  # Assume $10k portfolio
                    self.logger.warning(f"Insufficient funds for {signal.symbol}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating signal: {e}")
            return False
    
    def _calculate_position_size(self, signal: TradingSignal, user_id: int) -> int:
        """Calculate position size based on risk management rules"""
        try:
            user_profile = self.profile_manager.get_user_profile(user_id)
            if not user_profile:
                return 0
            
            # Get risk parameters
            max_position_pct = user_profile.get('max_position_pct', 0.1)  # 10% max per position
            portfolio_value = 10000  # Mock portfolio value - in real system would get from account
            
            # Calculate position size based on signal strength and confidence
            base_size = portfolio_value * max_position_pct / signal.price
            
            # Adjust for signal strength
            strength_multiplier = {
                1: 0.5,   # WEAK
                2: 0.75,  # MODERATE
                3: 1.0,   # STRONG
                4: 1.25   # VERY_STRONG
            }.get(signal.strength.value, 1.0)
            
            # Adjust for confidence
            confidence_multiplier = signal.confidence
            
            final_size = int(base_size * strength_multiplier * confidence_multiplier)
            
            # Ensure minimum and maximum sizes
            final_size = max(1, min(final_size, 1000))  # Between 1 and 1000 shares
            
            self.logger.info(f"Calculated position size for {signal.symbol}: {final_size} shares")
            return final_size
            
        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return 0
    
    def _create_order(self, signal: TradingSignal, user_id: int, quantity: int) -> Optional[TradeOrder]:
        """Create a trade order from signal"""
        try:
            # Determine order type based on signal
            if signal.signal_type in [SignalType.STRONG_BUY, SignalType.STRONG_SELL]:
                order_type = OrderType.MARKET  # Strong signals use market orders
            else:
                order_type = OrderType.LIMIT  # Regular signals use limit orders
            
            # Create order
            order = TradeOrder(
                uid=str(uuid.uuid4()),
                user_id=user_id,
                symbol=signal.symbol,
                order_type=order_type,
                quantity=quantity,
                price=signal.price,
                signal_id=getattr(signal, 'uid', None),
                created_at=datetime.now(),
                notes=f"Signal: {signal.signal_type.value}, Confidence: {signal.confidence:.2f}, Reasoning: {signal.reasoning[:100]}"
            )
            
            # Set limit price for limit orders
            if order_type == OrderType.LIMIT:
                if signal.signal_type in [SignalType.BUY, SignalType.STRONG_BUY]:
                    order.limit_price = signal.price * 1.01  # 1% above current price
                else:
                    order.limit_price = signal.price * 0.99  # 1% below current price
            
            return order
            
        except Exception as e:
            self.logger.error(f"Error creating order: {e}")
            return None
    
    def _store_order(self, order: TradeOrder) -> bool:
        """Store order in database"""
        try:
            # Get symbol ID
            symbol_manager = self.db_manager.get_manager('symbol')
            symbol_id = symbol_manager.get_symbol_id(order.symbol)
            if not symbol_id:
                self.logger.error(f"Symbol not found: {order.symbol}")
                return False
            
            # Insert into trades table
            query = """
                INSERT INTO trades (uid, user_id, symbol_id, signal_id, trade_type, quantity, 
                                  price, total_amount, commission, trade_date, is_paper, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            trade_type = 'buy' if order.order_type in [OrderType.MARKET, OrderType.LIMIT] else 'sell'
            total_amount = order.filled_price * order.filled_quantity if order.filled_price else order.price * order.quantity
            
            params = (
                order.uid,
                order.user_id,
                symbol_id,
                order.signal_id,
                trade_type,
                order.quantity,
                order.price,
                total_amount,
                order.commission,
                int(order.created_at.timestamp()),
                1 if self.paper_trading else 0,
                order.status.value
            )
            
            self.db_manager.execute_query(query, params)
            self.logger.info(f"Order stored in database: {order.uid}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing order: {e}")
            return False
    
    def get_pending_orders(self, user_id: int) -> List[TradeOrder]:
        """Get all pending orders for a user"""
        return [order for order in self.pending_orders.values() if order.user_id == user_id]
    
    def cancel_order(self, order_uid: str) -> bool:
        """Cancel a pending order"""
        try:
            if order_uid in self.pending_orders:
                order = self.pending_orders[order_uid]
                if self.broker.cancel_order(order_uid):
                    order.status = OrderStatus.CANCELLED
                    self._update_order_status(order_uid, OrderStatus.CANCELLED)
                    del self.pending_orders[order_uid]
                    self.logger.info(f"Order cancelled: {order_uid}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error cancelling order: {e}")
            return False
    
    def _update_order_status(self, order_uid: str, status: OrderStatus) -> bool:
        """Update order status in database"""
        try:
            query = "UPDATE trades SET status = ? WHERE uid = ?"
            self.db_manager.execute_query(query, (status.value, order_uid))
            return True
        except Exception as e:
            self.logger.error(f"Error updating order status: {e}")
            return False
    
    def get_execution_summary(self, user_id: int) -> Dict:
        """Get execution summary for a user"""
        try:
            query = """
                SELECT COUNT(*) as total_orders,
                       SUM(CASE WHEN status = 'filled' THEN 1 ELSE 0 END) as filled_orders,
                       SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_orders,
                       SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled_orders,
                       SUM(total_amount) as total_volume,
                       SUM(commission) as total_commission
                FROM trades 
                WHERE user_id = ?
            """
            
            result = self.db_manager.fetch_one(query, (user_id,))
            if result:
                summary = {
                    'total_orders': result[0] or 0,
                    'filled_orders': result[1] or 0,
                    'pending_orders': result[2] or 0,
                    'cancelled_orders': result[3] or 0,
                    'total_volume': result[4] or 0.0,
                    'total_commission': result[5] or 0.0,
                    'execution_enabled': self.execution_enabled,
                    'paper_trading': self.paper_trading
                }
                
                # Add broker information
                broker_info = self.get_broker_info()
                summary['broker_info'] = broker_info
                
                return summary
            
            return {
                'execution_enabled': self.execution_enabled,
                'paper_trading': self.paper_trading,
                'broker_info': self.get_broker_info()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting execution summary: {e}")
            return {}
    
    def get_broker_info(self) -> Dict:
        """Get current broker information"""
        if self.broker is None:
            return {
                'type': 'none',
                'connected': False,
                'status': 'not_initialized'
            }
        
        try:
            if isinstance(self.broker, AlpacaBroker):
                account_info = self.broker.get_account_info()
                return {
                    'type': 'alpaca',
                    'connected': self.broker.is_connected(),
                    'paper_trading': self.broker.paper_trading,
                    'account_info': account_info
                }
            else:
                return {
                    'type': 'mock',
                    'connected': True,
                    'status': 'simulation_mode'
                }
        except Exception as e:
            self.logger.error(f"Error getting broker info: {e}")
            return {
                'type': 'unknown',
                'connected': False,
                'status': 'error'
            } 