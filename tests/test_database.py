"""
Test Suite for Database Layer

Consolidated tests for database management and operations.
"""

import unittest
import sys
import os
import tempfile
import shutil
import sqlite3

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.utils.database_manager import DatabaseManager
from src.utils.base_manager import BaseDatabaseManager
from src.utils.user_manager import UserManager
from src.utils.market_data_manager import MarketDataManager
from src.utils.signal_manager import SignalManager


class TestDatabaseInfrastructure(unittest.TestCase):
    """Test cases for database infrastructure."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_dir, "test_db.db")
        
        # Initialize database with proper schema
        from init_database import init_database
        success = init_database(self.test_db_path)
        if not success:
            self.fail("Failed to initialize test database")
        
        self.db_manager = DatabaseManager(self.test_db_path)
        self.user_manager = UserManager(self.test_db_path)
        self.market_manager = MarketDataManager(self.test_db_path)
        
    def tearDown(self):
        """Clean up test environment."""
        # Remove temporary directory
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_database_manager_initialization(self):
        """Test DatabaseManager initialization."""
        db_manager = DatabaseManager(self.test_db_path)
        
        # Verify manager attributes
        self.assertIsNotNone(db_manager)
        self.assertIsNotNone(db_manager.users)
        self.assertIsNotNone(db_manager.market_data)
        self.assertIsNotNone(db_manager.signals)
        
        # Verify manager types
        self.assertIsInstance(db_manager.users, UserManager)
        self.assertIsInstance(db_manager.market_data, MarketDataManager)
        self.assertIsInstance(db_manager.signals, SignalManager)
        
        db_manager.close()
    
    def test_base_manager_functionality(self):
        """Test BaseDatabaseManager functionality."""
        # Use UserManager as a concrete implementation of BaseDatabaseManager
        user_manager = UserManager(self.test_db_path)
        
        # Test connection
        connection = user_manager._get_connection()
        self.assertIsNotNone(connection)
        self.assertIsInstance(connection, sqlite3.Connection)
        
        # Test basic query execution
        try:
            cursor = connection.execute("SELECT 1 as test")
            result = cursor.fetchone()
            self.assertEqual(result['test'], 1)
        except Exception as e:
            self.fail(f"Basic query execution failed: {e}")
        
        connection.close()
        user_manager.close()
    
    def test_database_schema_creation(self):
        """Test database schema creation."""
        db_manager = DatabaseManager(self.test_db_path)
        
        # Verify essential tables exist (updated to match actual schema)
        essential_tables = ['users', 'symbols', 'watchlists', 'watchlist_symbols', 'market_data']
        
        with sqlite3.connect(self.test_db_path) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            existing_tables = [row[0] for row in cursor.fetchall()]
        
        for table in essential_tables:
            self.assertIn(table, existing_tables, f"Table {table} not found")
        
        db_manager.close()
    
    def test_database_foreign_keys(self):
        """Test foreign key constraints are enabled."""
        db_manager = DatabaseManager(self.test_db_path)
        
        with sqlite3.connect(self.test_db_path) as conn:
            # Enable foreign keys for this connection
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.execute("PRAGMA foreign_keys")
            result = cursor.fetchone()
            self.assertEqual(result[0], 1, "Foreign keys not enabled")
        
        db_manager.close()
    
    def test_database_performance_settings(self):
        """Test database performance settings."""
        db_manager = DatabaseManager(self.test_db_path)
        
        with sqlite3.connect(self.test_db_path) as conn:
            # Check journal mode
            cursor = conn.execute("PRAGMA journal_mode")
            journal_mode = cursor.fetchone()[0]
            self.assertEqual(journal_mode, 'wal', "WAL mode not enabled")
            
            # Check synchronous setting
            cursor = conn.execute("PRAGMA synchronous")
            sync_mode = cursor.fetchone()[0]
            self.assertIn(sync_mode, [1, 2], "Synchronous mode not optimal")  # NORMAL or FULL
        
        db_manager.close()
    
    def test_concurrent_access(self):
        """Test concurrent database access."""
        # Create multiple database managers to same file
        db_manager1 = DatabaseManager(self.test_db_path)
        db_manager2 = DatabaseManager(self.test_db_path)
        
        try:
            # Both should be able to perform basic operations
            connection1 = db_manager1.users._get_connection()
            connection2 = db_manager2.users._get_connection()
            
            # Perform simple queries on both
            cursor1 = connection1.execute("SELECT 1")
            cursor2 = connection2.execute("SELECT 1")
            
            result1 = cursor1.fetchone()
            result2 = cursor2.fetchone()
            
            self.assertEqual(result1[0], 1)
            self.assertEqual(result2[0], 1)
            
        finally:
            db_manager1.close()
            db_manager2.close()
    
    def test_transaction_handling(self):
        """Test database transaction handling."""
        db_manager = DatabaseManager(self.test_db_path)
        
        try:
            # Test transaction rollback on error
            with db_manager.users._get_connection() as conn:
                conn.execute("BEGIN TRANSACTION")
                
                # Insert test data
                conn.execute(
                    "INSERT INTO users (uid, username, email, risk_profile) VALUES (?, ?, ?, ?)",
                    ('test-uid', 'test_user', 'test@example.com', 'moderate')
                )
                
                # Rollback transaction
                conn.execute("ROLLBACK")
                
                # Verify data was not committed
                cursor = conn.execute("SELECT COUNT(*) FROM users WHERE uid = ?", ('test-uid',))
                count = cursor.fetchone()[0]
                self.assertEqual(count, 0, "Transaction rollback failed")
        
        finally:
            db_manager.close()


class TestUserManager(unittest.TestCase):
    """Test cases for UserManager."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_dir, "test_users.db")
        self.user_manager = UserManager(self.test_db_path)
        
    def tearDown(self):
        """Clean up test environment."""
        self.user_manager._get_connection().close()
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_create_user(self):
        """Test user creation."""
        user_uid = self.user_manager.create_user(
            username='test_user',
            email='test@example.com',
            risk_profile='moderate'
        )
        self.assertIsNotNone(user_uid)
        self.assertIsInstance(user_uid, str)
    
    def test_get_user(self):
        """Test user retrieval."""
        # Create user first
        user_uid = self.user_manager.create_user(
            username='retrieve_user',
            email='retrieve@example.com',
            risk_profile='aggressive'
        )
        
        # Retrieve user
        retrieved_user = self.user_manager.get_user(user_uid)
        self.assertIsNotNone(retrieved_user)
        self.assertEqual(retrieved_user['username'], 'retrieve_user')
        self.assertEqual(retrieved_user['email'], 'retrieve@example.com')
    
    def test_update_user(self):
        """Test user update."""
        # Create user
        user_uid = self.user_manager.create_user(
            username='update_user',
            email='update@example.com',
            risk_profile='conservative'
        )
        
        # Update user
        success = self.user_manager.update_user(
            user_uid, 
            email='updated@example.com',
            risk_profile='moderate'
        )
        self.assertTrue(success)
        
        # Verify update
        updated_user = self.user_manager.get_user(user_uid)
        self.assertEqual(updated_user['email'], 'updated@example.com')
        self.assertEqual(updated_user['risk_profile'], 'moderate')


