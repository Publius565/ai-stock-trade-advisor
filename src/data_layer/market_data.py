"""
Market Data Manager Module

Coordinates data retrieval between API clients and cache system.
Provides unified interface for market data access with intelligent caching.
"""

import logging
import threading
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from .api_client import APIClient
from .data_cache import DataCache

logger = logging.getLogger(__name__)


class MarketDataManager:
    """
    Central market data management system.
    
    Features:
    - Intelligent caching with automatic refresh
    - Multi-threaded data retrieval for multiple symbols
    - Real-time data streaming capabilities
    - Data validation and quality checks
    - Automatic fallback between data sources
    """
    
    def __init__(self, cache_dir: str = "data/cache", max_workers: int = 4):
        """
        Initialize the market data manager.
        
        Args:
            cache_dir: Directory for cache storage
            max_workers: Maximum number of worker threads
        """
        self.api_client = APIClient()
        self.cache = DataCache(cache_dir)
        self.max_workers = max_workers
        
        # Data update callbacks
        self.update_callbacks: List[Callable] = []
        
        # Threading
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._update_thread = None
        
        # Statistics
        self.stats = {
            'api_calls': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'errors': 0,
            'last_update': None
        }
        
        logger.info("Market data manager initialized")
    
    def get_market_data(self, symbol: str, force_refresh: bool = False,
                       source: str = 'auto') -> Optional[Dict[str, Any]]:
        """
        Get market data for a symbol with intelligent caching.
        
        Args:
            symbol: Stock symbol
            force_refresh: Force refresh from API
            source: Preferred data source
            
        Returns:
            Market data dictionary or None if error
        """
        symbol = symbol.upper()
        
        # Check cache first (unless force refresh)
        if not force_refresh:
            cached_data = self.cache.get(symbol, 'market_data')
            if cached_data:
                self.stats['cache_hits'] += 1
                logger.debug(f"Cache hit for {symbol}")
                return cached_data
        
        self.stats['cache_misses'] += 1
        
        # Fetch from API
        try:
            data = self.api_client.get_market_data(symbol, source)
            if data:
                # Cache the data
                self.cache.set(symbol, data, 'market_data')
                self.stats['api_calls'] += 1
                self.stats['last_update'] = datetime.now().isoformat()
                
                logger.info(f"Retrieved market data for {symbol} from {data.get('source', 'unknown')}")
                return data
            else:
                self.stats['errors'] += 1
                logger.warning(f"Failed to retrieve market data for {symbol}")
                return None
                
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Error retrieving market data for {symbol}: {e}")
            return None
    
    def get_multiple_symbols(self, symbols: List[str], force_refresh: bool = False,
                           source: str = 'auto') -> Dict[str, Dict[str, Any]]:
        """
        Get market data for multiple symbols concurrently.
        
        Args:
            symbols: List of stock symbols
            force_refresh: Force refresh from API
            source: Preferred data source
            
        Returns:
            Dictionary mapping symbols to their data
        """
        symbols = [s.upper() for s in symbols]
        results = {}
        
        # Use thread pool for concurrent requests
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all requests
            future_to_symbol = {
                executor.submit(self.get_market_data, symbol, force_refresh, source): symbol
                for symbol in symbols
            }
            
            # Collect results
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    data = future.result()
                    if data:
                        results[symbol] = data
                except Exception as e:
                    logger.error(f"Error processing {symbol}: {e}")
                    self.stats['errors'] += 1
        
        logger.info(f"Retrieved data for {len(results)}/{len(symbols)} symbols")
        return results
    
    def get_company_info(self, symbol: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        Get company information and fundamentals.
        
        Args:
            symbol: Stock symbol
            force_refresh: Force refresh from API
            
        Returns:
            Company information dictionary or None if error
        """
        symbol = symbol.upper()
        
        # Check cache first
        if not force_refresh:
            cached_info = self.cache.get(symbol, 'company_info')
            if cached_info:
                self.stats['cache_hits'] += 1
                return cached_info
        
        self.stats['cache_misses'] += 1
        
        # Fetch from API
        try:
            info = self.api_client.get_company_info(symbol)
            if info:
                # Cache with longer expiration (company info changes less frequently)
                self.cache.set(symbol, info, 'company_info', expiry_hours=168)  # 1 week
                self.stats['api_calls'] += 1
                
                logger.info(f"Retrieved company info for {symbol}")
                return info
            else:
                self.stats['errors'] += 1
                logger.warning(f"Failed to retrieve company info for {symbol}")
                return None
                
        except Exception as e:
            self.stats['errors'] += 1
            logger.error(f"Error retrieving company info for {symbol}: {e}")
            return None
    
    def start_real_time_updates(self, symbols: List[str], interval_minutes: int = 15,
                               callback: Optional[Callable] = None):
        """
        Start real-time data updates for specified symbols.
        
        Args:
            symbols: List of symbols to monitor
            interval_minutes: Update interval in minutes
            callback: Optional callback function for data updates
        """
        if self._update_thread and self._update_thread.is_alive():
            logger.warning("Real-time updates already running")
            return
        
        if callback:
            self.update_callbacks.append(callback)
        
        self._stop_event.clear()
        self._update_thread = threading.Thread(
            target=self._update_loop,
            args=(symbols, interval_minutes),
            daemon=True
        )
        self._update_thread.start()
        
        logger.info(f"Started real-time updates for {len(symbols)} symbols, interval: {interval_minutes} minutes")
    
    def stop_real_time_updates(self):
        """Stop real-time data updates."""
        if self._update_thread and self._update_thread.is_alive():
            self._stop_event.set()
            self._update_thread.join(timeout=5)
            logger.info("Stopped real-time updates")
    
    def _update_loop(self, symbols: List[str], interval_minutes: int):
        """Background thread for real-time updates."""
        interval_seconds = interval_minutes * 60
        
        while not self._stop_event.is_set():
            try:
                # Update all symbols
                updated_data = self.get_multiple_symbols(symbols, force_refresh=True)
                
                # Notify callbacks
                if updated_data and self.update_callbacks:
                    for callback in self.update_callbacks:
                        try:
                            callback(updated_data)
                        except Exception as e:
                            logger.error(f"Error in update callback: {e}")
                
                # Wait for next update
                self._stop_event.wait(interval_seconds)
                
            except Exception as e:
                logger.error(f"Error in update loop: {e}")
                self._stop_event.wait(60)  # Wait 1 minute on error
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """
        Get the latest closing price for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Latest closing price or None if error
        """
        data = self.get_market_data(symbol)
        if data and data.get('data'):
            # Get the most recent data point
            latest_data = data['data'][-1]
            return latest_data.get('close')
        return None
    
    def get_price_history(self, symbol: str, days: int = 30) -> Optional[List[Dict[str, Any]]]:
        """
        Get price history for a symbol.
        
        Args:
            symbol: Stock symbol
            days: Number of days of history
            
        Returns:
            List of price data points or None if error
        """
        data = self.get_market_data(symbol)
        if data and data.get('data'):
            # Return the last N days of data
            return data['data'][-days:] if len(data['data']) >= days else data['data']
        return None
    
    def validate_symbol(self, symbol: str) -> bool:
        """
        Validate if a symbol exists and has data.
        
        Args:
            symbol: Stock symbol to validate
            
        Returns:
            True if symbol is valid, False otherwise
        """
        try:
            data = self.get_market_data(symbol)
            return data is not None and len(data.get('data', [])) > 0
        except Exception:
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        cache_stats = self.cache.get_stats()
        return {
            'cache': cache_stats,
            'api': self.stats,
            'total_requests': self.stats['api_calls'] + self.stats['cache_hits'] + self.stats['cache_misses']
        }
    
    def clear_cache(self, symbol: Optional[str] = None):
        """Clear cache for specific symbol or all symbols."""
        self.cache.clear(symbol)
        logger.info(f"Cleared cache for {symbol if symbol else 'all symbols'}")
    
    def get_supported_symbols(self) -> List[str]:
        """
        Get list of symbols that have been successfully retrieved.
        
        Returns:
            List of supported symbols
        """
        cache_info = self.cache.get_cache_info()
        symbols = set()
        
        for entry in cache_info['entries'].values():
            if entry['data_type'] == 'market_data':
                symbols.add(entry['symbol'])
        
        return sorted(list(symbols))
    
    def shutdown(self):
        """Shutdown the market data manager."""
        self.stop_real_time_updates()
        logger.info("Market data manager shutdown complete") 