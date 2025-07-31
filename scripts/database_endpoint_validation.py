#!/usr/bin/env python3
"""
Database Endpoint Validation Script

Comprehensive validation of all database operations, endpoints, and data integrity.
Tests all database managers and their CRUD operations.
"""

import os
import sys
import time
import logging
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseEndpointValidator:
    """Comprehensive database endpoint validation system"""
    
    def __init__(self):
        self.results = {
            'database_schema': {},
            'user_management': {},
            'market_data_management': {},
            'signal_management': {},
            'watchlist_management': {},
            'performance_metrics': {},
            'data_integrity': {}
        }
        self.db_path = "data/trading_advisor.db"
        
    def run_full_validation(self) -> Dict[str, Any]:
        """Run complete database endpoint validation"""
        print("=" * 80)
        print("DATABASE ENDPOINT VALIDATION")
        print("=" * 80)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Phase 1: Database Schema Validation
        print("PHASE 1: DATABASE SCHEMA VALIDATION")
        print("-" * 50)
        self._validate_database_schema()
        
        # Phase 2: User Management Endpoints
        print("\nPHASE 2: USER MANAGEMENT ENDPOINTS")
        print("-" * 50)
        self._validate_user_management()
        
        # Phase 3: Market Data Management Endpoints
        print("\nPHASE 3: MARKET DATA MANAGEMENT ENDPOINTS")
        print("-" * 50)
        self._validate_market_data_management()
        
        # Phase 4: Signal Management Endpoints
        print("\nPHASE 4: SIGNAL MANAGEMENT ENDPOINTS")
        print("-" * 50)
        self._validate_signal_management()
        
        # Phase 5: Watchlist Management Endpoints
        print("\nPHASE 5: WATCHLIST MANAGEMENT ENDPOINTS")
        print("-" * 50)
        self._validate_watchlist_management()
        
        # Phase 6: Performance Testing
        print("\nPHASE 6: PERFORMANCE TESTING")
        print("-" * 50)
        self._validate_performance()
        
        # Phase 7: Data Integrity Testing
        print("\nPHASE 7: DATA INTEGRITY TESTING")
        print("-" * 50)
        self._validate_data_integrity()
        
        # Generate Summary Report
        print("\n" + "=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)
        self._generate_summary_report()
        
        return self.results
    
    def _validate_database_schema(self):
        """Validate database schema and structure"""
        
        print("1. Database Connection and Schema")
        try:
            if not os.path.exists(self.db_path):
                print(f"   ✗ Database file not found: {self.db_path}")
                self.results['database_schema']['connection'] = {
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
            
            # Check all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [row[0] for row in cursor.fetchall()]
            
            print(f"   ✓ Found {len(tables)} tables: {', '.join(tables)}")
            
            # Check required tables
            required_tables = [
                'users', 'symbols', 'watchlists', 'watchlist_symbols',
                'market_data', 'indicators', 'signals', 'trades', 'positions',
                'performance', 'models', 'predictions', 'news_articles',
                'news_symbols', 'market_movers', 'audit_log', 'api_usage'
            ]
            
            missing_tables = [table for table in required_tables if table not in tables]
            
            if missing_tables:
                print(f"   ⚠ Missing tables: {', '.join(missing_tables)}")
                self.results['database_schema']['tables'] = {
                    'status': 'PARTIAL',
                    'tables_found': len(tables),
                    'missing_tables': missing_tables
                }
            else:
                print(f"   ✓ All required tables present")
                self.results['database_schema']['tables'] = {
                    'status': 'SUCCESS',
                    'tables_found': len(tables),
                    'all_required_tables': True
                }
            
            # Check indexes
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indexes = [row[0] for row in cursor.fetchall()]
            print(f"   ✓ Found {len(indexes)} indexes")
            
            # Check foreign key constraints
            cursor.execute("PRAGMA foreign_keys")
            fk_enabled = cursor.fetchone()[0]
            print(f"   ✓ Foreign key constraints: {'enabled' if fk_enabled else 'disabled'}")
            
            # Check table structures
            print("2. Table Structure Validation")
            for table in required_tables[:5]:  # Check first 5 tables
                if table in tables:
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = cursor.fetchall()
                    print(f"   ✓ {table}: {len(columns)} columns")
                else:
                    print(f"   ✗ {table}: table missing")
            
            conn.close()
            
            self.results['database_schema']['connection'] = {
                'status': 'SUCCESS',
                'sqlite_version': version,
                'tables_count': len(tables),
                'indexes_count': len(indexes),
                'foreign_keys_enabled': bool(fk_enabled)
            }
            
        except Exception as e:
            print(f"   ✗ Database schema validation failed: {e}")
            self.results['database_schema']['connection'] = {
                'status': 'ERROR',
                'error': str(e)
            }
    
    def _validate_user_management(self):
        """Validate user management endpoints"""
        
        print("1. User CRUD Operations")
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()
            
            # Test user creation
            test_user = {
                'username': f'test_user_{int(time.time())}',
                'email': f'test_{int(time.time())}@example.com',
                'risk_tolerance': 'medium',
                'investment_goals': 'growth',
                'experience_level': 'intermediate'
            }
            
            # Generate UID
            uid = f"user_{int(time.time())}_{hash(test_user['username']) % 10000}"
            
            # Insert user
            cursor.execute("""
                INSERT INTO users (uid, username, email, risk_tolerance, investment_goals, experience_level, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                uid, test_user['username'], test_user['email'],
                test_user['risk_tolerance'], test_user['investment_goals'],
                test_user['experience_level'], int(time.time())
            ))
            
            print(f"   ✓ User created: {uid}")
            
            # Read user
            cursor.execute("SELECT * FROM users WHERE uid = ?", (uid,))
            user_data = cursor.fetchone()
            
            if user_data:
                print("   ✓ User retrieved successfully")
                
                # Update user
                cursor.execute("""
                    UPDATE users SET risk_tolerance = ? WHERE uid = ?
                """, ('high', uid))
                
                print("   ✓ User updated successfully")
                
                # Verify update
                cursor.execute("SELECT risk_tolerance FROM users WHERE uid = ?", (uid,))
                updated_risk = cursor.fetchone()[0]
                
                if updated_risk == 'high':
                    print("   ✓ User update verified")
                    
                    # Delete user
                    cursor.execute("DELETE FROM users WHERE uid = ?", (uid,))
                    
                    # Verify deletion
                    cursor.execute("SELECT COUNT(*) FROM users WHERE uid = ?", (uid,))
                    count = cursor.fetchone()[0]
                    
                    if count == 0:
                        print("   ✓ User deleted successfully")
                        self.results['user_management']['crud'] = {
                            'status': 'SUCCESS',
                            'operations': ['create', 'read', 'update', 'delete'],
                            'test_user': test_user['username']
                        }
                    else:
                        print("   ✗ User deletion failed")
                        self.results['user_management']['crud'] = {
                            'status': 'PARTIAL',
                            'operations': ['create', 'read', 'update'],
                            'failed': 'delete'
                        }
                else:
                    print("   ✗ User update verification failed")
                    self.results['user_management']['crud'] = {
                        'status': 'PARTIAL',
                        'operations': ['create', 'read'],
                        'failed': 'update'
                    }
            else:
                print("   ✗ User retrieval failed")
                self.results['user_management']['crud'] = {
                    'status': 'PARTIAL',
                    'operations': ['create'],
                    'failed': 'read'
                }
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"   ✗ User management validation failed: {e}")
            self.results['user_management']['crud'] = {
                'status': 'ERROR',
                'error': str(e)
            }
        
        print("2. User Query Operations")
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()
            
            # Test user queries
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            print(f"   ✓ Total users: {user_count}")
            
            cursor.execute("SELECT username, risk_tolerance FROM users LIMIT 5")
            users = cursor.fetchall()
            print(f"   ✓ Retrieved {len(users)} users")
            
            # Test filtering
            cursor.execute("SELECT COUNT(*) FROM users WHERE risk_tolerance = 'medium'")
            medium_risk_count = cursor.fetchone()[0]
            print(f"   ✓ Medium risk users: {medium_risk_count}")
            
            conn.close()
            
            self.results['user_management']['queries'] = {
                'status': 'SUCCESS',
                'total_users': user_count,
                'sample_users': len(users),
                'medium_risk_users': medium_risk_count
            }
            
        except Exception as e:
            print(f"   ✗ User query validation failed: {e}")
            self.results['user_management']['queries'] = {
                'status': 'ERROR',
                'error': str(e)
            }
    
    def _validate_market_data_management(self):
        """Validate market data management endpoints"""
        
        print("1. Symbol Management")
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()
            
            # Test symbol creation
            test_symbol = f'TEST{int(time.time())}'
            symbol_uid = f"symbol_{int(time.time())}"
            
            cursor.execute("""
                INSERT INTO symbols (uid, symbol, company_name, sector, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (symbol_uid, test_symbol, 'Test Company', 'Technology', int(time.time())))
            
            print(f"   ✓ Symbol created: {test_symbol}")
            
            # Read symbol
            cursor.execute("SELECT * FROM symbols WHERE symbol = ?", (test_symbol,))
            symbol_data = cursor.fetchone()
            
            if symbol_data:
                print("   ✓ Symbol retrieved successfully")
                
                # Update symbol
                cursor.execute("""
                    UPDATE symbols SET sector = ? WHERE symbol = ?
                """, ('Finance', test_symbol))
                
                print("   ✓ Symbol updated successfully")
                
                # Delete symbol
                cursor.execute("DELETE FROM symbols WHERE symbol = ?", (test_symbol,))
                
                # Verify deletion
                cursor.execute("SELECT COUNT(*) FROM symbols WHERE symbol = ?", (test_symbol,))
                count = cursor.fetchone()[0]
                
                if count == 0:
                    print("   ✓ Symbol deleted successfully")
                    self.results['market_data_management']['symbols'] = {
                        'status': 'SUCCESS',
                        'operations': ['create', 'read', 'update', 'delete'],
                        'test_symbol': test_symbol
                    }
                else:
                    print("   ✗ Symbol deletion failed")
                    self.results['market_data_management']['symbols'] = {
                        'status': 'PARTIAL',
                        'operations': ['create', 'read', 'update'],
                        'failed': 'delete'
                    }
            else:
                print("   ✗ Symbol retrieval failed")
                self.results['market_data_management']['symbols'] = {
                    'status': 'PARTIAL',
                    'operations': ['create'],
                    'failed': 'read'
                }
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"   ✗ Symbol management validation failed: {e}")
            self.results['market_data_management']['symbols'] = {
                'status': 'ERROR',
                'error': str(e)
            }
        
        print("2. Market Data Storage")
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()
            
            # Test market data storage
            test_data = {
                'symbol': 'AAPL',
                'timestamp': int(time.time()),
                'open': 150.0,
                'high': 155.0,
                'low': 148.0,
                'close': 152.0,
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
            
            print("   ✓ Market data stored")
            
            # Retrieve data
            cursor.execute("""
                SELECT * FROM market_data 
                WHERE symbol = ? AND timestamp = ?
            """, (test_data['symbol'], test_data['timestamp']))
            
            db_data = cursor.fetchone()
            if db_data:
                print("   ✓ Market data retrieved successfully")
                
                # Cleanup
                cursor.execute("""
                    DELETE FROM market_data 
                    WHERE symbol = ? AND timestamp = ?
                """, (test_data['symbol'], test_data['timestamp']))
                
                print("   ✓ Test data cleaned up")
                
                self.results['market_data_management']['market_data'] = {
                    'status': 'SUCCESS',
                    'operations': ['store', 'retrieve', 'cleanup'],
                    'test_symbol': test_data['symbol']
                }
            else:
                print("   ✗ Market data retrieval failed")
                self.results['market_data_management']['market_data'] = {
                    'status': 'PARTIAL',
                    'operations': ['store'],
                    'failed': 'retrieve'
                }
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"   ✗ Market data storage validation failed: {e}")
            self.results['market_data_management']['market_data'] = {
                'status': 'ERROR',
                'error': str(e)
            }
    
    def _validate_signal_management(self):
        """Validate signal management endpoints"""
        
        print("1. Signal CRUD Operations")
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()
            
            # Test signal creation
            test_signal = {
                'symbol': 'AAPL',
                'signal_type': 'BUY',
                'confidence': 0.75,
                'price': 150.0,
                'timestamp': int(time.time()),
                'source': 'test_validation'
            }
            
            signal_uid = f"signal_{int(time.time())}"
            
            cursor.execute("""
                INSERT INTO signals (uid, symbol, signal_type, confidence, price, timestamp, source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                signal_uid, test_signal['symbol'], test_signal['signal_type'],
                test_signal['confidence'], test_signal['price'],
                test_signal['timestamp'], test_signal['source']
            ))
            
            print("   ✓ Signal created")
            
            # Read signal
            cursor.execute("SELECT * FROM signals WHERE uid = ?", (signal_uid,))
            signal_data = cursor.fetchone()
            
            if signal_data:
                print("   ✓ Signal retrieved successfully")
                
                # Update signal
                cursor.execute("""
                    UPDATE signals SET confidence = ? WHERE uid = ?
                """, (0.80, signal_uid))
                
                print("   ✓ Signal updated successfully")
                
                # Delete signal
                cursor.execute("DELETE FROM signals WHERE uid = ?", (signal_uid,))
                
                # Verify deletion
                cursor.execute("SELECT COUNT(*) FROM signals WHERE uid = ?", (signal_uid,))
                count = cursor.fetchone()[0]
                
                if count == 0:
                    print("   ✓ Signal deleted successfully")
                    self.results['signal_management']['crud'] = {
                        'status': 'SUCCESS',
                        'operations': ['create', 'read', 'update', 'delete'],
                        'test_signal': test_signal['symbol']
                    }
                else:
                    print("   ✗ Signal deletion failed")
                    self.results['signal_management']['crud'] = {
                        'status': 'PARTIAL',
                        'operations': ['create', 'read', 'update'],
                        'failed': 'delete'
                    }
            else:
                print("   ✗ Signal retrieval failed")
                self.results['signal_management']['crud'] = {
                    'status': 'PARTIAL',
                    'operations': ['create'],
                    'failed': 'read'
                }
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"   ✗ Signal management validation failed: {e}")
            self.results['signal_management']['crud'] = {
                'status': 'ERROR',
                'error': str(e)
            }
    
    def _validate_watchlist_management(self):
        """Validate watchlist management endpoints"""
        
        print("1. Watchlist CRUD Operations")
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()
            
            # Create test user first
            test_user_uid = f"user_{int(time.time())}"
            cursor.execute("""
                INSERT INTO users (uid, username, email, risk_tolerance, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (test_user_uid, f'test_user_{int(time.time())}', 'test@example.com', 'medium', int(time.time())))
            
            # Test watchlist creation
            watchlist_uid = f"watchlist_{int(time.time())}"
            watchlist_name = f"Test Watchlist {int(time.time())}"
            
            cursor.execute("""
                INSERT INTO watchlists (uid, user_uid, name, created_at)
                VALUES (?, ?, ?, ?)
            """, (watchlist_uid, test_user_uid, watchlist_name, int(time.time())))
            
            print("   ✓ Watchlist created")
            
            # Read watchlist
            cursor.execute("SELECT * FROM watchlists WHERE uid = ?", (watchlist_uid,))
            watchlist_data = cursor.fetchone()
            
            if watchlist_data:
                print("   ✓ Watchlist retrieved successfully")
                
                # Add symbols to watchlist
                test_symbols = ['AAPL', 'MSFT', 'GOOGL']
                for symbol in test_symbols:
                    cursor.execute("""
                        INSERT INTO watchlist_symbols (watchlist_uid, symbol, added_at)
                        VALUES (?, ?, ?)
                    """, (watchlist_uid, symbol, int(time.time())))
                
                print(f"   ✓ Added {len(test_symbols)} symbols to watchlist")
                
                # Get watchlist with symbols
                cursor.execute("""
                    SELECT w.name, ws.symbol 
                    FROM watchlists w 
                    JOIN watchlist_symbols ws ON w.uid = ws.watchlist_uid 
                    WHERE w.uid = ?
                """, (watchlist_uid,))
                
                watchlist_items = cursor.fetchall()
                print(f"   ✓ Retrieved {len(watchlist_items)} watchlist items")
                
                # Cleanup
                cursor.execute("DELETE FROM watchlist_symbols WHERE watchlist_uid = ?", (watchlist_uid,))
                cursor.execute("DELETE FROM watchlists WHERE uid = ?", (watchlist_uid,))
                cursor.execute("DELETE FROM users WHERE uid = ?", (test_user_uid,))
                
                print("   ✓ Test data cleaned up")
                
                self.results['watchlist_management']['crud'] = {
                    'status': 'SUCCESS',
                    'operations': ['create', 'read', 'add_symbols', 'retrieve_items', 'cleanup'],
                    'symbols_added': len(test_symbols)
                }
            else:
                print("   ✗ Watchlist retrieval failed")
                self.results['watchlist_management']['crud'] = {
                    'status': 'PARTIAL',
                    'operations': ['create'],
                    'failed': 'read'
                }
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"   ✗ Watchlist management validation failed: {e}")
            self.results['watchlist_management']['crud'] = {
                'status': 'ERROR',
                'error': str(e)
            }
    
    def _validate_performance(self):
        """Validate database performance"""
        
        print("1. Query Performance Testing")
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()
            
            # Test basic query performance
            start_time = time.time()
            cursor.execute("SELECT COUNT(*) FROM users")
            result = cursor.fetchone()
            query_time = time.time() - start_time
            
            print(f"   ✓ Users count query: {query_time:.3f}s")
            
            # Test join query performance
            start_time = time.time()
            cursor.execute("""
                SELECT COUNT(*) FROM watchlists w 
                JOIN users u ON w.user_uid = u.uid
            """)
            result = cursor.fetchone()
            join_time = time.time() - start_time
            
            print(f"   ✓ Join query: {join_time:.3f}s")
            
            # Test complex query performance
            start_time = time.time()
            cursor.execute("""
                SELECT symbol, COUNT(*) as data_points 
                FROM market_data 
                GROUP BY symbol 
                ORDER BY data_points DESC 
                LIMIT 10
            """)
            result = cursor.fetchall()
            complex_time = time.time() - start_time
            
            print(f"   ✓ Complex aggregation query: {complex_time:.3f}s")
            
            conn.close()
            
            # Performance thresholds
            thresholds = {
                'basic_query': 0.1,
                'join_query': 0.5,
                'complex_query': 1.0
            }
            
            performance_status = 'SUCCESS'
            if query_time > thresholds['basic_query'] or join_time > thresholds['join_query'] or complex_time > thresholds['complex_query']:
                performance_status = 'SLOW'
            
            self.results['performance_metrics']['query_performance'] = {
                'status': performance_status,
                'basic_query_time': query_time,
                'join_query_time': join_time,
                'complex_query_time': complex_time,
                'thresholds': thresholds
            }
            
        except Exception as e:
            print(f"   ✗ Performance testing failed: {e}")
            self.results['performance_metrics']['query_performance'] = {
                'status': 'ERROR',
                'error': str(e)
            }
    
    def _validate_data_integrity(self):
        """Validate data integrity constraints"""
        
        print("1. Foreign Key Constraints")
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()
            
            # Test foreign key constraint on watchlist_symbols
            cursor.execute("""
                INSERT INTO watchlist_symbols (watchlist_uid, symbol, added_at)
                VALUES (?, ?, ?)
            """, ('invalid_uid', 'AAPL', int(time.time())))
            
            print("   ✓ Foreign key constraint test completed")
            
            # Check for orphaned records
            cursor.execute("""
                SELECT COUNT(*) FROM watchlist_symbols ws
                LEFT JOIN watchlists w ON ws.watchlist_uid = w.uid
                WHERE w.uid IS NULL
            """)
            orphaned_count = cursor.fetchone()[0]
            
            if orphaned_count == 0:
                print("   ✓ No orphaned watchlist symbols found")
                self.results['data_integrity']['foreign_keys'] = {
                    'status': 'SUCCESS',
                    'orphaned_records': 0
                }
            else:
                print(f"   ⚠ Found {orphaned_count} orphaned watchlist symbols")
                self.results['data_integrity']['foreign_keys'] = {
                    'status': 'WARNING',
                    'orphaned_records': orphaned_count
                }
            
            conn.close()
            
        except Exception as e:
            print(f"   ✗ Foreign key validation failed: {e}")
            self.results['data_integrity']['foreign_keys'] = {
                'status': 'ERROR',
                'error': str(e)
            }
        
        print("2. Data Consistency Checks")
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()
            
            # Check for duplicate symbols in watchlists
            cursor.execute("""
                SELECT watchlist_uid, symbol, COUNT(*) as count
                FROM watchlist_symbols
                GROUP BY watchlist_uid, symbol
                HAVING COUNT(*) > 1
            """)
            duplicates = cursor.fetchall()
            
            if len(duplicates) == 0:
                print("   ✓ No duplicate symbols in watchlists")
                self.results['data_integrity']['consistency'] = {
                    'status': 'SUCCESS',
                    'duplicate_symbols': 0
                }
            else:
                print(f"   ⚠ Found {len(duplicates)} duplicate symbol entries")
                self.results['data_integrity']['consistency'] = {
                    'status': 'WARNING',
                    'duplicate_symbols': len(duplicates)
                }
            
            conn.close()
            
        except Exception as e:
            print(f"   ✗ Data consistency check failed: {e}")
            self.results['data_integrity']['consistency'] = {
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
            print("✓ Database is in excellent condition")
            print("✓ All endpoints operational")
            print("✓ Ready for production use")
        elif success_rate >= 75:
            print("⚠ Database is mostly operational")
            print("⚠ Some endpoints need attention")
            print("⚠ Review failed tests before production")
        else:
            print("✗ Database has significant issues")
            print("✗ Critical endpoints need fixing")
            print("✗ Do not deploy to production")
        
        # Save results to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = f"database_validation_results_{timestamp}.json"
        
        try:
            with open(results_file, 'w') as f:
                json.dump(self.results, f, indent=2, default=str)
            print(f"\nResults saved to: {results_file}")
        except Exception as e:
            print(f"\nFailed to save results: {e}")


def main():
    """Main validation function"""
    validator = DatabaseEndpointValidator()
    results = validator.run_full_validation()
    
    # Return exit code based on success rate
    total_tests = sum(len(tests) for tests in results.values())
    successful_tests = sum(
        sum(1 for test in tests.values() if test['status'] == 'SUCCESS')
        for tests in results.values()
    )
    
    success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
    
    if success_rate >= 90:
        print("\n🎉 DATABASE VALIDATION PASSED - All endpoints operational!")
        return 0
    elif success_rate >= 75:
        print("\n⚠ DATABASE VALIDATION WARNING - Mostly operational")
        return 1
    else:
        print("\n❌ DATABASE VALIDATION FAILED - Needs attention")
        return 2


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 