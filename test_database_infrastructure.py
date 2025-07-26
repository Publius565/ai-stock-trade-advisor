#!/usr/bin/env python3
"""
Database Infrastructure Test Script

This script tests the optimized database schema and infrastructure:
- Schema creation and validation
- UID generation and management
- Data operations and relationships
- Performance and indexing
- Business logic alignment
"""

import sys
import os
import logging
import time
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.database_manager import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_database_initialization():
    """Test database initialization and schema creation."""
    print("\n=== Testing Database Initialization ===")
    
    try:
        # Use context manager to ensure proper connection handling
        with DatabaseManager("data/test_trading_advisor.db") as db:
            # Test basic connection
            print("  - Testing database connection...")
            result = db.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row['name'] for row in result]
            
            expected_tables = [
                'users', 'symbols', 'market_data', 'indicators', 'signals',
                'trades', 'positions', 'performance', 'models', 'predictions',
                'audit_log', 'api_usage', 'watchlists', 'watchlist_symbols',
                'news_articles', 'news_symbols', 'market_movers'
            ]
            
            missing_tables = set(expected_tables) - set(tables)
            if missing_tables:
                print(f"    ✗ Missing tables: {missing_tables}")
                return False
            else:
                print(f"    ✓ All {len(tables)} tables created successfully")
            
            # Test views
            print("  - Testing database views...")
            views_result = db.execute_query("SELECT name FROM sqlite_master WHERE type='view'")
            views = [row['name'] for row in views_result]
            
            expected_views = ['v_positions', 'v_recent_signals', 'v_portfolio_summary', 
                             'v_user_watchlists', 'v_top_movers', 'v_news_symbols']
            missing_views = set(expected_views) - set(views)
            
            if missing_views:
                print(f"    ✗ Missing views: {missing_views}")
                return False
            else:
                print(f"    ✓ All {len(views)} views created successfully")
            
            # Test indexes
            print("  - Testing database indexes...")
            indexes_result = db.execute_query("SELECT name FROM sqlite_master WHERE type='index'")
            indexes = [row['name'] for row in indexes_result]
            
            print(f"    ✓ {len(indexes)} indexes created successfully")
        
        return True
        
    except Exception as e:
        print(f"    ✗ Database initialization failed: {e}")
        return False


def test_uid_generation():
    """Test UID generation and uniqueness."""
    print("\n=== Testing UID Generation ===")
    
    try:
        with DatabaseManager("data/test_trading_advisor.db") as db:
            # Test UID generation
            print("  - Testing UID generation...")
            uids = set()
            for i in range(100):
                uid = db.generate_uid('test')
                if uid in uids:
                    print(f"    ✗ Duplicate UID generated: {uid}")
                    return False
                uids.add(uid)
            
            print(f"    ✓ Generated {len(uids)} unique UIDs")
            
            # Test UID format
            print("  - Testing UID format...")
            for uid in list(uids)[:10]:  # Test first 10 UIDs
                if not uid.startswith('test_'):
                    print(f"    ✗ Invalid UID format: {uid}")
                    return False
            
            print("    ✓ UID format validation passed")
        
        return True
        
    except Exception as e:
        print(f"    ✗ UID generation test failed: {e}")
        return False


def test_user_management():
    """Test user creation and management."""
    print("\n=== Testing User Management ===")
    
    try:
        with DatabaseManager("data/test_trading_advisor.db") as db:
            # Test user creation
            print("  - Testing user creation...")
            user_uid = db.create_user(
                username="testuser_management",
                email="test_management@example.com",
                risk_profile="moderate"
            )
            
            if not user_uid:
                print("    ✗ User creation failed")
                return False
            
            print(f"    ✓ User created: {user_uid}")
            
            # Test user retrieval
            print("  - Testing user retrieval...")
            user_data = db.get_user(uid=user_uid)
            if not user_data:
                print("    ✗ User retrieval failed")
                return False
            
            if user_data['username'] != "testuser_management":
                print(f"    ✗ User data mismatch: expected 'testuser_management', got '{user_data['username']}'")
                return False
            
            print(f"    ✓ User retrieved: {user_data['username']}")
            
            # Test user update
            print("  - Testing user update...")
            success = db.update_user(user_uid, risk_profile="aggressive")
            if not success:
                print("    ✗ User update failed")
                return False
            
            updated_user = db.get_user(uid=user_uid)
            if updated_user['risk_profile'] != "aggressive":
                print(f"    ✗ Update not reflected: expected 'aggressive', got '{updated_user['risk_profile']}'")
                return False
            
            print("    ✓ User updated successfully")
        
        return True
        
    except Exception as e:
        print(f"    ✗ User management test failed: {e}")
        return False


