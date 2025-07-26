"""
Tests for Machine Learning Components

Tests for ModelManager, FeatureEngineer, and PredictionEngine classes.
"""

import unittest
import pandas as pd
import numpy as np
import tempfile
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the components to test
from src.ml_models.model_manager import ModelManager
from src.ml_models.feature_engineering import FeatureEngineer
from src.ml_models.prediction_engine import PredictionEngine
from src.strategy.trade_suggestion_engine import TradeSuggestionEngine


class TestModelManager(unittest.TestCase):
    """Test cases for ModelManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.model_manager = ModelManager(models_dir=self.temp_dir)
        
        # Create sample data
        np.random.seed(42)
        self.sample_data = pd.DataFrame({
            'feature1': np.random.randn(100),
            'feature2': np.random.randn(100),
            'feature3': np.random.randn(100)
        })
        self.sample_target = pd.Series(np.random.randn(100))
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test ModelManager initialization."""
        self.assertIsNotNone(self.model_manager)
        self.assertEqual(len(self.model_manager.models), 3)
        self.assertIn('random_forest', self.model_manager.models)
        self.assertIn('gradient_boosting', self.model_manager.models)
        self.assertIn('linear_regression', self.model_manager.models)
    
    def test_train_model(self):
        """Test model training functionality."""
        model_name = 'random_forest'
        
        # Train the model
        metrics = self.model_manager.train_model(model_name, self.sample_data, self.sample_target)
        
        # Check that metrics are returned
        self.assertIn('mse', metrics)
        self.assertIn('r2', metrics)
        self.assertIn('cv_mean', metrics)
        self.assertIn('cv_std', metrics)
        
        # Check that model metadata was updated
        metadata = self.model_manager.get_model_performance(model_name)
        self.assertIsNotNone(metadata['last_trained'])
        self.assertEqual(metadata['training_samples'], 80)  # 80% of 100 samples
    
    def test_predict(self):
        """Test prediction functionality."""
        model_name = 'linear_regression'
        
        # Train the model first
        self.model_manager.train_model(model_name, self.sample_data, self.sample_target)
        
        # Make prediction
        prediction = self.model_manager.predict(model_name, self.sample_data.iloc[:5])
        
        # Check prediction shape
        self.assertEqual(len(prediction), 5)
        self.assertTrue(isinstance(prediction, np.ndarray))
    
    def test_save_and_load_model(self):
        """Test model saving and loading."""
        model_name = 'gradient_boosting'
        
        # Train the model
        self.model_manager.train_model(model_name, self.sample_data, self.sample_target)
        
        # Save the model
        filepath = self.model_manager.save_model(model_name)
        self.assertTrue(os.path.exists(filepath))
        
        # Create new model manager and load the model
        new_manager = ModelManager(models_dir=self.temp_dir)
        loaded_name = new_manager.load_model(filepath)
        
        # Check that model was loaded correctly
        self.assertEqual(loaded_name, model_name)
        self.assertIn(model_name, new_manager.models)
    
    def test_get_best_model(self):
        """Test getting the best performing model."""
        # Train all models
        for model_name in self.model_manager.list_models():
            self.model_manager.train_model(model_name, self.sample_data, self.sample_target)
        
        # Get best model
        best_model = self.model_manager.get_best_model()
        self.assertIsNotNone(best_model)
        self.assertIn(best_model, self.model_manager.list_models())
    
    def test_invalid_model_name(self):
        """Test handling of invalid model names."""
        with self.assertRaises(ValueError):
            self.model_manager.train_model('invalid_model', self.sample_data, self.sample_target)
        
        with self.assertRaises(ValueError):
            self.model_manager.predict('invalid_model', self.sample_data)
        
        with self.assertRaises(ValueError):
            self.model_manager.get_model_performance('invalid_model')


