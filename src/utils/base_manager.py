"""
Base Database Manager

Provides common database operations and connection management.
"""

import sqlite3
import uuid
import logging
import threading
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseDatabaseManager(ABC):
    """
    Abstract base class for database managers.
    
    Provides common functionality:
    - Connection management with thread safety
    - UID generation
    - Basic query execution
    - Transaction management
    """
    
    def __init__(self, db_path: str = "data/trading_advisor.db"):
        """
        Initialize base database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Connection management
        self._connection = None
        
        # Initialize database if needed
        self._ensure_database_exists()
        
        logger.info(f"Base database manager initialized: {self.db_path}")
    
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
    
    def _ensure_database_exists(self):
        """Ensure database schema exists."""
        # Try multiple possible schema file locations, prioritize optimized schema
        script_dir = Path(__file__).parent.parent.parent
        schema_paths = [
            script_dir / "config" / "optimized_database_schema.sql",
            Path("config/optimized_database_schema.sql"),
            script_dir / "config" / "database_schema.sql",
            Path("config/database_schema.sql")
        ]
        
        schema_path = None
        for path in schema_paths:
            if path.exists():
                schema_path = path
                logger.info(f"Found schema file: {schema_path}")
                break
        
        if schema_path and schema_path.exists():
            with self._lock:
                conn = self._get_connection()
                
                # Check if symbols table exists (from optimized schema)
                check_query = "SELECT name FROM sqlite_master WHERE type='table' AND name='symbols'"
                cursor = conn.execute(check_query)
                tables_exist = cursor.fetchone() is not None
                
                if not tables_exist:
                    # Read and execute schema
                    with open(schema_path, 'r') as f:
                        schema_sql = f.read()
                    
                    conn.executescript(schema_sql)
                    conn.commit()
                    logger.info(f"Database schema initialized from {schema_path}")
                else:
                    logger.debug("Database schema already exists")
        else:
            logger.warning(f"Schema file not found in any of these locations: {schema_paths}")
    
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
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
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
    
    @abstractmethod
    def get_manager_type(self) -> str:
        """Return the type of manager for logging."""
        pass 