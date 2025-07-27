#!/usr/bin/env python3
"""
Debug script to test position monitor directly
"""

import sys
import logging
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Setup logging
logging.basicConfig(level=logging.DEBUG)

from src.utils.database_manager import DatabaseManager
from src.execution.position_monitor import PositionMonitor

def main():
    try:
        # Initialize database manager
        print("Initializing database manager...")
        db_manager = DatabaseManager("data/trading_advisor.db")
        
        # Create position monitor
        print("Creating position monitor...")
        monitor = PositionMonitor(db_manager)
        
        # Test adding position
        print("Testing add_position...")
        result = monitor.add_position(1, "AAPL", 100, 150.0)
        print(f"Add position result: {result}")
        
        db_manager.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 