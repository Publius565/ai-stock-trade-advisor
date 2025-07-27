"""
Portfolio Management Tests
Comprehensive tests for portfolio analytics, risk management, and backtesting components.
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.execution.portfolio_analytics import PortfolioAnalytics, PortfolioMetrics, RiskMetric
from src.execution.risk_manager import RiskManager, RiskLevel, PositionRisk, PortfolioRisk
from src.execution.backtesting_engine import BacktestingEngine, BacktestResult, BacktestOrder, BacktestPosition


class TestPortfolioAnalytics(unittest.TestCase):
    """Test portfolio analytics functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.analytics = PortfolioAnalytics()
        
        # Create test returns data
        np.random.seed(42)
        dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
        self.returns = pd.Series(np.random.normal(0.0005, 0.02, len(dates)), index=dates)
        
        # Create benchmark returns
        self.benchmark_returns = pd.Series(np.random.normal(0.0004, 0.018, len(dates)), index=dates)
    
    def test_calculate_portfolio_metrics(self):
        """Test portfolio metrics calculation."""
        metrics = self.analytics.calculate_portfolio_metrics(self.returns)
        
        self.assertIsInstance(metrics, PortfolioMetrics)
        self.assertIsInstance(metrics.total_return, float)
        self.assertIsInstance(metrics.annualized_return, float)
        self.assertIsInstance(metrics.volatility, float)
        self.assertIsInstance(metrics.sharpe_ratio, float)
        self.assertIsInstance(metrics.max_drawdown, float)
        
        # Test that metrics are reasonable
        self.assertGreater(metrics.volatility, 0)
        self.assertLessEqual(metrics.max_drawdown, 0)  # Max drawdown should be negative
    
    def test_calculate_portfolio_metrics_with_benchmark(self):
        """Test portfolio metrics calculation with benchmark."""
        metrics = self.analytics.calculate_portfolio_metrics(self.returns, self.benchmark_returns)
        
        self.assertIsInstance(metrics.beta, float)
        self.assertIsInstance(metrics.alpha, float)
        self.assertIsInstance(metrics.information_ratio, float)
    
    def test_calculate_annualized_return(self):
        """Test annualized return calculation."""
        annual_return = self.analytics._calculate_annualized_return(self.returns)
        self.assertIsInstance(annual_return, float)
        self.assertNotEqual(annual_return, 0)
    
    def test_calculate_sharpe_ratio(self):
        """Test Sharpe ratio calculation."""
        sharpe = self.analytics._calculate_sharpe_ratio(self.returns)
        self.assertIsInstance(sharpe, float)
    
    def test_calculate_max_drawdown(self):
        """Test maximum drawdown calculation."""
        drawdown = self.analytics._calculate_max_drawdown(self.returns)
        self.assertIsInstance(drawdown, float)
        self.assertLessEqual(drawdown, 0)  # Drawdown should be negative
    
    def test_calculate_var_cvar(self):
        """Test Value at Risk and Conditional VaR calculation."""
        var_95 = self.analytics._calculate_var(self.returns, 0.05)
        cvar_95 = self.analytics._calculate_cvar(self.returns, 0.05)
        
        self.assertIsInstance(var_95, float)
        self.assertIsInstance(cvar_95, float)
        self.assertLessEqual(cvar_95, var_95)  # CVaR should be <= VaR
    
    def test_generate_performance_report(self):
        """Test performance report generation."""
        metrics = self.analytics.calculate_portfolio_metrics(self.returns)
        report = self.analytics.generate_performance_report(metrics)
        
        self.assertIsInstance(report, dict)
        self.assertIn('summary', report)
        self.assertIn('risk_metrics', report)
        self.assertIn('trading_metrics', report)
    
    def test_calculate_rolling_metrics(self):
        """Test rolling metrics calculation."""
        rolling_metrics = self.analytics.calculate_rolling_metrics(self.returns, window=60)
        
        self.assertIsInstance(rolling_metrics, pd.DataFrame)
        self.assertIn('rolling_return', rolling_metrics.columns)
        self.assertIn('rolling_volatility', rolling_metrics.columns)
        self.assertIn('rolling_sharpe', rolling_metrics.columns)