class TestFeatureEngineer(unittest.TestCase):
    """Test cases for FeatureEngineer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.feature_engineer = FeatureEngineer()
        
        # Create sample OHLCV data
        np.random.seed(42)
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        self.sample_data = pd.DataFrame({
            'open': np.random.uniform(100, 200, 100),
            'high': np.random.uniform(150, 250, 100),
            'low': np.random.uniform(50, 150, 100),
            'close': np.random.uniform(100, 200, 100),
            'volume': np.random.uniform(1000000, 5000000, 100)
        }, index=dates)
        
        # Ensure high > close > low
        self.sample_data['high'] = self.sample_data[['open', 'close', 'high']].max(axis=1)
        self.sample_data['low'] = self.sample_data[['open', 'close', 'low']].min(axis=1)
    
    def test_initialization(self):
        """Test FeatureEngineer initialization."""
        self.assertIsNotNone(self.feature_engineer)
        self.assertEqual(len(self.feature_engineer.feature_columns), 0)
    
    def test_create_technical_indicators(self):
        """Test technical indicator creation."""
        features_df = self.feature_engineer.create_technical_indicators(self.sample_data)
        
        # Check that features were created
        self.assertGreater(len(features_df.columns), len(self.sample_data.columns))
        
        # Check for specific indicators
        expected_indicators = ['sma_20', 'rsi_14', 'macd', 'bb_upper_20']
        for indicator in expected_indicators:
            self.assertIn(indicator, features_df.columns)
    
    def test_empty_dataframe(self):
        """Test handling of empty dataframe."""
        empty_df = pd.DataFrame()
        features_df = self.feature_engineer.create_technical_indicators(empty_df)
        self.assertTrue(features_df.empty)
    
    def test_missing_columns(self):
        """Test handling of missing columns."""
        incomplete_data = self.sample_data.drop(columns=['volume'])
        features_df = self.feature_engineer.create_technical_indicators(incomplete_data)
        
        # Should still create some features but log warning
        self.assertGreater(len(features_df.columns), len(incomplete_data.columns))
    
    def test_create_target_variable(self):
        """Test target variable creation."""
        target = self.feature_engineer.create_target_variable(self.sample_data, target_period=5)
        
        # Check target properties
        self.assertEqual(len(target), len(self.sample_data))
        self.assertTrue(isinstance(target, pd.Series))
        
        # Last 5 values should be NaN (no future data)
        self.assertTrue(target.iloc[-5:].isna().all())
    
    def test_prepare_features(self):
        """Test feature preparation for ML."""
        X, y = self.feature_engineer.prepare_features(self.sample_data, target_period=5)
        
        # Check that features and target are prepared
        self.assertIsInstance(X, pd.DataFrame)
        self.assertIsInstance(y, pd.Series)
        
        # Check that there are no NaN values
        self.assertFalse(X.isna().any().any())
        self.assertFalse(y.isna().any())
        
        # Check that X and y have same length
        self.assertEqual(len(X), len(y))
    
    def test_get_feature_columns(self):
        """Test getting feature columns."""
        columns = self.feature_engineer.get_feature_columns()
        
        # Should return list of expected technical indicators
        self.assertIsInstance(columns, list)
        self.assertGreater(len(columns), 0)
        
        # Check for specific indicator types
        sma_indicators = [col for col in columns if 'sma_' in col]
        self.assertGreater(len(sma_indicators), 0)


class TestPredictionEngine(unittest.TestCase):
    """Test cases for PredictionEngine class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.prediction_engine = PredictionEngine()
        
        # Create sample market data
        np.random.seed(42)
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        self.sample_market_data = pd.DataFrame({
            'open': np.random.uniform(100, 200, 100),
            'high': np.random.uniform(150, 250, 100),
            'low': np.random.uniform(50, 150, 100),
            'close': np.random.uniform(100, 200, 100),
            'volume': np.random.uniform(1000000, 5000000, 100)
        }, index=dates)
        
        # Ensure high > close > low
        self.sample_market_data['high'] = self.sample_market_data[['open', 'close', 'high']].max(axis=1)
        self.sample_market_data['low'] = self.sample_market_data[['open', 'close', 'low']].min(axis=1)
    
    def test_initialization(self):
        """Test PredictionEngine initialization."""
        self.assertIsNotNone(self.prediction_engine)
        self.assertEqual(self.prediction_engine.confidence_threshold, 0.6)
        self.assertEqual(len(self.prediction_engine.prediction_history), 0)
    
    def test_generate_prediction_empty_data(self):
        """Test prediction generation with empty data."""
        empty_data = pd.DataFrame()
        prediction = self.prediction_engine.generate_prediction('AAPL', empty_data)
        
        # Should return empty prediction structure
        self.assertEqual(prediction['symbol'], 'AAPL')
        self.assertEqual(prediction['predicted_return'], 0.0)
        self.assertEqual(prediction['confidence'], 0.0)
        self.assertIn('error', prediction)
    
    @patch('src.ml_models.prediction_engine.ModelManager')
    def test_generate_prediction_with_trained_models(self, mock_model_manager):
        """Test prediction generation with trained models."""
        # Mock the model manager to simulate trained models
        mock_manager = Mock()
        mock_manager.list_models.return_value = ['random_forest', 'linear_regression']
        mock_manager.predict.side_effect = lambda model, data: np.array([0.05, 0.03])
        mock_manager.get_model_performance.return_value = {
            'last_trained': '2023-01-01T00:00:00',
            'performance_metrics': {'r2': 0.8}
        }
        
        self.prediction_engine.model_manager = mock_manager
        
        prediction = self.prediction_engine.generate_prediction('AAPL', self.sample_market_data)
        
        # Check prediction structure
        self.assertEqual(prediction['symbol'], 'AAPL')
        self.assertIn('predicted_return', prediction)
        self.assertIn('confidence', prediction)
        self.assertIn('prediction_direction', prediction)
        self.assertIn('risk_level', prediction)
        
        # Check that prediction was added to history
        self.assertEqual(len(self.prediction_engine.prediction_history), 1)
    
    def test_aggregate_predictions(self):
        """Test prediction aggregation."""
        predictions = {'model1': 0.05, 'model2': 0.03, 'model3': 0.04}
        confidences = {'model1': 0.8, 'model2': 0.6, 'model3': 0.9}
        
        aggregated = self.prediction_engine._aggregate_predictions(predictions, confidences)
        
        # Should return weighted average
        self.assertIsInstance(aggregated, float)
        self.assertGreater(aggregated, 0)
    
    def test_get_prediction_direction(self):
        """Test prediction direction calculation."""
        # Test bullish
        direction = self.prediction_engine._get_prediction_direction(0.02)
        self.assertEqual(direction, 'bullish')
        
        # Test bearish
        direction = self.prediction_engine._get_prediction_direction(-0.02)
        self.assertEqual(direction, 'bearish')
        
        # Test neutral
        direction = self.prediction_engine._get_prediction_direction(0.005)
        self.assertEqual(direction, 'neutral')
    
    def test_assess_risk_level(self):
        """Test risk level assessment."""
        # Low risk
        risk = self.prediction_engine._assess_risk_level(0.9, 0.02)
        self.assertEqual(risk, 'low')
        
        # High risk
        risk = self.prediction_engine._assess_risk_level(0.3, 0.1)
        self.assertEqual(risk, 'high')
    
    def test_update_confidence_threshold(self):
        """Test confidence threshold update."""
        self.prediction_engine.update_confidence_threshold(0.8)
        self.assertEqual(self.prediction_engine.confidence_threshold, 0.8)
        
        # Test invalid threshold
        original_threshold = self.prediction_engine.confidence_threshold
        self.prediction_engine.update_confidence_threshold(1.5)  # Invalid
        self.assertEqual(self.prediction_engine.confidence_threshold, original_threshold)
    
    def test_clear_prediction_history(self):
        """Test clearing prediction history."""
        # Add some predictions to history
        self.prediction_engine.prediction_history = [{'test': 'prediction'}]
        
        self.prediction_engine.clear_prediction_history()
        self.assertEqual(len(self.prediction_engine.prediction_history), 0)


