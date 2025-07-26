"""
Main Window UI for AI-Driven Stock Trade Advisor

Provides a simple interface for testing user profiles and market scanning functionality.
"""

import sys
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox, QSpinBox,
    QTabWidget, QGroupBox, QTableWidget, QTableWidgetItem, QMessageBox,
    QProgressBar, QSplitter, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.utils.database_manager import DatabaseManager
from src.profile.profile_manager import ProfileManager
from src.data_layer.market_scanner import MarketScanner

logger = logging.getLogger(__name__)


class ScannerWorker(QThread):
    """Background worker for market scanning operations."""
    
    scan_complete = pyqtSignal(dict)
    scan_error = pyqtSignal(str)
    
    def __init__(self, scanner: MarketScanner, scan_type: str, **kwargs):
        super().__init__()
        self.scanner = scanner
        self.scan_type = scan_type
        self.kwargs = kwargs
    
    def run(self):
        try:
            if self.scan_type == "top_movers":
                result = self.scanner.scan_top_movers(**self.kwargs)
            elif self.scan_type == "watchlist":
                result = self.scanner.scan_user_watchlists(**self.kwargs)
            elif self.scan_type == "intelligent":
                result = self.scanner.get_intelligent_symbols(**self.kwargs)
            else:
                raise ValueError(f"Unknown scan type: {self.scan_type}")
            
            self.scan_complete.emit(result)
        except Exception as e:
            self.scan_error.emit(str(e))


