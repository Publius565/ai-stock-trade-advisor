#!/usr/bin/env python3
"""
UI Launcher for AI-Driven Stock Trade Advisor

Simple launcher script to run the main application UI.
"""

import sys
import os
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def setup_environment():
    """Set up the environment for the UI."""
    # Create data directory if it doesn't exist
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Create cache directory if it doesn't exist
    cache_dir = data_dir / "cache"
    cache_dir.mkdir(exist_ok=True)
    
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

def main():
    """Main launcher function."""
    try:
        # Set up environment
        setup_environment()
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/ui.log'),
                logging.StreamHandler()
            ]
        )
        
        logger = logging.getLogger(__name__)
        logger.info("Starting AI-Driven Stock Trade Advisor UI")
        
        # Import and run UI
        from src.ui.main_window import main as ui_main
        ui_main()
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Please ensure all dependencies are installed:")
        print("pip install PyQt6 pandas numpy requests python-dotenv yfinance")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting UI: {e}")
        logging.error(f"UI startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 