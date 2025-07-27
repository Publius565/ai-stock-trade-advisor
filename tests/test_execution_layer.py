"""
Test Execution Layer - Comprehensive tests for Phase 4A implementation
Tests trade execution, position monitoring, and performance tracking
"""

import unittest
import tempfile
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.execution.trade_executor import TradeExecutor, MockBroker, TradeOrder, OrderType, OrderStatus
from src.execution.position_monitor import PositionMonitor, Position, PositionStatus
from src.execution.performance_tracker import PerformanceTracker, PerformanceSnapshot, PerformanceMetric
from src.strategy.trading_engine import TradingSignal, SignalType, SignalStrength
from src.utils.database_manager import DatabaseManager
from src.profile.profile_manager import ProfileManager


class TestMockBroker(unittest.TestCase):
    """Test MockBroker functionality"""
    
    def setUp(self):
        self.broker = MockBroker()
        self.test_order = TradeOrder(
            uid="test-uid",
            user_id=1,
            symbol="AAPL",
            order_type=OrderType.MARKET,
            quantity=100,
            price=150.0,
            created_at=datetime.now()
        )
    
    def test_broker_initialization(self):
        """Test broker initialization"""
        self.assertEqual(self.broker.commission_rate, 0.005)
        self.assertEqual(self.broker.min_commission, 1.0)
    
    def test_market_order_execution(self):
        """Test market order execution"""
        result = self.broker.place_order(self.test_order)
        
        self.assertTrue(result)
        self.assertEqual(self.test_order.status, OrderStatus.FILLED)
        self.assertEqual(self.test_order.filled_quantity, 100)
        self.assertEqual(self.test_order.filled_price, 150.0)
        self.assertIsNotNone(self.test_order.filled_at)
        self.assertGreater(self.test_order.commission, 0)
    
    def test_limit_order_execution(self):
        """Test limit order execution"""
        limit_order = TradeOrder(
            uid="limit-uid",
            user_id=1,
            symbol="AAPL",
            order_type=OrderType.LIMIT,
            quantity=100,
            price=150.0,
            limit_price=145.0,
            created_at=datetime.now()
        )
        
        result = self.broker.place_order(limit_order)
        
        self.assertTrue(result)
        self.assertEqual(limit_order.status, OrderStatus.FILLED)
        self.assertEqual(limit_order.filled_price, 145.0)
    
    def test_order_cancellation(self):
        """Test order cancellation"""
        result = self.broker.cancel_order("test-uid")
        self.assertTrue(result)
    
    def test_order_status_check(self):
        """Test order status retrieval"""
        status = self.broker.get_order_status("test-uid")
        self.assertEqual(status, OrderStatus.FILLED)


