#!/usr/bin/env python3
"""
Profile Management and Market Scanner Test

This script tests the user profile management system and market scanner functionality.
"""

import sys
import os
import logging
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.database_manager import DatabaseManager
from src.profile.profile_manager import ProfileManager
from src.data_layer.market_scanner import MarketScanner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_profile_management():
    """Test user profile management system."""
    print("\n=== Testing Profile Management System ===")
    
    try:
        with DatabaseManager("data/test_profile.db") as db:
            # Initialize profile manager
            profile_manager = ProfileManager(db)
            
            # Test 1: Create user profile
            print("1. Testing user profile creation...")
            user_uid = profile_manager.create_user_profile(
                username="test_profile_user",
                email="test_profile@example.com",
                risk_profile="moderate"
            )
            
            if not user_uid:
                print("   ✗ User profile creation failed")
                return False
            
            print(f"   ✓ User profile created: {user_uid}")
            
            # Test 2: Get user profile
            print("2. Testing user profile retrieval...")
            profile_data = profile_manager.get_user_profile(user_uid)
            
            if not profile_data:
                print("   ✗ User profile retrieval failed")
                return False
            
            if profile_data['user']['username'] != "test_profile_user":
                print("   ✗ Profile data mismatch")
                return False
            
            print("   ✓ User profile retrieved successfully")
            
            # Test 3: Risk assessment
            print("3. Testing risk assessment...")
            risk_assessment = {
                'investment_timeline': 'long',
                'risk_tolerance': 'high',
                'experience': 'expert',
                'goals': 'aggressive'
            }
            
            success = profile_manager.update_risk_profile(user_uid, risk_assessment)
            if not success:
                print("   ✗ Risk profile update failed")
                return False
            
            # Verify risk profile was updated
            updated_profile = profile_manager.get_user_profile(user_uid)
            if updated_profile['user']['risk_profile'] != 'aggressive':
                print("   ✗ Risk profile not updated correctly")
                return False
            
            print("   ✓ Risk assessment completed successfully")
            
            # Test 4: Watchlist creation
            print("4. Testing watchlist creation...")
            watchlist_uid = profile_manager.create_watchlist(
                user_uid=user_uid,
                name="Test Watchlist",
                description="Test watchlist for profile management",
                is_default=True
            )
            
            if not watchlist_uid:
                print("   ✗ Watchlist creation failed")
                return False
            
            print(f"   ✓ Watchlist created: {watchlist_uid}")
            
            # Test 5: Add symbols to watchlist
            print("5. Testing symbol addition to watchlist...")
            test_symbols = ['AAPL', 'MSFT', 'GOOGL']
            
            for symbol in test_symbols:
                success = profile_manager.add_symbol_to_watchlist(
                    watchlist_uid=watchlist_uid,
                    symbol=symbol,
                    priority=5,
                    notes=f"Test symbol {symbol}"
                )
                
                if not success:
                    print(f"   ✗ Failed to add {symbol} to watchlist")
                    return False
            
            print("   ✓ Symbols added to watchlist successfully")
            
            # Test 6: Get user watchlists
            print("6. Testing watchlist retrieval...")
            watchlists = profile_manager.get_user_watchlists(user_uid)
            
            if not watchlists:
                print("   ✗ Watchlist retrieval failed")
                return False
            
            print(f"   ✓ Retrieved {len(watchlists)} watchlists")
            
            # Test 7: User preferences
            print("7. Testing user preferences...")
            preferences = {
                'max_position_pct': 0.15,
                'stop_loss_pct': 0.08,
                'take_profit_pct': 0.20
            }
            
            success = profile_manager.update_user_preferences(user_uid, preferences)
            if not success:
                print("   ✗ Preferences update failed")
                return False
            
            # Verify preferences
            user_prefs = profile_manager.get_user_preferences(user_uid)
            if user_prefs['max_position_pct'] != 0.15:
                print("   ✗ Preferences not updated correctly")
                return False
            
            print("   ✓ User preferences updated successfully")
            
            # Test 8: Risk assessment questions
            print("8. Testing risk assessment questions...")
            questions = profile_manager.get_risk_assessment_questions()
            
            if not questions or len(questions) < 4:
                print("   ✗ Risk assessment questions not generated")
                return False
            
            print(f"   ✓ Generated {len(questions)} risk assessment questions")
            
            # Test 9: Profile validation
            print("9. Testing profile validation...")
            valid_profile = {
                'username': 'valid_user',
                'email': 'valid@example.com',
                'risk_profile': 'moderate',
                'max_position_pct': 0.1
            }
            
            is_valid, errors = profile_manager.validate_profile_data(valid_profile)
            if not is_valid:
                print(f"   ✗ Valid profile failed validation: {errors}")
                return False
            
            invalid_profile = {
                'username': 'ab',  # Too short
                'email': 'invalid-email',
                'risk_profile': 'invalid',
                'max_position_pct': 1.5  # Too high
            }
            
            is_valid, errors = profile_manager.validate_profile_data(invalid_profile)
            if is_valid:
                print("   ✗ Invalid profile passed validation")
                return False
            
            print(f"   ✓ Profile validation working correctly ({len(errors)} errors caught)")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Profile management test failed: {e}")
        return False


