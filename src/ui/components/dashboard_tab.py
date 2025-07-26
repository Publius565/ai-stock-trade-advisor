"""
Dashboard Tab Component

Handles dashboard display and statistics.
"""

import logging
from typing import Dict, Optional
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QTextEdit, QGroupBox
)
from PyQt6.QtCore import pyqtSignal, QTimer

logger = logging.getLogger(__name__)


class DashboardTab(QWidget):
    """Dashboard tab component."""
    
    # Signals for communication with parent
    activity_logged = pyqtSignal(str)  # activity message
    status_updated = pyqtSignal(str)   # status message
    quick_scan_requested = pyqtSignal()  # request quick market scan
    
    def __init__(self, market_scanner=None, profile_manager=None):
        super().__init__()
        self.market_scanner = market_scanner
        self.profile_manager = profile_manager
        self.current_user_uid = None
        self.stats_labels = {}
        self.init_ui()
        
        # Set up auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_statistics)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds
    
    def init_ui(self):
        """Initialize the dashboard tab UI."""
        layout = QVBoxLayout(self)
        
        # Quick Stats
        stats_group = QGroupBox("Quick Statistics")
        stats_layout = QGridLayout(stats_group)
        
        # Define statistics to display
        stats_config = [
            ("Total Scans", "0"),
            ("Watchlists", "0"),
            ("Symbols Tracked", "0"),
            ("Last Scan", "Never"),
            ("API Calls Today", "0"),
            ("Cache Hits", "0")
        ]
        
        row, col = 0, 0
        for stat_name, default_value in stats_config:
            label_key = QLabel(f"{stat_name}:")
            label_value = QLabel(default_value)
            label_value.setStyleSheet("font-weight: bold; color: #2E8B57;")
            
            stats_layout.addWidget(label_key, row, col)
            stats_layout.addWidget(label_value, row, col + 1)
            
            self.stats_labels[stat_name] = label_value
            
            col += 2
            if col >= 4:  # Two columns of stats
                col = 0
                row += 1
        
        layout.addWidget(stats_group)
        
        # Quick Actions
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QHBoxLayout(actions_group)
        
        self.quick_scan_btn = QPushButton("Quick Market Scan")
        self.quick_scan_btn.setToolTip("Perform a quick scan of top 10 market movers")
        
        self.refresh_stats_btn = QPushButton("Refresh Statistics")
        self.refresh_stats_btn.setToolTip("Manually refresh all statistics")
        
        self.clear_activity_btn = QPushButton("Clear Activity")
        self.clear_activity_btn.setToolTip("Clear the activity log display")
        
        actions_layout.addWidget(self.quick_scan_btn)
        actions_layout.addWidget(self.refresh_stats_btn)
        actions_layout.addWidget(self.clear_activity_btn)
        actions_layout.addStretch()
        
        layout.addWidget(actions_group)
        
        # Activity Log
        activity_group = QGroupBox("Activity Log")
        activity_layout = QVBoxLayout(activity_group)
        
        self.activity_display = QTextEdit()
        self.activity_display.setReadOnly(True)
        self.activity_display.setMaximumHeight(200)
        activity_layout.addWidget(self.activity_display)
        
        layout.addWidget(activity_group)
        
        # System Status
        status_group = QGroupBox("System Status")
        status_layout = QVBoxLayout(status_group)
        
        self.status_display = QTextEdit()
        self.status_display.setReadOnly(True)
        self.status_display.setMaximumHeight(100)
        self.status_display.setText("System ready")
        status_layout.addWidget(self.status_display)
        
        layout.addWidget(status_group)
        
        layout.addStretch()
        
        # Connect signals
        self.setup_connections()
        
        # Log initial activity
        self.log_activity("Dashboard initialized")
    
    def setup_connections(self):
        """Set up signal connections."""
        self.quick_scan_btn.clicked.connect(self.request_quick_scan)
        self.refresh_stats_btn.clicked.connect(self.refresh_statistics)
        self.clear_activity_btn.clicked.connect(self.clear_activity)
    
    def set_market_scanner(self, market_scanner):
        """Set the market scanner instance."""
        self.market_scanner = market_scanner
    
    def set_profile_manager(self, profile_manager):
        """Set the profile manager instance."""
        self.profile_manager = profile_manager
    
    def set_current_user(self, user_uid: str):
        """Set the current user UID."""
        self.current_user_uid = user_uid
        self.refresh_statistics()
    
    def request_quick_scan(self):
        """Request a quick market scan."""
        self.quick_scan_requested.emit()
        self.log_activity("Requested quick market scan")
    
    def refresh_statistics(self):
        """Refresh dashboard statistics."""
        try:
            # Get scanner statistics
            if self.market_scanner:
                stats = self.market_scanner.get_scan_statistics()
                self.stats_labels["Total Scans"].setText(str(stats.get('scans_completed', 0)))
                self.stats_labels["API Calls Today"].setText(str(stats.get('api_calls', 0)))
                self.stats_labels["Cache Hits"].setText(str(stats.get('cache_hits', 0)))
                
                # Update last scan
                last_scan = stats.get('last_scan')
                if last_scan:
                    self.stats_labels["Last Scan"].setText(last_scan)
            
            # Get watchlist statistics
            if self.current_user_uid and self.profile_manager:
                try:
                    watchlists = self.profile_manager.get_user_watchlists(self.current_user_uid)
                    self.stats_labels["Watchlists"].setText(str(len(watchlists)))
                    
                    # Get symbols count
                    total_symbols = 0
                    for watchlist in watchlists:
                        symbols = self.profile_manager.get_watchlist_symbols(watchlist['uid'])
                        total_symbols += len(symbols)
                    self.stats_labels["Symbols Tracked"].setText(str(total_symbols))
                except Exception as e:
                    logger.warning(f"Failed to get watchlist statistics: {e}")
                    self.stats_labels["Watchlists"].setText("Error")
                    self.stats_labels["Symbols Tracked"].setText("Error")
            else:
                self.stats_labels["Watchlists"].setText("No profile")
                self.stats_labels["Symbols Tracked"].setText("No profile")
            
            # Update status
            self.update_status("Statistics refreshed")
            
        except Exception as e:
            logger.error(f"Statistics refresh failed: {e}")
            self.update_status(f"Statistics refresh failed: {e}")
    
    def log_activity(self, message: str):
        """Log activity to the dashboard."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.activity_display.append(f"[{timestamp}] {message}")
        
        # Keep only last 50 entries to prevent excessive memory usage
        document = self.activity_display.document()
        if document.blockCount() > 50:
            cursor = self.activity_display.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.movePosition(cursor.MoveOperation.Down, cursor.MoveMode.KeepAnchor)
            cursor.removeSelectedText()
        
        # Scroll to bottom
        self.activity_display.verticalScrollBar().setValue(
            self.activity_display.verticalScrollBar().maximum()
        )
    
    def update_status(self, message: str):
        """Update the system status display."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.status_display.setText(f"[{timestamp}] {message}")
    
    def clear_activity(self):
        """Clear the activity display."""
        self.activity_display.clear()
        self.log_activity("Activity cleared")
    
    def update_statistics_from_external(self, stats_dict: Dict[str, str]):
        """Update statistics from external source."""
        for key, value in stats_dict.items():
            if key in self.stats_labels:
                self.stats_labels[key].setText(str(value))
    
    def get_stats_summary(self) -> Dict[str, str]:
        """Get current statistics summary."""
        return {key: label.text() for key, label in self.stats_labels.items()} 