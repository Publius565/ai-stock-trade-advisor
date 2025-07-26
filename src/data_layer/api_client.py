"""
API Client Module for Data Ingestion

Handles communication with external financial data APIs including Alpha Vantage
and Yahoo Finance. Provides unified interface for market data retrieval.
"""

import os
import time
import logging
import requests
import yfinance as yf
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv('config/api_keys.env')

logger = logging.getLogger(__name__)


class APIClient:
    """
    Unified API client for financial data sources.
    
    Handles Alpha Vantage and Yahoo Finance APIs with rate limiting,
    error handling, and data normalization.
    """
    
    def __init__(self):
        """Initialize API client with configuration."""
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        self.alpha_vantage_base_url = "https://www.alphavantage.co/query"
        
        # Rate limiting for Alpha Vantage (5 calls per minute for free tier)
        self.alpha_vantage_rate_limit = 5
        self.alpha_vantage_calls = []
        self.last_alpha_vantage_call = 0
        
        # Request timeout
        self.timeout = 30
        
        # Validate API keys
        self._validate_configuration()
    
    def _validate_configuration(self):
        """Validate API configuration and keys."""
        if not self.alpha_vantage_key or self.alpha_vantage_key == 'your_alpha_vantage_api_key_here':
            logger.warning("Alpha Vantage API key not configured. Some features may be limited.")
        
        logger.info("API client initialized successfully")
    
    def _check_alpha_vantage_rate_limit(self):
        """Check and enforce Alpha Vantage rate limits."""
        current_time = time.time()
        
        # Remove calls older than 1 minute
        self.alpha_vantage_calls = [
            call_time for call_time in self.alpha_vantage_calls 
            if current_time - call_time < 60
        ]
        
        # Check if we're at the rate limit
        if len(self.alpha_vantage_calls) >= self.alpha_vantage_rate_limit:
            sleep_time = 60 - (current_time - self.alpha_vantage_calls[0])
            if sleep_time > 0:
                logger.info(f"Rate limit reached. Waiting {sleep_time:.1f} seconds...")
                time.sleep(sleep_time)
        
        # Record this call
        self.alpha_vantage_calls.append(current_time)
    
    def get_stock_data_alpha_vantage(self, symbol: str, interval: str = 'daily') -> Optional[Dict[str, Any]]:
        """
        Get stock data from Alpha Vantage API.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            interval: Data interval ('daily', 'weekly', 'monthly')
            
        Returns:
            Dictionary containing stock data or None if error
        """
        if not self.alpha_vantage_key:
            logger.error("Alpha Vantage API key not configured")
            return None
        
        try:
            self._check_alpha_vantage_rate_limit()
            
            params = {
                'function': 'TIME_SERIES_DAILY' if interval == 'daily' else 'TIME_SERIES_WEEKLY',
                'symbol': symbol,
                'apikey': self.alpha_vantage_key,
                'outputsize': 'compact'  # Last 100 data points
            }
            
            response = requests.get(
                self.alpha_vantage_base_url,
                params=params,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for API errors
                if 'Error Message' in data:
                    logger.error(f"Alpha Vantage API error: {data['Error Message']}")
                    return None
                
                if 'Note' in data:
                    logger.warning(f"Alpha Vantage API note: {data['Note']}")
                    return None
                
                # Extract time series data
                time_series_key = list(data.keys())[1] if len(data.keys()) > 1 else None
                if time_series_key and time_series_key in data:
                    return self._normalize_alpha_vantage_data(data[time_series_key], symbol)
                
                logger.error(f"Unexpected Alpha Vantage response format: {data}")
                return None
                
            else:
                logger.error(f"Alpha Vantage API request failed: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Alpha Vantage API request exception: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in Alpha Vantage API call: {e}")
            return None
    
    def get_stock_data_yahoo(self, symbol: str, period: str = '1y') -> Optional[Dict[str, Any]]:
        """
        Get stock data from Yahoo Finance API.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            period: Data period ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
            
        Returns:
            Dictionary containing stock data or None if error
        """
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            
            if data.empty:
                logger.warning(f"No data returned from Yahoo Finance for {symbol}")
                return None
            
            return self._normalize_yahoo_data(data, symbol)
            
        except Exception as e:
            logger.error(f"Yahoo Finance API error for {symbol}: {e}")
            return None
    
    def get_market_data(self, symbol: str, source: str = 'auto') -> Optional[Dict[str, Any]]:
        """
        Get market data from preferred source with fallback.
        
        Args:
            symbol: Stock symbol
            source: Data source ('alpha_vantage', 'yahoo', 'auto')
            
        Returns:
            Dictionary containing market data or None if error
        """
        if source == 'alpha_vantage' or (source == 'auto' and self.alpha_vantage_key):
            data = self.get_stock_data_alpha_vantage(symbol)
            if data:
                return data
        
        # Fallback to Yahoo Finance
        data = self.get_stock_data_yahoo(symbol)
        if data:
            return data
        
        logger.error(f"Failed to get market data for {symbol} from all sources")
        return None
    
    def get_multiple_symbols(self, symbols: List[str], source: str = 'auto') -> Dict[str, Dict[str, Any]]:
        """
        Get market data for multiple symbols.
        
        Args:
            symbols: List of stock symbols
            source: Data source preference
            
        Returns:
            Dictionary mapping symbols to their data
        """
        results = {}
        
        for symbol in symbols:
            data = self.get_market_data(symbol, source)
            if data:
                results[symbol] = data
            else:
                logger.warning(f"Failed to get data for {symbol}")
        
        return results
    
    def _normalize_alpha_vantage_data(self, time_series: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """Normalize Alpha Vantage data format."""
        normalized_data = {
            'symbol': symbol,
            'source': 'alpha_vantage',
            'timestamp': datetime.now().isoformat(),
            'data': []
        }
        
        for date, values in time_series.items():
            try:
                data_point = {
                    'date': date,
                    'open': float(values['1. open']),
                    'high': float(values['2. high']),
                    'low': float(values['3. low']),
                    'close': float(values['4. close']),
                    'volume': int(values['5. volume'])
                }
                normalized_data['data'].append(data_point)
            except (KeyError, ValueError) as e:
                logger.warning(f"Error parsing Alpha Vantage data point: {e}")
                continue
        
        # Sort by date
        normalized_data['data'].sort(key=lambda x: x['date'])
        
        return normalized_data
    
    def _normalize_yahoo_data(self, data, symbol: str) -> Dict[str, Any]:
        """Normalize Yahoo Finance data format."""
        normalized_data = {
            'symbol': symbol,
            'source': 'yahoo',
            'timestamp': datetime.now().isoformat(),
            'data': []
        }
        
        for date, row in data.iterrows():
            data_point = {
                'date': date.strftime('%Y-%m-%d'),
                'open': float(row['Open']),
                'high': float(row['High']),
                'low': float(row['Low']),
                'close': float(row['Close']),
                'volume': int(row['Volume'])
            }
            normalized_data['data'].append(data_point)
        
        return normalized_data
    
    def get_company_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get company information and fundamentals.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary containing company information
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                'symbol': symbol,
                'name': info.get('longName', ''),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'dividend_yield': info.get('dividendYield', 0),
                'beta': info.get('beta', 0),
                'fifty_two_week_high': info.get('fiftyTwoWeekHigh', 0),
                'fifty_two_week_low': info.get('fiftyTwoWeekLow', 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting company info for {symbol}: {e}")
            return None 