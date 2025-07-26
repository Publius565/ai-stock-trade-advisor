"""
Test Suite for Profile Management

Consolidated tests for user profile creation, loading, and management.
"""

import unittest
import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.utils.database_manager import DatabaseManager
from src.profile.profile_manager import ProfileManager


class TestProfileManagement(unittest.TestCase):
    """Test cases for profile management functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary directory for test database
        self.test_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_dir, "test_trading_advisor.db")
        
        # Initialize test database manager
        self.db_manager = DatabaseManager(self.test_db_path)
        self.profile_manager = ProfileManager(self.db_manager)
        
    def tearDown(self):
        """Clean up test environment."""
        # Close database connections
        if self.db_manager:
            self.db_manager.close()
        
        # Remove temporary directory
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_create_user_profile(self):
        """Test user profile creation."""
        # Test data
        username = "test_user"
        email = "test@example.com"
        risk_profile = "moderate"
        
        # Create profile
        user_uid = self.profile_manager.create_user_profile(
            username=username,
            email=email,
            risk_profile=risk_profile
        )
        
        # Verify creation
        self.assertIsNotNone(user_uid)
        self.assertIsInstance(user_uid, str)
        self.assertTrue(len(user_uid) > 0)
        
        # Verify profile data
        profile = self.profile_manager.get_user_profile(user_uid=user_uid)
        self.assertIsNotNone(profile)
        self.assertEqual(profile['username'], username)
        self.assertEqual(profile['email'], email)
        self.assertEqual(profile['risk_profile'], risk_profile)
    
    def test_get_user_profile_by_username(self):
        """Test retrieving profile by username."""
        # Create test profile
        username = "lookup_user"
        email = "lookup@example.com"
        risk_profile = "aggressive"
        
        user_uid = self.profile_manager.create_user_profile(
            username=username,
            email=email,
            risk_profile=risk_profile
        )
        
        # Retrieve by username
        profile = self.profile_manager.get_user_profile(username=username)
        self.assertIsNotNone(profile)
        self.assertEqual(profile['uid'], user_uid)
        self.assertEqual(profile['username'], username)
        self.assertEqual(profile['email'], email)
    
    def test_update_user_profile(self):
        """Test updating user profile."""
        # Create initial profile
        user_uid = self.profile_manager.create_user_profile(
            username="update_user",
            email="update@example.com",
            risk_profile="conservative"
        )
        
        # Update profile
        new_email = "updated@example.com"
        new_risk_profile = "aggressive"
        
        success = self.profile_manager.update_user_profile(
            user_uid=user_uid,
            username="update_user",
            email=new_email,
            risk_profile=new_risk_profile
        )
        
        self.assertTrue(success)
        
        # Verify updates
        updated_profile = self.profile_manager.get_user_profile(user_uid=user_uid)
        self.assertEqual(updated_profile['email'], new_email)
        self.assertEqual(updated_profile['risk_profile'], new_risk_profile)
    
    def test_create_watchlist(self):
        """Test watchlist creation."""
        # Create user first
        user_uid = self.profile_manager.create_user_profile(
            username="watchlist_user",
            email="watchlist@example.com",
            risk_profile="moderate"
        )
        
        # Create watchlist
        watchlist_name = "Tech Stocks"
        description = "Technology sector watchlist"
        
        watchlist_uid = self.profile_manager.create_watchlist(
            user_uid=user_uid,
            name=watchlist_name,
            description=description
        )
        
        self.assertIsNotNone(watchlist_uid)
        
        # Verify watchlist
        watchlists = self.profile_manager.get_user_watchlists(user_uid)
        self.assertEqual(len(watchlists), 1)
        self.assertEqual(watchlists[0]['name'], watchlist_name)
        self.assertEqual(watchlists[0]['description'], description)
    
    def test_add_symbol_to_watchlist(self):
        """Test adding symbols to watchlist."""
        # Create user and watchlist
        user_uid = self.profile_manager.create_user_profile(
            username="symbol_user",
            email="symbol@example.com",
            risk_profile="moderate"
        )
        
        watchlist_uid = self.profile_manager.create_watchlist(
            user_uid=user_uid,
            name="Stock Picks",
            description="Selected stocks"
        )
        
        # Add symbol to watchlist
        symbol = "AAPL"
        priority = 8
        notes = "Apple Inc - strong fundamentals"
        
        success = self.profile_manager.add_symbol_to_watchlist(
            watchlist_uid=watchlist_uid,
            symbol=symbol,
            priority=priority,
            notes=notes
        )
        
        self.assertTrue(success)
        
        # Verify symbol was added
        symbols = self.profile_manager.get_watchlist_symbols(watchlist_uid)
        self.assertEqual(len(symbols), 1)
        self.assertEqual(symbols[0]['symbol'], symbol)
        self.assertEqual(symbols[0]['priority'], priority)
        self.assertEqual(symbols[0]['notes'], notes)
    
    def test_remove_symbol_from_watchlist(self):
        """Test removing symbols from watchlist."""
        # Setup: Create user, watchlist, and add symbol
        user_uid = self.profile_manager.create_user_profile(
            username="remove_user",
            email="remove@example.com",
            risk_profile="moderate"
        )
        
        watchlist_uid = self.profile_manager.create_watchlist(
            user_uid=user_uid,
            name="Test List",
            description="Test"
        )
        
        # Add symbol
        symbol = "GOOGL"
        self.profile_manager.add_symbol_to_watchlist(
            watchlist_uid=watchlist_uid,
            symbol=symbol,
            priority=5,
            notes="Test symbol"
        )
        
        # Verify symbol exists
        symbols = self.profile_manager.get_watchlist_symbols(watchlist_uid)
        self.assertEqual(len(symbols), 1)
        
        # Remove symbol
        success = self.profile_manager.remove_symbol_from_watchlist(
            watchlist_uid, symbol
        )
        
        self.assertTrue(success)
        
        # Verify symbol was removed
        symbols = self.profile_manager.get_watchlist_symbols(watchlist_uid)
        self.assertEqual(len(symbols), 0)
    
    def test_risk_assessment_update(self):
        """Test updating risk assessment."""
        # Create user
        user_uid = self.profile_manager.create_user_profile(
            username="risk_user",
            email="risk@example.com",
            risk_profile="moderate"
        )
        
        # Update risk assessment
        risk_data = {
            'investment_timeline': 'long',
            'risk_tolerance': 'high',
            'experience_level': 'expert',
            'investment_goals': 'aggressive'
        }
        
        success = self.profile_manager.update_risk_assessment(
            user_uid, risk_data
        )
        
        self.assertTrue(success)
        
        # Note: Verification would depend on actual implementation
        # of risk assessment storage in the profile manager
    
    def test_duplicate_username_handling(self):
        """Test handling of duplicate usernames."""
        username = "duplicate_user"
        email1 = "user1@example.com"
        email2 = "user2@example.com"
        
        # Create first user
        user_uid1 = self.profile_manager.create_user_profile(
            username=username,
            email=email1,
            risk_profile="moderate"
        )
        
        self.assertIsNotNone(user_uid1)
        
        # Attempt to create second user with same username
        # This should either fail or handle gracefully
        try:
            user_uid2 = self.profile_manager.create_user_profile(
                username=username,
                email=email2,
                risk_profile="conservative"
            )
            # If creation succeeds, UIDs should be different
            if user_uid2:
                self.assertNotEqual(user_uid1, user_uid2)
        except Exception:
            # If creation fails, that's also acceptable behavior
            pass
    
    def test_invalid_profile_data(self):
        """Test handling of invalid profile data."""
        # Test empty username
        with self.assertRaises((ValueError, TypeError, Exception)):
            self.profile_manager.create_user_profile(
                username="",
                email="test@example.com",
                risk_profile="moderate"
            )
        
        # Test invalid email format (basic check)
        with self.assertRaises((ValueError, TypeError, Exception)):
            self.profile_manager.create_user_profile(
                username="test_user",
                email="invalid_email",
                risk_profile="moderate"
            )
    
    def test_nonexistent_profile_retrieval(self):
        """Test retrieving non-existent profile."""
        # Try to get profile with non-existent UID
        profile = self.profile_manager.get_user_profile(user_uid="nonexistent-uid")
        self.assertIsNone(profile)
        
        # Try to get profile with non-existent username
        profile = self.profile_manager.get_user_profile(username="nonexistent_user")
        self.assertIsNone(profile)


if __name__ == '__main__':
    unittest.main() 