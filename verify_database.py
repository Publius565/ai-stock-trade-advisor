#!/usr/bin/env python3
"""
Database Verification Script

Verify and fix database issues.
"""

import os
import sqlite3
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_database(db_path: str = "data/trading_advisor.db"):
    """Verify database exists and has correct schema."""
    print(f"Verifying database: {db_path}")
    
    if not os.path.exists(db_path):
        print("✗ Database file not found")
        return False
    
    try:
        # Try to connect to database
        conn = sqlite3.connect(db_path, timeout=10)
        cursor = conn.cursor()
        
        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if cursor.fetchone():
            print("✓ Users table exists")
            
            # Check if users table has uid column
            cursor.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'uid' in columns:
                print("✓ Users table has uid column")
                
                # Check if there are any users
                cursor.execute("SELECT COUNT(*) FROM users")
                user_count = cursor.fetchone()[0]
                print(f"✓ Found {user_count} users in database")
                
                conn.close()
                return True
            else:
                print("✗ Users table missing uid column")
                conn.close()
                return False
        else:
            print("✗ Users table not found")
            conn.close()
            return False
            
    except sqlite3.OperationalError as e:
        print(f"✗ Database locked or in use: {e}")
        return False
    except Exception as e:
        print(f"✗ Database verification failed: {e}")
        return False

def create_minimal_database(db_path: str = "data/trading_advisor.db"):
    """Create minimal database with basic schema."""
    print(f"Creating minimal database: {db_path}")
    
    try:
        # Remove existing database if it exists
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
                print("✓ Removed existing database")
            except Exception as e:
                print(f"⚠ Could not remove existing database: {e}")
        
        # Create data directory
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Create new database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create basic tables
        cursor.execute("""
        CREATE TABLE users (
            uid TEXT PRIMARY KEY,
            id INTEGER UNIQUE,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE,
            risk_profile TEXT DEFAULT 'moderate',
            created_at INTEGER DEFAULT (unixepoch()),
            updated_at INTEGER DEFAULT (unixepoch()),
            is_active INTEGER DEFAULT 1
        )
        """)
        
        cursor.execute("""
        CREATE TABLE symbols (
            uid TEXT PRIMARY KEY,
            id INTEGER UNIQUE,
            symbol TEXT UNIQUE NOT NULL,
            name TEXT,
            sector TEXT,
            industry TEXT,
            market_cap REAL,
            is_active INTEGER DEFAULT 1,
            created_at INTEGER DEFAULT (unixepoch())
        )
        """)
        
        cursor.execute("""
        CREATE TABLE market_data (
            uid TEXT PRIMARY KEY,
            id INTEGER UNIQUE,
            symbol_id INTEGER NOT NULL,
            date INTEGER NOT NULL,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            volume INTEGER NOT NULL,
            created_at INTEGER DEFAULT (unixepoch())
        )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX idx_users_username ON users(username)")
        cursor.execute("CREATE INDEX idx_symbols_symbol ON symbols(symbol)")
        cursor.execute("CREATE INDEX idx_market_data_symbol_date ON market_data(symbol_id, date DESC)")
        
        conn.commit()
        conn.close()
        
        print("✓ Minimal database created successfully")
        return True
        
    except Exception as e:
        print(f"✗ Failed to create minimal database: {e}")
        return False

def create_default_user(db_path: str = "data/trading_advisor.db"):
    """Create a default user in the database."""
    print("Creating default user...")
    
    try:
        from src.utils.database_manager import DatabaseManager
        from src.profile.profile_manager import ProfileManager
        import time
        
        db = DatabaseManager(db_path)
        pm = ProfileManager(db)
        
        # Create default user with timestamp
        timestamp = int(time.time())
        user_uid = pm.create_user_profile(
            username=f"default_user_{timestamp}",
            email=f"default_{timestamp}@example.com",
            risk_profile="moderate"
        )
        
        if user_uid:
            print(f"✓ Default user created: {user_uid}")
            return True
        else:
            print("✗ Failed to create default user")
            return False
            
    except Exception as e:
        print(f"✗ Failed to create default user: {e}")
        return False

def main():
    """Main verification function."""
    print("=== Database Verification ===")
    
    db_path = "data/trading_advisor.db"
    
    # Verify database
    if verify_database(db_path):
        print("✓ Database is valid and ready")
        return True
    else:
        print("\nDatabase needs to be recreated...")
        
        # Create minimal database
        if create_minimal_database(db_path):
            # Create default user
            if create_default_user(db_path):
                print("✓ Database setup completed successfully")
                return True
            else:
                print("✗ Failed to create default user")
                return False
        else:
            print("✗ Failed to create minimal database")
            return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Database verification completed successfully!")
    else:
        print("\n❌ Database verification failed!")
    exit(0 if success else 1) 