class TestTradeExecutor(unittest.TestCase):
    """Test TradeExecutor functionality"""
    
    def setUp(self):
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Mock database manager
        self.mock_db_manager = Mock(spec=DatabaseManager)
        self.mock_db_manager.execute_query = Mock()
        self.mock_db_manager.fetch_one = Mock(return_value=(1,))  # Mock symbol ID
        
        # Mock profile manager
        self.mock_profile_manager = Mock(spec=ProfileManager)
        self.mock_profile_manager.get_user_profile = Mock(return_value={
            'max_position_pct': 0.2,  # 20% max per position
            'risk_profile': 'moderate',
            'portfolio_value': 100000  # $100k portfolio for sufficient funds
        })
        
        # Create trade executor
        self.executor = TradeExecutor(self.mock_db_manager, self.mock_profile_manager)
        
        # Test signal
        self.test_signal = TradingSignal(
            symbol="AAPL",
            signal_type=SignalType.BUY,
            strength=SignalStrength.STRONG,
            price=150.0,
            timestamp=datetime.now(),
            confidence=0.8,
            reasoning="Strong buy signal based on technical analysis",
            indicators={'rsi': 30, 'macd': 0.5},
            risk_level="low"
        )
    
    def tearDown(self):
        # Clean up temporary database
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_executor_initialization(self):
        """Test executor initialization"""
        self.assertFalse(self.executor.execution_enabled)
        self.assertTrue(self.executor.paper_trading)
        self.assertEqual(len(self.executor.pending_orders), 0)
    
    def test_enable_execution(self):
        """Test execution enable/disable"""
        self.executor.enable_execution(True, False)
        self.assertTrue(self.executor.execution_enabled)
        self.assertFalse(self.executor.paper_trading)
    
    def test_signal_validation_valid(self):
        """Test valid signal validation"""
        result = self.executor._validate_signal(self.test_signal, 1)
        self.assertTrue(result)
    
    def test_signal_validation_invalid_type(self):
        """Test invalid signal type validation"""
        invalid_signal = TradingSignal(
            symbol="AAPL",
            signal_type=SignalType.HOLD,
            strength=SignalStrength.STRONG,
            price=150.0,
            timestamp=datetime.now(),
            confidence=0.8,
            reasoning="Hold signal",
            indicators={},
            risk_level="low"
        )
        
        result = self.executor._validate_signal(invalid_signal, 1)
        self.assertFalse(result)
    
    def test_signal_validation_low_confidence(self):
        """Test low confidence signal validation"""
        low_confidence_signal = TradingSignal(
            symbol="AAPL",
            signal_type=SignalType.BUY,
            strength=SignalStrength.STRONG,
            price=150.0,
            timestamp=datetime.now(),
            confidence=0.5,  # Below 0.6 threshold
            reasoning="Low confidence signal",
            indicators={},
            risk_level="low"
        )
        
        result = self.executor._validate_signal(low_confidence_signal, 1)
        self.assertFalse(result)
    
    def test_position_size_calculation(self):
        """Test position size calculation"""
        size = self.executor._calculate_position_size(self.test_signal, 1)
        self.assertGreater(size, 0)
        self.assertLessEqual(size, 1000)  # Max size limit
    
    def test_order_creation(self):
        """Test order creation from signal"""
        order = self.executor._create_order(self.test_signal, 1, 100)
        
        self.assertIsNotNone(order)
        self.assertEqual(order.symbol, "AAPL")
        self.assertEqual(order.quantity, 100)
        self.assertEqual(order.price, 150.0)
        self.assertEqual(order.order_type, OrderType.LIMIT)  # Regular signal uses limit
    
    def test_strong_signal_order_type(self):
        """Test strong signal uses market order"""
        strong_signal = TradingSignal(
            symbol="AAPL",
            signal_type=SignalType.STRONG_BUY,
            strength=SignalStrength.VERY_STRONG,
            price=150.0,
            timestamp=datetime.now(),
            confidence=0.9,
            reasoning="Very strong buy signal",
            indicators={},
            risk_level="low"
        )
        
        order = self.executor._create_order(strong_signal, 1, 100)
        self.assertEqual(order.order_type, OrderType.MARKET)
    
    def test_execute_signal_disabled(self):
        """Test signal execution when disabled"""
        result = self.executor.execute_signal(self.test_signal, 1)
        self.assertIsNone(result)
    
    def test_execute_signal_enabled(self):
        """Test signal execution when enabled"""
        self.executor.enable_execution(True)
        
        with patch.object(self.executor, '_validate_signal', return_value=True):
            with patch.object(self.executor, '_calculate_position_size', return_value=100):
                with patch.object(self.executor, '_store_order', return_value=True):
                    result = self.executor.execute_signal(self.test_signal, 1)
                    
                    self.assertIsNotNone(result)
                    self.assertIsInstance(result, TradeOrder)
                    self.assertEqual(result.symbol, "AAPL")
    
    def test_get_pending_orders(self):
        """Test getting pending orders"""
        # Add a test order
        test_order = TradeOrder(
            uid="test-uid",
            user_id=1,
            symbol="AAPL",
            order_type=OrderType.MARKET,
            quantity=100,
            price=150.0,
            created_at=datetime.now()
        )
        self.executor.pending_orders["test-uid"] = test_order
        
        orders = self.executor.get_pending_orders(1)
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0].symbol, "AAPL")
    
    def test_execution_summary(self):
        """Test execution summary retrieval"""
        self.mock_db_manager.fetch_one.return_value = (10, 8, 2, 0, 15000.0, 75.0)
        
        summary = self.executor.get_execution_summary(1)
        
        self.assertEqual(summary['total_orders'], 10)
        self.assertEqual(summary['filled_orders'], 8)
        self.assertEqual(summary['pending_orders'], 2)
        self.assertEqual(summary['total_volume'], 15000.0)


