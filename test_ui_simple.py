#!/usr/bin/env python3
"""
Simple UI Test for AI-Driven Stock Trade Advisor

Tests UI components without launching the full application.
"""

import sys
import os
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_ui_imports():
    """Test that all UI components can be imported."""
    print("Testing UI imports...")
    
    try:
        from src.ui.main_window import MainWindow
        print("  ✓ MainWindow imported successfully")
        
        from src.ui import __version__, __author__
        print(f"  ✓ UI package version: {__version__}")
        print(f"  ✓ UI package author: {__author__}")
        
        return True
    except Exception as e:
        print(f"  ✗ UI import failed: {e}")
        return False

def test_database_connection():
    """Test database connection for UI."""
    print("Testing database connection...")
    
    try:
        from src.utils.database_manager import DatabaseManager
        from src.profile.profile_manager import ProfileManager
        from src.data_layer.market_scanner import MarketScanner
        
        # Test database initialization
        db_manager = DatabaseManager("data/test_ui.db")
        profile_manager = ProfileManager(db_manager)
        market_scanner = MarketScanner(db_manager)
        
        print("  ✓ Database connection successful")
        print("  ✓ Profile manager initialized")
        print("  ✓ Market scanner initialized")
        
        # Clean up
        db_manager.close()
        
        return True
    except Exception as e:
        print(f"  ✗ Database connection failed: {e}")
        return False

def test_ui_components():
    """Test UI component creation."""
    print("Testing UI component creation...")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from src.ui.main_window import MainWindow
        
        # Create minimal app for testing
        app = QApplication([])
        
        # Test window creation
        window = MainWindow()
        print("  ✓ MainWindow created successfully")
        
        # Test basic properties
        assert window.db_manager is not None, "Database manager not initialized"
        assert window.profile_manager is not None, "Profile manager not initialized"
        assert window.market_scanner is not None, "Market scanner not initialized"
        
        print("  ✓ All UI components initialized correctly")
        
        # Clean up
        window.close()
        app.quit()
        
        return True
    except Exception as e:
        print(f"  ✗ UI component test failed: {e}")
        return False

def main():
    """Run all UI tests."""
    print("AI-Driven Stock Trade Advisor - UI Test Suite")
    print("=" * 50)
    
    # Set up environment
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    test_results = []
    
    # Run tests
    test_results.append(("UI Imports", test_ui_imports()))
    test_results.append(("Database Connection", test_database_connection()))
    test_results.append(("UI Components", test_ui_components()))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name:25} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All UI tests passed! The application is ready to run.")
        print("\nTo launch the application, run:")
        print("  python run_ui.py")
        return 0
    else:
        print("❌ Some UI tests failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    exit(main()) 