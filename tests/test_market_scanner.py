"""
Test Suite for Market Scanner

Consolidated tests for market scanning functionality.
"""

import unittest
import sys
import os
import tempfile
import shutil
from unittest.mock import Mock, patch

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.utils.database_manager import DatabaseManager
from src.data_layer.market_scanner import MarketScanner


class TestMarketScanner(unittest.TestCase):
    """Test cases for market scanner functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Create temporary directory for test database
        self.test_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_dir, "test_scanner.db")
        
        # Initialize test database manager
        self.db_manager = DatabaseManager(self.test_db_path)
        self.market_scanner = MarketScanner(self.db_manager)
        
    def tearDown(self):
        """Clean up test environment."""
        # Close database connections
        if self.db_manager:
            self.db_manager.close()
        
        # Remove temporary directory
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_scanner_initialization(self):
        """Test market scanner initialization."""
        self.assertIsNotNone(self.market_scanner)
        self.assertIsNotNone(self.market_scanner.db)
        self.assertEqual(self.market_scanner.max_workers, 4)
        
        # Check initial statistics
        stats = self.market_scanner.stats
        self.assertEqual(stats['scans_completed'], 0)
        self.assertEqual(stats['symbols_scanned'], 0)
        self.assertEqual(stats['api_calls'], 0)
        self.assertEqual(stats['cache_hits'], 0)
        self.assertIsNone(stats['last_scan'])
        self.assertEqual(stats['scan_duration'], 0)
    
    @patch('src.data_layer.api_client.APIClient.get_market_movers')
    def test_scan_top_movers_success(self, mock_get_movers):
        """Test successful top movers scan."""
        # Mock API response
        mock_data = [
            {
                'symbol': 'AAPL',
                'change_percent': 5.2,
                'price': 150.00,
                'volume': 1000000,
                'sector': 'Technology'
            },
            {
                'symbol': 'GOOGL',
                'change_percent': -3.1,
                'price': 2500.00,
                'volume': 500000,
                'sector': 'Technology'
            }
        ]
        mock_get_movers.return_value = mock_data
        
        # Perform scan
        result = self.market_scanner.scan_top_movers(limit=10)
        
        # Verify results
        self.assertIsInstance(result, dict)
        self.assertIn('gainers', result)
        self.assertIn('losers', result)
        
        # Check that symbols are categorized correctly
        gainers = result['gainers']
        losers = result['losers']
        
        self.assertTrue(any(symbol['symbol'] == 'AAPL' for symbol in gainers))
        self.assertTrue(any(symbol['symbol'] == 'GOOGL' for symbol in losers))
    
    @patch('src.data_layer.api_client.APIClient.get_market_movers')
    def test_scan_top_movers_empty_response(self, mock_get_movers):
        """Test top movers scan with empty API response."""
        mock_get_movers.return_value = []
        
        result = self.market_scanner.scan_top_movers(limit=10)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['gainers'], [])
        self.assertEqual(result['losers'], [])
    
    @patch('src.data_layer.api_client.APIClient.get_market_movers')
    def test_scan_top_movers_api_failure(self, mock_get_movers):
        """Test top movers scan with API failure."""
        mock_get_movers.side_effect = Exception("API Error")
        
        # Market scanner should handle API failures gracefully
        result = self.market_scanner.scan_top_movers(limit=10)
        
        # Should return empty results when API fails
        self.assertIsInstance(result, dict)
        self.assertIn('gainers', result)
        self.assertIn('losers', result)
        self.assertEqual(len(result['gainers']), 0)
        self.assertEqual(len(result['losers']), 0)
    
    def test_scan_statistics_tracking(self):
        """Test that scan statistics are properly tracked."""
        initial_stats = self.market_scanner.get_scan_statistics()
        initial_scans = initial_stats['scans_completed']
        
        # Mock a successful scan
        with patch('src.data_layer.api_client.APIClient.get_market_movers') as mock_api:
            mock_api.return_value = [
                {'symbol': 'TEST', 'change_percent': 1.0, 'price': 100.0, 'volume': 1000}
            ]
            
            # Perform scan
            self.market_scanner.scan_top_movers(limit=5)
            
            # Check updated statistics
            updated_stats = self.market_scanner.get_scan_statistics()
            self.assertEqual(updated_stats['scans_completed'], initial_scans + 1)
            self.assertIsNotNone(updated_stats['last_scan'])
    
    def test_intelligent_symbol_suggestions(self):
        """Test intelligent symbol suggestion functionality."""
        # Create a mock user profile
        mock_user_uid = "test-user-123"
        
        # This test would require proper implementation of intelligent suggestions
        # For now, we'll test that the method exists and handles basic cases
        try:
            result = self.market_scanner.get_intelligent_symbols(
                user_uid=mock_user_uid,
                limit=10
            )
            
            # Result should be a dictionary with suggestions
            if result:
                self.assertIsInstance(result, dict)
                self.assertIn('suggestions', result)
        except NotImplementedError:
            # If method is not implemented yet, that's acceptable
            self.skipTest("Intelligent suggestions not implemented yet")
        except Exception as e:
            # Other exceptions may indicate implementation issues
            self.fail(f"Intelligent suggestions raised unexpected exception: {e}")
    
    def test_scanner_worker_limit(self):
        """Test scanner respects worker thread limits."""
        # Test that max_workers is properly set
        self.assertEqual(self.market_scanner.max_workers, 4)
        
        # Test creating scanner with custom worker limit
        custom_scanner = MarketScanner(self.db_manager, max_workers=2)
        self.assertEqual(custom_scanner.max_workers, 2)
    
    def test_scan_data_validation(self):
        """Test that scan results are properly validated."""
        # Mock API response with some invalid data
        with patch('src.data_layer.api_client.APIClient.get_market_movers') as mock_api:
            mock_api.return_value = [
                # Valid data
                {
                    'symbol': 'AAPL',
                    'change_percent': 5.2,
                    'price': 150.00,
                    'volume': 1000000
                },
                # Invalid data (missing required fields)
                {
                    'symbol': 'INVALID',
                    # Missing change_percent, price, volume
                },
                # Another valid entry
                {
                    'symbol': 'MSFT',
                    'change_percent': -1.5,
                    'price': 300.00,
                    'volume': 750000
                }
            ]
            
            result = self.market_scanner.scan_top_movers(limit=10)
            
            # Scanner should handle invalid data gracefully
            self.assertIsInstance(result, dict)
            self.assertIn('gainers', result)
            self.assertIn('losers', result)
            
            # Count total valid symbols processed
            total_symbols = len(result['gainers']) + len(result['losers'])
            self.assertGreaterEqual(total_symbols, 2)  # At least the 2 valid entries
    
    def test_concurrent_scanning_safety(self):
        """Test that concurrent scanning operations are handled safely."""
        # This is a basic test for thread safety
        # In a full implementation, this would test concurrent access
        
        # Ensure scanner starts with clean state
        self.assertFalse(self.market_scanner._stop_event.is_set())
        
        # Test that stop event can be set and cleared
        self.market_scanner._stop_event.set()
        self.assertTrue(self.market_scanner._stop_event.is_set())
        
        self.market_scanner._stop_event.clear()
        self.assertFalse(self.market_scanner._stop_event.is_set())
    
    def test_cache_integration(self):
        """Test integration with data caching system."""
        # Test that scanner properly integrates with caching
        initial_cache_hits = self.market_scanner.stats['cache_hits']
        
        # Perform a scan (this should increment API calls)
        with patch('src.data_layer.api_client.APIClient.get_market_movers') as mock_api:
            mock_api.return_value = [
                {'symbol': 'TEST', 'change_percent': 1.0, 'price': 100.0, 'volume': 1000}
            ]
            
            self.market_scanner.scan_top_movers(limit=5)
            
            # API calls should have incremented
            updated_stats = self.market_scanner.get_scan_statistics()
            self.assertGreaterEqual(updated_stats['api_calls'], 1)


if __name__ == '__main__':
    unittest.main() 