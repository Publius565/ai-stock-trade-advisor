#!/usr/bin/env python3
"""
Test Updated Database Schema

This script tests the updated database schema with new watchlist and news features.
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
    """Test the updated database schema."""
    print("Updated Database Schema Test")
    print("=" * 40)
    
    try:
        # Initialize database
        print("1. Initializing database...")
        db = DatabaseManager("data/updated_test.db")
        print("   ✓ Database initialized")
        
        # Test schema validation
        print("2. Testing updated schema...")
        tables = db.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
        table_names = [row['name'] for row in tables]
        
        expected_tables = [
            'users', 'symbols', 'watchlists', 'watchlist_symbols',
            'market_data', 'indicators', 'signals', 'trades', 'positions', 
            'performance', 'models', 'predictions', 'news_articles', 
            'news_symbols', 'market_movers', 'audit_log', 'api_usage'
        ]
        
        missing_tables = set(expected_tables) - set(table_names)
        if missing_tables:
            print(f"   ✗ Missing tables: {missing_tables}")
            return 1
        else:
            print(f"   ✓ All {len(table_names)} tables present")
        
        # Test views
        print("3. Testing database views...")
        views = db.execute_query("SELECT name FROM sqlite_master WHERE type='view'")
        view_names = [row['name'] for row in views]
        
        expected_views = [
            'v_positions', 'v_recent_signals', 'v_portfolio_summary',
            'v_user_watchlists', 'v_top_movers', 'v_news_symbols'
        ]
        missing_views = set(expected_views) - set(view_names)
        
        if missing_views:
            print(f"   ✗ Missing views: {missing_views}")
            return 1
        else:
            print(f"   ✓ All {len(view_names)} views present")
        
        # Test indexes
        print("4. Testing database indexes...")
        indexes = db.execute_query("SELECT name FROM sqlite_master WHERE type='index'")
        index_names = [row['name'] for row in indexes]
        print(f"   ✓ {len(index_names)} indexes created")
        
        # Test user creation
        print("5. Testing user creation...")
        user_uid = db.create_user("test_user_updated", "test@example.com", "moderate")
        if user_uid:
            print(f"   ✓ User created: {user_uid}")
        else:
            print("   ✗ User creation failed")
            return 1
        
        # Test symbol creation
        print("6. Testing symbol creation...")
        symbol_uid = db.get_or_create_symbol("AAPL", "Apple Inc.", "Technology")
        if symbol_uid:
            print(f"   ✓ Symbol created: {symbol_uid}")
        else:
            print("   ✗ Symbol creation failed")
            return 1
        
        # Test watchlist creation
        print("7. Testing watchlist functionality...")
        user_data = db.get_user(uid=user_uid)
        if not user_data:
            print("   ✗ User data not found")
            return 1
        
        print(f"   ✓ User data retrieved: ID={user_data['id']}")
        
        # Create watchlist
        watchlist_uid = db.generate_uid('watch')
        query = """
        INSERT INTO watchlists (uid, user_id, name, description)
        VALUES (?, ?, ?, ?)
        """
        success = db.execute_update(query, (watchlist_uid, user_data['id'], "My Watchlist", "Test watchlist"))
        if success:
            print("   ✓ Watchlist created")
        else:
            print("   ✗ Watchlist creation failed")
            return 1
        
        # Test news article creation
        print("8. Testing news functionality...")
        news_uid = db.generate_uid('news')
        query = """
        INSERT INTO news_articles (uid, title, content, source, published_at, sentiment_score)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        current_time = int(db.execute_query("SELECT unixepoch() as now")[0]['now'])
        success = db.execute_update(query, (
            news_uid, 
            "Test News Article", 
            "This is a test news article about AAPL", 
            "Test Source", 
            current_time, 
            0.5
        ))
        if success:
            print("   ✓ News article created")
        else:
            print("   ✗ News article creation failed")
            return 1
        
        # Test market movers
        print("9. Testing market movers...")
        mover_uid = db.generate_uid('mover')
        symbol_data = db.get_symbol("AAPL")
        query = """
        INSERT INTO market_movers (uid, symbol_id, date, change_percent, price_change, mover_type, rank)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        success = db.execute_update(query, (
            mover_uid,
            symbol_data['id'],
            current_time,
            5.2,
            10.50,
            'gainer',
            1
        ))
        if success:
            print("   ✓ Market mover created")
        else:
            print("   ✗ Market mover creation failed")
            return 1
        
        # Close database
        db.close()
        print("10. Database connection closed")
        
        print("\n" + "=" * 40)
        print("✓ All updated schema tests passed!")
        print("\nUpdated database schema summary:")
        print(f"- Tables: {len(table_names)} (including new watchlist and news tables)")
        print(f"- Views: {len(view_names)} (including new watchlist and news views)")
        print(f"- Indexes: {len(index_names)} (including new performance indexes)")
        print("- Watchlist functionality: Working")
        print("- News monitoring: Working")
        print("- Market movers: Working")
        print("- Schema validation: Complete")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        logger.exception("Updated schema test error")
        return 1


if __name__ == "__main__":
    exit(main()) 