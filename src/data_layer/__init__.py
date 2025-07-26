"""
Data Layer Module for AI-Driven Stock Trade Advisor

This module handles all data ingestion, caching, and management operations.
"""

from .api_client import APIClient
from .data_cache import DataCache
from .market_data import MarketDataManager
from .data_validator import DataValidator
from .streaming_data import StreamingDataManager

__all__ = [
    'APIClient',
    'DataCache', 
    'MarketDataManager',
    'DataValidator',
    'StreamingDataManager'
] 