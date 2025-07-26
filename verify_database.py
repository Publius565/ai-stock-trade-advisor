#!/usr/bin/env python3
"""
Database Verification Script

Comprehensive verification of database schema and tables.
"""

import sqlite3
import os
import sys

def verify_database(db_path: str = "data/trading_advisor.db"):
    """Verify database schema and tables."""
    print("=== Database Verification ===")
    print(f"Verifying database: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"✗ Database file not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"Found {len(tables)} tables: {', '.join(tables)}")
        
        # Required tables from the actual schema
        required_tables = [
            'users', 'symbols', 'watchlists', 'watchlist_symbols', 
            'market_data', 'indicators', 'signals', 'trades', 'positions', 
            'performance', 'models', 'predictions', 'news_articles', 
            'news_symbols', 'market_movers', 'audit_log', 'api_usage'
        ]
        
        missing_tables = []
        for table in required_tables:
            if table in tables:
                print(f"✓ {table} table exists")
            else:
                print(f"✗ {table} table missing")
                missing_tables.append(table)
        
        if missing_tables:
            print(f"\n❌ Missing tables: {', '.join(missing_tables)}")
            return False
        
        # Check specific table structures
        print("\n=== Table Structure Verification ===")
        
        # Check users table
        cursor.execute("PRAGMA table_info(users)")
        user_columns = [col[1] for col in cursor.fetchall()]
        if 'uid' in user_columns:
            print("✓ Users table has uid column")
        else:
            print("✗ Users table missing uid column")
            return False
        
        # Check symbols table
        cursor.execute("PRAGMA table_info(symbols)")
        symbol_columns = [col[1] for col in cursor.fetchall()]
        if 'symbol' in symbol_columns:
            print("✓ Symbols table has symbol column")
        else:
            print("✗ Symbols table missing symbol column")
            return False
        
        # Check watchlists table
        cursor.execute("PRAGMA table_info(watchlists)")
        watchlist_columns = [col[1] for col in cursor.fetchall()]
        if 'uid' in watchlist_columns:
            print("✓ Watchlists table has uid column")
        else:
            print("✗ Watchlists table missing uid column")
            return False
        
        # Check data counts
        print("\n=== Data Verification ===")
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"✓ Found {user_count} users in database")
        
        cursor.execute("SELECT COUNT(*) FROM symbols")
        symbol_count = cursor.fetchone()[0]
        print(f"✓ Found {symbol_count} symbols in database")
        
        cursor.execute("SELECT COUNT(*) FROM watchlists")
        watchlist_count = cursor.fetchone()[0]
        print(f"✓ Found {watchlist_count} watchlists in database")
        
        conn.close()
        
        print("\n🎉 Database verification completed successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Database verification failed: {e}")
        return False

def main():
    """Main verification function."""
    success = verify_database()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 