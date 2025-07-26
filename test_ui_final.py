#!/usr/bin/env python3
"""
Final UI Test

Test to verify the UI and API are working correctly after fixes.
"""

import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_api_key_no_warning():
    """Test that API key loads without warnings."""
    print("Testing API key loading without warnings...")
    
    try:
        # Load environment first
        from dotenv import load_dotenv
        load_dotenv('config/api_keys.env')
        
        # Import API client
        from src.data_layer.api_client import APIClient
        
        # Create client
        client = APIClient()
        
        # Check if warning would be shown
        if client.alpha_vantage_key and client.alpha_vantage_key != 'your_alpha_vantage_api_key_here':
            print("✓ API key loaded correctly without warnings")
            return True
        else:
            print("✗ API key not loaded correctly")
            return False
            
    except Exception as e:
        print(f"✗ API key test failed: {e}")
        return False

def test_database_access():
    """Test database access without locking issues."""
    print("\nTesting database access...")
    
    try:
        from src.utils.database_manager import DatabaseManager
        from src.profile.profile_manager import ProfileManager
        
        # Create managers
        db = DatabaseManager("data/trading_advisor.db")
        pm = ProfileManager(db)
        
        # Test user retrieval
        users = db.users.get_all_users(active_only=True)
        if users:
            print(f"✓ Database accessible, found {len(users)} users")
            return True
        else:
            print("⚠ Database accessible but no users found")
            return True  # This is OK
            
    except Exception as e:
        print(f"✗ Database access failed: {e}")
        return False

def test_ui_components():
    """Test UI component creation."""
    print("\nTesting UI components...")
    
    try:
        from PyQt6.QtWidgets import QApplication
        from src.ui.main_window import MainWindow
        
        # Create minimal app
        app = QApplication([])
        
        # Create window
        window = MainWindow()
        print("✓ MainWindow created successfully")
        
        # Test components
        if window.db_manager and window.profile_manager and window.market_scanner:
            print("✓ All managers initialized")
        else:
            print("✗ Some managers not initialized")
            return False
        
        # Test default profile loading
        if hasattr(window, 'current_user_uid') and window.current_user_uid:
            print(f"✓ Default profile loaded: {window.current_user_uid}")
        else:
            print("⚠ No default profile loaded (this is OK)")
        
        # Clean up
        window.close()
        app.quit()
        
        print("✓ UI components working correctly")
        return True
        
    except Exception as e:
        print(f"✗ UI component test failed: {e}")
        return False

def main():
    """Main test function."""
    print("=== Final UI Test ===")
    
    # Test API key
    api_ok = test_api_key_no_warning()
    
    # Test database
    db_ok = test_database_access()
    
    # Test UI
    ui_ok = test_ui_components()
    
    print("\n=== Test Results ===")
    print(f"API Key: {'✓ PASSED' if api_ok else '✗ FAILED'}")
    print(f"Database: {'✓ PASSED' if db_ok else '✗ FAILED'}")
    print(f"UI Components: {'✓ PASSED' if ui_ok else '✗ FAILED'}")
    
    if api_ok and db_ok and ui_ok:
        print("\n🎉 All tests passed! Application is ready for use.")
        return True
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 