def test_symbol_management():
    """Test symbol creation and management."""
    print("\n=== Testing Symbol Management ===")
    
    try:
        with DatabaseManager("data/test_trading_advisor.db") as db:
            # Test symbol creation
            print("  - Testing symbol creation...")
            symbol_uid = db.get_or_create_symbol(
                symbol="TEST",
                name="Test Company Inc.",
                sector="Technology"
            )
            
            if not symbol_uid:
                print("    ✗ Symbol creation failed")
                return False
            
            print(f"    ✓ Symbol created: {symbol_uid}")
            
            # Test symbol retrieval
            print("  - Testing symbol retrieval...")
            symbol_data = db.get_symbol("TEST")
            if not symbol_data:
                print("    ✗ Symbol retrieval failed")
                return False
            
            print(f"    ✓ Symbol retrieved: {symbol_data['name']}")
            
            # Test duplicate symbol handling
            print("  - Testing duplicate symbol handling...")
            duplicate_uid = db.get_or_create_symbol("TEST")
            if duplicate_uid != symbol_uid:
                print("    ✗ Duplicate symbol not handled correctly")
                return False
            
            print("    ✓ Duplicate symbol handled correctly")
        
        return True
        
    except Exception as e:
        print(f"    ✗ Symbol management test failed: {e}")
        return False


def test_market_data_operations():
    """Test market data storage and retrieval."""
    print("\n=== Testing Market Data Operations ===")
    
    try:
        with DatabaseManager("data/test_trading_advisor.db") as db:
            # Create test symbol first
            print("  - Creating test symbol...")
            symbol_uid = db.get_or_create_symbol("TEST_MKT", "Test Market Data Corp")
            if not symbol_uid:
                print("    ✗ Failed to create test symbol")
                return False
            
            # Create test market data
            test_data = [
                {
                    'date': '2024-01-01',
                    'open': 100.0,
                    'high': 105.0,
                    'low': 98.0,
                    'close': 102.0,
                    'volume': 1000000
                },
                {
                    'date': '2024-01-02',
                    'open': 102.0,
                    'high': 108.0,
                    'low': 100.0,
                    'close': 106.0,
                    'volume': 1200000
                }
            ]
            
            # Test market data storage
            print("  - Testing market data storage...")
            success = db.store_market_data("TEST_MKT", test_data)
            if not success:
                print("    ✗ Market data storage failed")
                return False
            
            print("    ✓ Market data stored successfully")
            
            # Test market data retrieval
            print("  - Testing market data retrieval...")
            retrieved_data = db.get_market_data("TEST_MKT", days=30)
            if len(retrieved_data) != 2:
                print(f"    ✗ Expected 2 data points, got {len(retrieved_data)}")
                return False
            
            print(f"    ✓ Retrieved {len(retrieved_data)} data points")
            
            # Verify data integrity
            first_point = retrieved_data[0]
            if first_point['close'] != 106.0:
                print(f"    ✗ Data integrity check failed: expected 106.0, got {first_point['close']}")
                return False
            
            print("    ✓ Data integrity verified")
        
        return True
        
    except Exception as e:
        print(f"    ✗ Market data operations test failed: {e}")
        return False


