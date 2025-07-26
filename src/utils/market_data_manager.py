"""
Market Data Database Manager

Handles all market data-related database operations including symbols,
market data storage, indicators, and news integration.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from .base_manager import BaseDatabaseManager

logger = logging.getLogger(__name__)


class MarketDataManager(BaseDatabaseManager):
    """
    Specialized manager for market data operations.
    
    Features:
    - Symbol management
    - Market data storage and retrieval
    - Technical indicators
    - News and market movers
    """
    
    def get_manager_type(self) -> str:
        """Return the type of manager for logging."""
        return "MarketDataManager"
    
    def get_or_create_symbol(self, symbol: str, name: str = None, 
                           sector: str = None) -> Optional[str]:
        """
        Get existing symbol or create new one.
        
        Args:
            symbol: Stock symbol
            name: Company name
            sector: Industry sector
            
        Returns:
            Symbol UID
        """
        # Check if symbol exists
        query = "SELECT uid FROM symbols WHERE symbol = ?"
        results = self.execute_query(query, (symbol,))
        
        if results:
            return results[0]['uid']
        
        # Create new symbol
        uid = self.generate_uid('sym')
        
        # Get next available ID
        id_query = "SELECT COALESCE(MAX(id), 0) + 1 as next_id FROM symbols"
        id_result = self.execute_query(id_query)
        next_id = id_result[0]['next_id'] if id_result else 1
        
        query = """
        INSERT INTO symbols (uid, id, symbol, name, sector)
        VALUES (?, ?, ?, ?, ?)
        """
        
        try:
            self.execute_update(query, (uid, next_id, symbol, name, sector))
            logger.info(f"Created symbol: {symbol} ({uid})")
            return uid
        except Exception as e:
            logger.error(f"Failed to create symbol {symbol}: {e}")
            return None
    
    def get_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get symbol data by symbol string."""
        query = "SELECT * FROM symbols WHERE symbol = ?"
        results = self.execute_query(query, (symbol,))
        return results[0] if results else None
    
    def store_market_data(self, symbol: str, data_points: List[Dict[str, Any]]) -> bool:
        """
        Store market data for a symbol.
        
        Args:
            symbol: Stock symbol
            data_points: List of OHLCV data points
            
        Returns:
            True if successful
        """
        # Get or create symbol and get its ID
        symbol_data = self.get_symbol(symbol)
        if not symbol_data:
            symbol_uid = self.get_or_create_symbol(symbol)
            if not symbol_uid:
                return False
            symbol_data = self.get_symbol(symbol)
        
        symbol_id = symbol_data['id']
        
        queries = []
        for data in data_points:
            uid = self.generate_uid('mkt')
            
            # Get next available ID
            id_query = "SELECT COALESCE(MAX(id), 0) + 1 as next_id FROM market_data"
            id_result = self.execute_query(id_query)
            next_id = id_result[0]['next_id'] if id_result else 1
            
            # Handle both string and datetime objects
            if isinstance(data['date'], str):
                date_ts = int(datetime.fromisoformat(data['date']).timestamp())
            else:
                date_ts = int(data['date'].timestamp())
            
            query = """
            INSERT OR REPLACE INTO market_data 
            (uid, id, symbol_id, date, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (uid, next_id, symbol_id, date_ts, data['open'], data['high'], 
                     data['low'], data['close'], data['volume'])
            queries.append((query, params))
        
        return self.execute_transaction(queries)
    
    def get_market_data(self, symbol: str, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get market data for a symbol.
        
        Args:
            symbol: Stock symbol
            days: Number of days to retrieve
            
        Returns:
            List of market data points
        """
        symbol_data = self.get_symbol(symbol)
        if not symbol_data:
            return []
        
        cutoff_date = int((datetime.now() - timedelta(days=days)).timestamp())
        
        query = """
        SELECT md.*, s.symbol, s.name
        FROM market_data md
        JOIN symbols s ON md.symbol_id = s.id
        WHERE s.symbol = ? AND md.date >= ?
        ORDER BY md.date DESC
        """
        
        results = self.execute_query(query, (symbol, cutoff_date))
        
        # Convert timestamps back to dates
        for row in results:
            row['date'] = datetime.fromtimestamp(row['date']).strftime('%Y-%m-%d')
        
        return results
    
    def store_indicator_data(self, symbol: str, indicator_type: str, 
                           data_points: List[Dict[str, Any]]) -> bool:
        """
        Store technical indicator data.
        
        Args:
            symbol: Stock symbol
            indicator_type: Type of indicator (sma, ema, rsi, etc.)
            data_points: List of indicator data points
            
        Returns:
            True if successful
        """
        symbol_data = self.get_symbol(symbol)
        if not symbol_data:
            return False
        
        symbol_id = symbol_data['id']
        queries = []
        
        for data in data_points:
            uid = self.generate_uid('ind')
            # Handle both string and datetime objects
            if isinstance(data['date'], str):
                date_ts = int(datetime.fromisoformat(data['date']).timestamp())
            else:
                date_ts = int(data['date'].timestamp())
            
            query = """
            INSERT OR REPLACE INTO indicators 
            (uid, symbol_id, date, indicator_type, value, params)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            params = (uid, symbol_id, date_ts, indicator_type, 
                     data['value'], data.get('params'))
            queries.append((query, params))
        
        return self.execute_transaction(queries)
    
    def get_indicator_data(self, symbol: str, indicator_type: str, 
                          days: int = 30) -> List[Dict[str, Any]]:
        """
        Get technical indicator data.
        
        Args:
            symbol: Stock symbol
            indicator_type: Type of indicator
            days: Number of days to retrieve
            
        Returns:
            List of indicator data points
        """
        symbol_data = self.get_symbol(symbol)
        if not symbol_data:
            return []
        
        cutoff_date = int((datetime.now() - timedelta(days=days)).timestamp())
        
        query = """
        SELECT i.*, s.symbol, s.name
        FROM indicators i
        JOIN symbols s ON i.symbol_id = s.id
        WHERE s.symbol = ? AND i.indicator_type = ? AND i.date >= ?
        ORDER BY i.date DESC
        """
        
        results = self.execute_query(query, (symbol, indicator_type, cutoff_date))
        
        # Convert timestamps back to dates
        for row in results:
            row['date'] = datetime.fromtimestamp(row['date']).strftime('%Y-%m-%d')
        
        return results
    
    def store_market_movers(self, movers_data: List[Dict[str, Any]]) -> bool:
        """
        Store market movers data.
        
        Args:
            movers_data: List of market mover data points
            
        Returns:
            True if successful
        """
        queries = []
        
        for data in movers_data:
            # Get or create symbol
            symbol_uid = self.get_or_create_symbol(data['symbol'], data.get('name'))
            if not symbol_uid:
                continue
            
            symbol_data = self.get_symbol(data['symbol'])
            symbol_id = symbol_data['id']
            
            uid = self.generate_uid('mv')
            
            query = """
            INSERT OR REPLACE INTO market_movers 
            (uid, symbol_id, date, change_percent, volume_change_percent, 
             price_change, mover_type, rank)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            date_ts = int(datetime.now().timestamp()) if 'date' not in data else int(data['date'].timestamp())
            
            params = (uid, symbol_id, date_ts, data['change_percent'],
                     data.get('volume_change_percent'), data['price_change'],
                     data['mover_type'], data.get('rank'))
            queries.append((query, params))
        
        return self.execute_transaction(queries)
    
    def get_top_movers(self, mover_type: str = 'gainer', limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get top market movers.
        
        Args:
            mover_type: Type of movers ('gainer', 'loser', 'volume')
            limit: Number of results to return
            
        Returns:
            List of market mover data
        """
        query = """
        SELECT mm.*, s.symbol, s.name
        FROM market_movers mm
        JOIN symbols s ON mm.symbol_id = s.id
        WHERE mm.mover_type = ?
        ORDER BY mm.date DESC, mm.rank ASC
        LIMIT ?
        """
        
        results = self.execute_query(query, (mover_type, limit))
        
        # Convert timestamps back to dates
        for row in results:
            row['date'] = datetime.fromtimestamp(row['date']).strftime('%Y-%m-%d')
        
        return results
    
    def get_symbol_statistics(self) -> Dict[str, Any]:
        """
        Get symbol and market data statistics.
        
        Returns:
            Dictionary with statistics
        """
        stats = {}
        
        # Total symbols
        total_query = "SELECT COUNT(*) as total FROM symbols WHERE is_active = 1"
        total_result = self.execute_query(total_query)
        stats['total_symbols'] = total_result[0]['total'] if total_result else 0
        
        # Market data points count
        data_query = "SELECT COUNT(*) as total FROM market_data"
        data_result = self.execute_query(data_query)
        stats['market_data_points'] = data_result[0]['total'] if data_result else 0
        
        # Indicators count
        indicators_query = "SELECT COUNT(*) as total FROM indicators"
        indicators_result = self.execute_query(indicators_query)
        stats['indicator_points'] = indicators_result[0]['total'] if indicators_result else 0
        
        # Sector distribution
        sector_query = """
        SELECT sector, COUNT(*) as count 
        FROM symbols 
        WHERE is_active = 1 AND sector IS NOT NULL
        GROUP BY sector
        ORDER BY count DESC
        """
        sector_results = self.execute_query(sector_query)
        stats['sector_distribution'] = {row['sector']: row['count'] for row in sector_results}
        
        return stats 