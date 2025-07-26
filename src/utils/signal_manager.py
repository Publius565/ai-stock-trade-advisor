"""
Signal and Portfolio Database Manager

Handles all trading signal and portfolio-related database operations including
signal generation, trade tracking, and performance monitoring.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from .base_manager import BaseDatabaseManager

logger = logging.getLogger(__name__)


class SignalManager(BaseDatabaseManager):
    """
    Specialized manager for trading signals and portfolio operations.
    
    Features:
    - Trading signal management
    - Trade execution tracking
    - Portfolio position management
    - Performance analytics
    """
    
    def get_manager_type(self) -> str:
        """Return the type of manager for logging."""
        return "SignalManager"
    
    def create_signal(self, user_uid: str, symbol: str, signal_type: str,
                     risk_level: str, confidence: float = None,
                     price_target: float = None, rationale: str = None,
                     source: str = 'rule_based') -> Optional[str]:
        """
        Create a trading signal.
        
        Args:
            user_uid: User UID
            symbol: Stock symbol
            signal_type: 'buy', 'sell', 'hold'
            risk_level: 'low', 'medium', 'high'
            confidence: Confidence score (0-1)
            price_target: Target price
            rationale: Signal rationale
            source: Signal source ('rule_based', 'ml_model', 'hybrid')
            
        Returns:
            Signal UID if successful
        """
        # Get user data
        user_query = "SELECT id, uid FROM users WHERE uid = ?"
        user_results = self.execute_query(user_query, (user_uid,))
        if not user_results:
            logger.error(f"User not found: {user_uid}")
            return None
        user_id = user_results[0]['id']
        
        # Get symbol data  
        symbol_query = "SELECT id, uid FROM symbols WHERE symbol = ?"
        symbol_results = self.execute_query(symbol_query, (symbol,))
        if not symbol_results:
            logger.error(f"Symbol not found: {symbol}")
            return None
        symbol_id = symbol_results[0]['id']
        
        uid = self.generate_uid('sig')
        
        query = """
        INSERT INTO signals 
        (uid, user_id, symbol_id, signal_type, risk_level, confidence, 
         price_target, rationale, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (uid, user_id, symbol_id, signal_type, 
                 risk_level, confidence, price_target, rationale, source)
        
        try:
            self.execute_update(query, params)
            logger.info(f"Created signal: {signal_type} {symbol} for user {user_uid}")
            return uid
        except Exception as e:
            logger.error(f"Failed to create signal: {e}")
            return None
    
    def get_user_signals(self, user_uid: str, active_only: bool = True,
                        limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get signals for a user.
        
        Args:
            user_uid: User UID
            active_only: Only return active signals
            limit: Maximum number of signals to return
            
        Returns:
            List of signal data
        """
        user_query = "SELECT id FROM users WHERE uid = ?"
        user_results = self.execute_query(user_query, (user_uid,))
        if not user_results:
            return []
        user_id = user_results[0]['id']
        
        if active_only:
            query = """
            SELECT sig.*, s.symbol, s.name
            FROM signals sig
            JOIN symbols s ON sig.symbol_id = s.id
            WHERE sig.user_id = ? AND sig.is_active = 1
            ORDER BY sig.created_at DESC
            LIMIT ?
            """
        else:
            query = """
            SELECT sig.*, s.symbol, s.name
            FROM signals sig
            JOIN symbols s ON sig.symbol_id = s.id
            WHERE sig.user_id = ?
            ORDER BY sig.created_at DESC
            LIMIT ?
            """
        
        results = self.execute_query(query, (user_id, limit))
        
        # Convert timestamps
        for row in results:
            row['created_at'] = datetime.fromtimestamp(row['created_at'])
            if row['expires_at']:
                row['expires_at'] = datetime.fromtimestamp(row['expires_at'])
        
        return results
    
    def expire_signal(self, signal_uid: str) -> bool:
        """
        Mark a signal as inactive.
        
        Args:
            signal_uid: Signal UID
            
        Returns:
            True if successful
        """
        query = "UPDATE signals SET is_active = 0 WHERE uid = ?"
        return self.execute_update(query, (signal_uid,)) > 0
    
    def create_trade(self, user_uid: str, symbol: str, trade_type: str,
                    quantity: int, price: float, signal_uid: str = None,
                    is_paper: bool = True) -> Optional[str]:
        """
        Create a trade record.
        
        Args:
            user_uid: User UID
            symbol: Stock symbol
            trade_type: 'buy' or 'sell'
            quantity: Number of shares
            price: Trade price
            signal_uid: Associated signal UID
            is_paper: Whether this is a paper trade
            
        Returns:
            Trade UID if successful
        """
        # Get user and symbol IDs
        user_query = "SELECT id FROM users WHERE uid = ?"
        user_results = self.execute_query(user_query, (user_uid,))
        if not user_results:
            return None
        user_id = user_results[0]['id']
        
        symbol_query = "SELECT id FROM symbols WHERE symbol = ?"
        symbol_results = self.execute_query(symbol_query, (symbol,))
        if not symbol_results:
            return None
        symbol_id = symbol_results[0]['id']
        
        # Get signal ID if provided
        signal_id = None
        if signal_uid:
            signal_query = "SELECT id FROM signals WHERE uid = ?"
            signal_results = self.execute_query(signal_query, (signal_uid,))
            if signal_results:
                signal_id = signal_results[0]['id']
        
        uid = self.generate_uid('trade')
        total_amount = quantity * price
        
        query = """
        INSERT INTO trades 
        (uid, user_id, symbol_id, signal_id, trade_type, quantity, price, 
         total_amount, is_paper, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (uid, user_id, symbol_id, signal_id, trade_type, 
                 quantity, price, total_amount, 1 if is_paper else 0, 'filled')
        
        try:
            self.execute_update(query, params)
            logger.info(f"Created trade: {trade_type} {quantity} {symbol} at {price}")
            return uid
        except Exception as e:
            logger.error(f"Failed to create trade: {e}")
            return None
    
    def get_user_trades(self, user_uid: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get trades for a user.
        
        Args:
            user_uid: User UID
            limit: Maximum number of trades to return
            
        Returns:
            List of trade data
        """
        user_query = "SELECT id FROM users WHERE uid = ?"
        user_results = self.execute_query(user_query, (user_uid,))
        if not user_results:
            return []
        user_id = user_results[0]['id']
        
        query = """
        SELECT t.*, s.symbol, s.name
        FROM trades t
        JOIN symbols s ON t.symbol_id = s.id
        WHERE t.user_id = ?
        ORDER BY t.trade_date DESC
        LIMIT ?
        """
        
        results = self.execute_query(query, (user_id, limit))
        
        # Convert timestamps
        for row in results:
            row['trade_date'] = datetime.fromtimestamp(row['trade_date'])
        
        return results
    
    def update_positions(self, user_uid: str, symbol: str, quantity_change: int,
                        price: float) -> bool:
        """
        Update user positions based on trade.
        
        Args:
            user_uid: User UID
            symbol: Stock symbol
            quantity_change: Change in quantity (positive for buy, negative for sell)
            price: Current price
            
        Returns:
            True if successful
        """
        # Get user and symbol IDs
        user_query = "SELECT id FROM users WHERE uid = ?"
        user_results = self.execute_query(user_query, (user_uid,))
        if not user_results:
            return False
        user_id = user_results[0]['id']
        
        symbol_query = "SELECT id FROM symbols WHERE symbol = ?"
        symbol_results = self.execute_query(symbol_query, (symbol,))
        if not symbol_results:
            return False
        symbol_id = symbol_results[0]['id']
        
        # Check if position exists
        position_query = """
        SELECT * FROM positions WHERE user_id = ? AND symbol_id = ?
        """
        position_results = self.execute_query(position_query, (user_id, symbol_id))
        
        if position_results:
            # Update existing position
            position = position_results[0]
            old_quantity = position['quantity']
            old_avg_price = position['avg_price']
            
            new_quantity = old_quantity + quantity_change
            
            if new_quantity > 0:
                # Calculate new average price
                if quantity_change > 0:  # Buy
                    total_cost = (old_quantity * old_avg_price) + (quantity_change * price)
                    new_avg_price = total_cost / new_quantity
                else:  # Sell
                    new_avg_price = old_avg_price
                
                market_value = new_quantity * price
                unrealized_pnl = market_value - (new_quantity * new_avg_price)
                
                update_query = """
                UPDATE positions 
                SET quantity = ?, avg_price = ?, current_price = ?, 
                    market_value = ?, unrealized_pnl = ?, last_updated = unixepoch()
                WHERE uid = ?
                """
                params = (new_quantity, new_avg_price, price, market_value, 
                         unrealized_pnl, position['uid'])
            else:
                # Position closed, remove it
                update_query = "DELETE FROM positions WHERE uid = ?"
                params = (position['uid'],)
            
            return self.execute_update(update_query, params) > 0
        
        elif quantity_change > 0:
            # Create new position
            uid = self.generate_uid('pos')
            market_value = quantity_change * price
            
            insert_query = """
            INSERT INTO positions 
            (uid, user_id, symbol_id, quantity, avg_price, current_price, 
             market_value, unrealized_pnl)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (uid, user_id, symbol_id, quantity_change, price, price, 
                     market_value, 0.0)
            
            return self.execute_update(insert_query, params) > 0
        
        return True
    
    def get_user_positions(self, user_uid: str) -> List[Dict[str, Any]]:
        """Get current positions for a user."""
        query = """
        SELECT p.*, s.symbol, s.name as company_name
        FROM positions p
        JOIN symbols s ON p.symbol_id = s.id
        JOIN users u ON p.user_id = u.id
        WHERE u.uid = ? AND p.quantity > 0
        ORDER BY p.market_value DESC
        """
        
        results = self.execute_query(query, (user_uid,))
        
        # Convert timestamps
        for row in results:
            row['last_updated'] = datetime.fromtimestamp(row['last_updated'])
        
        return results
    
    def get_portfolio_summary(self, user_uid: str) -> Optional[Dict[str, Any]]:
        """
        Get portfolio summary for a user.
        
        Args:
            user_uid: User UID
            
        Returns:
            Portfolio summary data
        """
        user_query = "SELECT username FROM users WHERE uid = ?"
        user_results = self.execute_query(user_query, (user_uid,))
        if not user_results:
            return None
        username = user_results[0]['username']
        
        query = """
        SELECT 
            COUNT(p.uid) as total_positions,
            COALESCE(SUM(p.market_value), 0) as total_value,
            COALESCE(SUM(p.unrealized_pnl), 0) as total_unrealized_pnl,
            COALESCE(SUM(p.realized_pnl), 0) as total_realized_pnl
        FROM users u
        LEFT JOIN positions p ON u.id = p.user_id
        WHERE u.uid = ?
        GROUP BY u.id, u.username
        """
        
        results = self.execute_query(query, (user_uid,))
        
        if results:
            summary = results[0]
            summary['username'] = username
            return summary
        
        return {
            'username': username,
            'total_positions': 0,
            'total_value': 0.0,
            'total_unrealized_pnl': 0.0,
            'total_realized_pnl': 0.0
        } 