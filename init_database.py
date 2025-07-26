#!/usr/bin/env python3
"""
Database Initialization Script for AI-Driven Stock Trade Advisor

This script initializes the database with the correct schema and clears cache.
"""

import os
import shutil
import sqlite3
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clear_cache():
    """Clear all cache directories."""
    cache_dirs = [
        "data/cache",
        "data/test_cache"
    ]
    
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                shutil.rmtree(cache_dir)
                os.makedirs(cache_dir, exist_ok=True)
                logger.info(f"Cleared cache directory: {cache_dir}")
            except Exception as e:
                logger.error(f"Failed to clear cache {cache_dir}: {e}")

def init_database(db_path: str = "data/trading_advisor.db"):
    """Initialize database with correct schema."""
    try:
        # Check if database is in use
        if os.path.exists(db_path):
            try:
                # Try to connect to see if it's locked
                test_conn = sqlite3.connect(db_path, timeout=1)
                test_conn.close()
                # If we can connect, remove the file
                os.remove(db_path)
                logger.info(f"Removed existing database: {db_path}")
            except sqlite3.OperationalError:
                logger.warning(f"Database {db_path} is in use. Skipping reinitialization.")
                return True  # Return True to continue with existing database
            except Exception as e:
                logger.warning(f"Could not remove database {db_path}: {e}")
                return True  # Return True to continue with existing database
        
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Read schema file - try multiple possible locations with absolute paths
        script_dir = os.path.dirname(os.path.abspath(__file__))
        schema_files = [
            os.path.join(script_dir, "config", "optimized_database_schema.sql"),
            os.path.join(script_dir, "config", "database_schema.sql"),
            os.path.join(script_dir, "optimized_database_schema.sql"),
            os.path.join(script_dir, "database_schema.sql")
        ]
        
        schema_file = None
        for file_path in schema_files:
            if os.path.exists(file_path):
                schema_file = file_path
                logger.info(f"Found schema file: {schema_file}")
                break
        
        if not schema_file:
            logger.error(f"Schema file not found in any of these locations: {schema_files}")
            return False
        
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
        
        # Create database and apply schema
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Execute schema
        cursor.executescript(schema_sql)
        conn.commit()
        conn.close()
        
        logger.info(f"Database initialized successfully: {db_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False

def create_default_profile():
    """Create a default user profile for testing."""
    try:
        from src.utils.database_manager import DatabaseManager
        from src.profile.profile_manager import ProfileManager
        import time
        
        db = DatabaseManager("data/trading_advisor.db")
        pm = ProfileManager(db)
        
        # Create default user with unique timestamp
        timestamp = int(time.time())
        user_uid = pm.create_user_profile(
            username=f"default_user_{timestamp}",
            email=f"default_{timestamp}@example.com",
            risk_profile="moderate"
        )
        
        if user_uid:
            # Set up default risk assessment
            risk_assessment = {
                'investment_timeline': 'medium',
                'risk_tolerance': 'medium',
                'experience': 'intermediate',
                'goals': 'balanced'
            }
            
            pm.update_risk_profile(user_uid, risk_assessment)
            
            # Create default watchlist
            watchlist_uid = pm.create_watchlist(
                user_uid=user_uid,
                name="Default Watchlist",
                description="Default watchlist for testing",
                is_default=True
            )
            
            if watchlist_uid:
                # Add some default symbols
                default_symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"]
                for symbol in default_symbols:
                    pm.add_symbol_to_watchlist(
                        watchlist_uid=watchlist_uid,
                        symbol=symbol,
                        priority=1,
                        notes=f"Default symbol: {symbol}"
                    )
            
            logger.info(f"Default profile created: {user_uid}")
            return user_uid
        else:
            logger.error("Failed to create default profile")
            return None
            
    except Exception as e:
        logger.error(f"Failed to create default profile: {e}")
        return None

def main():
    """Main initialization function."""
    logger.info("Starting database initialization...")
    
    # Clear cache
    clear_cache()
    
    # Initialize database
    if init_database():
        # Create default profile
        default_uid = create_default_profile()
        if default_uid:
            logger.info("Database initialization completed successfully!")
            logger.info(f"Default user UID: {default_uid}")
            logger.info("Username: default_user_{timestamp}")
            logger.info("Email: default_{timestamp}@example.com")
        else:
            logger.error("Failed to create default profile")
    else:
        logger.error("Database initialization failed")

if __name__ == "__main__":
    main() 