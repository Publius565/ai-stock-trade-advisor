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
    
    def get_symbol_id(self, symbol: str) -> Optional[int]:
        """Get symbol ID by symbol string."""
        query = "SELECT id FROM symbols WHERE symbol = ?"
        results = self.execute_query(query, (symbol,))
        return results[0]['id'] if results else None
    
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
        Get symbol statistics.
        
        Returns:
            Dictionary with symbol statistics
        """
        stats = {}
        
        # Total symbols
        total_query = "SELECT COUNT(*) as total FROM symbols"
        total_result = self.execute_query(total_query)
        stats['total_symbols'] = total_result[0]['total'] if total_result else 0
        
        # Active symbols
        active_query = "SELECT COUNT(*) as active FROM symbols WHERE is_active = 1"
        active_result = self.execute_query(active_query)
        stats['active_symbols'] = active_result[0]['active'] if active_result else 0
        
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
    
    # ============================================================================
    # WATCHLIST MANAGEMENT
    # ============================================================================
    
    def create_watchlist(self, user_id: int, name: str, 
                        description: str = None, is_default: bool = False) -> Optional[str]:
        """
        Create a new watchlist for user.
        
        Args:
            user_id: User ID
            name: Watchlist name
            description: Watchlist description
            is_default: Whether this is the default watchlist
            
        Returns:
            Watchlist UID if successful, None otherwise
        """
        uid = self.generate_uid('wl')
        
        # Get next available ID
        id_query = "SELECT COALESCE(MAX(id), 0) + 1 as next_id FROM watchlists"
        id_result = self.execute_query(id_query)
        next_id = id_result[0]['next_id'] if id_result else 1
        
        query = """
        INSERT INTO watchlists (uid, id, user_id, name, description, is_default)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        
        try:
            self.execute_update(query, (uid, next_id, user_id, name, description, is_default))
            logger.info(f"Created watchlist: {name} ({uid})")
            return uid
        except Exception as e:
            logger.error(f"Failed to create watchlist {name}: {e}")
            return None
    
    def add_symbol_to_watchlist(self, watchlist_uid: str, symbol_uid: str, 
                               priority: int = 0, notes: str = None) -> bool:
        """
        Add symbol to watchlist.
        
        Args:
            watchlist_uid: Watchlist UID
            symbol_uid: Symbol UID
            priority: User-defined priority (0-10)
            notes: User notes about symbol
            
        Returns:
            True if successful
        """
        # Get watchlist and symbol IDs
        watchlist_query = "SELECT id FROM watchlists WHERE uid = ?"
        watchlist_result = self.execute_query(watchlist_query, (watchlist_uid,))
        if not watchlist_result:
            return False
        watchlist_id = watchlist_result[0]['id']
        
        symbol_query = "SELECT id FROM symbols WHERE uid = ?"
        symbol_result = self.execute_query(symbol_query, (symbol_uid,))
        if not symbol_result:
            return False
        symbol_id = symbol_result[0]['id']
        
        # Create watchlist symbol entry
        uid = self.generate_uid('wls')
        
        # Get next available ID
        id_query = "SELECT COALESCE(MAX(id), 0) + 1 as next_id FROM watchlist_symbols"
        id_result = self.execute_query(id_query)
        next_id = id_result[0]['next_id'] if id_result else 1
        
        query = """
        INSERT INTO watchlist_symbols (uid, id, watchlist_id, symbol_id, priority, notes)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        
        try:
            self.execute_update(query, (uid, next_id, watchlist_id, symbol_id, priority, notes))
            logger.info(f"Added symbol to watchlist: {watchlist_uid}")
            return True
        except Exception as e:
            logger.error(f"Failed to add symbol to watchlist: {e}")
            return False
    
    def get_user_watchlists(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all watchlists for user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of watchlist data
        """
        query = """
        SELECT w.*, COUNT(ws.id) as symbol_count
        FROM watchlists w
        LEFT JOIN watchlist_symbols ws ON w.id = ws.watchlist_id
        WHERE w.user_id = ? AND w.is_active = 1
        GROUP BY w.id
        ORDER BY w.is_default DESC, w.created_at DESC
        """
        
        return self.execute_query(query, (user_id,))
    
    def get_watchlist_symbols(self, watchlist_uid: str) -> List[Dict[str, Any]]:
        """
        Get all symbols in a watchlist.
        
        Args:
            watchlist_uid: Watchlist UID
            
        Returns:
            List of symbol data with watchlist metadata
        """
        query = """
        SELECT s.*, ws.priority, ws.notes, ws.added_at
        FROM watchlist_symbols ws
        JOIN symbols s ON ws.symbol_id = s.id
        JOIN watchlists w ON ws.watchlist_id = w.id
        WHERE w.uid = ?
        ORDER BY ws.priority DESC, s.symbol
        """
        
        return self.execute_query(query, (watchlist_uid,))
    
    def remove_symbol_from_watchlist(self, watchlist_uid: str, symbol_uid: str) -> bool:
        """
        Remove symbol from watchlist.
        
        Args:
            watchlist_uid: Watchlist UID
            symbol_uid: Symbol UID
            
        Returns:
            True if successful
        """
        query = """
        DELETE FROM watchlist_symbols 
        WHERE watchlist_id = (SELECT id FROM watchlists WHERE uid = ?)
        AND symbol_id = (SELECT id FROM symbols WHERE uid = ?)
        """
        
        return self.execute_update(query, (watchlist_uid, symbol_uid)) > 0
    
    def delete_watchlist(self, watchlist_uid: str) -> bool:
        """
        Delete a watchlist and all its symbols.
        
        Args:
            watchlist_uid: Watchlist UID
            
        Returns:
            True if successful
        """
        # First delete all symbols in the watchlist
        symbol_delete_query = """
        DELETE FROM watchlist_symbols 
        WHERE watchlist_id = (SELECT id FROM watchlists WHERE uid = ?)
        """
        self.execute_update(symbol_delete_query, (watchlist_uid,))
        
        # Then delete the watchlist
        watchlist_delete_query = "DELETE FROM watchlists WHERE uid = ?"
        return self.execute_update(watchlist_delete_query, (watchlist_uid,)) > 0
    
    # ============================================================================
    # NEWS AND MARKET MOVERS
    # ============================================================================
    
    def store_market_mover(self, symbol_uid: str, change_percent: float, 
                          volume: int = None, price: float = None,
                          market_cap: float = None, sector: str = None) -> bool:
        """
        Store market mover data.
        
        Args:
            symbol_uid: Symbol UID
            change_percent: Percentage change
            volume: Trading volume
            price: Current price
            market_cap: Market capitalization
            sector: Industry sector
            
        Returns:
            True if successful
        """
        # Get symbol ID
        symbol_query = "SELECT id FROM symbols WHERE uid = ?"
        symbol_result = self.execute_query(symbol_query, (symbol_uid,))
        if not symbol_result:
            return False
        symbol_id = symbol_result[0]['id']
        
        # Store market mover data
        uid = self.generate_uid('mm')
        
        # Get next available ID
        id_query = "SELECT COALESCE(MAX(id), 0) + 1 as next_id FROM market_movers"
        id_result = self.execute_query(id_query)
        next_id = id_result[0]['next_id'] if id_result else 1
        
        # Determine mover type based on change percentage
        mover_type = 'gainer' if change_percent > 0 else 'loser'
        
        # Calculate price change (simplified)
        price_change = change_percent * (price or 100) / 100 if price else 0
        
        query = """
        INSERT INTO market_movers (uid, id, symbol_id, date, change_percent, 
                                  price_change, mover_type, created_at)
        VALUES (?, ?, ?, unixepoch(), ?, ?, ?, unixepoch())
        """
        
        try:
            self.execute_update(query, (uid, next_id, symbol_id, change_percent, 
                                       price_change, mover_type))
            return True
        except Exception as e:
            logger.error(f"Failed to store market mover: {e}")
            return False
    
    def store_news_article(self, symbol_uid: str, title: str, summary: str,
                          url: str, published_at: str, source: str,
                          sentiment: str = 'neutral', relevance_score: float = 0.5) -> bool:
        """
        Store news article data.
        
        Args:
            symbol_uid: Symbol UID
            title: Article title
            summary: Article summary
            url: Article URL
            published_at: Publication timestamp
            source: News source
            sentiment: Sentiment analysis result
            relevance_score: Relevance score (0-1)
            
        Returns:
            True if successful
        """
        # Get symbol ID
        symbol_query = "SELECT id FROM symbols WHERE uid = ?"
        symbol_result = self.execute_query(symbol_query, (symbol_uid,))
        if not symbol_result:
            return False
        symbol_id = symbol_result[0]['id']
        
        # Store news article
        uid = self.generate_uid('news')
        
        # Get next available ID
        id_query = "SELECT COALESCE(MAX(id), 0) + 1 as next_id FROM news_articles"
        id_result = self.execute_query(id_query)
        next_id = id_result[0]['next_id'] if id_result else 1
        
        query = """
        INSERT INTO news_articles (uid, id, symbol_id, title, summary, url, 
                                  published_at, source, sentiment, relevance_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        try:
            self.execute_update(query, (uid, next_id, symbol_id, title, summary, url,
                                       published_at, source, sentiment, relevance_score))
            return True
        except Exception as e:
            logger.error(f"Failed to store news article: {e}")
            return False 