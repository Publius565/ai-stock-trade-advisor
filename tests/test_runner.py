"""
Test Runner for AI-Driven Stock Trade Advisor

Comprehensive test runner for all organized test suites.
"""

import unittest
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import all test modules
from .test_profile_management import TestProfileManagement
from .test_market_scanner import TestMarketScanner
from .test_database import TestDatabaseInfrastructure, TestUserManager, TestMarketDataManager
from .test_ui_components import (
    TestUIComponentsStructure,
    TestProfileTabLogic,
    TestMarketScannerTabLogic,
    TestWatchlistTabLogic,
    TestDashboardTabLogic,
    TestUIComponentsIntegration
)


def create_test_suite():
    """Create comprehensive test suite."""
    suite = unittest.TestSuite()
    
    # Database Tests
    suite.addTest(unittest.makeSuite(TestDatabaseInfrastructure))
    suite.addTest(unittest.makeSuite(TestUserManager))
    suite.addTest(unittest.makeSuite(TestMarketDataManager))
    
    # Profile Management Tests
    suite.addTest(unittest.makeSuite(TestProfileManagement))
    
    # Market Scanner Tests
    suite.addTest(unittest.makeSuite(TestMarketScanner))
    
    # UI Component Tests
    suite.addTest(unittest.makeSuite(TestUIComponentsStructure))
    suite.addTest(unittest.makeSuite(TestProfileTabLogic))
    suite.addTest(unittest.makeSuite(TestMarketScannerTabLogic))
    suite.addTest(unittest.makeSuite(TestWatchlistTabLogic))
    suite.addTest(unittest.makeSuite(TestDashboardTabLogic))
    suite.addTest(unittest.makeSuite(TestUIComponentsIntegration))
    
    return suite


def run_tests(verbosity=2):
    """Run all tests with specified verbosity."""
    print("="*70)
    print("AI-Driven Stock Trade Advisor - Test Suite")
    print("="*70)
    
    suite = create_test_suite()
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    print("\n" + "="*70)
    print("Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    print("="*70)
    
    return result.wasSuccessful()


def run_specific_test_category(category):
    """Run specific category of tests."""
    suite = unittest.TestSuite()
    
    if category.lower() == 'database':
        suite.addTest(unittest.makeSuite(TestDatabaseInfrastructure))
        suite.addTest(unittest.makeSuite(TestUserManager))
        suite.addTest(unittest.makeSuite(TestMarketDataManager))
    
    elif category.lower() == 'profile':
        suite.addTest(unittest.makeSuite(TestProfileManagement))
    
    elif category.lower() == 'scanner':
        suite.addTest(unittest.makeSuite(TestMarketScanner))
    
    elif category.lower() == 'ui':
        suite.addTest(unittest.makeSuite(TestUIComponentsStructure))
        suite.addTest(unittest.makeSuite(TestProfileTabLogic))
        suite.addTest(unittest.makeSuite(TestMarketScannerTabLogic))
        suite.addTest(unittest.makeSuite(TestWatchlistTabLogic))
        suite.addTest(unittest.makeSuite(TestDashboardTabLogic))
        suite.addTest(unittest.makeSuite(TestUIComponentsIntegration))
    
    else:
        print(f"Unknown test category: {category}")
        print("Available categories: database, profile, scanner, ui")
        return False
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Run specific test category
        category = sys.argv[1]
        success = run_specific_test_category(category)
    else:
        # Run all tests
        success = run_tests()
    
    sys.exit(0 if success else 1) 