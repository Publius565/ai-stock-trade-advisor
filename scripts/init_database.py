#!/usr/bin/env python3
"""
Database Initialization Script

This script initializes the SQLite database for the AI-Driven Stock Trade Advisor.
It creates all necessary tables and inserts default data.
"""

import sqlite3
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.config import DATABASE_PATH
from config.logging_config import setup_logging, get_logger

def init_database():
    """Initialize the database with all tables and default data."""
    
    # Setup logging
    logger = get_logger('database_init')
    logger.info("Starting database initialization...")
    
    # Ensure data directory exists
    db_path = Path(DATABASE_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Connect to database (creates it if it doesn't exist)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        logger.info(f"Connected to database: {db_path}")
        
        # Read and execute schema file
        schema_file = Path(__file__).parent.parent / "config" / "database_schema.sql"
        
        if not schema_file.exists():
            logger.error(f"Schema file not found: {schema_file}")
            return False
        
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
        
        # Execute schema
        cursor.executescript(schema_sql)
        
        # Commit changes
        conn.commit()
        
        # Verify tables were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        logger.info(f"Created {len(tables)} tables:")
        for table in tables:
            logger.info(f"  - {table[0]}")
        
        # Verify default data
        cursor.execute("SELECT COUNT(*) FROM users;")
        user_count = cursor.fetchone()[0]
        logger.info(f"Default users created: {user_count}")
        
        cursor.execute("SELECT COUNT(*) FROM risk_disclosures;")
        disclosure_count = cursor.fetchone()[0]
        logger.info(f"Risk disclosures created: {disclosure_count}")
        
        # Close connection
        conn.close()
        
        logger.info("Database initialization completed successfully!")
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False

def verify_database():
    """Verify that the database is properly initialized."""
    
    logger = get_logger('database_verify')
    logger.info("Verifying database...")
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check required tables
        required_tables = [
            'users', 'market_data', 'technical_indicators', 'trade_suggestions',
            'trade_history', 'portfolio_positions', 'performance_metrics',
            'ml_models', 'model_predictions', 'audit_log', 'risk_disclosures',
            'api_usage_log'
        ]
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        existing_tables = [table[0] for table in cursor.fetchall()]
        
        missing_tables = [table for table in required_tables if table not in existing_tables]
        
        if missing_tables:
            logger.error(f"Missing tables: {missing_tables}")
            return False
        
        logger.info("All required tables exist")
        
        # Check indexes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index';")
        indexes = cursor.fetchall()
        logger.info(f"Found {len(indexes)} indexes")
        
        # Check foreign key constraints
        cursor.execute("PRAGMA foreign_keys;")
        fk_enabled = cursor.fetchone()[0]
        logger.info(f"Foreign key constraints enabled: {bool(fk_enabled)}")
        
        conn.close()
        
        logger.info("Database verification completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Database verification failed: {e}")
        return False

def reset_database():
    """Reset the database by deleting and recreating it."""
    
    logger = get_logger('database_reset')
    logger.warning("Resetting database...")
    
    try:
        # Close any existing connections
        conn = sqlite3.connect(DATABASE_PATH)
        conn.close()
        
        # Delete database file
        db_path = Path(DATABASE_PATH)
        if db_path.exists():
            db_path.unlink()
            logger.info("Deleted existing database file")
        
        # Reinitialize
        success = init_database()
        if success:
            logger.info("Database reset completed successfully!")
        else:
            logger.error("Database reset failed!")
        
        return success
        
    except Exception as e:
        logger.error(f"Database reset failed: {e}")
        return False

def main():
    """Main function to run database initialization."""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize AI-Driven Stock Trade Advisor database")
    parser.add_argument("--reset", action="store_true", help="Reset database (delete and recreate)")
    parser.add_argument("--verify", action="store_true", help="Verify database structure")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(log_level=args.log_level)
    logger = get_logger('main')
    
    logger.info("AI-Driven Stock Trade Advisor - Database Initialization")
    logger.info("=" * 60)
    
    if args.reset:
        success = reset_database()
    elif args.verify:
        success = verify_database()
    else:
        success = init_database()
    
    if success:
        logger.info("Operation completed successfully!")
        sys.exit(0)
    else:
        logger.error("Operation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 