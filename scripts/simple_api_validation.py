#!/usr/bin/env python3
"""
Simple End-to-End API Validation Script

Focused validation of API connections and database endpoints without complex dependencies.
"""

import os
import sys
import time
import logging
import sqlite3
import requests
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleAPIValidator:
    """Simplified API and database validation system"""
    
    def __init__(self):
        self.results = {
            'api_connections': {},
            'database_operations': {},
            'data_flow': {},
            'performance_metrics': {}
        }
        self.db_path = "data/trading_advisor.db"
        
    def run_full_validation(self) -> Dict[str, Any]:
        """Run complete end-to-end validation"""
        print("=" * 80)
        print("SIMPLE END-TO-END API VALIDATION")
        print("=" * 80)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Phase 1: External API Validation
        print("PHASE 1: EXTERNAL API VALIDATION")
        print("-" * 50)
        self._validate_external_apis()
        
        # Phase 2: Database Validation
        print("\nPHASE 2: DATABASE VALIDATION")
        print("-" * 50)
        self._validate_database()
        
        # Phase 3: Data Flow Validation
        print("\nPHASE 3: DATA FLOW VALIDATION")
        print("-" * 50)
        self._validate_data_flow()
        
        # Phase 4: Performance Testing
        print("\nPHASE 4: PERFORMANCE TESTING")
        print("-" * 50)
        self._validate_performance()
        
        # Generate Summary Report
        print("\n" + "=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)
        self._generate_summary_report()
        
        return self.results
    
    def _validate_external_apis(self):
        """Validate external API connections"""
        
        # 1. Yahoo Finance API (No API key required)
        print("1. Yahoo Finance API Validation")
        try:
            # Test Yahoo Finance API using requests
            url = "https://query1.finance.yahoo.com/v8/finance/chart/AAPL?range=1d&interval=1m"
            start_time = time.time()
            response = requests.get(url, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if 'chart' in data and 'result' in data['chart']:
                    print(f"   ✓ Yahoo Finance API working (response time: {response_time:.2f}s)")
                    self.results['api_connections']['yahoo_finance'] = {
                        'status': 'SUCCESS',
                        'response_time': response_time,
                        'data_available': True
                    }
                else:
                    print("   ✗ Yahoo Finance API returned invalid data")
                    self.results['api_connections']['yahoo_finance'] = {
                        'status': 'FAILED',
                        'error': 'Invalid data format'
                    }
            else:
                print(f"   ✗ Yahoo Finance API failed: HTTP {response.status_code}")
                self.results['api_connections']['yahoo_finance'] = {
                    'status': 'FAILED',
                    'error': f'HTTP {response.status_code}'
                }
                
        except Exception as e:
            print(f"   ✗ Yahoo Finance API validation failed: {e}")
            self.results['api_connections']['yahoo_finance'] = {
                'status': 'ERROR',
                'error': str(e)
            }
        
        # 2. Alpha Vantage API (if configured)
        print("2. Alpha Vantage API Validation")
        try:
            # Check for API key in environment
            api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
            
            if api_key and api_key != 'your_alpha_vantage_api_key_here':
                url = "https://www.alphavantage.co/query"
                params = {
                    'function': 'TIME_SERIES_DAILY',
                    'symbol': 'AAPL',
                    'apikey': api_key,
                    'outputsize': 'compact'
                }
                
                start_time = time.time()
                response = requests.get(url, params=params, timeout=30)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    if 'Time Series (Daily)' in data:
                        print(f"   ✓ Alpha Vantage API working (response time: {response_time:.2f}s)")
                        self.results['api_connections']['alpha_vantage'] = {
                            'status': 'SUCCESS',
                            'response_time': response_time,
                            'data_available': True
                        }
                    elif 'Note' in data:
                        print("   ⚠ Alpha Vantage API rate limited")
                        self.results['api_connections']['alpha_vantage'] = {
                            'status': 'RATE_LIMITED',
                            'note': data['Note']
                        }
                    else:
                        print("   ✗ Alpha Vantage API returned invalid data")
                        self.results['api_connections']['alpha_vantage'] = {
                            'status': 'FAILED',
                            'error': 'Invalid data format'
                        }
                else:
                    print(f"   ✗ Alpha Vantage API failed: HTTP {response.status_code}")
                    self.results['api_connections']['alpha_vantage'] = {
                        'status': 'FAILED',
                        'error': f'HTTP {response.status_code}'
                    }
            else:
                print("   ⚠ Alpha Vantage API key not configured")
                self.results['api_connections']['alpha_vantage'] = {
                    'status': 'NOT_CONFIGURED',
                    'note': 'API key required'
                }
                
        except Exception as e:
            print(f"   ✗ Alpha Vantage API validation failed: {e}")
            self.results['api_connections']['alpha_vantage'] = {
                'status': 'ERROR',
                'error': str(e)
            }
        
        # 3. Alpaca Trading API (if configured)
        print("3. Alpaca Trading API Validation")
        try:
            api_key = os.getenv('ALPACA_API_KEY')
            secret_key = os.getenv('ALPACA_SECRET_KEY')
            
            if api_key and secret_key:
                url = "https://paper-api.alpaca.markets/v2/account"
                headers = {
                    'APCA-API-KEY-ID': api_key,
                    'APCA-API-SECRET-KEY': secret_key
                }
                
                start_time = time.time()
                response = requests.get(url, headers=headers, timeout=10)
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    if 'account_id' in data:
                        print(f"   ✓ Alpaca API working (response time: {response_time:.2f}s)")
                        print(f"   ✓ Account Status: {data.get('status', 'Unknown')}")
                        self.results['api_connections']['alpaca'] = {
                            'status': 'SUCCESS',
                            'response_time': response_time,
                            'account_status': data.get('status'),
                            'paper_trading': True
                        }
                    else:
                        print("   ✗ Alpaca API returned invalid data")
                        self.results['api_connections']['alpaca'] = {
                            'status': 'FAILED',
                            'error': 'Invalid data format'
                        }
                else:
                    print(f"   ✗ Alpaca API failed: HTTP {response.status_code}")
                    self.results['api_connections']['alpaca'] = {
                        'status': 'FAILED',
                        'error': f'HTTP {response.status_code}'
                    }
            else:
                print("   ⚠ Alpaca API credentials not configured")
                self.results['api_connections']['alpaca'] = {
                    'status': 'NOT_CONFIGURED',
                    'note': 'API credentials required'
                }
                
        except Exception as e:
            print(f"   ✗ Alpaca API validation failed: {e}")
            self.results['api_connections']['alpaca'] = {
                'status': 'ERROR',
                'error': str(e)
            }
    
    def _validate_database(self):
        """Validate database operations"""
        
        print("1. Database Connection")
        try:
            if not os.path.exists(self.db_path):
                print(f"   ✗ Database file not found: {self.db_path}")
                self.results['database_operations']['connection'] = {
                    'status': 'FAILED',
                    'error': 'Database file not found'
                }
                return
            
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()
            
            # Test basic connection
            cursor.execute("SELECT sqlite_version()")
            version = cursor.fetchone()[0]
            print(f"   ✓ Database connected (SQLite {version})")
            
            # Check required tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = [
                'users', 'symbols', 'watchlists', 'watchlist_symbols',
                'market_data', 'indicators', 'signals', 'trades', 'positions',
                'performance', 'models', 'predictions', 'news_articles',
                'news_symbols', 'market_movers', 'audit_log', 'api_usage'
            ]
            
            missing_tables = [table for table in required_tables if table not in tables]
            
            if missing_tables:
                print(f"   ⚠ Missing tables: {', '.join(missing_tables)}")
                self.results['database_operations']['connection'] = {
                    'status': 'PARTIAL',
                    'tables_found': len(tables),
                    'missing_tables': missing_tables
                }
            else:
                print(f"   ✓ All required tables present ({len(tables)} total)")
                self.results['database_operations']['connection'] = {
                    'status': 'SUCCESS',
                    'tables_found': len(tables),
                    'all_required_tables': True
                }
            
            conn.close()
            
        except Exception as e:
            print(f"   ✗ Database connection failed: {e}")
            self.results['database_operations']['connection'] = {
                'status': 'ERROR',
                'error': str(e)
            }
            return
        
        print("2. Database Operations")
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()
            
            # Test basic CRUD operations
            test_table = f"test_validation_{int(time.time())}"
            
            # Create test table
            cursor.execute(f"""
                CREATE TABLE {test_table} (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    value REAL,
                    timestamp INTEGER
                )
            """)
            
            # Insert data
            cursor.execute(f"""
                INSERT INTO {test_table} (name, value, timestamp) 
                VALUES (?, ?, ?)
            """, ('test', 123.45, int(time.time())))
            
            # Read data
            cursor.execute(f"SELECT * FROM {test_table}")
            result = cursor.fetchone()
            
            if result:
                print("   ✓ Database CRUD operations working")
                
                # Update data
                cursor.execute(f"""
                    UPDATE {test_table} SET value = ? WHERE name = ?
                """, (543.21, 'test'))
                
                # Delete data
                cursor.execute(f"DELETE FROM {test_table}")
                
                # Drop test table
                cursor.execute(f"DROP TABLE {test_table}")
                
                self.results['database_operations']['crud'] = {
                    'status': 'SUCCESS',
                    'operations': ['create', 'read', 'update', 'delete']
                }
            else:
                print("   ✗ Database read operation failed")
                self.results['database_operations']['crud'] = {
                    'status': 'FAILED',
                    'error': 'Read operation failed'
                }
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"   ✗ Database operations failed: {e}")
            self.results['database_operations']['crud'] = {
                'status': 'ERROR',
                'error': str(e)
            }
    
    def _validate_data_flow(self):
        """Validate data flow from APIs to database"""
        
        print("1. API to Database Data Flow")
        try:
            # Get data from Yahoo Finance
            url = "https://query1.finance.yahoo.com/v8/finance/chart/AAPL?range=1d&interval=1m"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'chart' in data and 'result' in data['chart']:
                    result = data['chart']['result'][0]
                    
                    # Extract price data
                    if 'timestamp' in result and 'indicators' in result:
                        timestamps = result['timestamp']
                        quotes = result['indicators']['quote'][0]
                        
                        if timestamps and quotes and 'close' in quotes:
                            # Get latest price
                            latest_price = quotes['close'][-1]
                            latest_timestamp = timestamps[-1]
                            
                            print(f"   ✓ API data retrieved: ${latest_price:.2f} at {datetime.fromtimestamp(latest_timestamp)}")
                            
                            # Test database storage
                            conn = sqlite3.connect(self.db_path, timeout=10)
                            cursor = conn.cursor()
                            
                            # Check if symbols table exists
                            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='symbols'")
                            if cursor.fetchone():
                                # Insert test data
                                test_data = {
                                    'symbol': 'AAPL',
                                    'timestamp': latest_timestamp,
                                    'open': latest_price,
                                    'high': latest_price,
                                    'low': latest_price,
                                    'close': latest_price,
                                    'volume': 1000000
                                }
                                
                                cursor.execute("""
                                    INSERT INTO market_data (symbol, timestamp, open, high, low, close, volume)
                                    VALUES (?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    test_data['symbol'], test_data['timestamp'],
                                    test_data['open'], test_data['high'], test_data['low'],
                                    test_data['close'], test_data['volume']
                                ))
                                
                                # Retrieve data
                                cursor.execute("""
                                    SELECT * FROM market_data 
                                    WHERE symbol = ? 
                                    ORDER BY timestamp DESC 
                                    LIMIT 1
                                """, (test_data['symbol'],))
                                
                                db_result = cursor.fetchone()
                                if db_result:
                                    print("   ✓ Data stored and retrieved from database")
                                    
                                    # Cleanup test data
                                    cursor.execute("""
                                        DELETE FROM market_data 
                                        WHERE symbol = ? AND timestamp = ?
                                    """, (test_data['symbol'], test_data['timestamp']))
                                    
                                    self.results['data_flow']['api_to_database'] = {
                                        'status': 'SUCCESS',
                                        'api_price': latest_price,
                                        'database_integration': 'working'
                                    }
                                else:
                                    print("   ✗ Database retrieval failed")
                                    self.results['data_flow']['api_to_database'] = {
                                        'status': 'FAILED',
                                        'error': 'Database retrieval failed'
                                    }
                            else:
                                print("   ⚠ Symbols table not found, skipping database test")
                                self.results['data_flow']['api_to_database'] = {
                                    'status': 'PARTIAL',
                                    'api_working': True,
                                    'database_tables': 'missing'
                                }
                            
                            conn.commit()
                            conn.close()
                        else:
                            print("   ✗ No price data in API response")
                            self.results['data_flow']['api_to_database'] = {
                                'status': 'FAILED',
                                'error': 'No price data'
                            }
                    else:
                        print("   ✗ Invalid API response format")
                        self.results['data_flow']['api_to_database'] = {
                            'status': 'FAILED',
                            'error': 'Invalid response format'
                        }
                else:
                    print("   ✗ API response missing required data")
                    self.results['data_flow']['api_to_database'] = {
                        'status': 'FAILED',
                        'error': 'Missing required data'
                    }
            else:
                print(f"   ✗ API request failed: HTTP {response.status_code}")
                self.results['data_flow']['api_to_database'] = {
                    'status': 'FAILED',
                    'error': f'HTTP {response.status_code}'
                }
                
        except Exception as e:
            print(f"   ✗ Data flow validation failed: {e}")
            self.results['data_flow']['api_to_database'] = {
                'status': 'ERROR',
                'error': str(e)
            }
    
    def _validate_performance(self):
        """Validate performance metrics"""
        
        print("1. API Response Time Testing")
        try:
            # Test Yahoo Finance API response time
            url = "https://query1.finance.yahoo.com/v8/finance/chart/AAPL?range=1d&interval=1m"
            
            start_time = time.time()
            response = requests.get(url, timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                print(f"   ✓ API response time: {response_time:.2f} seconds")
                
                if response_time < 5.0:
                    print("   ✓ API performance acceptable")
                    self.results['performance_metrics']['api_response_time'] = {
                        'status': 'SUCCESS',
                        'response_time': response_time,
                        'threshold': 5.0
                    }
                else:
                    print("   ⚠ API response time slow")
                    self.results['performance_metrics']['api_response_time'] = {
                        'status': 'SLOW',
                        'response_time': response_time,
                        'threshold': 5.0
                    }
            else:
                print("   ✗ API performance test failed")
                self.results['performance_metrics']['api_response_time'] = {
                    'status': 'FAILED',
                    'error': f'HTTP {response.status_code}'
                }
                
        except Exception as e:
            print(f"   ✗ API performance test failed: {e}")
            self.results['performance_metrics']['api_response_time'] = {
                'status': 'ERROR',
                'error': str(e)
            }
        
        print("2. Database Query Performance")
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()
            
            start_time = time.time()
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            result = cursor.fetchone()
            query_time = time.time() - start_time
            
            if result:
                print(f"   ✓ Database query time: {query_time:.3f} seconds")
                
                if query_time < 1.0:
                    print("   ✓ Database performance acceptable")
                    self.results['performance_metrics']['database_query_time'] = {
                        'status': 'SUCCESS',
                        'query_time': query_time,
                        'threshold': 1.0
                    }
                else:
                    print("   ⚠ Database query time slow")
                    self.results['performance_metrics']['database_query_time'] = {
                        'status': 'SLOW',
                        'query_time': query_time,
                        'threshold': 1.0
                    }
            else:
                print("   ✗ Database performance test failed")
                self.results['performance_metrics']['database_query_time'] = {
                    'status': 'FAILED',
                    'error': 'Query failed'
                }
            
            conn.close()
            
        except Exception as e:
            print(f"   ✗ Database performance test failed: {e}")
            self.results['performance_metrics']['database_query_time'] = {
                'status': 'ERROR',
                'error': str(e)
            }
    
    def _generate_summary_report(self):
        """Generate comprehensive summary report"""
        
        # Count successes and failures
        total_tests = 0
        successful_tests = 0
        failed_tests = 0
        error_tests = 0
        
        for category, tests in self.results.items():
            for test_name, result in tests.items():
                total_tests += 1
                if result['status'] == 'SUCCESS':
                    successful_tests += 1
                elif result['status'] in ['FAILED', 'ERROR']:
                    failed_tests += 1
                elif result['status'] == 'ERROR':
                    error_tests += 1
        
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Errors: {error_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print()
        
        # Detailed breakdown
        print("DETAILED BREAKDOWN:")
        print("-" * 30)
        
        for category, tests in self.results.items():
            print(f"\n{category.upper()}:")
            for test_name, result in tests.items():
                status_icon = "✓" if result['status'] == 'SUCCESS' else "✗" if result['status'] in ['FAILED', 'ERROR'] else "⚠"
                print(f"  {status_icon} {test_name}: {result['status']}")
        
        # Recommendations
        print("\nRECOMMENDATIONS:")
        print("-" * 20)
        
        if success_rate >= 90:
            print("✓ System is in excellent condition")
            print("✓ All major components operational")
            print("✓ Ready for production use")
        elif success_rate >= 75:
            print("⚠ System is mostly operational")
            print("⚠ Some components need attention")
            print("⚠ Review failed tests before production")
        else:
            print("✗ System has significant issues")
            print("✗ Critical components need fixing")
            print("✗ Do not deploy to production")
        
        # Save results to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = f"simple_validation_results_{timestamp}.json"
        
        try:
            with open(results_file, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            print(f"\nResults saved to: {results_file}")
        except Exception as e:
            print(f"\nFailed to save results: {e}")


def main():
    """Main validation function"""
    validator = SimpleAPIValidator()
    results = validator.run_full_validation()
    
    # Return exit code based on success rate
    total_tests = sum(len(tests) for tests in results.values())
    successful_tests = sum(
        sum(1 for test in tests.values() if test['status'] == 'SUCCESS')
        for tests in results.values()
    )
    
    success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
    
    if success_rate >= 90:
        print("\n🎉 VALIDATION PASSED - System ready for production!")
        return 0
    elif success_rate >= 75:
        print("\n⚠ VALIDATION WARNING - System mostly operational")
        return 1
    else:
        print("\n❌ VALIDATION FAILED - System needs attention")
        return 2


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 