def test_market_scanner():
    """Test market scanner functionality."""
    print("\n=== Testing Market Scanner System ===")
    
    try:
        with DatabaseManager("data/test_scanner.db") as db:
            # Initialize market scanner
            scanner = MarketScanner(db)
            
            # Test 1: Top movers scan
            print("1. Testing top movers scan...")
            movers_result = scanner.scan_top_movers(limit=10)
            
            if not movers_result:
                print("   ✗ Top movers scan failed")
                return False
            
            gainers = movers_result.get('gainers', [])
            losers = movers_result.get('losers', [])
            
            print(f"   ✓ Top movers scan completed: {len(gainers)} gainers, {len(losers)} losers")
            
            # Test 2: Scanner statistics
            print("2. Testing scanner statistics...")
            stats = scanner.get_scan_statistics()
            
            if stats['scans_completed'] < 1:
                print("   ✗ Scanner statistics not updated")
                return False
            
            print(f"   ✓ Scanner statistics: {stats['scans_completed']} scans completed")
            
            # Test 3: Create test user for watchlist scanning
            print("3. Testing watchlist scanning...")
            
            # Create test user
            user_uid = db.create_user("scanner_test_user", "scanner@example.com", "moderate")
            if not user_uid:
                print("   ✗ Failed to create test user for scanner")
                return False
            
            # Create watchlist
            user_data = db.get_user(uid=user_uid)
            watchlist_uid = db.market_data.create_watchlist(
                user_data['id'], "Scanner Test Watchlist", "Test watchlist for scanner"
            )
            
            if not watchlist_uid:
                print("   ✗ Failed to create test watchlist")
                return False
            
            # Add test symbols
            test_symbols = ['AAPL', 'MSFT']
            for symbol in test_symbols:
                symbol_uid = db.get_or_create_symbol(symbol)
                if symbol_uid:
                    db.market_data.add_symbol_to_watchlist(watchlist_uid, symbol_uid, 5, "Test")
            
            # Test watchlist scanning
            watchlist_result = scanner.scan_user_watchlists(user_uid)
            
            if not watchlist_result:
                print("   ✗ Watchlist scanning failed")
                return False
            
            print(f"   ✓ Watchlist scanning completed: {len(watchlist_result.get('updates', []))} watchlists")
            
            # Test 4: News scanning (mock test)
            print("4. Testing news scanning...")
            news_result = scanner.scan_news_for_symbols(['AAPL', 'MSFT'], hours_back=1)
            
            # Note: This might return empty if no recent news, which is okay
            print(f"   ✓ News scanning completed: {len(news_result)} symbols with news")
            
            # Test 5: Intelligent symbol suggestions
            print("5. Testing intelligent symbol suggestions...")
            suggestions = scanner.get_intelligent_symbols(user_uid, limit=5)
            
            if not suggestions:
                print("   ✗ Intelligent symbol suggestions failed")
                return False
            
            print(f"   ✓ Generated {len(suggestions)} intelligent symbol suggestions")
            
            # Test 6: Continuous scanning (start and stop)
            print("6. Testing continuous scanning...")
            scanner.start_continuous_scanning(interval_minutes=1)
            
            # Wait a moment for scan to start
            import time
            time.sleep(2)
            
            # Check if scanning is active
            stats = scanner.get_scan_statistics()
            if not stats['is_continuous_scanning']:
                print("   ✗ Continuous scanning not started")
                return False
            
            # Stop scanning
            scanner.stop_continuous_scanning()
            
            print("   ✓ Continuous scanning start/stop working")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Market scanner test failed: {e}")
        return False


def test_integration():
    """Test integration between profile management and market scanner."""
    print("\n=== Testing Integration ===")
    
    try:
        with DatabaseManager("data/test_integration.db") as db:
            # Initialize both systems
            profile_manager = ProfileManager(db)
            scanner = MarketScanner(db)
            
            # Create user with profile
            print("1. Creating integrated test user...")
            user_uid = profile_manager.create_user_profile(
                username="integration_test_user",
                email="integration@example.com",
                risk_profile="moderate"
            )
            
            if not user_uid:
                print("   ✗ Failed to create integration test user")
                return False
            
            # Create watchlist
            watchlist_uid = profile_manager.create_watchlist(
                user_uid=user_uid,
                name="Integration Watchlist",
                description="Test integration between systems"
            )
            
            if not watchlist_uid:
                print("   ✗ Failed to create integration watchlist")
                return False
            
            # Add symbols to watchlist
            test_symbols = ['AAPL', 'MSFT', 'GOOGL']
            for symbol in test_symbols:
                profile_manager.add_symbol_to_watchlist(watchlist_uid, symbol, 5, "Integration test")
            
            # Test scanner with user profile
            print("2. Testing scanner with user profile...")
            suggestions = scanner.get_intelligent_symbols(user_uid, limit=10)
            
            if not suggestions:
                print("   ✗ Integration test failed - no suggestions generated")
                return False
            
            print(f"   ✓ Integration test successful: {len(suggestions)} suggestions based on user profile")
            
            # Test watchlist scanning with profile data
            print("3. Testing watchlist scanning with profile...")
            watchlist_result = scanner.scan_user_watchlists(user_uid)
            
            if not watchlist_result:
                print("   ✗ Watchlist scanning integration failed")
                return False
            
            print("   ✓ Watchlist scanning integration successful")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Integration test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("Profile Management and Market Scanner Test Suite")
    print("=" * 60)
    
    test_results = []
    
    # Run tests
    test_results.append(("Profile Management", test_profile_management()))
    test_results.append(("Market Scanner", test_market_scanner()))
    test_results.append(("Integration", test_integration()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name:25} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Profile management and market scanner systems are working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    exit(main()) 