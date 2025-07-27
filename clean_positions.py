#!/usr/bin/env python3
"""
Clean up existing position data
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
    
    # Delete all positions
    delete_query = "DELETE FROM positions"
    db_manager.execute_update(delete_query)
    print("Cleaned up all positions")
    
    db_manager.close()

if __name__ == "__main__":
    main() 