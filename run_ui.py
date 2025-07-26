#!/usr/bin/env python3
"""
UI Launcher for AI-Driven Stock Trade Advisor

Simple launcher script to run the main application UI.
"""

import sys
import os
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def setup_environment():
    """Set up the environment for the UI."""
    # Create data directory if it doesn't exist
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Create cache directory if it doesn't exist
    cache_dir = data_dir / "cache"
    cache_dir.mkdir(exist_ok=True)
    
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Clear cache on startup
    clear_cache_on_startup()

def clear_cache_on_startup():
    """Clear cache directories on application startup."""
    import shutil
    
    cache_dirs = [
        "data/cache",
        "data/test_cache"
    ]
    
    for cache_dir in cache_dirs:
        if os.path.exists(cache_dir):
            try:
                shutil.rmtree(cache_dir)
                os.makedirs(cache_dir, exist_ok=True)
                print(f"Cleared cache: {cache_dir}")
            except Exception as e:
                print(f"Warning: Failed to clear cache {cache_dir}: {e}")

def ensure_database_exists():
    """Ensure database exists with correct schema."""
    db_path = "data/trading_advisor.db"
    
    # Check if database exists and has correct schema
    if not os.path.exists(db_path):
        print("Database not found. Initializing...")
        init_database()
    else:
        # Check if database has correct schema by testing a simple query
        try:
            import sqlite3
            conn = sqlite3.connect(db_path, timeout=10)
            cursor = conn.cursor()
            
            # Check if users table exists and has uid column
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            if not cursor.fetchone():
                print("Users table not found. Reinitializing...")
                conn.close()
                init_database()
                return
            
            cursor.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'uid' not in columns:
                print("Database schema outdated. Reinitializing...")
                conn.close()
                init_database()
            else:
                print("Database schema verified.")
                
            conn.close()
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e).lower():
                print("Database is in use. Continuing with existing database...")
            else:
                print(f"Database verification failed: {e}")
                print("Reinitializing database...")
                init_database()
        except Exception as e:
            print(f"Database verification failed: {e}")
            print("Reinitializing database...")
            init_database()

def init_database():
    """Initialize database with correct schema."""
    try:
        from init_database import init_database as init_db
        success = init_db("data/trading_advisor.db")
        if success:
            print("Database initialized successfully.")
        else:
            print("Database initialization failed. Creating minimal database...")
            create_minimal_database()
    except Exception as e:
        print(f"Failed to initialize database: {e}")
        # Fallback: create minimal database
        create_minimal_database()

def create_minimal_database():
    """Create minimal database as fallback."""
    try:
        import sqlite3
        
        # Remove existing database
        if os.path.exists("data/trading_advisor.db"):
            os.remove("data/trading_advisor.db")
        
        # Create new database with basic schema
        conn = sqlite3.connect("data/trading_advisor.db")
        cursor = conn.cursor()
        
        # Create users table with uid column
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
        
        conn.commit()
        conn.close()
        print("Minimal database created.")
    except Exception as e:
        print(f"Failed to create minimal database: {e}")

def main():
    """Main launcher function."""
    try:
        # Load environment variables first - BEFORE any other imports
        from dotenv import load_dotenv
        load_dotenv('config/api_keys.env')
        
        # Set up environment
        setup_environment()
        
        # Ensure database exists with correct schema
        ensure_database_exists()
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/ui.log'),
                logging.StreamHandler()
            ]
        )
        
        logger = logging.getLogger(__name__)
        logger.info("Starting AI-Driven Stock Trade Advisor UI")
        
        # Import and run UI
        from src.ui.main_window import main as ui_main
        ui_main()
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Please ensure all dependencies are installed:")
        print("pip install PyQt6 pandas numpy requests python-dotenv yfinance")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting UI: {e}")
        logging.error(f"UI startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 