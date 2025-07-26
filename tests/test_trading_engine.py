"""
Test Trading Engine Components
Tests for trading engine, rules engine, and signal generator
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.strategy.trading_engine import (
    TradingEngine, TradingSignal, SignalType, SignalStrength, PortfolioPosition
)
from src.strategy.rules_engine import RulesEngine, TradingRule, RuleType
from src.strategy.signal_generator import SignalGenerator, SignalMetrics


class TestTradingEngine(unittest.TestCase):
    """Test cases for TradingEngine"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db_manager = Mock()
        self.mock_profile_manager = Mock()
        self.trading_engine = TradingEngine(self.mock_db_manager, self.mock_profile_manager)
    
    def test_initialization(self):
        """Test trading engine initialization"""
        self.assertFalse(self.trading_engine.trading_enabled)
        self.assertEqual(self.trading_engine.max_positions, 10)
        self.assertEqual(self.trading_engine.max_risk_per_trade, 0.02)
        self.assertEqual(len(self.trading_engine.active_signals), 0)
        self.assertEqual(len(self.trading_engine.portfolio_positions), 0)
    
    def test_enable_trading(self):
        """Test enabling/disabling trading"""
        self.trading_engine.enable_trading(True)
        self.assertTrue(self.trading_engine.trading_enabled)
        
        self.trading_engine.enable_trading(False)
        self.assertFalse(self.trading_engine.trading_enabled)
    
    def test_set_risk_parameters(self):
        """Test setting risk parameters"""
        self.trading_engine.set_risk_parameters(5, 0.01)
        self.assertEqual(self.trading_engine.max_positions, 5)
        self.assertEqual(self.trading_engine.max_risk_per_trade, 0.01)
    
    def test_assess_risk_level(self):
        """Test risk level assessment"""
        # High volatility
        market_data = {'volatility': 0.06}
        risk_level = self.trading_engine._assess_risk_level('AAPL', market_data)
        self.assertEqual(risk_level, "HIGH")
        
        # Medium volatility
        market_data = {'volatility': 0.04}
        risk_level = self.trading_engine._assess_risk_level('AAPL', market_data)
        self.assertEqual(risk_level, "MEDIUM")
        
        # Low volatility
        market_data = {'volatility': 0.02}
        risk_level = self.trading_engine._assess_risk_level('AAPL', market_data)
        self.assertEqual(risk_level, "LOW")
    
    def test_should_execute_signal(self):
        """Test signal execution criteria"""
        # Create a test signal
        signal = TradingSignal(
            symbol='AAPL',
            signal_type=SignalType.BUY,
            strength=SignalStrength.MODERATE,
            price=150.0,
            timestamp=datetime.now(),
            confidence=0.7,
            reasoning="Test signal",
            indicators={},
            risk_level="MEDIUM"
        )
        
        # Test with trading disabled
        self.trading_engine.trading_enabled = False
        should_execute = self.trading_engine._should_execute_signal(signal)
        self.assertFalse(should_execute)
        
        # Test with trading enabled
        self.trading_engine.trading_enabled = True
        should_execute = self.trading_engine._should_execute_signal(signal)
        self.assertTrue(should_execute)
        
        # Test with low confidence
        signal.confidence = 0.5
        should_execute = self.trading_engine._should_execute_signal(signal)
        self.assertFalse(should_execute)
    
    def test_get_portfolio_summary(self):
        """Test portfolio summary generation"""
        # Add a test position
        position = PortfolioPosition(
            symbol='AAPL',
            shares=10,
            avg_price=150.0,
            current_price=160.0,
            unrealized_pnl=100.0,
            entry_date=datetime.now(),
            last_updated=datetime.now()
        )
        self.trading_engine.portfolio_positions['AAPL'] = position
        
        summary = self.trading_engine.get_portfolio_summary()
        
        self.assertEqual(summary['total_positions'], 1)
        self.assertEqual(summary['total_value'], 1600.0)
        self.assertEqual(summary['total_unrealized_pnl'], 100.0)
        self.assertEqual(summary['max_positions'], 10)
        self.assertEqual(summary['trading_enabled'], False)