def test_signal_management():
    """Test signal creation and management."""
    print("\n=== Testing Signal Management ===")
    
    try:
        with DatabaseManager("data/test_trading_advisor.db") as db:
            # Create test user and symbol first
            user_uid = db.create_user("signaltest_signal", risk_profile="moderate")
            symbol_uid = db.get_or_create_symbol("SIGNAL_SIG", "Signal Test Corp Signal")
            
            if not user_uid or not symbol_uid:
                print("    ✗ Failed to create test user or symbol")
                return False
            
            # Test signal creation
            print("  - Testing signal creation...")
            signal_uid = db.create_signal(
                user_uid=user_uid,
                symbol="SIGNAL_SIG",
                signal_type="buy",
                risk_level="medium",
                confidence=0.75,
                price_target=110.0,
                rationale="Test signal for validation"
            )
            
            if not signal_uid:
                print("    ✗ Signal creation failed")
                return False
            
            print(f"    ✓ Signal created: {signal_uid}")
            
            # Test signal retrieval
            print("  - Testing signal retrieval...")
            signals = db.get_user_signals(user_uid, active_only=True)
            if len(signals) != 1:
                print(f"    ✗ Expected 1 signal, got {len(signals)}")
                return False
            
            signal = signals[0]
            if signal['signal_type'] != "buy":
                print(f"    ✗ Signal type mismatch: expected 'buy', got '{signal['signal_type']}'")
                return False
            
            print("    ✓ Signal retrieved successfully")
        
        return True
        
    except Exception as e:
        print(f"    ✗ Signal management test failed: {e}")
        return False


def test_performance_queries():
    """Test performance queries and views."""
    print("\n=== Testing Performance Queries ===")
    
    try:
        with DatabaseManager("data/test_trading_advisor.db") as db:
            # Test portfolio summary view
            print("  - Testing portfolio summary view...")
            user_uid = db.create_user("perftest_perf", risk_profile="conservative")
            
            if not user_uid:
                print("    ✗ Failed to create test user")
                return False
            
            summary = db.get_portfolio_summary(user_uid)
            if summary is None:
                print("    ✗ Portfolio summary not available")
                return False
            
            print("    ✓ Portfolio summary view working")
            
            # Test positions view
            print("  - Testing positions view...")
            positions = db.get_user_positions(user_uid)
            print(f"    ✓ Positions view working: {len(positions)} positions")
        
        return True
        
    except Exception as e:
        print(f"    ✗ Performance queries test failed: {e}")
        return False


def test_business_logic_alignment():
    """Test business logic constraints and validation."""
    print("\n=== Testing Business Logic Alignment ===")
    
    try:
        with DatabaseManager("data/test_trading_advisor.db") as db:
            # Test risk profile validation
            print("  - Testing risk profile validation...")
            user_uid = db.create_user("invalidrisk_logic", risk_profile="invalid")
            if user_uid is not None:
                print("    ✗ Invalid risk profile should have been rejected")
                return False
            else:
                print("    ✓ Invalid risk profile properly rejected")
            
            # Test signal type validation
            print("  - Testing signal type validation...")
            user_uid = db.create_user("signaltest_logic", risk_profile="moderate")
            symbol_uid = db.get_or_create_symbol("TEST_LOGIC", "Test Corp Logic")
            
            if not user_uid or not symbol_uid:
                print("    ✗ Failed to create test user or symbol")
                return False
            
            signal_uid = db.create_signal(
                user_uid=user_uid,
                symbol="TEST_LOGIC",
                signal_type="INVALID",
                risk_level="medium"
            )
            if signal_uid is not None:
                print("    ✗ Invalid signal type should have been rejected")
                return False
            else:
                print("    ✓ Invalid signal type properly rejected")
            
            print("    ✓ Business logic validation working")
        
        return True
        
    except Exception as e:
        print(f"    ✗ Business logic alignment test failed: {e}")
        return False


def main():
    """Run all database infrastructure tests."""
    print("Database Infrastructure Test Suite")
    print("=" * 60)
    
    # Test results
    tests = [
        test_database_initialization,
        test_uid_generation,
        test_user_management,
        test_symbol_management,
        test_market_data_operations,
        test_signal_management,
        test_performance_queries,
        test_business_logic_alignment
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"  ✗ {test.__name__} failed")
        except Exception as e:
            print(f"  ✗ {test.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All database infrastructure tests passed!")
        return True
    else:
        print("❌ Some tests failed. Please review the output above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 