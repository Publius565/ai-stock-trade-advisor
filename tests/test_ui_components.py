"""
Test Suite for UI Components

Tests for the modular UI components.
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import UI components without mocking PyQt6 for structure tests
from src.ui.components.profile_tab import ProfileTab
from src.ui.components.market_scanner_tab import MarketScannerTab
from src.ui.components.watchlist_tab import WatchlistTab
from src.ui.components.dashboard_tab import DashboardTab


class TestUIComponentsStructure(unittest.TestCase):
    """Test the structure and basic functionality of UI components."""
    
    def setUp(self):
        """Set up test environment."""
        # Mock the Qt classes
        self.mock_widget = MagicMock()
        self.mock_layout = MagicMock()
        
    def test_profile_tab_structure(self):
        """Test ProfileTab structure and methods."""
        # Test that ProfileTab can be imported and has expected methods
        self.assertTrue(hasattr(ProfileTab, '__init__'))
        self.assertTrue(hasattr(ProfileTab, 'init_ui'))
        self.assertTrue(hasattr(ProfileTab, 'setup_connections'))
        self.assertTrue(hasattr(ProfileTab, 'create_profile'))
        self.assertTrue(hasattr(ProfileTab, 'load_profile'))
        self.assertTrue(hasattr(ProfileTab, 'update_profile'))
        self.assertTrue(hasattr(ProfileTab, 'set_profile_manager'))
        self.assertTrue(hasattr(ProfileTab, 'set_current_user'))
    
    def test_market_scanner_tab_structure(self):
        """Test MarketScannerTab structure and methods."""
        self.assertTrue(hasattr(MarketScannerTab, '__init__'))
        self.assertTrue(hasattr(MarketScannerTab, 'init_ui'))
        self.assertTrue(hasattr(MarketScannerTab, 'setup_connections'))
        self.assertTrue(hasattr(MarketScannerTab, 'start_market_scan'))
        self.assertTrue(hasattr(MarketScannerTab, 'set_market_scanner'))
        self.assertTrue(hasattr(MarketScannerTab, 'get_scan_limit'))
        self.assertTrue(hasattr(MarketScannerTab, 'set_scan_limit'))
    
    def test_watchlist_tab_structure(self):
        """Test WatchlistTab structure and methods."""
        self.assertTrue(hasattr(WatchlistTab, '__init__'))
        self.assertTrue(hasattr(WatchlistTab, 'init_ui'))
        self.assertTrue(hasattr(WatchlistTab, 'setup_connections'))
        self.assertTrue(hasattr(WatchlistTab, 'create_watchlist'))
        self.assertTrue(hasattr(WatchlistTab, 'add_symbol_to_watchlist'))
        self.assertTrue(hasattr(WatchlistTab, 'set_profile_manager'))
        self.assertTrue(hasattr(WatchlistTab, 'set_current_user'))
    
    def test_dashboard_tab_structure(self):
        """Test DashboardTab structure and methods."""
        self.assertTrue(hasattr(DashboardTab, '__init__'))
        self.assertTrue(hasattr(DashboardTab, 'init_ui'))
        self.assertTrue(hasattr(DashboardTab, 'setup_connections'))
        self.assertTrue(hasattr(DashboardTab, 'refresh_statistics'))
        self.assertTrue(hasattr(DashboardTab, 'log_activity'))
        self.assertTrue(hasattr(DashboardTab, 'set_market_scanner'))
        self.assertTrue(hasattr(DashboardTab, 'set_profile_manager'))


class TestProfileTabLogic(unittest.TestCase):
    """Test ProfileTab business logic."""
    
    def setUp(self):
        """Set up test environment."""
        # Mock PyQt6 components at the class level
        with patch('PyQt6.QtWidgets.QWidget'), \
             patch('PyQt6.QtWidgets.QVBoxLayout'), \
             patch('PyQt6.QtWidgets.QGridLayout'), \
             patch('PyQt6.QtWidgets.QHBoxLayout'), \
             patch('PyQt6.QtWidgets.QPushButton'), \
             patch('PyQt6.QtWidgets.QLabel'), \
             patch('PyQt6.QtWidgets.QLineEdit'), \
             patch('PyQt6.QtWidgets.QTextEdit'), \
             patch('PyQt6.QtWidgets.QComboBox'), \
             patch('PyQt6.QtWidgets.QGroupBox'), \
             patch('PyQt6.QtWidgets.QMessageBox'), \
             patch('PyQt6.QtCore.pyqtSignal'):
            self.profile_tab = ProfileTab()
    
    def test_profile_manager_setting(self):
        """Test setting profile manager."""
        mock_manager = Mock()
        self.profile_tab.set_profile_manager(mock_manager)
        self.assertEqual(self.profile_tab.profile_manager, mock_manager)
    
    def test_current_user_setting(self):
        """Test setting current user."""
        test_uid = "test-user-123"
        
        # Mock the refresh method to avoid UI calls
        with patch.object(self.profile_tab, 'refresh_profile_display'):
            self.profile_tab.set_current_user(test_uid)
            self.assertEqual(self.profile_tab.current_user_uid, test_uid)


class TestMarketScannerTabLogic(unittest.TestCase):
    """Test MarketScannerTab business logic."""
    
    def setUp(self):
        """Set up test environment."""
        with patch('PyQt6.QtWidgets.QWidget'), \
             patch('PyQt6.QtWidgets.QVBoxLayout'), \
             patch('PyQt6.QtWidgets.QGridLayout'), \
             patch('PyQt6.QtWidgets.QPushButton'), \
             patch('PyQt6.QtWidgets.QLabel'), \
             patch('PyQt6.QtWidgets.QComboBox'), \
             patch('PyQt6.QtWidgets.QSpinBox'), \
             patch('PyQt6.QtWidgets.QGroupBox'), \
             patch('PyQt6.QtWidgets.QTableWidget'), \
             patch('PyQt6.QtWidgets.QTableWidgetItem'), \
             patch('PyQt6.QtWidgets.QMessageBox'), \
             patch('PyQt6.QtWidgets.QProgressBar'), \
             patch('PyQt6.QtCore.QThread'), \
             patch('PyQt6.QtCore.pyqtSignal'), \
             patch('PyQt6.QtCore.Qt'):
            self.scanner_tab = MarketScannerTab()
    
    def test_market_scanner_setting(self):
        """Test setting market scanner."""
        mock_scanner = Mock()
        self.scanner_tab.set_market_scanner(mock_scanner)
        self.assertEqual(self.scanner_tab.market_scanner, mock_scanner)
    
    def test_scan_limit_methods(self):
        """Test scan limit getter and setter."""
        # Mock the spin box
        mock_spin_box = Mock()
        mock_spin_box.value.return_value = 25
        mock_spin_box.setValue = Mock()
        
        self.scanner_tab.scan_limit_spin = mock_spin_box
        
        # Test getter
        limit = self.scanner_tab.get_scan_limit()
        self.assertEqual(limit, 25)
        
        # Test setter
        self.scanner_tab.set_scan_limit(50)
        mock_spin_box.setValue.assert_called_with(50)


class TestWatchlistTabLogic(unittest.TestCase):
    """Test WatchlistTab business logic."""
    
    def setUp(self):
        """Set up test environment."""
        with patch('PyQt6.QtWidgets.QWidget'), \
             patch('PyQt6.QtWidgets.QVBoxLayout'), \
             patch('PyQt6.QtWidgets.QGridLayout'), \
             patch('PyQt6.QtWidgets.QPushButton'), \
             patch('PyQt6.QtWidgets.QLabel'), \
             patch('PyQt6.QtWidgets.QLineEdit'), \
             patch('PyQt6.QtWidgets.QSpinBox'), \
             patch('PyQt6.QtWidgets.QGroupBox'), \
             patch('PyQt6.QtWidgets.QTableWidget'), \
             patch('PyQt6.QtWidgets.QTableWidgetItem'), \
             patch('PyQt6.QtWidgets.QMessageBox'), \
             patch('PyQt6.QtCore.pyqtSignal'):
            self.watchlist_tab = WatchlistTab()
    
    def test_profile_manager_setting(self):
        """Test setting profile manager."""
        mock_manager = Mock()
        self.watchlist_tab.set_profile_manager(mock_manager)
        self.assertEqual(self.watchlist_tab.profile_manager, mock_manager)
    
    def test_watchlist_count_no_manager(self):
        """Test watchlist count with no manager."""
        count = self.watchlist_tab.get_watchlist_count()
        self.assertEqual(count, 0)
    
    def test_symbols_count_no_manager(self):
        """Test symbols count with no manager."""
        count = self.watchlist_tab.get_symbols_count()
        self.assertEqual(count, 0)


class TestDashboardTabLogic(unittest.TestCase):
    """Test DashboardTab business logic."""
    
    def setUp(self):
        """Set up test environment."""
        with patch('PyQt6.QtWidgets.QWidget'), \
             patch('PyQt6.QtWidgets.QVBoxLayout'), \
             patch('PyQt6.QtWidgets.QHBoxLayout'), \
             patch('PyQt6.QtWidgets.QGridLayout'), \
             patch('PyQt6.QtWidgets.QPushButton'), \
             patch('PyQt6.QtWidgets.QLabel'), \
             patch('PyQt6.QtWidgets.QTextEdit'), \
             patch('PyQt6.QtWidgets.QGroupBox'), \
             patch('PyQt6.QtCore.pyqtSignal'), \
             patch('PyQt6.QtCore.QTimer'):
            self.dashboard_tab = DashboardTab()
    
    def test_manager_setting(self):
        """Test setting managers."""
        mock_scanner = Mock()
        mock_profile_manager = Mock()
        
        self.dashboard_tab.set_market_scanner(mock_scanner)
        self.dashboard_tab.set_profile_manager(mock_profile_manager)
        
        self.assertEqual(self.dashboard_tab.market_scanner, mock_scanner)
        self.assertEqual(self.dashboard_tab.profile_manager, mock_profile_manager)
    
    def test_activity_logging(self):
        """Test activity logging functionality."""
        # Mock the activity display
        mock_display = Mock()
        mock_display.append = Mock()
        self.dashboard_tab.activity_display = mock_display
        
        # Log activity
        test_message = "Test activity message"
        self.dashboard_tab.log_activity(test_message)
        
        # Verify append was called with timestamped message
        mock_display.append.assert_called_once()
        call_args = mock_display.append.call_args[0][0]
        self.assertIn(test_message, call_args)
    
    def test_statistics_update(self):
        """Test statistics update from external source."""
        # Mock stats labels
        mock_label = Mock()
        mock_label.setText = Mock()
        self.dashboard_tab.stats_labels = {"Test Stat": mock_label}
        
        # Update statistics
        stats_dict = {"Test Stat": "123"}
        self.dashboard_tab.update_statistics_from_external(stats_dict)
        
        # Verify label was updated
        mock_label.setText.assert_called_with("123")
    
    def test_stats_summary(self):
        """Test getting statistics summary."""
        # Mock stats labels
        mock_label1 = Mock()
        mock_label1.text.return_value = "100"
        mock_label2 = Mock()
        mock_label2.text.return_value = "50"
        
        self.dashboard_tab.stats_labels = {
            "Stat 1": mock_label1,
            "Stat 2": mock_label2
        }
        
        # Get summary
        summary = self.dashboard_tab.get_stats_summary()
        
        expected = {"Stat 1": "100", "Stat 2": "50"}
        self.assertEqual(summary, expected)


class TestUIComponentsIntegration(unittest.TestCase):
    """Test integration between UI components."""
    
    def test_signal_definitions(self):
        """Test that all components define expected signals."""
        # ProfileTab signals
        profile_signals = ['profile_created', 'profile_loaded', 'activity_logged', 'status_updated']
        for signal in profile_signals:
            self.assertTrue(hasattr(ProfileTab, signal))
        
        # MarketScannerTab signals
        scanner_signals = ['activity_logged', 'status_updated']
        for signal in scanner_signals:
            self.assertTrue(hasattr(MarketScannerTab, signal))
        
        # WatchlistTab signals
        watchlist_signals = ['activity_logged', 'status_updated']
        for signal in watchlist_signals:
            self.assertTrue(hasattr(WatchlistTab, signal))
        
        # DashboardTab signals
        dashboard_signals = ['activity_logged', 'status_updated', 'quick_scan_requested']
        for signal in dashboard_signals:
            self.assertTrue(hasattr(DashboardTab, signal))


if __name__ == '__main__':
    unittest.main() 