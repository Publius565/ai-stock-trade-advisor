#!/usr/bin/env python3
"""
Test script to check symbol existence and add if needed
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
    
    # Check if AAPL symbol exists
    symbol_data = db_manager.market_data.get_symbol("AAPL")
    print(f"AAPL symbol data: {symbol_data}")
    
    if not symbol_data:
        print("AAPL symbol not found, creating it...")
        symbol_uid = db_manager.market_data.get_or_create_symbol("AAPL", "Apple Inc.", "Technology")
        print(f"Created AAPL symbol with UID: {symbol_uid}")
        
        # Check again
        symbol_data = db_manager.market_data.get_symbol("AAPL")
        print(f"AAPL symbol data after creation: {symbol_data}")
    
    # Get symbol ID
    symbol_id = db_manager.market_data.get_symbol_id("AAPL")
    print(f"AAPL symbol ID: {symbol_id}")
    
    db_manager.close()

if __name__ == "__main__":
    main() 