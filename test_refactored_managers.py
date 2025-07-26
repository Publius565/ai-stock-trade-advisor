#!/usr/bin/env python3
"""
Test script for refactored database managers.

This script tests the new modular database management system to ensure
backward compatibility and proper functionality.
"""

import sys
import logging
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.database_manager import DatabaseManager
from utils.user_manager import UserManager
from utils.market_data_manager import MarketDataManager
from utils.signal_manager import SignalManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_factory_pattern():
    """Test the factory pattern DatabaseManager."""
    logger.info("Testing DatabaseManager factory pattern...")
    
    # Test database path
    test_db = "data/test_refactored.db"
    
    # Remove existing test database
    if os.path.exists(test_db):
        os.remove(test_db)
    
    with DatabaseManager(test_db) as db:
        # Test user creation through factory
        user_uid = db.create_user("test_user", "test@example.com", "moderate")
        assert user_uid is not None, "Failed to create user through factory"
        logger.info(f"✓ Created user through factory: {user_uid}")
        
        # Test getting user
        user = db.get_user(uid=user_uid)
        assert user is not None, "Failed to get user through factory"
        assert user['username'] == "test_user", "User data mismatch"
        logger.info(f"✓ Retrieved user: {user['username']}")
        
        # Test symbol creation through factory
        symbol_uid = db.get_or_create_symbol("AAPL", "Apple Inc.", "Technology")
        assert symbol_uid is not None, "Failed to create symbol through factory"
        logger.info(f"✓ Created symbol through factory: {symbol_uid}")
        
        # Test signal creation through factory
        signal_uid = db.create_signal(user_uid, "AAPL", "buy", "medium", 0.8, 150.0, "Test signal")
        assert signal_uid is not None, "Failed to create signal through factory"
        logger.info(f"✓ Created signal through factory: {signal_uid}")
        
        # Test getting signals
        signals = db.get_user_signals(user_uid)
        assert len(signals) > 0, "Failed to get signals through factory"
        logger.info(f"✓ Retrieved {len(signals)} signal(s)")
        
        logger.info("✓ Factory pattern tests passed!")


def test_specialized_managers():
    """Test the specialized managers directly."""
    logger.info("Testing specialized managers...")
    
    # Test database path
    test_db = "data/test_specialized.db"
    
    # Remove existing test database
    if os.path.exists(test_db):
        os.remove(test_db)
    
    # Test UserManager
    with UserManager(test_db) as user_mgr:
        user_uid = user_mgr.create_user("specialist_user", "specialist@example.com")
        assert user_uid is not None, "Failed to create user with UserManager"
        logger.info(f"✓ UserManager created user: {user_uid}")
        
        # Test user statistics
        stats = user_mgr.get_user_statistics()
        assert stats['total_users'] >= 1, "User statistics incorrect"
        logger.info(f"✓ User statistics: {stats}")
    
    # Test MarketDataManager
    with MarketDataManager(test_db) as market_mgr:
        symbol_uid = market_mgr.get_or_create_symbol("TSLA", "Tesla Inc.", "Automotive")
        assert symbol_uid is not None, "Failed to create symbol with MarketDataManager"
        logger.info(f"✓ MarketDataManager created symbol: {symbol_uid}")
        
        # Test market data storage
        recent_date = (datetime.now() - timedelta(hours=1)).strftime('%Y-%m-%d')
        test_data = [{
            'date': recent_date,
            'open': 100.0,
            'high': 105.0,
            'low': 98.0,
            'close': 103.0,
            'volume': 1000000
        }]
        result = market_mgr.store_market_data("TSLA", test_data)
        assert result is True, "Failed to store market data"
        logger.info("✓ Market data stored successfully")
        
        # Test market data retrieval
        retrieved_data = market_mgr.get_market_data("TSLA", days=1)
        assert len(retrieved_data) > 0, "Failed to retrieve market data"
        logger.info(f"✓ Retrieved {len(retrieved_data)} market data point(s)")
    
    # Test SignalManager
    with SignalManager(test_db) as signal_mgr:
        # Get the user we created earlier
        user_query = "SELECT uid FROM users WHERE username = 'specialist_user'"
        with UserManager(test_db) as user_mgr:
            results = user_mgr.execute_query(user_query)
            user_uid = results[0]['uid'] if results else None
        
        assert user_uid is not None, "User not found for signal test"
        
        signal_uid = signal_mgr.create_signal(user_uid, "TSLA", "buy", "high", 0.9, 200.0, "Test specialist signal")
        assert signal_uid is not None, "Failed to create signal with SignalManager"
        logger.info(f"✓ SignalManager created signal: {signal_uid}")
        
        # Test portfolio summary
        portfolio = signal_mgr.get_portfolio_summary(user_uid)
        assert portfolio is not None, "Failed to get portfolio summary"
        logger.info(f"✓ Portfolio summary: {portfolio}")
        
        logger.info("✓ Specialized manager tests passed!")


def test_backward_compatibility():
    """Test that existing code still works with the refactored managers."""
    logger.info("Testing backward compatibility...")
    
    # Test database path
    test_db = "data/test_backward_compat.db"
    
    # Remove existing test database
    if os.path.exists(test_db):
        os.remove(test_db)
    
    # This simulates how existing code would use the DatabaseManager
    db = DatabaseManager(test_db)
    
    try:
        # Test the same operations as existing code would
        user_uid = db.create_user("legacy_user", "legacy@example.com")
        user = db.get_user(uid=user_uid)
        
        symbol_uid = db.get_or_create_symbol("MSFT", "Microsoft Corp.")
        symbol = db.get_symbol("MSFT")
        
        signal_uid = db.create_signal(user_uid, "MSFT", "buy", "low", 0.7, 180.0, "Legacy test")
        signals = db.get_user_signals(user_uid)
        
        portfolio = db.get_portfolio_summary(user_uid)
        
        assert all([user_uid, user, symbol_uid, symbol, signal_uid, len(signals) > 0, portfolio])
        logger.info("✓ Backward compatibility tests passed!")
        
    finally:
        db.close()


def main():
    """Run all tests."""
    logger.info("Starting refactored database manager tests...")
    
    try:
        test_factory_pattern()
        test_specialized_managers()
        test_backward_compatibility()
        
        logger.info("🎉 All tests passed! Refactoring successful!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Cleanup test databases
    test_files = ["data/test_refactored.db", "data/test_specialized.db", "data/test_backward_compat.db"]
    for test_file in test_files:
        if os.path.exists(test_file):
            os.remove(test_file)
            logger.info(f"Cleaned up {test_file}")


if __name__ == "__main__":
    main() 