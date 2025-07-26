"""
Data Cache Module for Market Data Storage

Provides local caching of market data with expiration, size management,
and efficient retrieval for the AI-Driven Stock Trade Advisor.
"""

import os
import json
import pickle
import logging
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class DataCache:
    """
    Local cache system for market data with automatic expiration and size management.
    
    Features:
    - Automatic data expiration based on configurable time periods
    - Size-based cache management with LRU eviction
    - Compressed storage for efficiency
    - Cache statistics and monitoring
    """
    
    def __init__(self, cache_dir: str = "data/cache", max_size_mb: int = 1000, 
                 default_expiry_hours: int = 24):
        """
        Initialize the data cache.
        
        Args:
            cache_dir: Directory for cache storage
            max_size_mb: Maximum cache size in megabytes
            default_expiry_hours: Default expiration time in hours
        """
        self.cache_dir = Path(cache_dir)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.default_expiry_hours = default_expiry_hours
        
        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache metadata
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self.metadata = self._load_metadata()
        
        # Statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'total_size': 0
        }
        
        logger.info(f"Data cache initialized: {cache_dir}, max size: {max_size_mb}MB")
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load cache metadata from file."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cache metadata: {e}")
        
        return {
            'entries': {},
            'total_size': 0,
            'created': datetime.now().isoformat()
        }
    
    def _save_metadata(self):
        """Save cache metadata to file."""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache metadata: {e}")
    
    def _get_cache_key(self, symbol: str, data_type: str = 'market_data') -> str:
        """Generate cache key for data."""
        key_string = f"{symbol}_{data_type}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get file path for cache entry."""
        return self.cache_dir / f"{cache_key}.pkl"
    
    def get(self, symbol: str, data_type: str = 'market_data') -> Optional[Dict[str, Any]]:
        """
        Retrieve data from cache.
        
        Args:
            symbol: Stock symbol
            data_type: Type of data ('market_data', 'company_info', etc.)
            
        Returns:
            Cached data if valid, None if expired or not found
        """
        cache_key = self._get_cache_key(symbol, data_type)
        
        if cache_key not in self.metadata['entries']:
            self.stats['misses'] += 1
            return None
        
        entry = self.metadata['entries'][cache_key]
        cache_path = self._get_cache_path(cache_key)
        
        # Check if file exists
        if not cache_path.exists():
            self._remove_entry(cache_key)
            self.stats['misses'] += 1
            return None
        
        # Check expiration
        expiry_time = datetime.fromisoformat(entry['expires'])
        if datetime.now() > expiry_time:
            self._remove_entry(cache_key)
            self.stats['misses'] += 1
            return None
        
        # Load data
        try:
            with open(cache_path, 'rb') as f:
                data = pickle.load(f)
            
            self.stats['hits'] += 1
            logger.debug(f"Cache hit for {symbol} ({data_type})")
            return data
            
        except Exception as e:
            logger.error(f"Failed to load cached data for {symbol}: {e}")
            self._remove_entry(cache_key)
            self.stats['misses'] += 1
            return None
    
    def set(self, symbol: str, data: Dict[str, Any], data_type: str = 'market_data',
            expiry_hours: Optional[int] = None) -> bool:
        """
        Store data in cache.
        
        Args:
            symbol: Stock symbol
            data: Data to cache
            data_type: Type of data
            expiry_hours: Custom expiration time in hours
            
        Returns:
            True if successfully cached, False otherwise
        """
        cache_key = self._get_cache_key(symbol, data_type)
        cache_path = self._get_cache_path(cache_key)
        
        # Calculate expiration time
        if expiry_hours is None:
            expiry_hours = self.default_expiry_hours
        
        expires = datetime.now() + timedelta(hours=expiry_hours)
        
        try:
            # Serialize and save data
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f)
            
            # Get file size
            file_size = cache_path.stat().st_size
            
            # Remove old entry if exists
            if cache_key in self.metadata['entries']:
                self._remove_entry(cache_key, update_stats=False)
            
            # Add new entry
            self.metadata['entries'][cache_key] = {
                'symbol': symbol,
                'data_type': data_type,
                'created': datetime.now().isoformat(),
                'expires': expires.isoformat(),
                'size': file_size
            }
            
            self.metadata['total_size'] += file_size
            
            # Check cache size and evict if necessary
            self._enforce_size_limit()
            
            # Save metadata
            self._save_metadata()
            
            logger.debug(f"Cached data for {symbol} ({data_type}), expires: {expires}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache data for {symbol}: {e}")
            return False
    
    def _remove_entry(self, cache_key: str, update_stats: bool = True):
        """Remove cache entry."""
        if cache_key not in self.metadata['entries']:
            return
        
        entry = self.metadata['entries'][cache_key]
        cache_path = self._get_cache_path(cache_key)
        
        # Remove file
        if cache_path.exists():
            try:
                cache_path.unlink()
            except Exception as e:
                logger.warning(f"Failed to remove cache file {cache_path}: {e}")
        
        # Update metadata
        self.metadata['total_size'] -= entry['size']
        del self.metadata['entries'][cache_key]
        
        if update_stats:
            self.stats['evictions'] += 1
    
    def _enforce_size_limit(self):
        """Enforce cache size limit using LRU eviction."""
        if self.metadata['total_size'] <= self.max_size_bytes:
            return
        
        # Sort entries by creation time (oldest first)
        entries = list(self.metadata['entries'].items())
        entries.sort(key=lambda x: x[1]['created'])
        
        # Remove oldest entries until under limit
        for cache_key, entry in entries:
            if self.metadata['total_size'] <= self.max_size_bytes:
                break
            
            self._remove_entry(cache_key, update_stats=False)
            self.stats['evictions'] += 1
        
        logger.info(f"Cache size limit enforced, evicted {self.stats['evictions']} entries")
    
    def clear(self, symbol: Optional[str] = None, data_type: Optional[str] = None):
        """
        Clear cache entries.
        
        Args:
            symbol: Clear entries for specific symbol (None for all)
            data_type: Clear entries of specific type (None for all)
        """
        keys_to_remove = []
        
        for cache_key, entry in self.metadata['entries'].items():
            if symbol and entry['symbol'] != symbol:
                continue
            if data_type and entry['data_type'] != data_type:
                continue
            
            keys_to_remove.append(cache_key)
        
        for cache_key in keys_to_remove:
            self._remove_entry(cache_key, update_stats=False)
        
        self._save_metadata()
        logger.info(f"Cleared {len(keys_to_remove)} cache entries")
    
    def clear_expired(self):
        """Remove all expired cache entries."""
        current_time = datetime.now()
        keys_to_remove = []
        
        for cache_key, entry in self.metadata['entries'].items():
            expiry_time = datetime.fromisoformat(entry['expires'])
            if current_time > expiry_time:
                keys_to_remove.append(cache_key)
        
        for cache_key in keys_to_remove:
            self._remove_entry(cache_key, update_stats=False)
        
        if keys_to_remove:
            self._save_metadata()
            logger.info(f"Cleared {len(keys_to_remove)} expired cache entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        hit_rate = 0
        if self.stats['hits'] + self.stats['misses'] > 0:
            hit_rate = self.stats['hits'] / (self.stats['hits'] + self.stats['misses'])
        
        return {
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'evictions': self.stats['evictions'],
            'hit_rate': hit_rate,
            'total_entries': len(self.metadata['entries']),
            'total_size_mb': self.metadata['total_size'] / (1024 * 1024),
            'max_size_mb': self.max_size_bytes / (1024 * 1024)
        }
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get detailed cache information."""
        return {
            'cache_dir': str(self.cache_dir),
            'max_size_mb': self.max_size_bytes / (1024 * 1024),
            'default_expiry_hours': self.default_expiry_hours,
            'stats': self.get_stats(),
            'entries': self.metadata['entries']
        } 