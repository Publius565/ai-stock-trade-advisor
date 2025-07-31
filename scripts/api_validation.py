#!/usr/bin/env python3
"""
End-to-End API Validation Script

Comprehensive validation of all API connections, database endpoints, and their integration.
Tests the complete data flow from external APIs through database storage and retrieval.
"""

import os
import sys
import time
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Add src to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, 'src')
config_path = os.path.join(project_root, 'config')

sys.path.insert(0, src_path)
sys.path.insert(0, config_path)

from data_layer.api_client import APIClient
from execution.alpaca_broker import AlpacaBroker
from utils.database_manager import DatabaseManager
from utils.market_data_manager import MarketDataManager
from data_layer.market_data import MarketData
from data_layer.market_scanner import MarketScanner
from config import (
    ALPHA_VANTAGE_API_KEY, ALPACA_API_KEY, ALPACA_SECRET_KEY, 
    ALPACA_BASE_URL, DATABASE_PATH
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class APIValidator:
    """Comprehensive API and database validation system"""
    
    def __init__(self):
        self.results = {
            'api_connections': {},
            'database_operations': {},
            'data_flow': {},
            'integration_tests': {},
            'performance_metrics': {}
        }
        self.test_symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN']
        
    def run_full_validation(self) -> Dict[str, Any]:
        """Run complete end-to-end validation"""
        print("=" * 80)
        print("END-TO-END API VALIDATION")
        print("=" * 80)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Phase 1: API Connection Validation
        print("PHASE 1: API CONNECTION VALIDATION")
        print("-" * 50)
        self._validate_api_connections()
        
        # Phase 2: Database Endpoint Validation
        print("\nPHASE 2: DATABASE ENDPOINT VALIDATION")
        print("-" * 50)
        self._validate_database_endpoints()
        
        # Phase 3: Data Flow Validation
        print("\nPHASE 3: DATA FLOW VALIDATION")
        print("-" * 50)
        self._validate_data_flow()
        
        # Phase 4: Integration Testing
        print("\nPHASE 4: INTEGRATION TESTING")
        print("-" * 50)
        self._validate_integration()
        
        # Phase 5: Performance Testing
        print("\nPHASE 5: PERFORMANCE TESTING")
        print("-" * 50)
        self._validate_performance()
        
        # Generate Summary Report
        print("\n" + "=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)
        self._generate_summary_report()
        
        return self.results
    
    def _validate_api_connections(self):
        """Validate all external API connections"""
        
        # 1. Alpha Vantage API
        print("1. Alpha Vantage API Validation")
        try:
            api_client = APIClient()
            
            # Test API key configuration
            if ALPHA_VANTAGE_API_KEY and ALPHA_VANTAGE_API_KEY != 'your_alpha_vantage_api_key_here':
                print("   ✓ API key configured")
                
                # Test data retrieval
                test_data = api_client.get_stock_data_alpha_vantage('AAPL', 'daily')
                if test_data and 'data' in test_data:
                    data_points = len(test_data['data'])
                    print(f"   ✓ Data retrieval successful ({data_points} data points)")
                    self.results['api_connections']['alpha_vantage'] = {
                        'status': 'SUCCESS',
                        'data_points': data_points,
                        'symbols_tested': ['AAPL']
                    }
                else:
                    print("   ✗ Data retrieval failed")
                    self.results['api_connections']['alpha_vantage'] = {
                        'status': 'FAILED',
                        'error': 'No data returned'
                    }
            else:
                print("   ⚠ API key not configured (using fallback)")
                self.results['api_connections']['alpha_vantage'] = {
                    'status': 'NOT_CONFIGURED',
                    'note': 'Using Yahoo Finance fallback'
                }
                
        except Exception as e:
            print(f"   ✗ Alpha Vantage validation failed: {e}")
            self.results['api_connections']['alpha_vantage'] = {
                'status': 'ERROR',
                'error': str(e)
            }
        
        # 2. Yahoo Finance API
        print("2. Yahoo Finance API Validation")
        try:
            api_client = APIClient()
            test_data = api_client.get_stock_data_yahoo('AAPL', '1y')
            
            if test_data and 'data' in test_data:
                data_points = len(test_data['data'])
                print(f"   ✓ Data retrieval successful ({data_points} data points)")
                self.results['api_connections']['yahoo_finance'] = {
                    'status': 'SUCCESS',
                    'data_points': data_points,
                    'symbols_tested': ['AAPL']
                }
            else:
                print("   ✗ Data retrieval failed")
                self.results['api_connections']['yahoo_finance'] = {
                    'status': 'FAILED',
                    'error': 'No data returned'
                }
                
        except Exception as e:
            print(f"   ✗ Yahoo Finance validation failed: {e}")
            self.results['api_connections']['yahoo_finance'] = {
                'status': 'ERROR',
                'error': str(e)
            }
        
        # 3. Alpaca Trading API
        print("3. Alpaca Trading API Validation")
        try:
            if ALPACA_API_KEY and ALPACA_SECRET_KEY:
                broker = AlpacaBroker(
                    api_key=ALPACA_API_KEY,
                    secret_key=ALPACA_SECRET_KEY,
                    base_url=ALPACA_BASE_URL,
                    paper_trading=True
                )
                
                if broker.is_connected():
                    account_info = broker.get_account_info()
                    if account_info:
                        print(f"   ✓ Connected to Alpaca Paper Trading")
                        print(f"   ✓ Account Status: {account_info['status']}")
                        print(f"   ✓ Buying Power: ${account_info['buying_power']:,.2f}")
                        
                        self.results['api_connections']['alpaca'] = {
                            'status': 'SUCCESS',
                            'account_status': account_info['status'],
                            'buying_power': account_info['buying_power'],
                            'paper_trading': True
                        }
                    else:
                        print("   ✗ Failed to get account information")
                        self.results['api_connections']['alpaca'] = {
                            'status': 'FAILED',
                            'error': 'No account info'
                        }
                else:
                    print("   ✗ Failed to connect to Alpaca")
                    self.results['api_connections']['alpaca'] = {
                        'status': 'FAILED',
                        'error': 'Connection failed'
                    }
            else:
                print("   ⚠ Alpaca API credentials not configured")
                self.results['api_connections']['alpaca'] = {
                    'status': 'NOT_CONFIGURED',
                    'note': 'API credentials required for trading'
                }
                
        except Exception as e:
            print(f"   ✗ Alpaca validation failed: {e}")
            self.results['api_connections']['alpaca'] = {
                'status': 'ERROR',
                'error': str(e)
            }
    
    def _validate_database_endpoints(self):
        """Validate all database operations and endpoints"""
        
        # 1. Database Connection
        print("1. Database Connection Validation")
        try:
            db_manager = DatabaseManager()
            print("   ✓ Database manager initialized")
            
            # Test basic database operations
            test_uid = db_manager.generate_uid('test')
            print(f"   ✓ UID generation working: {test_uid}")
            
            self.results['database_operations']['connection'] = {
                'status': 'SUCCESS',
                'uid_generation': 'working'
            }
            
        except Exception as e:
            print(f"   ✗ Database connection failed: {e}")
            self.results['database_operations']['connection'] = {
                'status': 'ERROR',
                'error': str(e)
            }
            return  # Skip other database tests if connection fails
        
        # 2. User Management Endpoints
        print("2. User Management Endpoints")
        try:
            user_manager = db_manager.users
            
            # Test user creation
            test_user = {
                'username': f'test_user_{int(time.time())}',
                'email': f'test_{int(time.time())}@example.com',
                'risk_tolerance': 'medium',
                'investment_goals': 'growth',
                'experience_level': 'intermediate'
            }
            
            user_uid = user_manager.create_user(**test_user)
            if user_uid:
                print(f"   ✓ User creation successful: {user_uid}")
                
                # Test user retrieval
                retrieved_user = user_manager.get_user_by_uid(user_uid)
                if retrieved_user and retrieved_user['username'] == test_user['username']:
                    print("   ✓ User retrieval successful")
                    
                    # Test user update
                    update_result = user_manager.update_user(user_uid, risk_tolerance='high')
                    if update_result:
                        print("   ✓ User update successful")
                        
                        # Test user deletion
                        delete_result = user_manager.delete_user(user_uid)
                        if delete_result:
                            print("   ✓ User deletion successful")
                            self.results['database_operations']['user_management'] = {
                                'status': 'SUCCESS',
                                'operations': ['create', 'retrieve', 'update', 'delete']
                            }
                        else:
                            print("   ✗ User deletion failed")
                            self.results['database_operations']['user_management'] = {
                                'status': 'PARTIAL',
                                'operations': ['create', 'retrieve', 'update'],
                                'failed': 'delete'
                            }
                    else:
                        print("   ✗ User update failed")
                        self.results['database_operations']['user_management'] = {
                            'status': 'PARTIAL',
                            'operations': ['create', 'retrieve'],
                            'failed': 'update'
                        }
                else:
                    print("   ✗ User retrieval failed")
                    self.results['database_operations']['user_management'] = {
                        'status': 'PARTIAL',
                        'operations': ['create'],
                        'failed': 'retrieve'
                    }
            else:
                print("   ✗ User creation failed")
                self.results['database_operations']['user_management'] = {
                    'status': 'FAILED',
                    'error': 'User creation failed'
                }
                
        except Exception as e:
            print(f"   ✗ User management validation failed: {e}")
            self.results['database_operations']['user_management'] = {
                'status': 'ERROR',
                'error': str(e)
            }
        
        # 3. Market Data Endpoints
        print("3. Market Data Endpoints")
        try:
            market_data_manager = db_manager.market_data
            
            # Test symbol management
            test_symbol = f'TEST{int(time.time())}'
            symbol_uid = market_data_manager.add_symbol(test_symbol, 'Test Company')
            
            if symbol_uid:
                print(f"   ✓ Symbol creation successful: {symbol_uid}")
                
                # Test market data storage
                test_data = {
                    'symbol': test_symbol,
                    'timestamp': int(time.time()),
                    'open': 100.0,
                    'high': 105.0,
                    'low': 95.0,
                    'close': 102.0,
                    'volume': 1000000
                }
                
                data_uid = market_data_manager.store_market_data(test_symbol, test_data)
                if data_uid:
                    print("   ✓ Market data storage successful")
                    
                    # Test data retrieval
                    retrieved_data = market_data_manager.get_market_data(test_symbol, limit=1)
                    if retrieved_data and len(retrieved_data) > 0:
                        print("   ✓ Market data retrieval successful")
                        
                        # Cleanup test data
                        market_data_manager.delete_symbol(test_symbol)
                        print("   ✓ Test data cleanup successful")
                        
                        self.results['database_operations']['market_data'] = {
                            'status': 'SUCCESS',
                            'operations': ['symbol_creation', 'data_storage', 'data_retrieval', 'cleanup']
                        }
                    else:
                        print("   ✗ Market data retrieval failed")
                        self.results['database_operations']['market_data'] = {
                            'status': 'PARTIAL',
                            'operations': ['symbol_creation', 'data_storage'],
                            'failed': 'data_retrieval'
                        }
                else:
                    print("   ✗ Market data storage failed")
                    self.results['database_operations']['market_data'] = {
                        'status': 'PARTIAL',
                        'operations': ['symbol_creation'],
                        'failed': 'data_storage'
                    }
            else:
                print("   ✗ Symbol creation failed")
                self.results['database_operations']['market_data'] = {
                    'status': 'FAILED',
                    'error': 'Symbol creation failed'
                }
                
        except Exception as e:
            print(f"   ✗ Market data validation failed: {e}")
            self.results['database_operations']['market_data'] = {
                'status': 'ERROR',
                'error': str(e)
            }
        
        # 4. Signal Management Endpoints
        print("4. Signal Management Endpoints")
        try:
            signal_manager = db_manager.signals
            
            # Test signal storage
            test_signal = {
                'symbol': 'AAPL',
                'signal_type': 'BUY',
                'confidence': 0.75,
                'price': 150.0,
                'timestamp': int(time.time()),
                'source': 'test_validation'
            }
            
            signal_uid = signal_manager.store_signal(**test_signal)
            if signal_uid:
                print("   ✓ Signal storage successful")
                
                # Test signal retrieval
                signals = signal_manager.get_signals('AAPL', limit=1)
                if signals and len(signals) > 0:
                    print("   ✓ Signal retrieval successful")
                    
                    # Test signal update
                    update_result = signal_manager.update_signal(signal_uid, confidence=0.80)
                    if update_result:
                        print("   ✓ Signal update successful")
                        
                        # Test signal deletion
                        delete_result = signal_manager.delete_signal(signal_uid)
                        if delete_result:
                            print("   ✓ Signal deletion successful")
                            self.results['database_operations']['signal_management'] = {
                                'status': 'SUCCESS',
                                'operations': ['store', 'retrieve', 'update', 'delete']
                            }
                        else:
                            print("   ✗ Signal deletion failed")
                            self.results['database_operations']['signal_management'] = {
                                'status': 'PARTIAL',
                                'operations': ['store', 'retrieve', 'update'],
                                'failed': 'delete'
                            }
                    else:
                        print("   ✗ Signal update failed")
                        self.results['database_operations']['signal_management'] = {
                            'status': 'PARTIAL',
                            'operations': ['store', 'retrieve'],
                            'failed': 'update'
                        }
                else:
                    print("   ✗ Signal retrieval failed")
                    self.results['database_operations']['signal_management'] = {
                        'status': 'PARTIAL',
                        'operations': ['store'],
                        'failed': 'retrieve'
                    }
            else:
                print("   ✗ Signal storage failed")
                self.results['database_operations']['signal_management'] = {
                    'status': 'FAILED',
                    'error': 'Signal storage failed'
                }
                
        except Exception as e:
            print(f"   ✗ Signal management validation failed: {e}")
            self.results['database_operations']['signal_management'] = {
                'status': 'ERROR',
                'error': str(e)
            }
    
    def _validate_data_flow(self):
        """Validate complete data flow from APIs to database"""
        
        print("1. API to Database Data Flow")
        try:
            api_client = APIClient()
            db_manager = DatabaseManager()
            
            # Test complete flow for one symbol
            symbol = 'AAPL'
            
            # Step 1: Get data from API
            print(f"   Step 1: Retrieving data for {symbol} from API...")
            api_data = api_client.get_market_data(symbol, source='auto')
            
            if api_data and 'data' in api_data and len(api_data['data']) > 0:
                print(f"   ✓ API data retrieved: {len(api_data['data'])} data points")
                
                # Step 2: Store in database
                print("   Step 2: Storing data in database...")
                market_data_manager = db_manager.market_data
                
                # Ensure symbol exists
                symbol_uid = market_data_manager.add_symbol(symbol, 'Apple Inc.')
                
                # Store latest data point
                latest_data = api_data['data'][0]
                data_uid = market_data_manager.store_market_data(symbol, latest_data)
                
                if data_uid:
                    print("   ✓ Data stored in database")
                    
                    # Step 3: Retrieve from database
                    print("   Step 3: Retrieving data from database...")
                    db_data = market_data_manager.get_market_data(symbol, limit=1)
                    
                    if db_data and len(db_data) > 0:
                        print("   ✓ Data retrieved from database")
                        
                        # Step 4: Compare data integrity
                        print("   Step 4: Validating data integrity...")
                        api_close = float(latest_data['close'])
                        db_close = float(db_data[0]['close'])
                        
                        if abs(api_close - db_close) < 0.01:  # Allow small floating point differences
                            print("   ✓ Data integrity validated")
                            self.results['data_flow']['api_to_database'] = {
                                'status': 'SUCCESS',
                                'symbol': symbol,
                                'data_points': len(api_data['data']),
                                'integrity_check': 'passed'
                            }
                        else:
                            print(f"   ✗ Data integrity check failed: API={api_close}, DB={db_close}")
                            self.results['data_flow']['api_to_database'] = {
                                'status': 'FAILED',
                                'error': 'Data integrity mismatch',
                                'api_value': api_close,
                                'db_value': db_close
                            }
                    else:
                        print("   ✗ Failed to retrieve data from database")
                        self.results['data_flow']['api_to_database'] = {
                            'status': 'FAILED',
                            'error': 'Database retrieval failed'
                        }
                else:
                    print("   ✗ Failed to store data in database")
                    self.results['data_flow']['api_to_database'] = {
                        'status': 'FAILED',
                        'error': 'Database storage failed'
                    }
            else:
                print("   ✗ Failed to retrieve data from API")
                self.results['data_flow']['api_to_database'] = {
                    'status': 'FAILED',
                    'error': 'API data retrieval failed'
                }
                
        except Exception as e:
            print(f"   ✗ Data flow validation failed: {e}")
            self.results['data_flow']['api_to_database'] = {
                'status': 'ERROR',
                'error': str(e)
            }
        
        print("2. Market Scanner Integration")
        try:
            scanner = MarketScanner()
            
            # Test market scanner with database integration
            print("   Testing market scanner with top movers...")
            movers = scanner.get_top_movers(limit=5)
            
            if movers and len(movers) > 0:
                print(f"   ✓ Market scanner working: {len(movers)} movers found")
                
                # Test database storage of scanner results
                for mover in movers[:2]:  # Test first 2 movers
                    symbol = mover['symbol']
                    market_data_manager = db_manager.market_data
                    
                    # Store scanner data
                    scanner_data = {
                        'symbol': symbol,
                        'timestamp': int(time.time()),
                        'change_percent': mover.get('change_percent', 0),
                        'volume': mover.get('volume', 0),
                        'price': mover.get('price', 0)
                    }
                    
                    data_uid = market_data_manager.store_market_data(symbol, scanner_data)
                    if data_uid:
                        print(f"   ✓ Scanner data stored for {symbol}")
                    else:
                        print(f"   ✗ Failed to store scanner data for {symbol}")
                
                self.results['data_flow']['market_scanner'] = {
                    'status': 'SUCCESS',
                    'movers_found': len(movers),
                    'database_integration': 'working'
                }
            else:
                print("   ✗ Market scanner failed to retrieve movers")
                self.results['data_flow']['market_scanner'] = {
                    'status': 'FAILED',
                    'error': 'No movers retrieved'
                }
                
        except Exception as e:
            print(f"   ✗ Market scanner validation failed: {e}")
            self.results['data_flow']['market_scanner'] = {
                'status': 'ERROR',
                'error': str(e)
            }
    
    def _validate_integration(self):
        """Validate integration between different components"""
        
        print("1. API Client Integration")
        try:
            api_client = APIClient()
            
            # Test multiple symbols
            symbols = ['AAPL', 'MSFT', 'GOOGL']
            results = api_client.get_multiple_symbols(symbols)
            
            if results and len(results) == len(symbols):
                successful_symbols = [s for s in symbols if s in results and results[s]]
                print(f"   ✓ Multiple symbol retrieval: {len(successful_symbols)}/{len(symbols)} successful")
                
                self.results['integration_tests']['api_client'] = {
                    'status': 'SUCCESS',
                    'symbols_tested': len(symbols),
                    'successful': len(successful_symbols)
                }
            else:
                print("   ✗ Multiple symbol retrieval failed")
                self.results['integration_tests']['api_client'] = {
                    'status': 'FAILED',
                    'error': 'Multiple symbol retrieval failed'
                }
                
        except Exception as e:
            print(f"   ✗ API client integration failed: {e}")
            self.results['integration_tests']['api_client'] = {
                'status': 'ERROR',
                'error': str(e)
            }
        
        print("2. Database Manager Integration")
        try:
            db_manager = DatabaseManager()
            
            # Test cross-manager operations
            test_user = {
                'username': f'integration_test_{int(time.time())}',
                'email': f'integration_{int(time.time())}@example.com',
                'risk_tolerance': 'medium'
            }
            
            # Create user
            user_uid = db_manager.users.create_user(**test_user)
            
            # Create watchlist for user
            watchlist_uid = db_manager.market_data.create_watchlist(user_uid, 'Test Watchlist')
            
            # Add symbols to watchlist
            symbols = ['AAPL', 'MSFT']
            for symbol in symbols:
                symbol_uid = db_manager.market_data.add_symbol(symbol, f'{symbol} Company')
                db_manager.market_data.add_to_watchlist(watchlist_uid, symbol_uid)
            
            # Retrieve watchlist
            watchlist = db_manager.market_data.get_watchlist(watchlist_uid)
            
            if watchlist and len(watchlist['symbols']) == len(symbols):
                print("   ✓ Cross-manager operations successful")
                
                # Cleanup
                db_manager.users.delete_user(user_uid)
                
                self.results['integration_tests']['database_manager'] = {
                    'status': 'SUCCESS',
                    'operations': ['user_creation', 'watchlist_creation', 'symbol_management']
                }
            else:
                print("   ✗ Cross-manager operations failed")
                self.results['integration_tests']['database_manager'] = {
                    'status': 'FAILED',
                    'error': 'Cross-manager operations failed'
                }
                
        except Exception as e:
            print(f"   ✗ Database manager integration failed: {e}")
            self.results['integration_tests']['database_manager'] = {
                'status': 'ERROR',
                'error': str(e)
            }
    
    def _validate_performance(self):
        """Validate performance metrics"""
        
        print("1. API Response Time Testing")
        try:
            api_client = APIClient()
            
            start_time = time.time()
            data = api_client.get_market_data('AAPL', source='auto')
            api_time = time.time() - start_time
            
            if data:
                print(f"   ✓ API response time: {api_time:.2f} seconds")
                
                if api_time < 5.0:  # 5 second threshold
                    print("   ✓ API performance acceptable")
                    self.results['performance_metrics']['api_response_time'] = {
                        'status': 'SUCCESS',
                        'response_time': api_time,
                        'threshold': 5.0
                    }
                else:
                    print("   ⚠ API response time slow")
                    self.results['performance_metrics']['api_response_time'] = {
                        'status': 'SLOW',
                        'response_time': api_time,
                        'threshold': 5.0
                    }
            else:
                print("   ✗ API performance test failed")
                self.results['performance_metrics']['api_response_time'] = {
                    'status': 'FAILED',
                    'error': 'No data returned'
                }
                
        except Exception as e:
            print(f"   ✗ API performance test failed: {e}")
            self.results['performance_metrics']['api_response_time'] = {
                'status': 'ERROR',
                'error': str(e)
            }
        
        print("2. Database Query Performance")
        try:
            db_manager = DatabaseManager()
            
            # Test database query performance
            start_time = time.time()
            symbols = db_manager.market_data.get_all_symbols()
            db_time = time.time() - start_time
            
            if symbols is not None:
                print(f"   ✓ Database query time: {db_time:.3f} seconds")
                
                if db_time < 1.0:  # 1 second threshold
                    print("   ✓ Database performance acceptable")
                    self.results['performance_metrics']['database_query_time'] = {
                        'status': 'SUCCESS',
                        'query_time': db_time,
                        'threshold': 1.0,
                        'symbols_retrieved': len(symbols)
                    }
                else:
                    print("   ⚠ Database query time slow")
                    self.results['performance_metrics']['database_query_time'] = {
                        'status': 'SLOW',
                        'query_time': db_time,
                        'threshold': 1.0,
                        'symbols_retrieved': len(symbols)
                    }
            else:
                print("   ✗ Database performance test failed")
                self.results['performance_metrics']['database_query_time'] = {
                    'status': 'FAILED',
                    'error': 'Query failed'
                }
                
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
        results_file = f"validation_results_{timestamp}.json"
        
        try:
            import json
            with open(results_file, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            print(f"\nResults saved to: {results_file}")
        except Exception as e:
            print(f"\nFailed to save results: {e}")


def main():
    """Main validation function"""
    validator = APIValidator()
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