class TestRiskManager(unittest.TestCase):
    """Test risk management functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.risk_manager = RiskManager()
        
        # Test position data
        self.test_position = PositionRisk(
            symbol="AAPL",
            current_price=150.0,
            position_size=100,
            position_value=15000.0,
            unrealized_pnl=500.0,
            stop_loss_price=140.0,
            take_profit_price=160.0,
            risk_per_share=10.0,
            total_risk=1000.0,
            risk_percentage=0.01,
            max_position_size=150,
            suggested_position_size=150
        )
    
    def test_calculate_position_size(self):
        """Test position size calculation."""
        position_size = self.risk_manager.calculate_position_size(
            symbol="AAPL",
            current_price=150.0,
            stop_loss_price=140.0,
            portfolio_value=100000.0
        )
        
        self.assertIsInstance(position_size, int)
        self.assertGreater(position_size, 0)
    
    def test_calculate_stop_loss(self):
        """Test stop loss calculation."""
        stop_loss = self.risk_manager.calculate_stop_loss(
            entry_price=150.0,
            atr=5.0,
            risk_level=RiskLevel.MODERATE
        )
        
        self.assertIsInstance(stop_loss, float)
        self.assertLess(stop_loss, 150.0)  # Stop loss should be below entry
    
    def test_calculate_take_profit(self):
        """Test take profit calculation."""
        take_profit = self.risk_manager.calculate_take_profit(
            entry_price=150.0,
            stop_loss_price=140.0,
            risk_reward_ratio=2.0
        )
        
        self.assertIsInstance(take_profit, float)
        self.assertGreater(take_profit, 150.0)  # Take profit should be above entry
    
    def test_analyze_position_risk(self):
        """Test position risk analysis."""
        position_risk = self.risk_manager.analyze_position_risk(
            symbol="AAPL",
            current_price=150.0,
            position_size=100,
            stop_loss_price=140.0,
            portfolio_value=100000.0
        )
        
        self.assertIsInstance(position_risk, PositionRisk)
        self.assertEqual(position_risk.symbol, "AAPL")
        self.assertEqual(position_risk.current_price, 150.0)
        self.assertEqual(position_risk.position_size, 100)
    
    def test_analyze_portfolio_risk(self):
        """Test portfolio risk analysis."""
        positions = [self.test_position]
        sector_data = {"AAPL": "Technology"}
        
        portfolio_risk = self.risk_manager.analyze_portfolio_risk(
            positions=positions,
            portfolio_value=100000.0,
            sector_data=sector_data
        )
        
        self.assertIsInstance(portfolio_risk, PortfolioRisk)
        self.assertEqual(portfolio_risk.total_portfolio_value, 100000.0)
        self.assertEqual(portfolio_risk.position_count, 1)
        self.assertIn("Technology", portfolio_risk.sector_exposure)
    
    def test_should_close_position(self):
        """Test position closure logic."""
        portfolio_risk = PortfolioRisk(
            total_portfolio_value=100000.0,
            total_unrealized_pnl=500.0,
            total_risk=1000.0,
            portfolio_risk_percentage=0.01,
            max_portfolio_risk=0.02,
            current_risk_utilization=0.5,
            largest_position_risk=0.01,
            concentration_risk=0.1,
            correlation_risk=0.05,
            sector_exposure={"Technology": 0.1},
            position_count=1,
            risk_alerts=[]
        )
        
        should_close = self.risk_manager.should_close_position(
            self.test_position, portfolio_risk
        )
        
        self.assertIsInstance(should_close, bool)
    
    def test_get_risk_summary(self):
        """Test risk summary generation."""
        portfolio_risk = PortfolioRisk(
            total_portfolio_value=100000.0,
            total_unrealized_pnl=500.0,
            total_risk=1000.0,
            portfolio_risk_percentage=0.01,
            max_portfolio_risk=0.02,
            current_risk_utilization=0.5,
            largest_position_risk=0.01,
            concentration_risk=0.1,
            correlation_risk=0.05,
            sector_exposure={"Technology": 0.1},
            position_count=1,
            risk_alerts=[]
        )
        
        summary = self.risk_manager.get_risk_summary(portfolio_risk)
        
        self.assertIsInstance(summary, dict)
        self.assertIn('portfolio_risk', summary)
        self.assertIn('concentration_metrics', summary)
        self.assertIn('sector_exposure', summary)


class TestBacktestingEngine(unittest.TestCase):
    """Test backtesting engine functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.backtesting_engine = BacktestingEngine()
        
        # Create mock market data
        self.market_data = {}
        symbols = ["AAPL", "MSFT"]
        dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
        
        for symbol in symbols:
            np.random.seed(hash(symbol) % 1000)
            returns = np.random.normal(0.0005, 0.02, len(dates))
            prices = 100 * np.exp(np.cumsum(returns))
            
            self.market_data[symbol] = pd.DataFrame({
                'date': dates,
                'open': prices * (1 + np.random.normal(0, 0.01, len(dates))),
                'high': prices * (1 + np.abs(np.random.normal(0, 0.02, len(dates)))),
                'low': prices * (1 - np.abs(np.random.normal(0, 0.02, len(dates)))),
                'close': prices,
                'volume': np.random.randint(1000000, 10000000, len(dates))
            })
    
    def test_backtesting_engine_initialization(self):
        """Test backtesting engine initialization."""
        engine = BacktestingEngine(
            initial_capital=100000.0,
            commission_rate=0.005,
            slippage_rate=0.001,
            risk_level=RiskLevel.MODERATE
        )
        
        self.assertEqual(engine.initial_capital, 100000.0)
        self.assertEqual(engine.commission_rate, 0.005)
        self.assertEqual(engine.slippage_rate, 0.001)
        self.assertEqual(engine.risk_level, RiskLevel.MODERATE)
    
    def test_simple_strategy_function(self):
        """Test simple strategy function."""
        def simple_strategy(current_date, market_data, positions, **params):
            signals = []
            for symbol, data in market_data.items():
                if len(data) > 20:
                    current_data = data[data['date'] <= current_date].tail(20)
                    if len(current_data) >= 20:
                        sma = current_data['close'].mean()
                        current_price = current_data['close'].iloc[-1]
                        
                        if current_price > sma and symbol not in positions:
                            signals.append({
                                'symbol': symbol,
                                'action': 'buy',
                                'quantity': 100,
                                'price': current_price
                            })
            return signals
        
        # Test strategy function
        test_date = datetime(2024, 6, 1)
        signals = simple_strategy(test_date, self.market_data, {})
        
        self.assertIsInstance(signals, list)
        for signal in signals:
            self.assertIn('symbol', signal)
            self.assertIn('action', signal)
            self.assertIn('quantity', signal)
            self.assertIn('price', signal)
    
    def test_run_backtest(self):
        """Test backtest execution."""
        def simple_strategy(current_date, market_data, positions, **params):
            signals = []
            for symbol, data in market_data.items():
                if len(data) > 20:
                    current_data = data[data['date'] <= current_date].tail(20)
                    if len(current_data) >= 20:
                        sma = current_data['close'].mean()
                        current_price = current_data['close'].iloc[-1]
                        
                        if current_price > sma and symbol not in positions:
                            signals.append({
                                'symbol': symbol,
                                'action': 'buy',
                                'quantity': 100,
                                'price': current_price
                            })
            return signals
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)
        
        result = self.backtesting_engine.run_backtest(
            strategy_function=simple_strategy,
            market_data=self.market_data,
            start_date=start_date,
            end_date=end_date
        )
        
        self.assertIsInstance(result, BacktestResult)
        self.assertEqual(result.start_date, start_date)
        self.assertEqual(result.end_date, end_date)
        self.assertEqual(result.initial_capital, self.backtesting_engine.initial_capital)
        self.assertIsInstance(result.total_return, float)
        self.assertIsInstance(result.annualized_return, float)
        self.assertIsInstance(result.max_drawdown, float)
        self.assertIsInstance(result.sharpe_ratio, float)
        self.assertIsInstance(result.total_trades, int)
        self.assertIsInstance(result.win_rate, float)
    
    def test_generate_backtest_report(self):
        """Test backtest report generation."""
        # Create a simple backtest result
        result = BacktestResult(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            initial_capital=100000.0,
            final_capital=110000.0,
            total_return=0.10,
            annualized_return=0.10,
            max_drawdown=-0.05,
            sharpe_ratio=1.2,
            total_trades=10,
            winning_trades=6,
            losing_trades=4,
            win_rate=0.6,
            avg_win=1000.0,
            avg_loss=500.0,
            profit_factor=3.0,
            equity_curve=pd.Series([100000, 110000]),
            trade_history=[],
            portfolio_metrics=PortfolioMetrics(
                total_return=0.10,
                annualized_return=0.10,
                volatility=0.15,
                sharpe_ratio=1.2,
                sortino_ratio=1.5,
                max_drawdown=-0.05,
                var_95=-0.02,
                cvar_95=-0.025,
                beta=1.0,
                alpha=0.01,
                win_rate=0.6,
                profit_factor=3.0,
                avg_win=0.01,
                avg_loss=-0.005,
                max_consecutive_wins=3,
                max_consecutive_losses=2,
                calmar_ratio=2.0,
                information_ratio=0.5
            )
        )
        
        report = self.backtesting_engine.generate_backtest_report(result)
        
        self.assertIsInstance(report, dict)
        self.assertIn('summary', report)
        self.assertIn('risk_metrics', report)
        self.assertIn('trading_metrics', report)
        self.assertIn('portfolio_metrics', report)


