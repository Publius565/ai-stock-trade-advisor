"""
Position Monitor - Tracks portfolio positions, P&L, and position management
Part of Phase 4: Execution Layer implementation
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ..utils.database_manager import DatabaseManager
from ..data_layer.market_data import MarketDataManager


class PositionStatus(Enum):
    """Position status tracking"""
    ACTIVE = "active"
    CLOSED = "closed"
    PENDING = "pending"


@dataclass
class Position:
    """Portfolio position data structure"""
    uid: str
    user_id: int
    symbol: str
    quantity: int
    avg_price: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    realized_pnl: float
    total_pnl: float
    pnl_percentage: float
    entry_date: datetime
    last_updated: datetime
    status: PositionStatus = PositionStatus.ACTIVE


class PositionMonitor:
    """
    Position monitoring and management system
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        cache_dir = getattr(db_manager, 'get_cache_dir', lambda: "data/cache")()
        self.market_data_manager = MarketDataManager(cache_dir)
        self.logger = logging.getLogger(__name__)
        
        # Position tracking
        self.active_positions: Dict[str, Position] = {}
        self.position_history: Dict[str, List[Position]] = {}
        
        self.logger.info("Position Monitor initialized")
    
    def update_positions(self, user_id: int) -> bool:
        """
        Update all positions for a user with current market data
        """
        try:
            # Get user positions from database
            positions = self._get_user_positions(user_id)
            
            for position_data in positions:
                symbol = position_data['symbol']
                
                # Get current market price
                current_price = self._get_current_price(symbol)
                if current_price is None:
                    self.logger.warning(f"Could not get current price for {symbol}")
                    continue
                
                # Calculate position metrics
                position = self._calculate_position_metrics(position_data, current_price)
                
                # Update position in database
                self._update_position_in_db(position)
                
                # Update in-memory cache
                self.active_positions[position.uid] = position
                
                self.logger.debug(f"Updated position: {symbol} - P&L: ${position.unrealized_pnl:.2f}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating positions: {e}")
            return False
    
    def _get_user_positions(self, user_id: int) -> List[Dict]:
        """Get all positions for a user from database"""
        try:
            query = """
                SELECT p.uid, p.user_id, s.symbol, p.quantity, p.avg_price, 
                       p.current_price, p.market_value, p.unrealized_pnl, p.realized_pnl,
                       p.last_updated
                FROM positions p
                JOIN symbols s ON p.symbol_id = s.id
                WHERE p.user_id = ? AND p.quantity > 0
            """
            
            results = self.db_manager.fetch_all(query, (user_id,))
            positions = []
            
            for row in results:
                positions.append({
                    'uid': row[0],
                    'user_id': row[1],
                    'symbol': row[2],
                    'quantity': row[3],
                    'avg_price': row[4],
                    'current_price': row[5],
                    'market_value': row[6],
                    'unrealized_pnl': row[7],
                    'realized_pnl': row[8],
                    'last_updated': datetime.fromtimestamp(row[9]) if row[9] else datetime.now()
                })
            
            return positions
            
        except Exception as e:
            self.logger.error(f"Error getting user positions: {e}")
            return []
    
    def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current market price for a symbol"""
        try:
            # Try to get from market data manager
            market_data = self.market_data_manager.get_latest_data(symbol)
            if market_data and 'close' in market_data:
                return market_data['close']
            
            # Fallback: use cached price from database
            query = """
                SELECT md.close
                FROM market_data md
                JOIN symbols s ON md.symbol_id = s.id
                WHERE s.symbol = ?
                ORDER BY md.date DESC
                LIMIT 1
            """
            
            result = self.db_manager.fetch_one(query, (symbol,))
            if result and result[0]:
                return result[0]
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting current price for {symbol}: {e}")
            return None
    
    def _calculate_position_metrics(self, position_data: Dict, current_price: float) -> Position:
        """Calculate position metrics including P&L"""
        try:
            quantity = position_data['quantity']
            avg_price = position_data['avg_price']
            realized_pnl = position_data['realized_pnl']
            
            # Calculate metrics
            market_value = quantity * current_price
            unrealized_pnl = (current_price - avg_price) * quantity
            total_pnl = realized_pnl + unrealized_pnl
            pnl_percentage = (unrealized_pnl / (avg_price * quantity)) * 100 if avg_price > 0 else 0
            
            return Position(
                uid=position_data['uid'],
                user_id=position_data['user_id'],
                symbol=position_data['symbol'],
                quantity=quantity,
                avg_price=avg_price,
                current_price=current_price,
                market_value=market_value,
                unrealized_pnl=unrealized_pnl,
                realized_pnl=realized_pnl,
                total_pnl=total_pnl,
                pnl_percentage=pnl_percentage,
                entry_date=position_data['last_updated'],
                last_updated=datetime.now(),
                status=PositionStatus.ACTIVE
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating position metrics: {e}")
            raise
    
    def _update_position_in_db(self, position: Position) -> bool:
        """Update position in database"""
        try:
            query = """
                UPDATE positions 
                SET current_price = ?, market_value = ?, unrealized_pnl = ?, last_updated = ?
                WHERE uid = ?
            """
            
            params = (
                position.current_price,
                position.market_value,
                position.unrealized_pnl,
                int(position.last_updated.timestamp()),
                position.uid
            )
            
            self.db_manager.execute_query(query, params)
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating position in database: {e}")
            return False
    
    def add_position(self, user_id: int, symbol: str, quantity: int, price: float) -> bool:
        """
        Add a new position to the portfolio
        """
        try:
            # Get symbol ID
            symbol_manager = self.db_manager.get_manager('symbol')
            symbol_id = symbol_manager.get_symbol_id(symbol)
            if not symbol_id:
                self.logger.error(f"Symbol not found: {symbol}")
                return False
            
            # Check if position already exists
            existing_position = self._get_position(user_id, symbol_id)
            
            if existing_position:
                # Update existing position
                new_quantity = existing_position['quantity'] + quantity
                new_avg_price = ((existing_position['quantity'] * existing_position['avg_price']) + 
                               (quantity * price)) / new_quantity
                
                query = """
                    UPDATE positions 
                    SET quantity = ?, avg_price = ?, last_updated = ?
                    WHERE user_id = ? AND symbol_id = ?
                """
                
                params = (
                    new_quantity,
                    new_avg_price,
                    int(datetime.now().timestamp()),
                    user_id,
                    symbol_id
                )
                
            else:
                # Create new position
                query = """
                    INSERT INTO positions (uid, user_id, symbol_id, quantity, avg_price, 
                                         current_price, market_value, unrealized_pnl, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                import uuid
                position_uid = str(uuid.uuid4())
                market_value = quantity * price
                
                params = (
                    position_uid,
                    user_id,
                    symbol_id,
                    quantity,
                    price,
                    price,
                    market_value,
                    0.0,  # No unrealized P&L initially
                    int(datetime.now().timestamp())
                )
            
            self.db_manager.execute_query(query, params)
            self.logger.info(f"Position updated: {symbol} - Quantity: {quantity}, Price: ${price:.2f}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding position: {e}")
            return False
    
    def close_position(self, user_id: int, symbol: str, quantity: int, price: float) -> bool:
        """
        Close or reduce a position
        """
        try:
            # Get symbol ID
            symbol_manager = self.db_manager.get_manager('symbol')
            symbol_id = symbol_manager.get_symbol_id(symbol)
            if not symbol_id:
                self.logger.error(f"Symbol not found: {symbol}")
                return False
            
            # Get current position
            position = self._get_position(user_id, symbol_id)
            if not position:
                self.logger.error(f"No position found for {symbol}")
                return False
            
            current_quantity = position['quantity']
            avg_price = position['avg_price']
            
            if quantity > current_quantity:
                self.logger.error(f"Attempting to close more shares than owned: {quantity} > {current_quantity}")
                return False
            
            # Calculate realized P&L
            realized_pnl = (price - avg_price) * quantity
            
            if quantity == current_quantity:
                # Close entire position
                query = """
                    UPDATE positions 
                    SET quantity = 0, realized_pnl = ?, last_updated = ?
                    WHERE user_id = ? AND symbol_id = ?
                """
                params = (realized_pnl, int(datetime.now().timestamp()), user_id, symbol_id)
            else:
                # Reduce position
                remaining_quantity = current_quantity - quantity
                query = """
                    UPDATE positions 
                    SET quantity = ?, realized_pnl = ?, last_updated = ?
                    WHERE user_id = ? AND symbol_id = ?
                """
                params = (remaining_quantity, realized_pnl, int(datetime.now().timestamp()), user_id, symbol_id)
            
            self.db_manager.execute_query(query, params)
            self.logger.info(f"Position closed: {symbol} - Quantity: {quantity}, Price: ${price:.2f}, P&L: ${realized_pnl:.2f}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error closing position: {e}")
            return False
    
    def _get_position(self, user_id: int, symbol_id: int) -> Optional[Dict]:
        """Get position data from database"""
        try:
            query = """
                SELECT quantity, avg_price, realized_pnl
                FROM positions
                WHERE user_id = ? AND symbol_id = ?
            """
            
            result = self.db_manager.fetch_one(query, (user_id, symbol_id))
            if result:
                return {
                    'quantity': result[0],
                    'avg_price': result[1],
                    'realized_pnl': result[2]
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting position: {e}")
            return None
    
    def get_portfolio_summary(self, user_id: int) -> Dict:
        """
        Get comprehensive portfolio summary
        """
        try:
            # Update positions first
            self.update_positions(user_id)
            
            # Get portfolio data
            query = """
                SELECT 
                    COUNT(*) as total_positions,
                    SUM(quantity) as total_shares,
                    SUM(market_value) as total_market_value,
                    SUM(unrealized_pnl) as total_unrealized_pnl,
                    SUM(realized_pnl) as total_realized_pnl,
                    AVG(pnl_percentage) as avg_pnl_percentage
                FROM positions p
                WHERE p.user_id = ? AND p.quantity > 0
            """
            
            result = self.db_manager.fetch_one(query, (user_id,))
            if not result:
                return {}
            
            # Calculate additional metrics
            total_market_value = result[2] or 0.0
            total_unrealized_pnl = result[3] or 0.0
            total_realized_pnl = result[4] or 0.0
            total_pnl = total_unrealized_pnl + total_realized_pnl
            
            # Get top performers
            top_performers = self._get_top_performers(user_id, limit=5)
            
            # Get recent activity
            recent_trades = self._get_recent_trades(user_id, limit=10)
            
            return {
                'total_positions': result[0] or 0,
                'total_shares': result[1] or 0,
                'total_market_value': total_market_value,
                'total_unrealized_pnl': total_unrealized_pnl,
                'total_realized_pnl': total_realized_pnl,
                'total_pnl': total_pnl,
                'avg_pnl_percentage': result[5] or 0.0,
                'portfolio_return': (total_pnl / (total_market_value - total_unrealized_pnl)) * 100 if (total_market_value - total_unrealized_pnl) > 0 else 0.0,
                'top_performers': top_performers,
                'recent_trades': recent_trades,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting portfolio summary: {e}")
            return {}
    
    def _get_top_performers(self, user_id: int, limit: int = 5) -> List[Dict]:
        """Get top performing positions"""
        try:
            query = """
                SELECT s.symbol, p.unrealized_pnl, p.pnl_percentage, p.quantity, p.current_price
                FROM positions p
                JOIN symbols s ON p.symbol_id = s.id
                WHERE p.user_id = ? AND p.quantity > 0
                ORDER BY p.unrealized_pnl DESC
                LIMIT ?
            """
            
            results = self.db_manager.fetch_all(query, (user_id, limit))
            performers = []
            
            for row in results:
                performers.append({
                    'symbol': row[0],
                    'unrealized_pnl': row[1] or 0.0,
                    'pnl_percentage': row[2] or 0.0,
                    'quantity': row[3],
                    'current_price': row[4] or 0.0
                })
            
            return performers
            
        except Exception as e:
            self.logger.error(f"Error getting top performers: {e}")
            return []
    
    def _get_recent_trades(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get recent trade activity"""
        try:
            query = """
                SELECT s.symbol, t.trade_type, t.quantity, t.price, t.trade_date
                FROM trades t
                JOIN symbols s ON t.symbol_id = s.id
                WHERE t.user_id = ? AND t.status = 'filled'
                ORDER BY t.trade_date DESC
                LIMIT ?
            """
            
            results = self.db_manager.fetch_all(query, (user_id, limit))
            trades = []
            
            for row in results:
                trades.append({
                    'symbol': row[0],
                    'trade_type': row[1],
                    'quantity': row[2],
                    'price': row[3],
                    'trade_date': datetime.fromtimestamp(row[4]).strftime('%Y-%m-%d %H:%M:%S')
                })
            
            return trades
            
        except Exception as e:
            self.logger.error(f"Error getting recent trades: {e}")
            return []
    
    def get_position_details(self, user_id: int, symbol: str) -> Optional[Dict]:
        """Get detailed position information for a specific symbol"""
        try:
            query = """
                SELECT p.*, s.symbol
                FROM positions p
                JOIN symbols s ON p.symbol_id = s.id
                WHERE p.user_id = ? AND s.symbol = ?
            """
            
            result = self.db_manager.fetch_one(query, (user_id, symbol))
            if not result:
                return None
            
            # Get trade history for this symbol
            trade_history = self._get_symbol_trade_history(user_id, symbol)
            
            return {
                'symbol': symbol,
                'quantity': result[3],
                'avg_price': result[4],
                'current_price': result[5],
                'market_value': result[6],
                'unrealized_pnl': result[7],
                'realized_pnl': result[8],
                'last_updated': datetime.fromtimestamp(result[10]).strftime('%Y-%m-%d %H:%M:%S'),
                'trade_history': trade_history
            }
            
        except Exception as e:
            self.logger.error(f"Error getting position details: {e}")
            return None
    
    def _get_symbol_trade_history(self, user_id: int, symbol: str) -> List[Dict]:
        """Get trade history for a specific symbol"""
        try:
            query = """
                SELECT t.trade_type, t.quantity, t.price, t.trade_date, t.commission
                FROM trades t
                JOIN symbols s ON t.symbol_id = s.id
                WHERE t.user_id = ? AND s.symbol = ? AND t.status = 'filled'
                ORDER BY t.trade_date DESC
            """
            
            results = self.db_manager.fetch_all(query, (user_id, symbol))
            history = []
            
            for row in results:
                history.append({
                    'trade_type': row[0],
                    'quantity': row[1],
                    'price': row[2],
                    'trade_date': datetime.fromtimestamp(row[3]).strftime('%Y-%m-%d %H:%M:%S'),
                    'commission': row[4]
                })
            
            return history
            
        except Exception as e:
            self.logger.error(f"Error getting trade history: {e}")
            return [] 