class TestRulesEngine(unittest.TestCase):
    """Test cases for RulesEngine"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.rules_engine = RulesEngine()
    
    def test_initialization(self):
        """Test rules engine initialization"""
        self.assertGreater(len(self.rules_engine.rules), 0)
        
        # Check that default rules are present
        rule_names = [rule.name for rule in self.rules_engine.rules.values()]
        self.assertIn("SMA_Crossover_20_50", rule_names)
        self.assertIn("EMA_Crossover_12_26", rule_names)
        self.assertIn("Volume_Spike", rule_names)
        self.assertIn("RSI_Overbought_Oversold", rule_names)
        self.assertIn("Volatility_Check", rule_names)
    
    def test_add_rule(self):
        """Test adding a custom rule"""
        custom_rule = TradingRule(
            name="Custom_Test_Rule",
            rule_type=RuleType.TECHNICAL_INDICATOR,
            description="Test rule",
            parameters={"test_param": 10},
            weight=0.5
        )
        
        self.rules_engine.add_rule(custom_rule)
        self.assertIn("Custom_Test_Rule", self.rules_engine.rules)
    
    def test_remove_rule(self):
        """Test removing a rule"""
        rule_name = "SMA_Crossover_20_50"
        self.assertIn(rule_name, self.rules_engine.rules)
        
        self.rules_engine.remove_rule(rule_name)
        self.assertNotIn(rule_name, self.rules_engine.rules)
    
    def test_enable_rule(self):
        """Test enabling/disabling rules"""
        rule_name = "SMA_Crossover_20_50"
        
        # Disable rule
        self.rules_engine.enable_rule(rule_name, False)
        self.assertFalse(self.rules_engine.rules[rule_name].enabled)
        
        # Enable rule
        self.rules_engine.enable_rule(rule_name, True)
        self.assertTrue(self.rules_engine.rules[rule_name].enabled)
    
    def test_evaluate_sma_crossover(self):
        """Test SMA crossover evaluation"""
        rule = self.rules_engine.rules["SMA_Crossover_20_50"]
        
        # Bullish scenario
        market_data = {
            'price': 160.0,
            'sma_20': 155.0,
            'sma_50': 150.0
        }
        result = self.rules_engine._evaluate_sma_crossover(rule, market_data)
        self.assertIsNotNone(result)
        self.assertEqual(result['signal'], SignalType.BUY)
        
        # Bearish scenario
        market_data = {
            'price': 140.0,
            'sma_20': 145.0,
            'sma_50': 150.0
        }
        result = self.rules_engine._evaluate_sma_crossover(rule, market_data)
        self.assertIsNotNone(result)
        self.assertEqual(result['signal'], SignalType.SELL)
        
        # No signal scenario
        market_data = {
            'price': 150.0,
            'sma_20': 150.0,
            'sma_50': 150.0
        }
        result = self.rules_engine._evaluate_sma_crossover(rule, market_data)
        self.assertIsNone(result)
    
    def test_evaluate_volume_spike(self):
        """Test volume spike evaluation"""
        rule = self.rules_engine.rules["Volume_Spike"]
        
        # High volume with positive price action
        market_data = {
            'volume': 1500000,
            'avg_volume_20': 1000000,
            'price_change_pct': 0.05
        }
        result = self.rules_engine._evaluate_volume_spike(rule, market_data)
        self.assertIsNotNone(result)
        self.assertEqual(result['signal'], SignalType.BUY)
        
        # High volume with negative price action
        market_data = {
            'volume': 1500000,
            'avg_volume_20': 1000000,
            'price_change_pct': -0.05
        }
        result = self.rules_engine._evaluate_volume_spike(rule, market_data)
        self.assertIsNotNone(result)
        self.assertEqual(result['signal'], SignalType.SELL)
    
    def test_get_rule_summary(self):
        """Test rule summary generation"""
        summary = self.rules_engine.get_rule_summary()
        
        self.assertIn('total_rules', summary)
        self.assertIn('enabled_rules', summary)
        self.assertIn('rules', summary)
        self.assertGreater(summary['total_rules'], 0)
        self.assertGreater(summary['enabled_rules'], 0)


class TestSignalGenerator(unittest.TestCase):
    """Test cases for SignalGenerator"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db_manager = Mock()
        self.mock_trading_engine = Mock()
        self.signal_generator = SignalGenerator(self.mock_db_manager, self.mock_trading_engine)
    
    def test_initialization(self):
        """Test signal generator initialization"""
        self.assertEqual(len(self.signal_generator.signal_history), 0)
        self.assertIsInstance(self.signal_generator.signal_metrics, SignalMetrics)
        self.assertEqual(self.signal_generator.signal_metrics.total_signals, 0)
    
    def test_analyze_market_context(self):
        """Test market context analysis"""
        # High volume scenario
        market_data = {
            'volume': 2000000,
            'avg_volume_20': 1000000
        }
        context = self.signal_generator._analyze_market_context(market_data)
        self.assertIn("Very high volume", context)
        
        # Low volume scenario
        market_data = {
            'volume': 400000,
            'avg_volume_20': 1000000
        }
        context = self.signal_generator._analyze_market_context(market_data)
        self.assertIn("Low volume", context)
        
        # High volatility scenario
        market_data = {
            'volatility_20': 0.06
        }
        context = self.signal_generator._analyze_market_context(market_data)
        self.assertIn("High volatility environment", context)
    
    def test_analyze_trend(self):
        """Test trend analysis"""
        # Strong uptrend
        market_data = {
            'price': 160.0,
            'sma_20': 155.0,
            'sma_50': 150.0
        }
        trend = self.signal_generator._analyze_trend(market_data)
        self.assertEqual(trend, "Strong uptrend")
        
        # Strong downtrend
        market_data = {
            'price': 140.0,
            'sma_20': 145.0,
            'sma_50': 150.0
        }
        trend = self.signal_generator._analyze_trend(market_data)
        self.assertEqual(trend, "Strong downtrend")
    
    def test_calculate_priority(self):
        """Test priority calculation"""
        signal = TradingSignal(
            symbol='AAPL',
            signal_type=SignalType.BUY,
            strength=SignalStrength.STRONG,
            price=150.0,
            timestamp=datetime.now(),
            confidence=0.8,
            reasoning="Test signal",
            indicators={},
            risk_level="LOW"
        )
        
        priority = self.signal_generator._calculate_priority(signal)
        self.assertGreater(priority, 0)
        
        # Test with different signal types
        signal.signal_type = SignalType.STRONG_BUY
        priority_strong = self.signal_generator._calculate_priority(signal)
        self.assertGreater(priority_strong, priority)
    
    def test_get_signal_summary(self):
        """Test signal summary generation"""
        # Add some test signals
        signal1 = TradingSignal(
            symbol='AAPL',
            signal_type=SignalType.BUY,
            strength=SignalStrength.MODERATE,
            price=150.0,
            timestamp=datetime.now(),
            confidence=0.8,
            reasoning="Test signal 1",
            indicators={},
            risk_level="MEDIUM"
        )
        
        signal2 = TradingSignal(
            symbol='GOOGL',
            signal_type=SignalType.SELL,
            strength=SignalStrength.STRONG,
            price=2500.0,
            timestamp=datetime.now(),
            confidence=0.9,
            reasoning="Test signal 2",
            indicators={},
            risk_level="HIGH"
        )
        
        self.signal_generator.signal_history = [signal1, signal2]
        
        summary = self.signal_generator.get_signal_summary()
        
        self.assertEqual(summary['total_signals'], 2)
        self.assertEqual(summary['buy_signals'], 1)
        self.assertEqual(summary['sell_signals'], 1)
        self.assertEqual(summary['hold_signals'], 0)
        self.assertGreater(summary['avg_confidence'], 0.8)
        self.assertEqual(summary['high_confidence_signals'], 2)


