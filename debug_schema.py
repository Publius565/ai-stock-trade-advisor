#!/usr/bin/env python3
"""
Debug Database Schema Issues

This script helps identify specific issues with the database schema.
"""

import sys
import os
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.database_manager import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Debug the database schema issues."""
    print("Database Schema Debug")
    print("=" * 30)
    
    try:
        # Initialize database
        print("1. Initializing database...")
        db = DatabaseManager("data/debug_test.db")
        print("   ✓ Database initialized")
        
        # Check users table structure
        print("2. Checking users table structure...")
        columns = db.execute_query("PRAGMA table_info(users)")
        print("   Users table columns:")
        for col in columns:
            print(f"     - {col['name']}: {col['type']} (NOT NULL: {col['notnull']})")
        
        # Try to create a user with explicit values
        print("3. Testing user creation with explicit values...")
        uid = db.generate_uid('user')
        query = """
        INSERT INTO users (uid, username, email, risk_profile, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        current_time = int(db.execute_query("SELECT unixepoch() as now")[0]['now'])
        
        try:
            success = db.execute_update(query, (
                uid, 
                "debug_user", 
                "debug@example.com", 
                "moderate",
                current_time,
                current_time
            ))
            if success:
                print("   ✓ User created successfully")
            else:
                print("   ✗ User creation failed")
        except Exception as e:
            print(f"   ✗ User creation error: {e}")
        
        # Check if user was created
        print("4. Checking if user exists...")
        user_data = db.execute_query("SELECT * FROM users WHERE username = ?", ("debug_user",))
        if user_data:
            print(f"   ✓ User found: {user_data[0]}")
        else:
            print("   ✗ User not found")
        
        db.close()
        return 0
        
    except Exception as e:
        print(f"\n✗ Debug failed with error: {e}")
        logger.exception("Debug error")
        return 1


if __name__ == "__main__":
    exit(main()) 