#!/usr/bin/env python3
"""
Simple Database Schema Test

This script tests the core database schema and basic operations.
"""

import sys
import os
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.database_manager import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Test the database schema and basic operations."""
    print("Simple Database Schema Test")
    print("=" * 40)
    
    try:
        # Initialize database
        print("1. Initializing database...")
        db = DatabaseManager("data/simple_test.db")
        print("   ✓ Database initialized")
        
        # Test UID generation
        print("2. Testing UID generation...")
        uid1 = db.generate_uid('user')
        uid2 = db.generate_uid('user')
        if uid1 != uid2 and uid1.startswith('user_'):
            print("   ✓ UID generation working")
        else:
            print("   ✗ UID generation failed")
            return 1
        
        # Test user creation
        print("3. Testing user creation...")
        user_uid = db.create_user("test_user", "test@example.com", "moderate")
        if user_uid:
            print(f"   ✓ User created: {user_uid}")
        else:
            print("   ✗ User creation failed")
            return 1
        
        # Test user retrieval
        print("4. Testing user retrieval...")
        user_data = db.get_user(uid=user_uid)
        if user_data and user_data['username'] == 'test_user':
            print("   ✓ User retrieval working")
        else:
            print("   ✗ User retrieval failed")
            return 1
        
        # Test symbol creation
        print("5. Testing symbol creation...")
        symbol_uid = db.get_or_create_symbol("AAPL", "Apple Inc.", "Technology")
        if symbol_uid:
            print(f"   ✓ Symbol created: {symbol_uid}")
        else:
            print("   ✗ Symbol creation failed")
            return 1
        
        # Test symbol retrieval
        print("6. Testing symbol retrieval...")
        symbol_data = db.get_symbol("AAPL")
        if symbol_data and symbol_data['name'] == 'Apple Inc.':
            print("   ✓ Symbol retrieval working")
        else:
            print("   ✗ Symbol retrieval failed")
            return 1
        
        # Test database schema validation
        print("7. Testing database schema...")
        tables = db.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
        table_names = [row['name'] for row in tables]
        
        expected_tables = [
            'users', 'symbols', 'market_data', 'indicators', 'signals',
            'trades', 'positions', 'performance', 'models', 'predictions',
            'audit_log', 'api_usage'
        ]
        
        missing_tables = set(expected_tables) - set(table_names)
        if missing_tables:
            print(f"   ✗ Missing tables: {missing_tables}")
            return 1
        else:
            print(f"   ✓ All {len(table_names)} tables present")
        
        # Test views
        print("8. Testing database views...")
        views = db.execute_query("SELECT name FROM sqlite_master WHERE type='view'")
        view_names = [row['name'] for row in views]
        
        expected_views = ['v_positions', 'v_recent_signals', 'v_portfolio_summary']
        missing_views = set(expected_views) - set(view_names)
        
        if missing_views:
            print(f"   ✗ Missing views: {missing_views}")
            return 1
        else:
            print(f"   ✓ All {len(view_names)} views present")
        
        # Test indexes
        print("9. Testing database indexes...")
        indexes = db.execute_query("SELECT name FROM sqlite_master WHERE type='index'")
        index_names = [row['name'] for row in indexes]
        print(f"   ✓ {len(index_names)} indexes created")
        
        # Close database
        db.close()
        print("10. Database connection closed")
        
        print("\n" + "=" * 40)
        print("✓ All database tests passed!")
        print("\nDatabase schema and infrastructure summary:")
        print(f"- Tables: {len(table_names)}")
        print(f"- Views: {len(view_names)}")
        print(f"- Indexes: {len(index_names)}")
        print("- UID generation: Working")
        print("- User management: Working")
        print("- Symbol management: Working")
        print("- Schema validation: Complete")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        logger.exception("Database test error")
        return 1


if __name__ == "__main__":
    exit(main()) 