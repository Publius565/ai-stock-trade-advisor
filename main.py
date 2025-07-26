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
from src.utils.logging import setup_logging
from src.ui.main_window import MainWindow
from PyQt6.QtWidgets import QApplication


def main():
    """Main application entry point."""
    
    # Setup logging
    setup_logging(LOG_LEVEL, LOG_FILE)
    logger = logging.getLogger(__name__)
    
    logger.info(f"Starting {APP_NAME} v{APP_VERSION}")
    logger.info(f"Debug mode: {DEBUG_MODE}")
    
    try:
        # Create Qt application
        app = QApplication(sys.argv)
        app.setApplicationName(APP_NAME)
        app.setApplicationVersion(APP_VERSION)
        
        # Create and show main window
        main_window = MainWindow()
        main_window.show()
        
        logger.info("Application started successfully")
        
        # Start event loop
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 