#!/usr/bin/env python3
"""
Check database schema and positions table
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.utils.database_manager import DatabaseManager

def main():
    # Initialize database manager
    db_manager = DatabaseManager("data/trading_advisor.db")
    
    # Check if positions table exists
    query = """
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='positions'
    """
    result = db_manager.fetch_one(query)
    print(f"Positions table exists: {result is not None}")
    
    if result:
        # Check positions table schema
        schema_query = "PRAGMA table_info(positions)"
        schema = db_manager.fetch_all(schema_query)
        print("Positions table schema:")
        for column in schema:
            print(f"  {column['name']} {column['type']}")
    
    # Check if AAPL symbol exists
    symbol_query = "SELECT * FROM symbols WHERE symbol = 'AAPL'"
    symbol = db_manager.fetch_one(symbol_query)
    print(f"AAPL symbol: {symbol}")
    
    db_manager.close()

if __name__ == "__main__":
    main() 