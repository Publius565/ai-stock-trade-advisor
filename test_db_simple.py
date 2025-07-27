#!/usr/bin/env python3
"""
Simple database test
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.utils.database_manager import DatabaseManager

def main():
    try:
        print("Creating database manager...")
        db_manager = DatabaseManager("data/trading_advisor.db")
        
        print("Testing symbol lookup...")
        symbol_id = db_manager.market_data.get_symbol_id("AAPL")
        print(f"AAPL symbol ID: {symbol_id}")
        
        print("Testing position query...")
        query = """
            SELECT quantity, avg_price, realized_pnl
            FROM positions
            WHERE user_id = ? AND symbol_id = ?
        """
        result = db_manager.fetch_one(query, (1, symbol_id))
        print(f"Position result: {result}")
        
        print("Testing insert...")
        import uuid
        position_uid = str(uuid.uuid4())
        insert_query = """
            INSERT INTO positions (uid, user_id, symbol_id, quantity, avg_price, 
                                 current_price, market_value, unrealized_pnl, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            position_uid,
            1,
            symbol_id,
            100,
            150.0,
            150.0,
            15000.0,
            0.0,
            int(datetime.now().timestamp())
        )
        
        db_manager.execute_update(insert_query, params)
        print("Insert successful!")
        
        db_manager.close()
        print("Test completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    from datetime import datetime
    main() 