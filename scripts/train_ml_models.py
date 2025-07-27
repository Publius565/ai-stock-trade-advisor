#!/usr/bin/env python3
"""
ML Models Training Script

Trains the machine learning models with sample data for demonstration purposes.
"""

import sys
import os
import logging
import pandas as pd
import numpy as np
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ml_models.model_manager import ModelManager
from ml_models.feature_engineering import FeatureEngineer
from ml_models.prediction_engine import PredictionEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_sample_data(n_samples: int = 1000) -> pd.DataFrame:
    """Create sample market data for training."""
    logger.info(f"Creating sample market data with {n_samples} samples")
    
    # Generate dates
    dates = pd.date_range(start='2020-01-01', periods=n_samples, freq='D')
    
    # Generate price data with realistic patterns
    np.random.seed(42)
    base_price = 100.0
    returns = np.random.normal(0.001, 0.02, n_samples)  # Daily returns ~0.1% mean, 2% std
    
    # Add some trend and seasonality
    trend = np.linspace(0, 0.2, n_samples)  # 20% trend over the period
    seasonality = 0.05 * np.sin(2 * np.pi * np.arange(n_samples) / 252)  # Annual seasonality
    
    # Calculate prices
    prices = base_price * np.exp(np.cumsum(returns + trend/252 + seasonality/252))
    
    # Generate OHLCV data
    data = pd.DataFrame({
        'date': dates,
        'open': prices * (1 + np.random.normal(0, 0.005, n_samples)),
        'high': prices * (1 + np.abs(np.random.normal(0, 0.01, n_samples))),
        'low': prices * (1 - np.abs(np.random.normal(0, 0.01, n_samples))),
        'close': prices,
        'volume': np.random.lognormal(12, 0.5, n_samples)  # Realistic volume distribution
    })
    
    # Ensure high >= close >= low
    data['high'] = np.maximum(data[['open', 'close']].max(axis=1), data['high'])
    data['low'] = np.minimum(data[['open', 'close']].min(axis=1), data['low'])
    
    return data


def train_models():
    """Train all ML models with sample data."""
    logger.info("Starting ML models training")
    
    try:
        # Create sample data
        market_data = create_sample_data(1000)
        logger.info(f"Created sample data: {market_data.shape}")
        
        # Initialize components
        feature_engineer = FeatureEngineer()
        model_manager = ModelManager()
        
        # Prepare features
        logger.info("Preparing features for training")
        X, y = feature_engineer.prepare_features(market_data, target_period=5)
        logger.info(f"Prepared features: X={X.shape}, y={y.shape}")
        
        # Train all models
        logger.info("Training models...")
        for model_name in model_manager.list_models():
            try:
                logger.info(f"Training {model_name}...")
                metrics = model_manager.train_model(model_name, X, y)
                logger.info(f"{model_name} training completed: R²={metrics.get('r2', 0):.4f}")
            except Exception as e:
                logger.error(f"Failed to train {model_name}: {e}")
        
        # Test prediction engine
        logger.info("Testing prediction engine...")
        prediction_engine = PredictionEngine(model_manager, feature_engineer)
        
        # Generate a test prediction
        test_prediction = prediction_engine.generate_prediction('AAPL', market_data.tail(252))
        logger.info(f"Test prediction generated: {test_prediction.get('confidence', 0):.2%} confidence")
        
        # Save models
        logger.info("Saving trained models...")
        for model_name in model_manager.list_models():
            try:
                filepath = model_manager.save_model(model_name)
                logger.info(f"Saved {model_name} to {filepath}")
            except Exception as e:
                logger.error(f"Failed to save {model_name}: {e}")
        
        logger.info("ML models training completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error training models: {e}")
        return False


def verify_models():
    """Verify that models are working correctly."""
    logger.info("Verifying trained models...")
    
    try:
        # Initialize components
        model_manager = ModelManager()
        feature_engineer = FeatureEngineer()
        prediction_engine = PredictionEngine(model_manager, feature_engineer)
        
        # Check model status
        for model_name in model_manager.list_models():
            metadata = model_manager.get_model_performance(model_name)
            if metadata.get('last_trained'):
                logger.info(f"✅ {model_name}: Trained at {metadata['last_trained']}")
            else:
                logger.warning(f"⚠️ {model_name}: Not trained")
        
        # Test prediction
        sample_data = create_sample_data(252)
        prediction = prediction_engine.generate_prediction('TEST', sample_data)
        
        if prediction.get('confidence', 0) > 0:
            logger.info(f"✅ Prediction test successful: {prediction.get('confidence', 0):.2%} confidence")
            return True
        else:
            logger.warning("⚠️ Prediction test failed - no confidence")
            return False
            
    except Exception as e:
        logger.error(f"Error verifying models: {e}")
        return False


if __name__ == "__main__":
    logger.info("=== ML Models Training Script ===")
    
    # Train models
    success = train_models()
    
    if success:
        # Verify models
        verify_models()
        logger.info("✅ ML models training and verification completed!")
    else:
        logger.error("❌ ML models training failed!")
        sys.exit(1) 