class TestTradeSuggestionEngine(unittest.TestCase):
    """Test cases for TradeSuggestionEngine class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.suggestion_engine = TradeSuggestionEngine()
        
        # Create sample market data
        np.random.seed(42)
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        self.sample_market_data = pd.DataFrame({
            'open': np.random.uniform(100, 200, 100),
            'high': np.random.uniform(150, 250, 100),
            'low': np.random.uniform(50, 150, 100),
            'close': np.random.uniform(100, 200, 100),
            'volume': np.random.uniform(1000000, 5000000, 100)
        }, index=dates)
        
        # Ensure high > close > low
        self.sample_market_data['high'] = self.sample_market_data[['open', 'close', 'high']].max(axis=1)
        self.sample_market_data['low'] = self.sample_market_data[['open', 'close', 'low']].min(axis=1)
        
        # Sample user risk profile
        self.user_risk_profile = {
            'risk_tolerance': 'moderate',
            'max_position_size': 0.15,
            'investment_goals': ['growth', 'income']
        }
    
    def test_initialization(self):
        """Test TradeSuggestionEngine initialization."""
        self.assertIsNotNone(self.suggestion_engine)
        self.assertEqual(len(self.suggestion_engine.suggestion_types), 3)
        self.assertIn('high_risk_high_reward', self.suggestion_engine.suggestion_types)
        self.assertIn('low_risk_low_reward', self.suggestion_engine.suggestion_types)
        self.assertIn('moderate_risk_moderate_reward', self.suggestion_engine.suggestion_types)
    
    @patch('src.strategy.trade_suggestion_engine.PredictionEngine')
    @patch('src.strategy.trade_suggestion_engine.SignalGenerator')
    def test_generate_suggestions(self, mock_signal_generator, mock_prediction_engine):
        """Test suggestion generation."""
        # Mock prediction engine
        mock_prediction = {
            'predicted_return': 0.05,
            'confidence': 0.8,
            'current_price': 150.0,
            'predicted_price': 157.5,
            'prediction_direction': 'bullish'
        }
        mock_prediction_engine.return_value.generate_prediction.return_value = mock_prediction
        
        # Mock signal generator
        mock_signals = [
            {'action': 'buy', 'confidence': 0.7, 'rule': 'sma_crossover'},
            {'action': 'buy', 'confidence': 0.6, 'rule': 'rsi_oversold'}
        ]
        mock_signal_generator.return_value.generate_signals.return_value = mock_signals
        
        suggestions = self.suggestion_engine.generate_suggestions(
            'AAPL', self.sample_market_data, self.user_risk_profile
        )
        
        # Should generate suggestions
        self.assertIsInstance(suggestions, list)
        if suggestions:  # If any suggestions meet criteria
            suggestion = suggestions[0]
            self.assertIn('symbol', suggestion)
            self.assertIn('suggestion_type', suggestion)
            self.assertIn('action', suggestion)
            self.assertIn('rationale', suggestion)
    
    def test_meets_criteria(self):
        """Test criteria checking."""
        criteria = {'min_confidence': 0.7, 'min_predicted_return': 0.05}
        
        # Test meets criteria
        prediction = {'confidence': 0.8, 'predicted_return': 0.06}
        self.assertTrue(self.suggestion_engine._meets_criteria(prediction, criteria))
        
        # Test doesn't meet criteria
        prediction = {'confidence': 0.6, 'predicted_return': 0.06}
        self.assertFalse(self.suggestion_engine._meets_criteria(prediction, criteria))
    
    def test_determine_action(self):
        """Test action determination."""
        prediction = {'predicted_return': 0.03, 'confidence': 0.7}
        signals = [
            {'action': 'buy', 'confidence': 0.7},
            {'action': 'buy', 'confidence': 0.6}
        ]
        
        action = self.suggestion_engine._determine_action(prediction, signals)
        self.assertEqual(action, 'buy')
        
        # Test sell action
        prediction = {'predicted_return': -0.03, 'confidence': 0.7}
        signals = [
            {'action': 'sell', 'confidence': 0.7},
            {'action': 'sell', 'confidence': 0.6}
        ]
        
        action = self.suggestion_engine._determine_action(prediction, signals)
        self.assertEqual(action, 'sell')
    
    def test_filter_suggestions(self):
        """Test suggestion filtering."""
        suggestions = [
            {
                'confidence': 0.8,
                'suggestion_type': 'high_risk_high_reward',
                'action': 'buy',
                'expected_value': 0.05
            },
            {
                'confidence': 0.6,
                'suggestion_type': 'low_risk_low_reward',
                'action': 'sell',
                'expected_value': 0.02
            }
        ]
        
        # Filter by confidence
        filtered = self.suggestion_engine.filter_suggestions(
            suggestions, {'min_confidence': 0.7}
        )
        self.assertEqual(len(filtered), 1)
        
        # Filter by action
        filtered = self.suggestion_engine.filter_suggestions(
            suggestions, {'action': 'buy'}
        )
        self.assertEqual(len(filtered), 1)
    
    def test_rank_suggestions(self):
        """Test suggestion ranking."""
        suggestions = [
            {'expected_value': 0.03, 'risk_reward_ratio': 2.0, 'confidence': 0.7},
            {'expected_value': 0.05, 'risk_reward_ratio': 1.5, 'confidence': 0.8},
            {'expected_value': 0.02, 'risk_reward_ratio': 3.0, 'confidence': 0.6}
        ]
        
        # Rank by expected value
        ranked = self.suggestion_engine.rank_suggestions(suggestions, 'expected_value')
        self.assertEqual(ranked[0]['expected_value'], 0.05)
        
        # Rank by risk-reward ratio
        ranked = self.suggestion_engine.rank_suggestions(suggestions, 'risk_reward_ratio')
        self.assertEqual(ranked[0]['risk_reward_ratio'], 3.0)


if __name__ == '__main__':
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestModelManager))
    test_suite.addTest(unittest.makeSuite(TestFeatureEngineer))
    test_suite.addTest(unittest.makeSuite(TestPredictionEngine))
    test_suite.addTest(unittest.makeSuite(TestTradeSuggestionEngine))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"ML Components Test Results:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"{'='*60}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}") 