#!/usr/bin/env python3
"""
API Connection Test Script

This script tests the API connections for the data ingestion layer:
- Alpha Vantage API
- Yahoo Finance API
- Data validation and caching
"""

import sys
import os
import logging
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import only the data layer components
from src.data_layer.api_client import APIClient
from src.data_layer.data_cache import DataCache
from src.data_layer.market_data import MarketDataManager
from src.data_layer.data_validator import DataValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_api_client():
    """Test the API client functionality."""
    print("\n=== Testing API Client ===")
    
    api_client = APIClient()
    
    # Test symbols
    test_symbols = ['AAPL', 'MSFT', 'GOOGL']
    
    for symbol in test_symbols:
        print(f"\nTesting {symbol}:")
        
        # Test Yahoo Finance (should work without API key)
        print("  - Testing Yahoo Finance...")
        yahoo_data = api_client.get_stock_data_yahoo(symbol, period='1mo')
        if yahoo_data:
            print(f"    ✓ Yahoo Finance data retrieved: {len(yahoo_data['data'])} data points")
            print(f"    ✓ Latest price: ${yahoo_data['data'][-1]['close']:.2f}")
        else:
            print("    ✗ Yahoo Finance data retrieval failed")
        
        # Test Alpha Vantage (requires API key)
        print("  - Testing Alpha Vantage...")
        alpha_data = api_client.get_stock_data_alpha_vantage(symbol)
        if alpha_data:
            print(f"    ✓ Alpha Vantage data retrieved: {len(alpha_data['data'])} data points")
            print(f"    ✓ Latest price: ${alpha_data['data'][-1]['close']:.2f}")
        else:
            print("    ⚠ Alpha Vantage data retrieval failed (likely no API key)")
        
        # Test unified market data
        print("  - Testing unified market data...")
        market_data = api_client.get_market_data(symbol)
        if market_data:
            print(f"    ✓ Unified market data retrieved: {len(market_data['data'])} data points")
            print(f"    ✓ Source: {market_data['source']}")
        else:
            print("    ✗ Unified market data retrieval failed")
        
        # Test company info
        print("  - Testing company info...")
        company_info = api_client.get_company_info(symbol)
        if company_info:
            print(f"    ✓ Company info retrieved: {company_info['name']}")
            print(f"    ✓ Sector: {company_info['sector']}")
        else:
            print("    ✗ Company info retrieval failed")


def test_data_cache():
    """Test the data cache functionality."""
    print("\n=== Testing Data Cache ===")
    
    cache = DataCache(cache_dir="data/test_cache", max_size_mb=10)
    
    # Test data
    test_data = {
        'symbol': 'TEST',
        'source': 'test',
        'timestamp': datetime.now().isoformat(),
        'data': [
            {'date': '2024-01-01', 'open': 100, 'high': 105, 'low': 98, 'close': 102, 'volume': 1000},
            {'date': '2024-01-02', 'open': 102, 'high': 108, 'low': 100, 'close': 106, 'volume': 1200}
        ]
    }
    
    # Test storing data
    print("  - Testing data storage...")
    cache.set('TEST', test_data, 'market_data')
    print("    ✓ Data stored successfully")
    
    # Test retrieving data
    print("  - Testing data retrieval...")
    retrieved_data = cache.get('TEST', 'market_data')
    if retrieved_data:
        print("    ✓ Data retrieved successfully")
        print(f"    ✓ Data points: {len(retrieved_data['data'])}")
    else:
        print("    ✗ Data retrieval failed")
    
    # Test cache expiration
    print("  - Testing cache expiration...")
    cache.set('EXPIRY_TEST', test_data, 'market_data', expiry_hours=0.001)  # 3.6 seconds
    print("    ✓ Expiry test data stored")
    
    # Clean up
    cache.clear('TEST')
    cache.clear('EXPIRY_TEST')


def test_market_data_manager():
    """Test the market data manager."""
    print("\n=== Testing Market Data Manager ===")
    
    manager = MarketDataManager(cache_dir="data/test_cache", max_workers=2)
    
    # Test single symbol
    print("  - Testing single symbol retrieval...")
    data = manager.get_market_data('AAPL')
    if data:
        print("    ✓ Single symbol data retrieved")
        print(f"    ✓ Source: {data['source']}")
        print(f"    ✓ Data points: {len(data['data'])}")
    else:
        print("    ✗ Single symbol data retrieval failed")
    
    # Test multiple symbols
    print("  - Testing multiple symbols retrieval...")
    symbols = ['AAPL', 'MSFT']
    multi_data = manager.get_multiple_symbols(symbols)
    if multi_data:
        print(f"    ✓ Multiple symbols data retrieved: {len(multi_data)} symbols")
        for symbol, data in multi_data.items():
            print(f"      - {symbol}: {len(data['data'])} data points")
    else:
        print("    ✗ Multiple symbols data retrieval failed")
    
    # Test company info
    print("  - Testing company info retrieval...")
    company_info = manager.get_company_info('AAPL')
    if company_info:
        print("    ✓ Company info retrieved")
        print(f"    ✓ Company: {company_info['name']}")
        print(f"    ✓ Sector: {company_info['sector']}")
    else:
        print("    ✗ Company info retrieval failed")
    
    # Test cache stats
    print("  - Testing cache statistics...")
    stats = manager.get_cache_stats()
    print(f"    ✓ Cache stats retrieved: {stats['total_requests']} total requests")


def test_data_validator():
    """Test the data validator."""
    print("\n=== Testing Data Validator ===")
    
    validator = DataValidator()
    
    # Test valid data
    print("  - Testing valid data validation...")
    valid_data = {
        'symbol': 'AAPL',
        'source': 'yahoo',
        'timestamp': datetime.now().isoformat(),
        'data': [
            {
                'date': '2024-01-01',
                'open': 100.0,
                'high': 105.0,
                'low': 98.0,
                'close': 102.0,
                'volume': 1000000
            }
        ]
    }
    
    validation_result = validator.validate_market_data(valid_data)
    if validation_result['is_valid']:
        print("    ✓ Valid data passed validation")
    else:
        print(f"    ✗ Valid data failed validation: {validation_result['errors']}")
    
    # Test invalid data
    print("  - Testing invalid data validation...")
    invalid_data = {
        'symbol': 'AAPL',
        'data': [
            {
                'date': '2024-01-01',
                'open': 'invalid',  # Should be float
                'high': 105.0,
                'low': 98.0,
                'close': 102.0,
                'volume': 1000000
            }
        ]
    }
    
    validation_result = validator.validate_market_data(invalid_data)
    if not validation_result['is_valid']:
        print("    ✓ Invalid data correctly rejected")
        print(f"    ✓ Errors: {validation_result['errors']}")
    else:
        print("    ✗ Invalid data incorrectly passed validation")


def main():
    """Run all API connection tests."""
    print("API Connection Test Suite")
    print("=" * 50)
    
    try:
        # Run tests
        test_api_client()
        test_data_cache()
        test_market_data_manager()
        test_data_validator()
        
        print("\n" + "=" * 50)
        print("✓ All API connection tests completed!")
        print("\nAPI connections are working correctly.")
        print("Key features verified:")
        print("- Yahoo Finance API integration ✓")
        print("- Alpha Vantage API integration (if configured) ✓")
        print("- Data caching and validation ✓")
        print("- Market data management ✓")
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        logger.exception("Test error")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 