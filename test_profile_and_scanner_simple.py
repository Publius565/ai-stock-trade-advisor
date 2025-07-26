#!/usr/bin/env python3
"""
Simplified Profile Management and Market Scanner Test

This script tests the core functionality without email conflicts.
"""

import sys
import os
import logging
import time
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


def test_profile_management_simple():
    """Test user profile management system with unique emails."""
    print("\n=== Testing Profile Management System ===")
    
    try:
        with DatabaseManager("data/test_profile_simple.db") as db:
            # Initialize profile manager
            profile_manager = ProfileManager(db)
            
            # Test 1: Create user profile with unique email
            print("1. Testing user profile creation...")
            timestamp = int(time.time())
            user_uid = profile_manager.create_user_profile(
                username=f"test_user_{timestamp}",
                email=f"test_{timestamp}@example.com",
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
            
            print("   ✓ User preferences updated successfully")
            
            # Test 8: Risk assessment questions
            print("8. Testing risk assessment questions...")
            questions = profile_manager.get_risk_assessment_questions()
            
            if not questions or len(questions) < 4:
                print("   ✗ Risk assessment questions not generated")
                return False
            
            print(f"   ✓ Generated {len(questions)} risk assessment questions")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Profile management test failed: {e}")
        return False


def test_market_scanner_simple():
    """Test market scanner functionality."""
    print("\n=== Testing Market Scanner System ===")
    
    try:
        with DatabaseManager("data/test_scanner_simple.db") as db:
            # Initialize market scanner
            scanner = MarketScanner(db)
            
            # Test 1: Top movers scan
            print("1. Testing top movers scan...")
            movers_result = scanner.scan_top_movers(limit=5)
            
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
            
            # Create test user with unique email
            timestamp = int(time.time())
            user_uid = db.create_user(f"scanner_test_{timestamp}", f"scanner_{timestamp}@example.com", "moderate")
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
        
        return True
        
    except Exception as e:
        print(f"   ✗ Market scanner test failed: {e}")
        return False


def test_integration_simple():
    """Test integration between profile management and market scanner."""
    print("\n=== Testing Integration ===")
    
    try:
        with DatabaseManager("data/test_integration_simple.db") as db:
            # Initialize both systems
            profile_manager = ProfileManager(db)
            scanner = MarketScanner(db)
            
            # Create user with profile
            print("1. Creating integrated test user...")
            timestamp = int(time.time())
            user_uid = profile_manager.create_user_profile(
                username=f"integration_test_{timestamp}",
                email=f"integration_{timestamp}@example.com",
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
    print("Simplified Profile Management and Market Scanner Test Suite")
    print("=" * 60)
    
    test_results = []
    
    # Run tests
    test_results.append(("Profile Management", test_profile_management_simple()))
    test_results.append(("Market Scanner", test_market_scanner_simple()))
    test_results.append(("Integration", test_integration_simple()))
    
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