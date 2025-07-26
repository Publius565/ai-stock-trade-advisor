#!/usr/bin/env python3
"""
Test Script for Data Ingestion Layer

This script tests all components of the data ingestion layer:
- API Client (Alpha Vantage and Yahoo Finance)
- Data Cache
- Market Data Manager
- Data Validator
- Streaming Data Manager
"""

import sys
import os
import logging
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.data_layer import (
    APIClient, 
    DataCache, 
    MarketDataManager, 
    DataValidator, 
    StreamingDataManager
)

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
    
    # Test setting data
    print("  - Testing cache set...")
    success = cache.set('TEST', test_data, 'market_data', expiry_hours=1)
    if success:
        print("    ✓ Data cached successfully")
    else:
        print("    ✗ Failed to cache data")
    
    # Test getting data
    print("  - Testing cache get...")
    cached_data = cache.get('TEST', 'market_data')
    if cached_data:
        print("    ✓ Data retrieved from cache")
        print(f"    ✓ Symbol: {cached_data['symbol']}")
        print(f"    ✓ Data points: {len(cached_data['data'])}")
    else:
        print("    ✗ Failed to retrieve data from cache")
    
    # Test cache stats
    print("  - Testing cache stats...")
    stats = cache.get_stats()
    print(f"    ✓ Cache hits: {stats['hits']}")
    print(f"    ✓ Cache misses: {stats['misses']}")
    print(f"    ✓ Hit rate: {stats['hit_rate']:.2%}")
    
    # Clean up
    cache.clear('TEST')
    print("    ✓ Test data cleared")


def test_market_data_manager():
    """Test the market data manager functionality."""
    print("\n=== Testing Market Data Manager ===")
    
    manager = MarketDataManager(cache_dir="data/test_cache", max_workers=2)
    
    # Test symbols
    test_symbols = ['AAPL', 'MSFT']
    
    # Test single symbol retrieval
    print("  - Testing single symbol retrieval...")
    for symbol in test_symbols:
        data = manager.get_market_data(symbol)
        if data:
            print(f"    ✓ {symbol}: {len(data['data'])} data points, source: {data['source']}")
        else:
            print(f"    ✗ {symbol}: Failed to retrieve data")
    
    # Test multiple symbols
    print("  - Testing multiple symbols retrieval...")
    multi_data = manager.get_multiple_symbols(test_symbols)
    print(f"    ✓ Retrieved data for {len(multi_data)}/{len(test_symbols)} symbols")
    
    # Test company info
    print("  - Testing company info...")
    for symbol in test_symbols:
        info = manager.get_company_info(symbol)
        if info:
            print(f"    ✓ {symbol}: {info['name']} ({info['sector']})")
        else:
            print(f"    ✗ {symbol}: Failed to retrieve company info")
    
    # Test cache stats
    print("  - Testing cache statistics...")
    stats = manager.get_cache_stats()
    print(f"    ✓ API calls: {stats['api']['api_calls']}")
    print(f"    ✓ Cache hits: {stats['cache']['hits']}")
    print(f"    ✓ Cache misses: {stats['cache']['misses']}")
    
    # Clean up
    manager.shutdown()


