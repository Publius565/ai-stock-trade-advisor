"""
Database Manager for AI-Driven Stock Trade Advisor

Provides efficient database operations with the optimized schema.
Handles UID generation, connection management, and common queries.
"""

import sqlite3
import uuid
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import threading

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Optimized database manager for the trading advisor.
    
    Features:
    - UID-based object identification
    - Connection pooling and thread safety
    - Optimized queries with proper indexing
    - Transaction management
    - Data validation and integrity checks
    """
    
    def __init__(self, db_path: str = "data/trading_advisor.db"):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Connection management
        self._connection = None
        
        # Initialize database
        self._initialize_database()
        
        logger.info(f"Database manager initialized: {self.db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with proper configuration."""
        if self._connection is None:
            self._connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0
            )
            
            # Configure connection for performance
            self._connection.execute("PRAGMA foreign_keys = ON")
            self._connection.execute("PRAGMA journal_mode = WAL")
            self._connection.execute("PRAGMA synchronous = NORMAL")
            self._connection.execute("PRAGMA cache_size = 10000")
            self._connection.execute("PRAGMA temp_store = MEMORY")
            
            # Enable row factory for dict-like access
            self._connection.row_factory = sqlite3.Row
        
        return self._connection
    
    def _initialize_database(self):
        """Initialize database schema and initial data."""
        schema_path = Path("config/optimized_database_schema.sql")
        
        if not schema_path.exists():
            logger.error(f"Database schema not found: {schema_path}")
            raise FileNotFoundError(f"Database schema not found: {schema_path}")
        
        with self._lock:
            conn = self._get_connection()
            
            # Read and execute schema
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
            
            conn.executescript(schema_sql)
            conn.commit()
            
            logger.info("Database schema initialized successfully")
    
    def generate_uid(self, prefix: str = "obj") -> str:
        """
        Generate a unique identifier for database objects.
        
        Args:
            prefix: Prefix for the UID (e.g., 'user', 'trade', 'signal')
            
        Returns:
            Unique identifier string
        """
        unique_id = str(uuid.uuid4()).replace('-', '')[:12]
        return f"{prefix}_{unique_id}"
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query and return results as dictionaries.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            List of dictionaries representing rows
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """
        Execute an INSERT, UPDATE, or DELETE query.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Number of affected rows
        """
        with self._lock:
            conn = self._get_connection()
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.rowcount
    
    def execute_transaction(self, queries: List[Tuple[str, tuple]]) -> bool:
        """
        Execute multiple queries in a transaction.
        
        Args:
            queries: List of (query, params) tuples
            
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            conn = self._get_connection()
            try:
                for query, params in queries:
                    conn.execute(query, params)
                conn.commit()
                return True
            except Exception as e:
                conn.rollback()
                logger.error(f"Transaction failed: {e}")
                return False
    
    # ============================================================================
    # USER MANAGEMENT
    # ============================================================================
    
    def create_user(self, username: str, email: str = None, 
                   risk_profile: str = 'moderate') -> Optional[str]:
        """
        Create a new user.
        
        Args:
            username: Unique username
            email: User email
            risk_profile: Risk tolerance level
            
        Returns:
            User UID if successful, None otherwise
        """
        uid = self.generate_uid('user')
        
        query = """
        INSERT INTO users (uid, username, email, risk_profile)
        VALUES (?, ?, ?, ?)
        """
        
        try:
            self.execute_update(query, (uid, username, email, risk_profile))
            logger.info(f"Created user: {username} ({uid})")
            return uid
        except sqlite3.IntegrityError as e:
            logger.error(f"Failed to create user {username}: {e}")
            return None
    
    def get_user(self, uid: str = None, username: str = None) -> Optional[Dict[str, Any]]:
        """
        Get user by UID or username.
        
        Args:
            uid: User UID
            username: Username
            
        Returns:
            User data dictionary or None
        """
        if uid:
            query = "SELECT * FROM users WHERE uid = ?"
            params = (uid,)
        elif username:
            query = "SELECT * FROM users WHERE username = ?"
            params = (username,)
        else:
            return None
        
        results = self.execute_query(query, params)
        return results[0] if results else None
    
    def update_user(self, uid: str, **kwargs) -> bool:
        """
        Update user data.
        
        Args:
            uid: User UID
            **kwargs: Fields to update
            
        Returns:
            True if successful
        """
        if not kwargs:
            return False
        
        # Build dynamic update query
        fields = []
        values = []
        for key, value in kwargs.items():
            if key in ['risk_profile', 'max_position_pct', 'stop_loss_pct', 
                      'take_profit_pct', 'is_active']:
                fields.append(f"{key} = ?")
                values.append(value)
        
        if not fields:
            return False
        
        values.append(self.generate_uid())  # updated_at
        values.append(uid)
        
        query = f"""
        UPDATE users 
        SET {', '.join(fields)}, updated_at = ?
        WHERE uid = ?
        """
        
        return self.execute_update(query, tuple(values)) > 0
    
    # ============================================================================
    # SYMBOL MANAGEMENT
    # ============================================================================
    
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
        query = """
        INSERT INTO symbols (uid, symbol, name, sector)
        VALUES (?, ?, ?, ?)
        """
        
        try:
            self.execute_update(query, (uid, symbol, name, sector))
            logger.info(f"Created symbol: {symbol} ({uid})")
            return uid
        except sqlite3.IntegrityError as e:
            logger.error(f"Failed to create symbol {symbol}: {e}")
            return None
    
    def get_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get symbol data by symbol string."""
        query = "SELECT * FROM symbols WHERE symbol = ?"
        results = self.execute_query(query, (symbol,))
        return results[0] if results else None
    
    # ============================================================================
    # MARKET DATA MANAGEMENT
    # ============================================================================
    
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
            date_ts = int(datetime.fromisoformat(data['date']).timestamp())
            
            query = """
            INSERT OR REPLACE INTO market_data 
            (uid, symbol_id, date, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (uid, symbol_id, date_ts, data['open'], data['high'], 
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
    
    # ============================================================================
    # SIGNAL MANAGEMENT
    # ============================================================================
    
    def create_signal(self, user_uid: str, symbol: str, signal_type: str,
                     risk_level: str, confidence: float = None,
                     price_target: float = None, rationale: str = None) -> Optional[str]:
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
            
        Returns:
            Signal UID if successful
        """
        # Get user and symbol IDs
        user_data = self.get_user(uid=user_uid)
        if not user_data:
            logger.error(f"User not found: {user_uid}")
            return None
        
        symbol_data = self.get_symbol(symbol)
        if not symbol_data:
            # Create symbol if it doesn't exist
            symbol_uid = self.get_or_create_symbol(symbol)
            if not symbol_uid:
                logger.error(f"Failed to create symbol: {symbol}")
                return None
            symbol_data = self.get_symbol(symbol)
        
        uid = self.generate_uid('sig')
        
        query = """
        INSERT INTO signals 
        (uid, user_id, symbol_id, signal_type, risk_level, confidence, 
         price_target, rationale, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (uid, user_data['id'], symbol_data['id'], signal_type, 
                 risk_level, confidence, price_target, rationale, 'rule_based')
        
        try:
            self.execute_update(query, params)
            logger.info(f"Created signal: {signal_type} {symbol} for user {user_uid}")
            return uid
        except Exception as e:
            logger.error(f"Failed to create signal: {e}")
            return None
    
    def get_user_signals(self, user_uid: str, active_only: bool = True) -> List[Dict[str, Any]]:
        """
        Get signals for a user.
        
        Args:
            user_uid: User UID
            active_only: Only return active signals
            
        Returns:
            List of signal data
        """
        user_data = self.get_user(uid=user_uid)
        if not user_data:
            return []
        
        if active_only:
            query = """
            SELECT sig.*, s.symbol, s.name
            FROM signals sig
            JOIN symbols s ON sig.symbol_id = s.id
            WHERE sig.user_id = ? AND sig.is_active = 1
            ORDER BY sig.created_at DESC
            """
        else:
            query = """
            SELECT sig.*, s.symbol, s.name
            FROM signals sig
            JOIN symbols s ON sig.symbol_id = s.id
            WHERE sig.user_id = ?
            ORDER BY sig.created_at DESC
            """
        
        results = self.execute_query(query, (user_data['id'],))
        
        # Convert timestamps
        for row in results:
            row['created_at'] = datetime.fromtimestamp(row['created_at'])
            if row['expires_at']:
                row['expires_at'] = datetime.fromtimestamp(row['expires_at'])
        
        return results
    
    # ============================================================================
    # PORTFOLIO MANAGEMENT
    # ============================================================================
    
    def get_user_positions(self, user_uid: str) -> List[Dict[str, Any]]:
        """Get current positions for a user."""
        query = """
        SELECT * FROM v_positions WHERE user_id = ?
        """
        user_data = self.get_user(uid=user_uid)
        if not user_data:
            return []
        
        results = self.execute_query(query, (user_data['id'],))
        
        # Convert timestamps
        for row in results:
            row['last_updated'] = datetime.fromtimestamp(row['last_updated'])
        
        return results
    
    def get_portfolio_summary(self, user_uid: str) -> Optional[Dict[str, Any]]:
        """Get portfolio summary for a user."""
        query = """
        SELECT * FROM v_portfolio_summary WHERE username = ?
        """
        user_data = self.get_user(uid=user_uid)
        if not user_data:
            return None
        
        results = self.execute_query(query, (user_data['username'],))
        return results[0] if results else None
    
    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    def close(self):
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Database connection closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close() 