class MainWindow(QMainWindow):
    """Main application window for the AI-Driven Stock Trade Advisor."""
    
    def __init__(self):
        super().__init__()
        self.db_manager = None
        self.profile_manager = None
        self.market_scanner = None
        self.current_user_uid = None
        self.scanner_worker = None
        
        self.init_ui()
        self.init_database()
        self.setup_connections()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("AI-Driven Stock Trade Advisor")
        self.setGeometry(100, 100, 1200, 800)
        
        # Set up central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_profile_tab()
        self.create_market_scanner_tab()
        self.create_watchlist_tab()
        self.create_dashboard_tab()
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        # Apply styling
        self.apply_styling()
    
    def create_profile_tab(self):
        """Create the user profile management tab."""
        profile_widget = QWidget()
        layout = QVBoxLayout(profile_widget)
        
        # User Profile Section
        profile_group = QGroupBox("User Profile Management")
        profile_layout = QGridLayout(profile_group)
        
        # Profile creation
        profile_layout.addWidget(QLabel("Username:"), 0, 0)
        self.username_input = QLineEdit()
        profile_layout.addWidget(self.username_input, 0, 1)
        
        profile_layout.addWidget(QLabel("Email:"), 1, 0)
        self.email_input = QLineEdit()
        profile_layout.addWidget(self.email_input, 1, 1)
        
        profile_layout.addWidget(QLabel("Risk Profile:"), 2, 0)
        self.risk_profile_combo = QComboBox()
        self.risk_profile_combo.addItems(["conservative", "moderate", "aggressive"])
        profile_layout.addWidget(self.risk_profile_combo, 2, 1)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.create_profile_btn = QPushButton("Create Profile")
        self.load_profile_btn = QPushButton("Load Profile")
        self.update_profile_btn = QPushButton("Update Profile")
        
        button_layout.addWidget(self.create_profile_btn)
        button_layout.addWidget(self.load_profile_btn)
        button_layout.addWidget(self.update_profile_btn)
        profile_layout.addLayout(button_layout, 3, 0, 1, 2)
        
        layout.addWidget(profile_group)
        
        # Risk Assessment Section
        risk_group = QGroupBox("Risk Assessment")
        risk_layout = QGridLayout(risk_group)
        
        risk_layout.addWidget(QLabel("Investment Timeline:"), 0, 0)
        self.timeline_combo = QComboBox()
        self.timeline_combo.addItems(["short", "medium", "long"])
        risk_layout.addWidget(self.timeline_combo, 0, 1)
        
        risk_layout.addWidget(QLabel("Risk Tolerance:"), 1, 0)
        self.tolerance_combo = QComboBox()
        self.tolerance_combo.addItems(["low", "medium", "high"])
        risk_layout.addWidget(self.tolerance_combo, 1, 1)
        
        risk_layout.addWidget(QLabel("Experience Level:"), 2, 0)
        self.experience_combo = QComboBox()
        self.experience_combo.addItems(["beginner", "intermediate", "expert"])
        risk_layout.addWidget(self.experience_combo, 2, 1)
        
        risk_layout.addWidget(QLabel("Investment Goals:"), 3, 0)
        self.goals_combo = QComboBox()
        self.goals_combo.addItems(["conservative", "balanced", "aggressive"])
        risk_layout.addWidget(self.goals_combo, 3, 1)
        
        self.update_risk_btn = QPushButton("Update Risk Assessment")
        risk_layout.addWidget(self.update_risk_btn, 4, 0, 1, 2)
        
        layout.addWidget(risk_group)
        
        # Profile Display
        self.profile_display = QTextEdit()
        self.profile_display.setReadOnly(True)
        self.profile_display.setMaximumHeight(200)
        layout.addWidget(QLabel("Profile Information:"))
        layout.addWidget(self.profile_display)
        
        layout.addStretch()
        self.tab_widget.addTab(profile_widget, "User Profile")
    
    def create_market_scanner_tab(self):
        """Create the market scanner tab."""
        scanner_widget = QWidget()
        layout = QVBoxLayout(scanner_widget)
        
        # Scanner Controls
        controls_group = QGroupBox("Market Scanner Controls")
        controls_layout = QGridLayout(controls_group)
        
        controls_layout.addWidget(QLabel("Scan Type:"), 0, 0)
        self.scan_type_combo = QComboBox()
        self.scan_type_combo.addItems(["Top Movers", "Intelligent Suggestions"])
        controls_layout.addWidget(self.scan_type_combo, 0, 1)
        
        controls_layout.addWidget(QLabel("Limit:"), 1, 0)
        self.scan_limit_spin = QSpinBox()
        self.scan_limit_spin.setRange(5, 100)
        self.scan_limit_spin.setValue(20)
        controls_layout.addWidget(self.scan_limit_spin, 1, 1)
        
        self.scan_btn = QPushButton("Start Scan")
        controls_layout.addWidget(self.scan_btn, 2, 0, 1, 2)
        
        layout.addWidget(controls_group)
        
        # Progress bar
        self.scan_progress = QProgressBar()
        self.scan_progress.setVisible(False)
        layout.addWidget(self.scan_progress)
        
        # Results display
        results_group = QGroupBox("Scan Results")
        results_layout = QVBoxLayout(results_group)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels([
            "Symbol", "Change %", "Price", "Volume", "Sector", "Category"
        ])
        results_layout.addWidget(self.results_table)
        
        layout.addWidget(results_group)
        
        layout.addStretch()
        self.tab_widget.addTab(scanner_widget, "Market Scanner")
    
    def create_watchlist_tab(self):
        """Create the watchlist management tab."""
        watchlist_widget = QWidget()
        layout = QVBoxLayout(watchlist_widget)
        
        # Watchlist Creation
        create_group = QGroupBox("Create Watchlist")
        create_layout = QGridLayout(create_group)
        
        create_layout.addWidget(QLabel("Watchlist Name:"), 0, 0)
        self.watchlist_name_input = QLineEdit()
        create_layout.addWidget(self.watchlist_name_input, 0, 1)
        
        create_layout.addWidget(QLabel("Description:"), 1, 0)
        self.watchlist_desc_input = QLineEdit()
        create_layout.addWidget(self.watchlist_desc_input, 1, 1)
        
        self.create_watchlist_btn = QPushButton("Create Watchlist")
        create_layout.addWidget(self.create_watchlist_btn, 2, 0, 1, 2)
        
        layout.addWidget(create_group)
        
        # Add Symbols
        symbols_group = QGroupBox("Add Symbols to Watchlist")
        symbols_layout = QGridLayout(symbols_group)
        
        symbols_layout.addWidget(QLabel("Symbol:"), 0, 0)
        self.symbol_input = QLineEdit()
        symbols_layout.addWidget(self.symbol_input, 0, 1)
        
        symbols_layout.addWidget(QLabel("Priority:"), 1, 0)
        self.priority_spin = QSpinBox()
        self.priority_spin.setRange(1, 10)
        self.priority_spin.setValue(5)
        symbols_layout.addWidget(self.priority_spin, 1, 1)
        
        symbols_layout.addWidget(QLabel("Notes:"), 2, 0)
        self.notes_input = QLineEdit()
        symbols_layout.addWidget(self.notes_input, 2, 1)
        
        self.add_symbol_btn = QPushButton("Add Symbol")
        symbols_layout.addWidget(self.add_symbol_btn, 3, 0, 1, 2)
        
        layout.addWidget(symbols_group)
        
        # Watchlist Display
        self.watchlist_table = QTableWidget()
        self.watchlist_table.setColumnCount(5)
        self.watchlist_table.setHorizontalHeaderLabels([
            "Symbol", "Priority", "Notes", "Added Date", "Actions"
        ])
        layout.addWidget(QLabel("Current Watchlist:"))
        layout.addWidget(self.watchlist_table)
        
        layout.addStretch()
        self.tab_widget.addTab(watchlist_widget, "Watchlist")
    
    def create_dashboard_tab(self):
        """Create the dashboard tab."""
        dashboard_widget = QWidget()
        layout = QVBoxLayout(dashboard_widget)
        
        # Quick Stats
        stats_group = QGroupBox("Quick Statistics")
        stats_layout = QGridLayout(stats_group)
        
        self.stats_labels = {}
        stats = ["Total Scans", "Symbols Tracked", "Watchlists", "Last Scan"]
        
        for i, stat in enumerate(stats):
            stats_layout.addWidget(QLabel(f"{stat}:"), i, 0)
            self.stats_labels[stat] = QLabel("0")
            stats_layout.addWidget(self.stats_labels[stat], i, 1)
        
        layout.addWidget(stats_group)
        
        # Recent Activity
        activity_group = QGroupBox("Recent Activity")
        activity_layout = QVBoxLayout(activity_group)
        
        self.activity_display = QTextEdit()
        self.activity_display.setReadOnly(True)
        self.activity_display.setMaximumHeight(300)
        activity_layout.addWidget(self.activity_display)
        
        layout.addWidget(activity_group)
        
        # Quick Actions
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QHBoxLayout(actions_group)
        
        self.quick_scan_btn = QPushButton("Quick Market Scan")
        self.refresh_stats_btn = QPushButton("Refresh Statistics")
        self.clear_activity_btn = QPushButton("Clear Activity")
        
        actions_layout.addWidget(self.quick_scan_btn)
        actions_layout.addWidget(self.refresh_stats_btn)
        actions_layout.addWidget(self.clear_activity_btn)
        
        layout.addWidget(actions_group)
        
        layout.addStretch()
        self.tab_widget.addTab(dashboard_widget, "Dashboard")
    
    def init_database(self):
        """Initialize database connection."""
        try:
            self.db_manager = DatabaseManager("data/trading_advisor.db")
            self.profile_manager = ProfileManager(self.db_manager)
            self.market_scanner = MarketScanner(self.db_manager)
            
            self.statusBar().showMessage("Database connected successfully")
            self.log_activity("Database initialized successfully")
            
            # Try to load default profile
            self.load_default_profile()
            
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to initialize database: {e}")
            logger.error(f"Database initialization failed: {e}")
    
    def load_default_profile(self):
        """Load default profile if available."""
        try:
            # Look for a default user profile
            users = self.db_manager.users.get_all_users(active_only=True)
            if users:
                # Use the first available user
                default_user = users[0]
                self.current_user_uid = default_user['uid']
                
                # Populate UI with default user data
                self.username_input.setText(default_user.get('username', ''))
                self.email_input.setText(default_user.get('email', ''))
                
                risk_profile = default_user.get('risk_profile', 'moderate')
                index = self.risk_profile_combo.findText(risk_profile)
                if index >= 0:
                    self.risk_profile_combo.setCurrentIndex(index)
                
                self.statusBar().showMessage(f"Loaded default profile: {default_user['username']}")
                self.log_activity(f"Loaded default profile: {default_user['username']}")
                self.display_profile_info()
                
                logger.info(f"Loaded default profile: {default_user['username']} ({self.current_user_uid})")
            else:
                logger.info("No default profile found")
                
        except Exception as e:
            logger.error(f"Failed to load default profile: {e}")
    
    def setup_connections(self):
        """Set up signal connections."""
        # Profile management
        self.create_profile_btn.clicked.connect(self.create_user_profile)
        self.load_profile_btn.clicked.connect(self.load_user_profile)
        self.update_profile_btn.clicked.connect(self.update_user_profile)
        self.update_risk_btn.clicked.connect(self.update_risk_assessment)
        
        # Market scanner
        self.scan_btn.clicked.connect(self.start_market_scan)
        
        # Watchlist management
        self.create_watchlist_btn.clicked.connect(self.create_watchlist)
        self.add_symbol_btn.clicked.connect(self.add_symbol_to_watchlist)
        
        # Dashboard
        self.quick_scan_btn.clicked.connect(self.quick_market_scan)
        self.refresh_stats_btn.clicked.connect(self.refresh_statistics)
        self.clear_activity_btn.clicked.connect(self.clear_activity)
    
    def create_user_profile(self):
        """Create a new user profile."""
        try:
            username = self.username_input.text().strip()
            email = self.email_input.text().strip()
            risk_profile = self.risk_profile_combo.currentText()
            
            if not username or not email:
                QMessageBox.warning(self, "Input Error", "Please enter both username and email")
                return
            
            user_uid = self.profile_manager.create_user_profile(
                username=username,
                email=email,
                risk_profile=risk_profile
            )
            
            if user_uid:
                self.current_user_uid = user_uid
                self.statusBar().showMessage(f"Profile created: {user_uid}")
                self.log_activity(f"Created user profile: {username}")
                self.display_profile_info()
                QMessageBox.information(self, "Success", f"Profile created successfully: {user_uid}")
            else:
                QMessageBox.critical(self, "Error", "Failed to create profile")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create profile: {e}")
            logger.error(f"Profile creation failed: {e}")
    
    def load_user_profile(self):
        """Load an existing user profile."""
        try:
            username = self.username_input.text().strip()
            if not username:
                QMessageBox.warning(self, "Input Error", "Please enter a username")
                return
            
            profile_data = self.profile_manager.get_user_profile_by_username(username)
            if profile_data:
                self.current_user_uid = profile_data['uid']
                self.email_input.setText(profile_data.get('email', ''))
                self.risk_profile_combo.setCurrentText(profile_data.get('risk_profile', 'moderate'))
                
                self.statusBar().showMessage(f"Profile loaded: {self.current_user_uid}")
                self.log_activity(f"Loaded user profile: {username}")
                self.display_profile_info()
            else:
                QMessageBox.warning(self, "Not Found", f"No profile found for username: {username}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load profile: {e}")
            logger.error(f"Profile loading failed: {e}")
    
    def update_user_profile(self):
        """Update the current user profile."""
        if not self.current_user_uid:
            QMessageBox.warning(self, "No Profile", "Please create or load a profile first")
            return
        
        try:
            email = self.email_input.text().strip()
            risk_profile = self.risk_profile_combo.currentText()
            
            success = self.profile_manager.update_user_profile(
                user_uid=self.current_user_uid,
                email=email,
                risk_profile=risk_profile
            )
            
            if success:
                self.statusBar().showMessage("Profile updated successfully")
                self.log_activity("Updated user profile")
                self.display_profile_info()
                QMessageBox.information(self, "Success", "Profile updated successfully")
            else:
                QMessageBox.critical(self, "Error", "Failed to update profile")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update profile: {e}")
            logger.error(f"Profile update failed: {e}")
    
    def update_risk_assessment(self):
        """Update the user's risk assessment."""
        if not self.current_user_uid:
            QMessageBox.warning(self, "No Profile", "Please create or load a profile first")
            return
        
        try:
            risk_assessment = {
                'investment_timeline': self.timeline_combo.currentText(),
                'risk_tolerance': self.tolerance_combo.currentText(),
                'experience': self.experience_combo.currentText(),
                'goals': self.goals_combo.currentText()
            }
            
            success = self.profile_manager.update_risk_profile(
                user_uid=self.current_user_uid,
                risk_assessment=risk_assessment
            )
            
            if success:
                self.statusBar().showMessage("Risk assessment updated successfully")
                self.log_activity("Updated risk assessment")
                self.display_profile_info()
                QMessageBox.information(self, "Success", "Risk assessment updated successfully")
            else:
                QMessageBox.critical(self, "Error", "Failed to update risk assessment")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update risk assessment: {e}")
            logger.error(f"Risk assessment update failed: {e}")
    
    def display_profile_info(self):
        """Display current profile information."""
        if not self.current_user_uid:
            self.profile_display.setText("No profile loaded")
            return
        
        try:
            profile_data = self.profile_manager.get_user_profile(self.current_user_uid)
            if profile_data and 'user' in profile_data:
                user_data = profile_data['user']
                info = f"User ID: {user_data.get('uid', 'N/A')}\n"
                info += f"Username: {user_data.get('username', 'N/A')}\n"
                info += f"Email: {user_data.get('email', 'N/A')}\n"
                info += f"Risk Profile: {user_data.get('risk_profile', 'N/A')}\n"
                info += f"Created: {user_data.get('created_at', 'N/A')}\n"
                info += f"Updated: {user_data.get('updated_at', 'N/A')}\n"
                
                # Watchlists info
                watchlists = profile_data.get('watchlists', [])
                if watchlists:
                    info += f"\nWatchlists ({len(watchlists)}):\n"
                    for watchlist in watchlists:
                        info += f"  • {watchlist.get('name', 'N/A')}\n"
                
                # Preferences info
                preferences = profile_data.get('preferences', {})
                if preferences:
                    info += f"\nPreferences:\n"
                    for key, value in preferences.items():
                        info += f"  {key}: {value}\n"
                
                self.profile_display.setText(info)
            else:
                self.profile_display.setText("Profile not found")
                
        except Exception as e:
            self.profile_display.setText(f"Error loading profile: {e}")
            logger.error(f"Profile display failed: {e}")
    
    def start_market_scan(self):
        """Start a market scan operation."""
        if not self.current_user_uid:
            QMessageBox.warning(self, "No Profile", "Please create or load a profile first")
            return
        
        try:
            scan_type = self.scan_type_combo.currentText()
            limit = self.scan_limit_spin.value()
            
            self.scan_btn.setEnabled(False)
            self.scan_progress.setVisible(True)
            self.scan_progress.setRange(0, 0)  # Indeterminate progress
            
            # Determine scan type
            if scan_type == "Top Movers":
                scan_type_enum = "top_movers"
                kwargs = {"limit": limit}
            else:  # Intelligent Suggestions
                scan_type_enum = "intelligent"
                kwargs = {"user_uid": self.current_user_uid, "limit": limit}
            
            # Start background scan
            self.scanner_worker = ScannerWorker(self.market_scanner, scan_type_enum, **kwargs)
            self.scanner_worker.scan_complete.connect(self.handle_scan_results)
            self.scanner_worker.scan_error.connect(self.handle_scan_error)
            self.scanner_worker.finished.connect(self.scan_finished)
            self.scanner_worker.start()
            
            self.statusBar().showMessage("Scanning market data...")
            self.log_activity(f"Started {scan_type} scan")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start scan: {e}")
            logger.error(f"Market scan failed: {e}")
            self.scan_finished()
    
    def handle_scan_results(self, results: Dict[str, Any]):
        """Handle scan results from background worker."""
        try:
            self.populate_results_table(results)
            self.statusBar().showMessage("Scan completed successfully")
            self.log_activity("Market scan completed")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process scan results: {e}")
            logger.error(f"Scan results processing failed: {e}")
    
    def handle_scan_error(self, error: str):
        """Handle scan error from background worker."""
        QMessageBox.critical(self, "Scan Error", f"Market scan failed: {error}")
        logger.error(f"Market scan error: {error}")
        self.statusBar().showMessage("Scan failed")
    
    def scan_finished(self):
        """Handle scan completion."""
        self.scan_btn.setEnabled(True)
        self.scan_progress.setVisible(False)
    
    def populate_results_table(self, results: Dict[str, Any]):
        """Populate the results table with scan data."""
        try:
            self.results_table.setRowCount(0)
            
            # Handle different result formats
            if 'gainers' in results and 'losers' in results:
                # Top movers format
                all_symbols = results.get('gainers', []) + results.get('losers', [])
            elif isinstance(results, list):
                # Intelligent suggestions format
                all_symbols = results
            else:
                all_symbols = []
            
            self.results_table.setRowCount(len(all_symbols))
            
            for row, symbol_data in enumerate(all_symbols):
                self.results_table.setItem(row, 0, QTableWidgetItem(symbol_data.get('symbol', '')))
                
                change_pct = symbol_data.get('change_percent', 0)
                change_text = f"{change_pct:.2f}%" if change_pct else "N/A"
                self.results_table.setItem(row, 1, QTableWidgetItem(change_text))
                
                price = symbol_data.get('price', 0)
                price_text = f"${price:.2f}" if price else "N/A"
                self.results_table.setItem(row, 2, QTableWidgetItem(price_text))
                
                volume = symbol_data.get('volume', 0)
                volume_text = f"{volume:,}" if volume else "N/A"
                self.results_table.setItem(row, 3, QTableWidgetItem(volume_text))
                
                self.results_table.setItem(row, 4, QTableWidgetItem(symbol_data.get('sector', 'N/A')))
                self.results_table.setItem(row, 5, QTableWidgetItem(symbol_data.get('category', 'N/A')))
            
            # Update statistics
            self.stats_labels["Total Scans"].setText(str(int(self.stats_labels["Total Scans"].text()) + 1))
            self.stats_labels["Symbols Tracked"].setText(str(len(all_symbols)))
            
        except Exception as e:
            logger.error(f"Failed to populate results table: {e}")
    
    def create_watchlist(self):
        """Create a new watchlist."""
        if not self.current_user_uid:
            QMessageBox.warning(self, "No Profile", "Please create or load a profile first")
            return
        
        try:
            name = self.watchlist_name_input.text().strip()
            description = self.watchlist_desc_input.text().strip()
            
            if not name:
                QMessageBox.warning(self, "Input Error", "Please enter a watchlist name")
                return
            
            watchlist_uid = self.profile_manager.create_watchlist(
                user_uid=self.current_user_uid,
                name=name,
                description=description
            )
            
            if watchlist_uid:
                self.statusBar().showMessage(f"Watchlist created: {watchlist_uid}")
                self.log_activity(f"Created watchlist: {name}")
                self.refresh_watchlist_display()
                QMessageBox.information(self, "Success", f"Watchlist created successfully: {watchlist_uid}")
            else:
                QMessageBox.critical(self, "Error", "Failed to create watchlist")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create watchlist: {e}")
            logger.error(f"Watchlist creation failed: {e}")
    
    def add_symbol_to_watchlist(self):
        """Add a symbol to the current watchlist."""
        if not self.current_user_uid:
            QMessageBox.warning(self, "No Profile", "Please create or load a profile first")
            return
        
        try:
            symbol = self.symbol_input.text().strip().upper()
            priority = self.priority_spin.value()
            notes = self.notes_input.text().strip()
            
            if not symbol:
                QMessageBox.warning(self, "Input Error", "Please enter a symbol")
                return
            
            # Get user's default watchlist
            watchlists = self.profile_manager.get_user_watchlists(self.current_user_uid)
            if not watchlists:
                QMessageBox.warning(self, "No Watchlist", "Please create a watchlist first")
                return
            
            watchlist_uid = watchlists[0]['uid']  # Use first watchlist
            
            success = self.profile_manager.add_symbol_to_watchlist(
                watchlist_uid=watchlist_uid,
                symbol=symbol,
                priority=priority,
                notes=notes
            )
            
            if success:
                self.statusBar().showMessage(f"Added {symbol} to watchlist")
                self.log_activity(f"Added {symbol} to watchlist")
                self.refresh_watchlist_display()
                self.symbol_input.clear()
                self.notes_input.clear()
                QMessageBox.information(self, "Success", f"Added {symbol} to watchlist")
            else:
                QMessageBox.critical(self, "Error", f"Failed to add {symbol} to watchlist")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add symbol: {e}")
            logger.error(f"Symbol addition failed: {e}")
    
    def refresh_watchlist_display(self):
        """Refresh the watchlist display."""
        if not self.current_user_uid:
            return
        
        try:
            watchlists = self.profile_manager.get_user_watchlists(self.current_user_uid)
            if not watchlists:
                self.watchlist_table.setRowCount(0)
                return
            
            # Get symbols from first watchlist
            watchlist_uid = watchlists[0]['uid']
            symbols = self.profile_manager.get_watchlist_symbols(watchlist_uid)
            
            self.watchlist_table.setRowCount(len(symbols))
            
            for row, symbol_data in enumerate(symbols):
                self.watchlist_table.setItem(row, 0, QTableWidgetItem(symbol_data.get('symbol', '')))
                self.watchlist_table.setItem(row, 1, QTableWidgetItem(str(symbol_data.get('priority', ''))))
                self.watchlist_table.setItem(row, 2, QTableWidgetItem(symbol_data.get('notes', '')))
                self.watchlist_table.setItem(row, 3, QTableWidgetItem(symbol_data.get('added_at', '')))
                
                # Add remove button
                remove_btn = QPushButton("Remove")
                remove_btn.clicked.connect(lambda checked, s=symbol_data['symbol']: self.remove_symbol_from_watchlist(s))
                self.watchlist_table.setCellWidget(row, 4, remove_btn)
            
            # Update statistics
            self.stats_labels["Watchlists"].setText(str(len(watchlists)))
            
        except Exception as e:
            logger.error(f"Failed to refresh watchlist display: {e}")
    
    def remove_symbol_from_watchlist(self, symbol: str):
        """Remove a symbol from the watchlist."""
        try:
            watchlists = self.profile_manager.get_user_watchlists(self.current_user_uid)
            if watchlists:
                watchlist_uid = watchlists[0]['uid']
                success = self.profile_manager.remove_symbol_from_watchlist(watchlist_uid, symbol)
                
                if success:
                    self.statusBar().showMessage(f"Removed {symbol} from watchlist")
                    self.log_activity(f"Removed {symbol} from watchlist")
                    self.refresh_watchlist_display()
                else:
                    QMessageBox.warning(self, "Error", f"Failed to remove {symbol}")
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to remove symbol: {e}")
            logger.error(f"Symbol removal failed: {e}")
    
    def quick_market_scan(self):
        """Perform a quick market scan."""
        self.tab_widget.setCurrentIndex(1)  # Switch to scanner tab
        self.scan_limit_spin.setValue(10)
        self.scan_type_combo.setCurrentText("Top Movers")
        self.start_market_scan()
    
    def refresh_statistics(self):
        """Refresh dashboard statistics."""
        try:
            if self.current_user_uid:
                # Get scanner statistics
                stats = self.market_scanner.get_scan_statistics()
                self.stats_labels["Total Scans"].setText(str(stats.get('scans_completed', 0)))
                
                # Get watchlist count
                watchlists = self.profile_manager.get_user_watchlists(self.current_user_uid)
                self.stats_labels["Watchlists"].setText(str(len(watchlists)))
                
                # Get symbols count
                total_symbols = 0
                for watchlist in watchlists:
                    symbols = self.profile_manager.get_watchlist_symbols(watchlist['uid'])
                    total_symbols += len(symbols)
                self.stats_labels["Symbols Tracked"].setText(str(total_symbols))
                
                # Update last scan
                last_scan = stats.get('last_scan')
                if last_scan:
                    self.stats_labels["Last Scan"].setText(last_scan)
                
                self.statusBar().showMessage("Statistics refreshed")
                self.log_activity("Refreshed statistics")
            else:
                self.statusBar().showMessage("No profile loaded")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh statistics: {e}")
            logger.error(f"Statistics refresh failed: {e}")
    
    def clear_activity(self):
        """Clear the activity display."""
        self.activity_display.clear()
        self.log_activity("Activity cleared")
    
    def log_activity(self, message: str):
        """Log activity to the dashboard."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.activity_display.append(f"[{timestamp}] {message}")
    
    def apply_styling(self):
        """Apply custom styling to the application."""
        # Set application style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 8px 16px;
                text-align: center;
                font-size: 14px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QLineEdit, QComboBox, QSpinBox {
                padding: 5px;
                border: 1px solid #cccccc;
                border-radius: 3px;
                font-size: 12px;
            }
            QTableWidget {
                gridline-color: #cccccc;
                background-color: white;
                alternate-background-color: #f9f9f9;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTextEdit {
                border: 1px solid #cccccc;
                border-radius: 3px;
                background-color: white;
            }
        """)
    
    def closeEvent(self, event):
        """Handle application close event."""
        try:
            if self.db_manager:
                self.db_manager.close()
            event.accept()
        except Exception as e:
            logger.error(f"Error during application close: {e}")
            event.accept()


def main():
    """Main application entry point."""
    import sys
    from PyQt6.QtWidgets import QApplication
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("AI-Driven Stock Trade Advisor")
    app.setApplicationVersion("0.2.0")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 