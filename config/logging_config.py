"""
Logging Configuration

This module configures logging for the AI-Driven Stock Trade Advisor application.
It sets up different loggers for different components and handles log rotation.
"""

import logging
import logging.handlers
import os
from pathlib import Path
from datetime import datetime

def setup_logging(log_level="INFO", log_file=None, max_size_mb=10, backup_count=5):
    """
    Setup logging configuration for the application.
    
    Args:
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file (str): Path to log file
        max_size_mb (int): Maximum log file size in MB
        backup_count (int): Number of backup log files to keep
    """
    
    # Create logs directory if it doesn't exist
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert string log level to logging constant
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_size_mb * 1024 * 1024,  # Convert MB to bytes
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Create specific loggers for different components
    loggers = {
        'data_layer': logging.getLogger('data_layer'),
        'profile': logging.getLogger('profile'),
        'strategy': logging.getLogger('strategy'),
        'execution': logging.getLogger('execution'),
        'ml_models': logging.getLogger('ml_models'),
        'ui': logging.getLogger('ui'),
        'utils': logging.getLogger('utils'),
        'database': logging.getLogger('database'),
        'api': logging.getLogger('api'),
        'security': logging.getLogger('security'),
        'audit': logging.getLogger('audit')
    }
    
    # Set levels for specific loggers
    for logger_name, logger in loggers.items():
        logger.setLevel(level)
    
    # Log startup message
    startup_logger = logging.getLogger('startup')
    startup_logger.info("=" * 60)
    startup_logger.info("AI-Driven Stock Trade Advisor - Application Startup")
    startup_logger.info(f"Log level: {log_level}")
    startup_logger.info(f"Log file: {log_file}")
    startup_logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    startup_logger.info("=" * 60)
    
    return loggers

def get_logger(name):
    """
    Get a logger instance for a specific component.
    
    Args:
        name (str): Logger name (component name)
    
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)

def log_function_call(logger, function_name, args=None, kwargs=None):
    """
    Decorator to log function calls for debugging.
    
    Args:
        logger: Logger instance
        function_name (str): Name of the function being called
        args: Function arguments
        kwargs: Function keyword arguments
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.debug(f"Calling {function_name} with args={args}, kwargs={kwargs}")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"{function_name} returned: {result}")
                return result
            except Exception as e:
                logger.error(f"Error in {function_name}: {e}")
                raise
        return wrapper
    return decorator

def log_api_call(logger, api_name, endpoint, response_code, response_time_ms):
    """
    Log API call details for monitoring and debugging.
    
    Args:
        logger: Logger instance
        api_name (str): Name of the API
        endpoint (str): API endpoint
        response_code (int): HTTP response code
        response_time_ms (int): Response time in milliseconds
    """
    level = logging.INFO if response_code < 400 else logging.WARNING
    logger.log(level, f"API Call: {api_name} {endpoint} - Status: {response_code} - Time: {response_time_ms}ms")

def log_trade_activity(logger, user_id, action, symbol, quantity=None, price=None):
    """
    Log trade-related activities for audit purposes.
    
    Args:
        logger: Logger instance
        user_id (int): User ID
        action (str): Trade action (buy, sell, suggestion, etc.)
        symbol (str): Stock symbol
        quantity (int): Number of shares
        price (float): Price per share
    """
    logger.info(f"Trade Activity - User: {user_id}, Action: {action}, Symbol: {symbol}, "
                f"Quantity: {quantity}, Price: {price}")

def log_security_event(logger, event_type, user_id=None, details=None):
    """
    Log security-related events.
    
    Args:
        logger: Logger instance
        event_type (str): Type of security event
        user_id (int): User ID if applicable
        details (str): Additional details about the event
    """
    logger.warning(f"Security Event - Type: {event_type}, User: {user_id}, Details: {details}")

def log_performance_metric(logger, metric_name, value, user_id=None):
    """
    Log performance metrics for monitoring.
    
    Args:
        logger: Logger instance
        metric_name (str): Name of the performance metric
        value (float): Metric value
        user_id (int): User ID if applicable
    """
    logger.info(f"Performance Metric - {metric_name}: {value}, User: {user_id}")

def cleanup_old_logs(log_dir, days_to_keep=30):
    """
    Clean up old log files to prevent disk space issues.
    
    Args:
        log_dir (str): Directory containing log files
        days_to_keep (int): Number of days to keep log files
    """
    try:
        log_path = Path(log_dir)
        if not log_path.exists():
            return
        
        cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
        
        for log_file in log_path.glob("*.log*"):
            if log_file.stat().st_mtime < cutoff_date:
                log_file.unlink()
                logging.getLogger('cleanup').info(f"Deleted old log file: {log_file}")
    except Exception as e:
        logging.getLogger('cleanup').error(f"Error cleaning up old logs: {e}")

# Default logging configuration
DEFAULT_LOG_CONFIG = {
    'log_level': 'INFO',
    'log_file': 'logs/trading_advisor.log',
    'max_size_mb': 10,
    'backup_count': 5
} 