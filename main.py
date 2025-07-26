#!/usr/bin/env python3
"""
AI-Driven Stock Trade Advisor - Main Application Entry Point

This is the main entry point for the AI-Driven Stock Trade Advisor application.
It initializes all components and starts the user interface.
"""

import sys
import logging
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from config.config import (
    APP_NAME, 
    APP_VERSION, 
    LOG_LEVEL, 
    LOG_FILE, 
    DEBUG_MODE
)
from config.logging_config import setup_logging
from src.utils.database_manager import DatabaseManager
from src.profile.profile_manager import ProfileManager
from src.strategy.trading_engine import TradingEngine
from src.strategy.signal_generator import SignalGenerator
from src.ui.main_window import MainWindow
from PyQt6.QtWidgets import QApplication


def initialize_trading_system():
    """Initialize the trading system components."""
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize database manager
        db_manager = DatabaseManager()
        logger.info("Database manager initialized")
        
        # Initialize profile manager
        profile_manager = ProfileManager(db_manager)
        logger.info("Profile manager initialized")
        
        # Initialize trading engine
        trading_engine = TradingEngine(db_manager, profile_manager)
        logger.info("Trading engine initialized")
        
        # Initialize signal generator
        signal_generator = SignalGenerator(db_manager, trading_engine)
        logger.info("Signal generator initialized")
        
        return {
            'db_manager': db_manager,
            'profile_manager': profile_manager,
            'trading_engine': trading_engine,
            'signal_generator': signal_generator
        }
        
    except Exception as e:
        logger.error(f"Failed to initialize trading system: {e}")
        raise


def main():
    """Main application entry point."""
    
    # Setup logging
    setup_logging(LOG_LEVEL, LOG_FILE)
    logger = logging.getLogger(__name__)
    
    logger.info(f"Starting {APP_NAME} v{APP_VERSION}")
    logger.info(f"Debug mode: {DEBUG_MODE}")
    
    try:
        # Initialize trading system
        trading_system = initialize_trading_system()
        logger.info("Trading system initialized successfully")
        
        # Create Qt application
        app = QApplication(sys.argv)
        app.setApplicationName(APP_NAME)
        app.setApplicationVersion(APP_VERSION)
        
        # Create and show main window with trading system
        main_window = MainWindow(trading_system)
        main_window.show()
        
        logger.info("Application started successfully")
        
        # Start event loop
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 