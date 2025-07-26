"""
Configuration Management

This module handles all application configuration settings, API keys, and system parameters.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
LOGS_DIR = BASE_DIR / "logs"
CONFIG_DIR = BASE_DIR / "config"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Database configuration
DATABASE_PATH = DATA_DIR / "trading_advisor.db"

# API Configuration
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")
YAHOO_FINANCE_ENABLED = True
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY", "")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY", "")
ALPACA_BASE_URL = "https://paper-api.alpaca.markets"  # Paper trading

# Application settings
APP_NAME = "AI-Driven Stock Trade Advisor"
APP_VERSION = "0.1.0"
DEBUG_MODE = os.getenv("DEBUG_MODE", "False").lower() == "true"

# Trading settings
DEFAULT_RISK_TOLERANCE = "medium"
MAX_POSITION_SIZE = 0.1  # 10% of portfolio
STOP_LOSS_PERCENTAGE = 0.05  # 5%
TAKE_PROFIT_PERCENTAGE = 0.15  # 15%

# Data settings
CACHE_DURATION_HOURS = 24
MAX_CACHE_SIZE_MB = 1000
DATA_UPDATE_INTERVAL_MINUTES = 15

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = LOGS_DIR / "trading_advisor.log"
MAX_LOG_SIZE_MB = 10
LOG_BACKUP_COUNT = 5

# Security settings
ENCRYPTION_KEY_FILE = CONFIG_DIR / "encryption.key"
API_KEYS_FILE = CONFIG_DIR / "api_keys.env"

# UI settings
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
THEME = "light"  # or "dark"

# Machine Learning settings
MODEL_UPDATE_INTERVAL_DAYS = 7
TRAINING_DATA_DAYS = 365
PREDICTION_CONFIDENCE_THRESHOLD = 0.7

# Compliance and legal
RISK_DISCLOSURE_REQUIRED = True
AUDIT_LOGGING_ENABLED = True
DATA_RETENTION_DAYS = 2555  # 7 years 