class TestPositionMonitor(unittest.TestCase):
    """Test PositionMonitor functionality"""
    
    def setUp(self):
        # Mock database manager
        self.mock_db_manager = Mock(spec=DatabaseManager)
        self.mock_db_manager.execute_query = Mock()
        self.mock_db_manager.fetch_all = Mock()
        self.mock_db_manager.fetch_one = Mock()
        
        # Create position monitor
        self.monitor = PositionMonitor(self.mock_db_manager)
    
    def test_monitor_initialization(self):
        """Test position monitor initialization"""
        self.assertEqual(len(self.monitor.active_positions), 0)
        self.assertEqual(len(self.monitor.position_history), 0)
    
    def test_get_user_positions(self):
        """Test getting user positions"""
        mock_data = [
            ("pos-uid", 1, "AAPL", 100, 150.0, 155.0, 15500.0, 500.0, 0.0, 1234567890)
        ]
        self.mock_db_manager.fetch_all.return_value = mock_data
        
        positions = self.monitor._get_user_positions(1)
        
        self.assertEqual(len(positions), 1)
        self.assertEqual(positions[0]['symbol'], "AAPL")
        self.assertEqual(positions[0]['quantity'], 100)
    
    def test_calculate_position_metrics(self):
        """Test position metrics calculation"""
        position_data = {
            'uid': 'pos-uid',
            'user_id': 1,
            'symbol': 'AAPL',
            'quantity': 100,
            'avg_price': 150.0,
            'current_price': 155.0,
            'market_value': 15500.0,
            'unrealized_pnl': 500.0,
            'realized_pnl': 0.0,
            'last_updated': datetime.now()
        }
        
        position = self.monitor._calculate_position_metrics(position_data, 155.0)
        
        self.assertEqual(position.symbol, "AAPL")
        self.assertEqual(position.quantity, 100)
        self.assertEqual(position.avg_price, 150.0)
        self.assertEqual(position.current_price, 155.0)
        self.assertEqual(position.market_value, 15500.0)
        self.assertEqual(position.unrealized_pnl, 500.0)
        self.assertEqual(position.total_pnl, 500.0)
        self.assertEqual(position.pnl_percentage, 3.33)  # (500 / 15000) * 100
    
    def test_add_position_new(self):
        """Test adding new position"""
        self.mock_db_manager.get_manager.return_value.get_symbol_id.return_value = 1
        self.mock_db_manager.fetch_one.return_value = None  # No existing position
        
        result = self.monitor.add_position(1, "AAPL", 100, 150.0)
        self.assertTrue(result)
    
    def test_add_position_existing(self):
        """Test adding to existing position"""
        self.mock_db_manager.get_manager.return_value.get_symbol_id.return_value = 1
        self.mock_db_manager.fetch_one.return_value = (50, 140.0, 0.0)  # Existing position
        
        result = self.monitor.add_position(1, "AAPL", 100, 150.0)
        self.assertTrue(result)
    
    def test_close_position(self):
        """Test closing position"""
        self.mock_db_manager.get_manager.return_value.get_symbol_id.return_value = 1
        self.mock_db_manager.fetch_one.return_value = (100, 150.0, 0.0)  # Existing position
        
        result = self.monitor.close_position(1, "AAPL", 50, 155.0)
        self.assertTrue(result)
    
    def test_portfolio_summary(self):
        """Test portfolio summary retrieval"""
        self.mock_db_manager.fetch_one.return_value = (5, 500, 25000.0, 1000.0, 500.0, 2.5)
        self.mock_db_manager.fetch_all.side_effect = [
            [("AAPL", 500.0, 2.5, 100, 155.0)],  # Top performers
            [("AAPL", "buy", 100, 150.0, 1234567890)]  # Recent trades
        ]
        
        summary = self.monitor.get_portfolio_summary(1)
        
        self.assertEqual(summary['total_positions'], 5)
        self.assertEqual(summary['total_shares'], 500)
        self.assertEqual(summary['total_market_value'], 25000.0)
        self.assertEqual(summary['total_unrealized_pnl'], 1000.0)
        self.assertEqual(summary['total_realized_pnl'], 500.0)
        self.assertEqual(summary['total_pnl'], 1500.0)


