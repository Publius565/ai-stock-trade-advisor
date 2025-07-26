#!/usr/bin/env python3
"""
Debug test for database managers.
"""

import sys
import logging
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.database_manager import DatabaseManager

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def debug_test():
    """Debug the specific issue."""
    test_db = "data/debug_test.db"
    
    # Remove existing test database
    if os.path.exists(test_db):
        os.remove(test_db)
    
    with DatabaseManager(test_db) as db:
        # Create user
        user_uid = db.create_user("debug_user", "debug@example.com", "moderate")
        logger.info(f"Created user: {user_uid}")
        
        # Check if user exists
        user = db.get_user(uid=user_uid)
        logger.info(f"User from factory: {user}")
        
        # Check users directly in signal manager
        logger.info("Checking users table in signal manager...")
        users = db.signals.execute_query("SELECT * FROM users")
        logger.info(f"Users in signals manager: {users}")
        
        # Check symbols
        symbol_uid = db.get_or_create_symbol("AAPL", "Apple Inc.", "Technology")
        logger.info(f"Created symbol: {symbol_uid}")
        
        symbols = db.signals.execute_query("SELECT * FROM symbols")
        logger.info(f"Symbols in signals manager: {symbols}")
        
        # Try to create signal with debug
        try:
            signal_uid = db.create_signal(user_uid, "AAPL", "buy", "medium", 0.8, 150.0, "Test signal")
            logger.info(f"Created signal: {signal_uid}")
        except Exception as e:
            logger.error(f"Signal creation failed: {e}")
        
        # Test market data
        logger.info("Testing market data...")
        from datetime import datetime, timedelta
        recent_date = (datetime.now() - timedelta(hours=1)).strftime('%Y-%m-%d')
        test_data = [{
            'date': recent_date,
            'open': 100.0,
            'high': 105.0,
            'low': 98.0,
            'close': 103.0,
            'volume': 1000000
        }]
        result = db.market_data.store_market_data("AAPL", test_data)
        logger.info(f"Market data storage result: {result}")
        
        # Check what was stored
        all_data = db.market_data.execute_query("SELECT * FROM market_data")
        logger.info(f"All market data: {all_data}")
        
        # Try to retrieve 
        retrieved_data = db.market_data.get_market_data("AAPL", days=1)
        logger.info(f"Retrieved market data: {retrieved_data}")
    
    # Cleanup
    if os.path.exists(test_db):
        os.remove(test_db)


if __name__ == "__main__":
    debug_test() 