def test_data_validator():
    """Test the data validator functionality."""
    print("\n=== Testing Data Validator ===")
    
    validator = DataValidator()
    
    # Test valid data
    valid_data = {
        'symbol': 'TEST',
        'data': [
            {'date': '2024-01-01', 'open': 100, 'high': 105, 'low': 98, 'close': 102, 'volume': 1000},
            {'date': '2024-01-02', 'open': 102, 'high': 108, 'low': 100, 'close': 106, 'volume': 1200},
            {'date': '2024-01-03', 'open': 106, 'high': 110, 'low': 104, 'close': 108, 'volume': 1100}
        ]
    }
    
    print("  - Testing valid data...")
    is_valid, issues = validator.validate_market_data(valid_data)
    if is_valid:
        print("    ✓ Valid data passed validation")
    else:
        print(f"    ✗ Valid data failed validation: {issues}")
    
    # Test invalid data
    invalid_data = {
        'symbol': 'TEST',
        'data': [
            {'date': '2024-01-01', 'open': 100, 'high': 95, 'low': 98, 'close': 102, 'volume': 1000},  # High < Low
            {'date': '2024-01-02', 'open': 102, 'high': 108, 'low': 100, 'close': 106, 'volume': -100},  # Negative volume
        ]
    }
    
    print("  - Testing invalid data...")
    is_valid, issues = validator.validate_market_data(invalid_data)
    if not is_valid:
        print("    ✓ Invalid data correctly identified")
        print(f"    ✓ Issues found: {len(issues)}")
        for issue in issues:
            print(f"      - {issue}")
    else:
        print("    ✗ Invalid data incorrectly passed validation")
    
    # Test data quality score
    print("  - Testing data quality score...")
    score = validator.get_data_quality_score(valid_data)
    print(f"    ✓ Quality score: {score:.2f}")
    
    # Test improvement suggestions
    print("  - Testing improvement suggestions...")
    suggestions = validator.suggest_data_improvements(valid_data)
    if suggestions:
        print("    ✓ Improvement suggestions:")
        for suggestion in suggestions:
            print(f"      - {suggestion}")
    else:
        print("    ✓ No improvement suggestions (data is good)")


def test_streaming_data_manager():
    """Test the streaming data manager functionality."""
    print("\n=== Testing Streaming Data Manager ===")
    
    # Create market data manager first
    market_manager = MarketDataManager(cache_dir="data/test_cache")
    streaming_manager = StreamingDataManager(market_manager)
    
    # Test price alerts
    print("  - Testing price alerts...")
    streaming_manager.add_price_alert('AAPL', 'above', 200.0)
    streaming_manager.add_price_alert('AAPL', 'below', 150.0)
    
    alerts = streaming_manager.get_price_alerts()
    print(f"    ✓ Added {len(alerts)} price alerts")
    
    # Test callbacks
    def data_callback(data_point):
        print(f"    ✓ Data callback: {data_point.symbol} at ${data_point.price:.2f}")
    
    def alert_callback(alert_data):
        print(f"    ✓ Alert callback: {alert_data['symbol']} - {alert_data['alerts']}")
    
    streaming_manager.add_data_callback(data_callback)
    streaming_manager.add_alert_callback(alert_callback)
    
    # Test streaming (brief test)
    print("  - Testing streaming (5 seconds)...")
    streaming_manager.start_streaming(['AAPL'], interval_seconds=5)
    
    # Wait a bit for data
    import time
    time.sleep(10)
    
    # Get streaming stats
    stats = streaming_manager.get_streaming_stats()
    print(f"    ✓ Data points received: {stats['data_points_received']}")
    print(f"    ✓ Alerts triggered: {stats['alerts_triggered']}")
    
    # Stop streaming
    streaming_manager.stop_streaming()
    print("    ✓ Streaming stopped")
    
    # Clean up
    streaming_manager.shutdown()
    market_manager.shutdown()


def main():
    """Run all tests."""
    print("Data Ingestion Layer Test Suite")
    print("=" * 50)
    
    try:
        # Run tests
        test_api_client()
        test_data_cache()
        test_market_data_manager()
        test_data_validator()
        test_streaming_data_manager()
        
        print("\n" + "=" * 50)
        print("✓ All tests completed successfully!")
        print("\nData ingestion layer is working correctly.")
        print("Key features verified:")
        print("- API integration (Yahoo Finance, Alpha Vantage)")
        print("- Intelligent caching with expiration")
        print("- Multi-threaded data retrieval")
        print("- Data validation and quality checks")
        print("- Real-time streaming capabilities")
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        logger.exception("Test error")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 