class TestPerformanceTracker(unittest.TestCase):
    """Test PerformanceTracker functionality"""
    
    def setUp(self):
        # Mock database manager
        self.mock_db_manager = Mock(spec=DatabaseManager)
        self.mock_db_manager.execute_query = Mock()
        self.mock_db_manager.fetch_all = Mock()
        self.mock_db_manager.fetch_one = Mock()
        
        # Create performance tracker
        self.tracker = PerformanceTracker(self.mock_db_manager)
    
    def test_tracker_initialization(self):
        """Test performance tracker initialization"""
        self.assertEqual(self.tracker.risk_free_rate, 0.02)
        self.assertEqual(self.tracker.trading_days_per_year, 252)
    
    def test_calculate_total_return(self):
        """Test total return calculation"""
        portfolio_data = [
            {'portfolio_value': 10000.0},
            {'portfolio_value': 11000.0}
        ]
        
        total_return = self.tracker._calculate_total_return(portfolio_data)
        self.assertEqual(total_return, 0.1)  # 10% return
    
    def test_calculate_daily_returns(self):
        """Test daily returns calculation"""
        portfolio_data = [
            {'portfolio_value': 10000.0},
            {'portfolio_value': 10100.0},
            {'portfolio_value': 10200.0}
        ]
        
        returns = self.tracker._calculate_daily_returns(portfolio_data)
        self.assertEqual(len(returns), 2)
        self.assertAlmostEqual(returns[0], 0.01)  # 1% daily return
        self.assertAlmostEqual(returns[1], 0.0099)  # ~0.99% daily return
    
    def test_calculate_sharpe_ratio(self):
        """Test Sharpe ratio calculation"""
        daily_returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        
        sharpe_ratio = self.tracker._calculate_sharpe_ratio(daily_returns)
        self.assertIsInstance(sharpe_ratio, float)
    
    def test_calculate_max_drawdown(self):
        """Test maximum drawdown calculation"""
        portfolio_data = [
            {'portfolio_value': 10000.0},
            {'portfolio_value': 11000.0},
            {'portfolio_value': 9000.0},
            {'portfolio_value': 10500.0}
        ]
        
        max_drawdown = self.tracker._calculate_max_drawdown(portfolio_data)
        self.assertAlmostEqual(max_drawdown, 0.1818, places=3)  # ~18.18% drawdown
    
    def test_calculate_volatility(self):
        """Test volatility calculation"""
        daily_returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        
        volatility = self.tracker._calculate_volatility(daily_returns)
        self.assertIsInstance(volatility, float)
        self.assertGreater(volatility, 0)
    
    def test_annualize_return(self):
        """Test return annualization"""
        total_return = 0.1  # 10% return
        days = 365
        
        annualized = self.tracker._annualize_return(total_return, days)
        self.assertEqual(annualized, 0.1)  # Same for 1 year
    
    def test_performance_metrics_calculation(self):
        """Test comprehensive performance metrics calculation"""
        # Mock portfolio data
        portfolio_data = [
            {'date': datetime.now() - timedelta(days=2), 'portfolio_value': 10000.0, 'daily_return': 0.0, 'cumulative_return': 0.0},
            {'date': datetime.now() - timedelta(days=1), 'portfolio_value': 10100.0, 'daily_return': 0.01, 'cumulative_return': 0.01},
            {'date': datetime.now(), 'portfolio_value': 10200.0, 'daily_return': 0.0099, 'cumulative_return': 0.02}
        ]
        
        with patch.object(self.tracker, '_get_portfolio_data', return_value=portfolio_data):
            with patch.object(self.tracker, '_calculate_win_rate', return_value=0.6):
                with patch.object(self.tracker, '_calculate_profit_factor', return_value=1.5):
                    with patch.object(self.tracker, '_get_performance_breakdown', return_value={}):
                        metrics = self.tracker.calculate_performance_metrics(1)
                        
                        self.assertIn('total_return', metrics)
                        self.assertIn('sharpe_ratio', metrics)
                        self.assertIn('max_drawdown', metrics)
                        self.assertIn('win_rate', metrics)
                        self.assertIn('profit_factor', metrics)
                        self.assertIn('volatility', metrics)
    
    def test_create_performance_snapshot(self):
        """Test performance snapshot creation"""
        self.mock_db_manager.fetch_one.return_value = (10000.0,)  # Portfolio value
        
        result = self.tracker.create_performance_snapshot(1)
        self.assertTrue(result)
    
    def test_generate_performance_report(self):
        """Test performance report generation"""
        with patch.object(self.tracker, 'calculate_performance_metrics', return_value={}):
            report = self.tracker.generate_performance_report(1, "summary")
            self.assertIsInstance(report, dict)