class TestIntegration(unittest.TestCase):
    """Integration tests for trading system components"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_db_manager = Mock()
        self.mock_profile_manager = Mock()
        self.trading_engine = TradingEngine(self.mock_db_manager, self.mock_profile_manager)
        self.rules_engine = RulesEngine()
        self.signal_generator = SignalGenerator(self.mock_db_manager, self.trading_engine)
    
    def test_trading_system_integration(self):
        """Test integration between trading engine and rules engine"""
        # Mock market data
        market_data = {
            'price': 160.0,
            'sma_20': 155.0,
            'sma_50': 150.0,
            'volume': 1500000,
            'avg_volume_20': 1000000,
            'price_change_pct': 0.05,
            'volatility_20': 0.03
        }
        
        # Test rules engine evaluation
        signal = self.rules_engine.evaluate_symbol('AAPL', market_data)
        self.assertIsNotNone(signal)
        self.assertEqual(signal.symbol, 'AAPL')
        self.assertIn(signal.signal_type, [SignalType.BUY, SignalType.SELL, SignalType.HOLD])
        self.assertGreater(signal.confidence, 0)
    
    def test_signal_processing_workflow(self):
        """Test complete signal processing workflow"""
        # Create a test signal
        signal = TradingSignal(
            symbol='AAPL',
            signal_type=SignalType.BUY,
            strength=SignalStrength.MODERATE,
            price=150.0,
            timestamp=datetime.now(),
            confidence=0.7,
            reasoning="Test signal",
            indicators={},
            risk_level="MEDIUM"
        )
        
        # Test signal processing
        recommendations = self.signal_generator.get_signal_recommendations([signal])
        
        # Should have one recommendation
        self.assertEqual(len(recommendations), 1)
        recommendation = recommendations[0]
        self.assertEqual(recommendation['symbol'], 'AAPL')
        self.assertEqual(recommendation['action'], 'BUY')
        self.assertIn('priority', recommendation)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2) 