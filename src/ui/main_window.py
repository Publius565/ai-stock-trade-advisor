"""
Main Window UI for AI-Driven Stock Trade Advisor

Orchestrates modular UI components and application-level functionality.
"""

import sys
import os
import logging
from datetime import datetime
from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout,
    QTabWidget, QMessageBox
)
from PyQt6.QtCore import Qt

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.utils.database_manager import DatabaseManager
from src.profile.profile_manager import ProfileManager
from src.data_layer.market_scanner import MarketScanner
from src.ui.components import (
    ProfileTab, MarketScannerTab, WatchlistTab, DashboardTab, 
    MLPredictionsTab, TradingSignalsTab
)

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window for the AI-Driven Stock Trade Advisor."""
    
    def __init__(self):
        super().__init__()
        self.db_manager = None
        self.profile_manager = None
        self.market_scanner = None
        self.current_user_uid = None
        
        # Initialize components
        self.profile_tab = None
        self.scanner_tab = None
        self.watchlist_tab = None
        self.dashboard_tab = None
        self.ml_predictions_tab = None
        self.trading_signals_tab = None
        
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
        
        # Create modular tabs
        self.create_tabs()
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        # Apply styling
        self.apply_styling()
    
    def create_tabs(self):
        """Create all application tabs using modular components."""
        # Profile Tab
        self.profile_tab = ProfileTab()
        self.tab_widget.addTab(self.profile_tab, "User Profile")
        
        # Market Scanner Tab
        self.scanner_tab = MarketScannerTab()
        self.tab_widget.addTab(self.scanner_tab, "Market Scanner")
        
        # Watchlist Tab
        self.watchlist_tab = WatchlistTab()
        self.tab_widget.addTab(self.watchlist_tab, "Watchlist")
        
        # ML Predictions Tab - NEW FEATURE
        self.ml_predictions_tab = MLPredictionsTab()
        self.tab_widget.addTab(self.ml_predictions_tab, "🤖 AI Predictions")
        
        # Trading Signals Tab - NEW FEATURE  
        self.trading_signals_tab = TradingSignalsTab()
        self.tab_widget.addTab(self.trading_signals_tab, "📈 Trading Signals")
        
        # Dashboard Tab
        self.dashboard_tab = DashboardTab()
        self.tab_widget.addTab(self.dashboard_tab, "Dashboard")
    
    def init_database(self):
        """Initialize database and managers."""
        try:
            # Initialize database manager
            self.db_manager = DatabaseManager()
            logger.info("Database manager initialized")
            
            # Initialize profile manager
            self.profile_manager = ProfileManager(self.db_manager)
            logger.info("Profile manager initialized")
            
            # Initialize market scanner
            self.market_scanner = MarketScanner(self.db_manager)
            logger.info("Market scanner initialized")
            
            # Set managers in tabs
            self.profile_tab.set_profile_manager(self.profile_manager)
            self.scanner_tab.set_market_scanner(self.market_scanner)
            self.watchlist_tab.set_profile_manager(self.profile_manager)
            self.dashboard_tab.set_market_scanner(self.market_scanner)
            self.dashboard_tab.set_profile_manager(self.profile_manager)
            
            # Set managers in new ML and Trading tabs
            self.ml_predictions_tab.set_db_manager(self.db_manager)
            self.ml_predictions_tab.set_profile_manager(self.profile_manager)
            self.trading_signals_tab.set_db_manager(self.db_manager)
            self.trading_signals_tab.set_profile_manager(self.profile_manager)
            
            self.statusBar().showMessage("Managers initialized successfully")
            
        except Exception as e:
            error_msg = f"Failed to initialize database/managers: {e}"
            logger.error(error_msg)
            QMessageBox.critical(self, "Initialization Error", error_msg)
            self.statusBar().showMessage("Initialization failed")
    
    def setup_connections(self):
        """Set up signal connections between components."""
        if self.profile_tab:
            # Profile tab signals
            self.profile_tab.profile_created.connect(self.on_profile_created)
            self.profile_tab.profile_loaded.connect(self.on_profile_loaded)
            self.profile_tab.activity_logged.connect(self.log_activity)
            self.profile_tab.status_updated.connect(self.update_status)
        
        if self.scanner_tab:
            # Scanner tab signals
            self.scanner_tab.activity_logged.connect(self.log_activity)
            self.scanner_tab.status_updated.connect(self.update_status)
        
        if self.watchlist_tab:
            # Watchlist tab signals
            self.watchlist_tab.activity_logged.connect(self.log_activity)
            self.watchlist_tab.status_updated.connect(self.update_status)
        
        if self.dashboard_tab:
            # Dashboard tab signals
            self.dashboard_tab.activity_logged.connect(self.log_activity)
            self.dashboard_tab.status_updated.connect(self.update_status)
            self.dashboard_tab.quick_scan_requested.connect(self.quick_market_scan)
        
        if self.ml_predictions_tab:
            # ML Predictions tab signals
            self.ml_predictions_tab.activity_logged.connect(self.log_activity)
            self.ml_predictions_tab.status_updated.connect(self.update_status)
        
        if self.trading_signals_tab:
            # Trading Signals tab signals
            self.trading_signals_tab.activity_logged.connect(self.log_activity)
            self.trading_signals_tab.status_updated.connect(self.update_status)
    
    def on_profile_created(self, user_uid: str):
        """Handle profile creation."""
        self.current_user_uid = user_uid
        self.update_all_tabs_user(user_uid)
        logger.info(f"Profile created: {user_uid}")
    
    def on_profile_loaded(self, user_uid: str):
        """Handle profile loading."""
        self.current_user_uid = user_uid
        self.update_all_tabs_user(user_uid)
        logger.info(f"Profile loaded: {user_uid}")
    
    def update_all_tabs_user(self, user_uid: str):
        """Update all tabs with current user UID."""
        if self.profile_tab:
            self.profile_tab.set_current_user(user_uid)
        if self.watchlist_tab:
            self.watchlist_tab.set_current_user(user_uid)
        if self.dashboard_tab:
            self.dashboard_tab.set_current_user(user_uid)
        if self.ml_predictions_tab:
            self.ml_predictions_tab.set_current_user(user_uid)
        if self.trading_signals_tab:
            self.trading_signals_tab.set_current_user(user_uid)
    
    def log_activity(self, message: str):
        """Log activity to dashboard."""
        if self.dashboard_tab:
            self.dashboard_tab.log_activity(message)
    
    def update_status(self, message: str):
        """Update status bar and dashboard status."""
        self.statusBar().showMessage(message)
        if self.dashboard_tab:
            self.dashboard_tab.update_status(message)
    
    def quick_market_scan(self):
        """Perform a quick market scan."""
        try:
            # Switch to scanner tab
            self.tab_widget.setCurrentIndex(1)
            
            # Set quick scan parameters
            if self.scanner_tab:
                self.scanner_tab.set_scan_limit(10)
                self.scanner_tab.set_scan_type("Top Movers")
                self.scanner_tab.start_market_scan()
            
            self.log_activity("Quick market scan initiated")
            
        except Exception as e:
            error_msg = f"Quick scan failed: {e}"
            logger.error(error_msg)
            QMessageBox.critical(self, "Scan Error", error_msg)
    
    def apply_styling(self):
        """Apply custom styling to the application."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
                color: #333333;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 15px;
                background-color: #fafafa;
                color: #333333;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                color: #2c3e50;
                font-size: 13px;
            }
            QPushButton {
                background-color: #3498db;
                border: none;
                color: white;
                padding: 10px 20px;
                text-align: center;
                font-size: 13px;
                font-weight: bold;
                border-radius: 6px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
            QLineEdit, QComboBox, QSpinBox {
                padding: 8px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                font-size: 12px;
                background-color: white;
                color: #333333;
                selection-background-color: #3498db;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
                border-color: #3498db;
            }
            QTableWidget {
                gridline-color: #e0e0e0;
                background-color: white;
                alternate-background-color: #f8f9fa;
                color: #333333;
                font-size: 12px;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
            }
            QTableWidget::item {
                padding: 8px;
                color: #333333;
                background-color: transparent;
                border-bottom: 1px solid #f0f0f0;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QTableWidget::item:hover {
                background-color: #ecf0f1;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
                font-size: 12px;
            }
            QTextEdit {
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                background-color: white;
                color: #333333;
                padding: 8px;
                font-size: 12px;
            }
            QTabWidget::pane {
                border: 2px solid #e0e0e0;
                background-color: white;
                border-radius: 6px;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                padding: 12px 20px;
                margin-right: 3px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                color: #2c3e50;
                font-weight: bold;
                font-size: 13px;
            }
            QTabBar::tab:selected {
                background-color: #3498db;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #2980b9;
                color: white;
            }
            QLabel {
                color: #2c3e50;
                font-size: 12px;
            }
            QProgressBar {
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                text-align: center;
                background-color: #ecf0f1;
                color: #2c3e50;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 4px;
            }
        """)
    
    def get_current_user_uid(self) -> Optional[str]:
        """Get the current user UID."""
        return self.current_user_uid
    
    def get_profile_manager(self) -> Optional[ProfileManager]:
        """Get the profile manager instance."""
        return self.profile_manager
    
    def get_market_scanner(self) -> Optional[MarketScanner]:
        """Get the market scanner instance."""
        return self.market_scanner
    
    def closeEvent(self, event):
        """Handle application close event."""
        try:
            # Stop any running timers in dashboard
            if self.dashboard_tab and hasattr(self.dashboard_tab, 'refresh_timer'):
                self.dashboard_tab.refresh_timer.stop()
            
            # Close database connections
            if self.db_manager:
                self.db_manager.close()
            
            self.log_activity("Application shutting down")
            logger.info("Application closed successfully")
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
    app.setApplicationVersion("0.3.0")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 