class TestExecutionLayerIntegration(unittest.TestCase):
    """Integration tests for execution layer components"""
    
    def setUp(self):
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Mock components
        self.mock_db_manager = Mock(spec=DatabaseManager)
        self.mock_profile_manager = Mock(spec=ProfileManager)
        
        # Create execution components
        self.executor = TradeExecutor(self.mock_db_manager, self.mock_profile_manager)
        self.monitor = PositionMonitor(self.mock_db_manager)
        self.tracker = PerformanceTracker(self.mock_db_manager)
    
    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_end_to_end_execution_flow(self):
        """Test complete execution flow from signal to position"""
        # Setup mocks
        self.mock_profile_manager.get_user_profile.return_value = {
            'max_position_pct': 0.1,
            'risk_profile': 'moderate'
        }
        self.mock_db_manager.get_manager.return_value.get_symbol_id.return_value = 1
        self.mock_db_manager.fetch_one.return_value = (1,)
        
        # Create test signal
        signal = TradingSignal(
            symbol="AAPL",
            signal_type=SignalType.STRONG_BUY,
            strength=SignalStrength.VERY_STRONG,
            price=150.0,
            timestamp=datetime.now(),
            confidence=0.9,
            reasoning="Strong buy signal",
            indicators={},
            risk_level="low"
        )
        
        # Enable execution
        self.executor.enable_execution(True)
        
        # Execute signal
        order = self.executor.execute_signal(signal, 1)
        
        # Verify order was created
        self.assertIsNotNone(order)
        self.assertEqual(order.symbol, "AAPL")
        self.assertEqual(order.status, OrderStatus.FILLED)
        
        # Verify position would be added
        result = self.monitor.add_position(1, "AAPL", order.quantity, order.filled_price)
        self.assertTrue(result)
    
    def test_performance_tracking_integration(self):
        """Test performance tracking integration"""
        # Mock portfolio data
        self.mock_db_manager.fetch_one.return_value = (10000.0,)  # Portfolio value
        
        # Create performance snapshot
        result = self.tracker.create_performance_snapshot(1)
        self.assertTrue(result)
        
        # Calculate performance metrics
        with patch.object(self.tracker, '_get_portfolio_data', return_value=[]):
            metrics = self.tracker.calculate_performance_metrics(1)
            self.assertIsInstance(metrics, dict)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2) 