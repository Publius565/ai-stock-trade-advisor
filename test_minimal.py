#!/usr/bin/env python3
"""
Minimal test to isolate position monitor issue
"""

import sys
import logging
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Setup logging
logging.basicConfig(level=logging.INFO)

def test_minimal():
    try:
        print("Testing imports...")
        from src.utils.database_manager import DatabaseManager
        print("✓ DatabaseManager imported")
        
        from src.execution.position_monitor import PositionMonitor
        print("✓ PositionMonitor imported")
        
        print("Testing database manager creation...")
        db_manager = DatabaseManager("data/trading_advisor.db")
        print("✓ DatabaseManager created")
        
        print("Testing position monitor creation...")
        monitor = PositionMonitor(db_manager)
        print("✓ PositionMonitor created")
        
        print("Testing add_position...")
        result = monitor.add_position(1, "AAPL", 100, 150.0)
        print(f"✓ add_position result: {result}")
        
        db_manager.close()
        print("✓ Test completed successfully")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_minimal() 