class TestIntegration(unittest.TestCase):
    """Test integration between portfolio management components."""
    
    def setUp(self):
        """Set up test data."""
        self.analytics = PortfolioAnalytics()
        self.risk_manager = RiskManager()
        self.backtesting_engine = BacktestingEngine()
        
        # Create test data
        np.random.seed(42)
        dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
        self.returns = pd.Series(np.random.normal(0.0005, 0.02, len(dates)), index=dates)
        
        # Create mock market data
        self.market_data = {}
        symbols = ["AAPL", "MSFT"]
        
        for symbol in symbols:
            np.random.seed(hash(symbol) % 1000)
            returns = np.random.normal(0.0005, 0.02, len(dates))
            prices = 100 * np.exp(np.cumsum(returns))
            
            self.market_data[symbol] = pd.DataFrame({
                'date': dates,
                'open': prices * (1 + np.random.normal(0, 0.01, len(dates))),
                'high': prices * (1 + np.abs(np.random.normal(0, 0.02, len(dates)))),
                'low': prices * (1 - np.abs(np.random.normal(0, 0.02, len(dates)))),
                'close': prices,
                'volume': np.random.randint(1000000, 10000000, len(dates))
            })
    
    def test_full_portfolio_analysis_workflow(self):
        """Test complete portfolio analysis workflow."""
        # 1. Calculate portfolio metrics
        metrics = self.analytics.calculate_portfolio_metrics(self.returns)
        
        # 2. Create positions
        positions = [
            PositionRisk(
                symbol="AAPL",
                current_price=150.0,
                position_size=100,
                position_value=15000.0,
                unrealized_pnl=500.0,
                stop_loss_price=140.0,
                take_profit_price=160.0,
                risk_per_share=10.0,
                total_risk=1000.0,
                risk_percentage=0.01,
                max_position_size=150,
                suggested_position_size=150
            )
        ]
        
        # 3. Analyze portfolio risk
        sector_data = {"AAPL": "Technology"}
        portfolio_risk = self.risk_manager.analyze_portfolio_risk(
            positions, 100000.0, sector_data
        )
        
        # 4. Generate reports
        performance_report = self.analytics.generate_performance_report(metrics)
        risk_summary = self.risk_manager.get_risk_summary(portfolio_risk)
        
        # Verify all components work together
        self.assertIsInstance(metrics, PortfolioMetrics)
        self.assertIsInstance(portfolio_risk, PortfolioRisk)
        self.assertIsInstance(performance_report, dict)
        self.assertIsInstance(risk_summary, dict)
    
    def test_backtesting_with_risk_management(self):
        """Test backtesting with risk management integration."""
        def risk_aware_strategy(current_date, market_data, positions, **params):
            signals = []
            for symbol, data in market_data.items():
                if len(data) > 20:
                    current_data = data[data['date'] <= current_date].tail(20)
                    if len(current_data) >= 20:
                        sma = current_data['close'].mean()
                        current_price = current_data['close'].iloc[-1]
                        
                        # Use risk manager to calculate position size
                        position_size = self.risk_manager.calculate_position_size(
                            symbol, current_price, current_price * 0.95, 100000.0
                        )
                        
                        if current_price > sma and symbol not in positions and position_size > 0:
                            signals.append({
                                'symbol': symbol,
                                'action': 'buy',
                                'quantity': position_size,
                                'price': current_price
                            })
            return signals
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)
        
        result = self.backtesting_engine.run_backtest(
            strategy_function=risk_aware_strategy,
            market_data=self.market_data,
            start_date=start_date,
            end_date=end_date
        )
        
        # Verify backtest results
        self.assertIsInstance(result, BacktestResult)
        self.assertGreaterEqual(result.total_trades, 0)
        self.assertGreaterEqual(result.win_rate, 0)
        self.assertLessEqual(result.win_rate, 1)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2) 