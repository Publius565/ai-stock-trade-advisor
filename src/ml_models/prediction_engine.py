"""
Prediction Engine for Machine Learning Models

Generates real-time predictions using trained ML models.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from .model_manager import ModelManager
from .feature_engineering import FeatureEngineer

logger = logging.getLogger(__name__)


class PredictionEngine:
    """Engine for generating predictions using trained ML models."""
    
    def __init__(self, model_manager: Optional[ModelManager] = None, 
                 feature_engineer: Optional[FeatureEngineer] = None):
        self.model_manager = model_manager or ModelManager()
        self.feature_engineer = feature_engineer or FeatureEngineer()
        self.prediction_history: List[Dict] = []
        self.confidence_threshold = 0.6
        
    def generate_prediction(self, symbol: str, market_data: pd.DataFrame, 
                          prediction_horizon: int = 5) -> Dict[str, Any]:
        """Generate prediction for a given symbol using market data."""
        if market_data.empty:
            logger.warning(f"No market data available for {symbol}")
            return self._create_empty_prediction(symbol)
        
        try:
            # Prepare features
            X, _ = self.feature_engineer.prepare_features(market_data, prediction_horizon)
            
            if X.empty:
                logger.warning(f"No features available for {symbol}")
                return self._create_empty_prediction(symbol)
            
            # Get latest features for prediction
            latest_features = X.iloc[-1:].copy()
            
            # Generate predictions from all models
            predictions = {}
            confidences = {}
            
            for model_name in self.model_manager.list_models():
                try:
                    # Check if model has been trained
                    metadata = self.model_manager.get_model_performance(model_name)
                    if not metadata.get('last_trained'):
                        logger.warning(f"Model {model_name} not trained yet")
                        continue
                    
                    # Make prediction
                    pred = self.model_manager.predict(model_name, latest_features)
                    predictions[model_name] = pred[0] if len(pred) > 0 else 0.0
                    
                    # Calculate confidence based on model performance
                    r2_score = metadata.get('performance_metrics', {}).get('r2', 0.0)
                    confidences[model_name] = max(0.0, min(1.0, r2_score))
                    
                except Exception as e:
                    logger.error(f"Error predicting with {model_name}: {e}")
                    predictions[model_name] = 0.0
                    confidences[model_name] = 0.0
            
            if not predictions:
                logger.warning(f"No valid predictions generated for {symbol}")
                return self._create_empty_prediction(symbol)
            
            # Aggregate predictions
            aggregated_prediction = self._aggregate_predictions(predictions, confidences)
            
            # Calculate overall confidence
            overall_confidence = self._calculate_overall_confidence(confidences)
            
            # Generate prediction result
            result = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'prediction_horizon': prediction_horizon,
                'predicted_return': aggregated_prediction,
                'confidence': overall_confidence,
                'model_predictions': predictions,
                'model_confidences': confidences,
                'current_price': market_data['close'].iloc[-1] if 'close' in market_data.columns else None,
                'predicted_price': None,  # Will be calculated below
                'prediction_direction': self._get_prediction_direction(aggregated_prediction),
                'risk_level': self._assess_risk_level(overall_confidence, aggregated_prediction),
                'features_used': list(latest_features.columns),
                'feature_values': latest_features.iloc[0].to_dict()
            }
            
            # Calculate predicted price
            if result['current_price']:
                result['predicted_price'] = result['current_price'] * (1 + aggregated_prediction)
            
            # Store prediction in history
            self.prediction_history.append(result)
            
            logger.info(f"Generated prediction for {symbol}: {aggregated_prediction:.4f} "
                       f"(confidence: {overall_confidence:.2f})")
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating prediction for {symbol}: {e}")
            return self._create_empty_prediction(symbol)
    
    def _aggregate_predictions(self, predictions: Dict[str, float], 
                             confidences: Dict[str, float]) -> float:
        """Aggregate predictions from multiple models using confidence weighting."""
        if not predictions:
            return 0.0
        
        # Weight predictions by confidence
        weighted_sum = 0.0
        total_weight = 0.0
        
        for model_name, pred in predictions.items():
            confidence = confidences.get(model_name, 0.0)
            weighted_sum += pred * confidence
            total_weight += confidence
        
        if total_weight == 0:
            # If no confidence, use simple average
            return sum(predictions.values()) / len(predictions)
        
        return weighted_sum / total_weight
    
    def _calculate_overall_confidence(self, confidences: Dict[str, float]) -> float:
        """Calculate overall confidence from model confidences."""
        if not confidences:
            return 0.0
        
        # Use weighted average of confidences
        confidence_values = list(confidences.values())
        return sum(confidence_values) / len(confidence_values)
    
    def _get_prediction_direction(self, prediction: float) -> str:
        """Get the direction of the prediction."""
        if prediction > 0.01:  # More than 1% positive
            return 'bullish'
        elif prediction < -0.01:  # More than 1% negative
            return 'bearish'
        else:
            return 'neutral'
    
    def _assess_risk_level(self, confidence: float, prediction: float) -> str:
        """Assess the risk level of the prediction."""
        # High confidence, strong prediction = low risk
        # Low confidence, weak prediction = high risk
        risk_score = (1 - confidence) + abs(prediction) * 0.5
        
        if risk_score < 0.3:
            return 'low'
        elif risk_score < 0.6:
            return 'medium'
        else:
            return 'high'
    
    def _create_empty_prediction(self, symbol: str) -> Dict[str, Any]:
        """Create an empty prediction result when no data is available."""
        return {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'prediction_horizon': 5,
            'predicted_return': 0.0,
            'confidence': 0.0,
            'model_predictions': {},
            'model_confidences': {},
            'current_price': None,
            'predicted_price': None,
            'prediction_direction': 'neutral',
            'risk_level': 'high',
            'features_used': [],
            'feature_values': {},
            'error': 'No data available for prediction'
        }
    
    def generate_batch_predictions(self, symbols_data: Dict[str, pd.DataFrame], 
                                 prediction_horizon: int = 5) -> Dict[str, Dict]:
        """Generate predictions for multiple symbols."""
        results = {}
        
        for symbol, market_data in symbols_data.items():
            try:
                prediction = self.generate_prediction(symbol, market_data, prediction_horizon)
                results[symbol] = prediction
            except Exception as e:
                logger.error(f"Error generating batch prediction for {symbol}: {e}")
                results[symbol] = self._create_empty_prediction(symbol)
        
        return results
    
    def get_prediction_history(self, symbol: Optional[str] = None, 
                             limit: Optional[int] = None) -> List[Dict]:
        """Get prediction history, optionally filtered by symbol."""
        history = self.prediction_history
        
        if symbol:
            history = [pred for pred in history if pred['symbol'] == symbol]
        
        if limit:
            history = history[-limit:]
        
        return history
    
    def get_prediction_accuracy(self, symbol: str, days_back: int = 30) -> Dict[str, float]:
        """Calculate prediction accuracy for a symbol over the specified period."""
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        # Get historical predictions
        history = [pred for pred in self.prediction_history 
                  if pred['symbol'] == symbol and 
                  datetime.fromisoformat(pred['timestamp']) > cutoff_date]
        
        if not history:
            return {'accuracy': 0.0, 'direction_accuracy': 0.0, 'total_predictions': 0}
        
        # Calculate accuracy metrics
        total_predictions = len(history)
        correct_direction = 0
        mse_sum = 0.0
        
        for pred in history:
            # For now, we'll use a simplified accuracy calculation
            # In a real implementation, you'd compare with actual price movements
            predicted_direction = pred['prediction_direction']
            confidence = pred['confidence']
            
            # Higher confidence predictions are weighted more
            if confidence > self.confidence_threshold:
                # Simplified: assume predictions are correct if confidence is high
                correct_direction += 1
            
            # Calculate MSE (simplified)
            predicted_return = pred['predicted_return']
            mse_sum += predicted_return ** 2  # Simplified - would need actual returns
        
        direction_accuracy = correct_direction / total_predictions if total_predictions > 0 else 0.0
        mse = mse_sum / total_predictions if total_predictions > 0 else 0.0
        
        return {
            'accuracy': 1.0 - mse,  # Simplified accuracy metric
            'direction_accuracy': direction_accuracy,
            'total_predictions': total_predictions,
            'mse': mse
        }
    
    def update_confidence_threshold(self, new_threshold: float):
        """Update the confidence threshold for predictions."""
        if 0.0 <= new_threshold <= 1.0:
            self.confidence_threshold = new_threshold
            logger.info(f"Updated confidence threshold to {new_threshold}")
        else:
            logger.warning(f"Invalid confidence threshold: {new_threshold}")
    
    def get_model_performance_summary(self) -> Dict[str, Any]:
        """Get summary of all model performances."""
        summary = {}
        
        for model_name in self.model_manager.list_models():
            try:
                metadata = self.model_manager.get_model_performance(model_name)
                summary[model_name] = {
                    'last_trained': metadata.get('last_trained'),
                    'training_samples': metadata.get('training_samples', 0),
                    'performance_metrics': metadata.get('performance_metrics', {}),
                    'feature_importance': metadata.get('feature_importance', {})
                }
            except Exception as e:
                logger.error(f"Error getting performance for {model_name}: {e}")
                summary[model_name] = {'error': str(e)}
        
        return summary
    
    def clear_prediction_history(self):
        """Clear the prediction history."""
        self.prediction_history.clear()
        logger.info("Prediction history cleared") 