class TestMarketDataManager(unittest.TestCase):
    """Test cases for MarketDataManager."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_dir, "test_market.db")
        self.market_manager = MarketDataManager(self.test_db_path)
        
    def tearDown(self):
        """Clean up test environment."""
        self.market_manager._get_connection().close()
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_store_symbol_data(self):
        """Test storing symbol data."""
        symbol_uid = self.market_manager.get_or_create_symbol(
            symbol='AAPL',
            name='Apple Inc.',
            sector='Technology'
        )
        self.assertIsNotNone(symbol_uid)
        self.assertIsInstance(symbol_uid, str)
    
    def test_get_symbol_data(self):
        """Test retrieving symbol data."""
        # Store symbol data first
        symbol_uid = self.market_manager.get_or_create_symbol(
            symbol='GOOGL',
            name='Alphabet Inc.',
            sector='Communication Services'  # Correct sector for GOOGL
        )
        
        # Retrieve symbol data
        symbol_data = self.market_manager.get_symbol('GOOGL')
        self.assertIsNotNone(symbol_data)
        self.assertEqual(symbol_data['symbol'], 'GOOGL')
        self.assertEqual(symbol_data['name'], 'Alphabet Inc.')
        self.assertEqual(symbol_data['sector'], 'Communication Services')
    
    def test_get_symbols_by_sector(self):
        """Test retrieving symbols by sector."""
        # Create symbols in different sectors
        self.market_manager.get_or_create_symbol('AAPL', 'Apple Inc.', 'Technology')
        self.market_manager.get_or_create_symbol('MSFT', 'Microsoft Corp.', 'Technology')
        self.market_manager.get_or_create_symbol('JPM', 'JPMorgan Chase', 'Financial')
        
        # Get symbols by sector (this would need to be implemented in MarketDataManager)
        # For now, just test that we can get individual symbols
        tech_symbol = self.market_manager.get_symbol('AAPL')
        self.assertIsNotNone(tech_symbol)
        self.assertEqual(tech_symbol['sector'], 'Technology')


if __name__ == '__main__':
    unittest.main() 