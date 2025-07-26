"""
Trade Suggestion Engine

Generates trading suggestions based on ML predictions, technical analysis, and user risk profile.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from ..ml_models.prediction_engine import PredictionEngine
from ..ml_models.feature_engineering import FeatureEngineer
from .rules_engine import RulesEngine
from .signal_generator import SignalGenerator

logger = logging.getLogger(__name__)


class TradeSuggestionEngine:
    """Engine for generating trade suggestions with risk assessment and rationale."""
    
    def __init__(self, prediction_engine: Optional[PredictionEngine] = None,
                 rules_engine: Optional[RulesEngine] = None,
                 signal_generator: Optional[SignalGenerator] = None,
                 db_manager=None, trading_engine=None):
        self.prediction_engine = prediction_engine or PredictionEngine()
        self.rules_engine = rules_engine or RulesEngine()
        
        # Initialize signal_generator with proper dependencies or None if not available
        if signal_generator:
            self.signal_generator = signal_generator
        elif db_manager and trading_engine:
            self.signal_generator = SignalGenerator(db_manager, trading_engine)
        else:
            self.signal_generator = None
            logger.warning("SignalGenerator not initialized - missing db_manager or trading_engine")
        
        self.feature_engineer = FeatureEngineer()
        
        # Suggestion categories
        self.suggestion_types = {
            'high_risk_high_reward': {
                'min_confidence': 0.7,
                'min_predicted_return': 0.05,  # 5%
                'max_risk_score': 0.8
            },
            'low_risk_low_reward': {
                'min_confidence': 0.8,
                'min_predicted_return': 0.02,  # 2%
                'max_risk_score': 0.4
            },
            'moderate_risk_moderate_reward': {
                'min_confidence': 0.6,
                'min_predicted_return': 0.03,  # 3%
                'max_risk_score': 0.6
            }
        }
    
    def generate_suggestions(self, symbol: str, market_data: pd.DataFrame,
                           user_risk_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate trading suggestions for a symbol based on user risk profile."""
        suggestions = []
        
        try:
            # Generate ML prediction
            prediction = self.prediction_engine.generate_prediction(symbol, market_data)
            
            # Generate technical signals
            signals = []
            if self.signal_generator:
                try:
                    signal = self.signal_generator.generate_signal_for_symbol(symbol)
                    if signal:
                        signals = [signal]
                except Exception as e:
                    logger.warning(f"Could not generate signals for {symbol}: {e}")
            else:
                logger.warning(f"SignalGenerator not available for {symbol}")
            
            # Create feature-based analysis
            features = self._analyze_features(market_data)
            
            # Generate suggestions for different risk levels
            for suggestion_type, criteria in self.suggestion_types.items():
                suggestion = self._create_suggestion(
                    symbol, prediction, signals, features, 
                    suggestion_type, criteria, user_risk_profile
                )
                
                if suggestion and self._validate_suggestion(suggestion, user_risk_profile):
                    suggestions.append(suggestion)
            
            # Sort suggestions by expected value (reward * probability)
            suggestions.sort(key=lambda x: x['expected_value'], reverse=True)
            
            logger.info(f"Generated {len(suggestions)} suggestions for {symbol}")
            
        except Exception as e:
            logger.error(f"Error generating suggestions for {symbol}: {e}")
        
        return suggestions
    
    def _create_suggestion(self, symbol: str, prediction: Dict[str, Any],
                          signals: List[Dict], features: Dict[str, Any],
                          suggestion_type: str, criteria: Dict[str, Any],
                          user_risk_profile: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a specific type of trading suggestion."""
        
        # Check if prediction meets criteria
        if not self._meets_criteria(prediction, criteria):
            return None
        
        # Calculate suggestion parameters based on type
        suggestion_params = self._calculate_suggestion_params(
            suggestion_type, prediction, user_risk_profile
        )
        
        # Generate rationale
        rationale = self._generate_rationale(
            symbol, prediction, signals, features, suggestion_type
        )
        
        # Calculate risk metrics
        risk_metrics = self._calculate_risk_metrics(
            prediction, signals, features, suggestion_params
        )
        
        # Create suggestion
        suggestion = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'suggestion_type': suggestion_type,
            'action': self._determine_action(prediction, signals),
            'confidence': prediction.get('confidence', 0.0),
            'predicted_return': prediction.get('predicted_return', 0.0),
            'predicted_price': prediction.get('predicted_price'),
            'current_price': prediction.get('current_price'),
            'position_size': suggestion_params['position_size'],
            'stop_loss': suggestion_params['stop_loss'],
            'take_profit': suggestion_params['take_profit'],
            'time_horizon': suggestion_params['time_horizon'],
            'expected_value': suggestion_params['expected_value'],
            'risk_score': risk_metrics['risk_score'],
            'max_loss': risk_metrics['max_loss'],
            'potential_gain': risk_metrics['potential_gain'],
            'risk_reward_ratio': risk_metrics['risk_reward_ratio'],
            'rationale': rationale,
            'technical_signals': signals,
            'feature_analysis': features,
            'user_risk_compatibility': self._assess_user_risk_compatibility(
                suggestion_params, user_risk_profile
            )
        }
        
        return suggestion
    
    def _meets_criteria(self, prediction: Dict[str, Any], criteria: Dict[str, Any]) -> bool:
        """Check if prediction meets the criteria for a suggestion type."""
        confidence = prediction.get('confidence', 0.0)
        predicted_return = abs(prediction.get('predicted_return', 0.0))
        
        return (confidence >= criteria['min_confidence'] and
                predicted_return >= criteria['min_predicted_return'])
    
    def _calculate_suggestion_params(self, suggestion_type: str, 
                                   prediction: Dict[str, Any],
                                   user_risk_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate suggestion parameters based on type and user profile."""
        predicted_return = prediction.get('predicted_return', 0.0)
        confidence = prediction.get('confidence', 0.0)
        current_price = prediction.get('current_price', 0.0)
        
        # Base parameters
        if suggestion_type == 'high_risk_high_reward':
            position_size = min(0.15, user_risk_profile.get('max_position_size', 0.1))
            stop_loss_pct = 0.08  # 8% stop loss
            take_profit_pct = 0.15  # 15% take profit
            time_horizon = 5  # 5 days
            
        elif suggestion_type == 'low_risk_low_reward':
            position_size = min(0.25, user_risk_profile.get('max_position_size', 0.2))
            stop_loss_pct = 0.03  # 3% stop loss
            take_profit_pct = 0.06  # 6% take profit
            time_horizon = 10  # 10 days
            
        else:  # moderate_risk_moderate_reward
            position_size = min(0.20, user_risk_profile.get('max_position_size', 0.15))
            stop_loss_pct = 0.05  # 5% stop loss
            take_profit_pct = 0.10  # 10% take profit
            time_horizon = 7  # 7 days
        
        # Calculate expected value
        expected_value = predicted_return * confidence * position_size
        
        # Calculate price levels
        if current_price:
            if predicted_return > 0:  # Buy suggestion
                stop_loss = current_price * (1 - stop_loss_pct)
                take_profit = current_price * (1 + take_profit_pct)
            else:  # Sell suggestion
                stop_loss = current_price * (1 + stop_loss_pct)
                take_profit = current_price * (1 - take_profit_pct)
        else:
            stop_loss = None
            take_profit = None
        
        return {
            'position_size': position_size,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'time_horizon': time_horizon,
            'expected_value': expected_value
        }
    
    def _determine_action(self, prediction: Dict[str, Any], signals: List[Dict]) -> str:
        """Determine the suggested action (buy/sell/hold)."""
        predicted_return = prediction.get('predicted_return', 0.0)
        confidence = prediction.get('confidence', 0.0)
        
        # Check technical signals
        buy_signals = sum(1 for signal in signals if signal.get('action') == 'buy')
        sell_signals = sum(1 for signal in signals if signal.get('action') == 'sell')
        
        # Combine ML prediction with technical signals
        if predicted_return > 0.02 and confidence > 0.6 and buy_signals >= sell_signals:
            return 'buy'
        elif predicted_return < -0.02 and confidence > 0.6 and sell_signals >= buy_signals:
            return 'sell'
        else:
            return 'hold'
    
    def _generate_rationale(self, symbol: str, prediction: Dict[str, Any],
                           signals: List[Dict], features: Dict[str, Any],
                           suggestion_type: str) -> str:
        """Generate human-readable rationale for the suggestion."""
        rationale_parts = []
        
        # ML prediction rationale
        predicted_return = prediction.get('predicted_return', 0.0)
        confidence = prediction.get('confidence', 0.0)
        direction = prediction.get('prediction_direction', 'neutral')
        
        rationale_parts.append(
            f"ML models predict a {direction} movement with {predicted_return:.2%} "
            f"expected return (confidence: {confidence:.1%})"
        )
        
        # Technical analysis rationale
        if signals:
            signal_summary = self._summarize_signals(signals)
            rationale_parts.append(f"Technical analysis: {signal_summary}")
        
        # Feature analysis rationale
        if features:
            feature_summary = self._summarize_features(features)
            rationale_parts.append(f"Market indicators: {feature_summary}")
        
        # Risk level explanation
        risk_explanation = self._explain_risk_level(suggestion_type)
        rationale_parts.append(risk_explanation)
        
        return ". ".join(rationale_parts)
    
    def _summarize_signals(self, signals: List[Dict]) -> str:
        """Summarize technical signals for rationale."""
        if not signals:
            return "No strong technical signals"
        
        buy_count = sum(1 for s in signals if s.get('action') == 'buy')
        sell_count = sum(1 for s in signals if s.get('action') == 'sell')
        
        if buy_count > sell_count:
            return f"{buy_count} bullish signals vs {sell_count} bearish signals"
        elif sell_count > buy_count:
            return f"{sell_count} bearish signals vs {buy_count} bullish signals"
        else:
            return "Mixed technical signals"
    
    def _summarize_features(self, features: Dict[str, Any]) -> str:
        """Summarize feature analysis for rationale."""
        summary_parts = []
        
        # RSI analysis
        if 'rsi_14' in features:
            rsi = features['rsi_14']
            if rsi < 30:
                summary_parts.append("oversold conditions")
            elif rsi > 70:
                summary_parts.append("overbought conditions")
        
        # Moving average analysis
        if 'sma_20' in features and 'close' in features:
            if features['close'] > features['sma_20']:
                summary_parts.append("above 20-day moving average")
            else:
                summary_parts.append("below 20-day moving average")
        
        # Volume analysis
        if 'volume_ratio' in features:
            vol_ratio = features['volume_ratio']
            if vol_ratio > 1.5:
                summary_parts.append("high volume activity")
            elif vol_ratio < 0.5:
                summary_parts.append("low volume activity")
        
        return ", ".join(summary_parts) if summary_parts else "neutral market conditions"
    
    def _explain_risk_level(self, suggestion_type: str) -> str:
        """Explain the risk level for the suggestion type."""
        if suggestion_type == 'high_risk_high_reward':
            return "High-risk strategy targeting significant gains with potential for larger losses"
        elif suggestion_type == 'low_risk_low_reward':
            return "Conservative strategy prioritizing capital preservation with modest gains"
        else:
            return "Balanced strategy with moderate risk and reward expectations"
    
    def _calculate_risk_metrics(self, prediction: Dict[str, Any], signals: List[Dict],
                               features: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, float]:
        """Calculate risk metrics for the suggestion."""
        confidence = prediction.get('confidence', 0.0)
        predicted_return = prediction.get('predicted_return', 0.0)
        position_size = params['position_size']
        
        # Risk score (0-1, higher = more risky)
        risk_score = (1 - confidence) + abs(predicted_return) * 0.3
        
        # Maximum potential loss
        max_loss = position_size * 0.1  # Assume 10% max loss
        
        # Potential gain
        potential_gain = position_size * abs(predicted_return)
        
        # Risk-reward ratio
        risk_reward_ratio = potential_gain / max_loss if max_loss > 0 else 0
        
        return {
            'risk_score': min(1.0, risk_score),
            'max_loss': max_loss,
            'potential_gain': potential_gain,
            'risk_reward_ratio': risk_reward_ratio
        }
    
    def _assess_user_risk_compatibility(self, suggestion_params: Dict[str, Any],
                                      user_risk_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Assess how well the suggestion matches the user's risk profile."""
        user_risk_tolerance = user_risk_profile.get('risk_tolerance', 'moderate')
        suggestion_type = suggestion_params.get('suggestion_type', 'moderate')
        
        # Risk compatibility mapping
        risk_compatibility = {
            'conservative': ['low_risk_low_reward'],
            'moderate': ['low_risk_low_reward', 'moderate_risk_moderate_reward'],
            'aggressive': ['low_risk_low_reward', 'moderate_risk_moderate_reward', 'high_risk_high_reward']
        }
        
        is_compatible = suggestion_type in risk_compatibility.get(user_risk_tolerance, [])
        
        return {
            'is_compatible': is_compatible,
            'user_risk_tolerance': user_risk_tolerance,
            'suggestion_risk_level': suggestion_type,
            'compatibility_score': 1.0 if is_compatible else 0.3
        }
    
    def _validate_suggestion(self, suggestion: Dict[str, Any], 
                           user_risk_profile: Dict[str, Any]) -> bool:
        """Validate if suggestion is appropriate for the user."""
        # Check risk compatibility
        if not suggestion['user_risk_compatibility']['is_compatible']:
            return False
        
        # Check minimum confidence
        if suggestion['confidence'] < 0.5:
            return False
        
        # Check position size limits
        max_position = user_risk_profile.get('max_position_size', 0.1)
        if suggestion['position_size'] > max_position:
            return False
        
        return True
    
    def _analyze_features(self, market_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze market features for suggestion generation."""
        if market_data.empty:
            return {}
        
        try:
            # Create features
            df_features = self.feature_engineer.create_technical_indicators(market_data)
            
            # Get latest feature values
            if not df_features.empty:
                latest_features = df_features.iloc[-1]
                return latest_features.to_dict()
            
        except Exception as e:
            logger.error(f"Error analyzing features: {e}")
        
        return {}
    
    def filter_suggestions(self, suggestions: List[Dict[str, Any]], 
                          filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter suggestions based on user criteria."""
        filtered = suggestions
        
        # Filter by minimum confidence
        if 'min_confidence' in filters:
            filtered = [s for s in filtered if s['confidence'] >= filters['min_confidence']]
        
        # Filter by risk level
        if 'risk_level' in filters:
            filtered = [s for s in filtered if s['suggestion_type'] == filters['risk_level']]
        
        # Filter by action
        if 'action' in filters:
            filtered = [s for s in filtered if s['action'] == filters['action']]
        
        # Filter by minimum expected value
        if 'min_expected_value' in filters:
            filtered = [s for s in filtered if s['expected_value'] >= filters['min_expected_value']]
        
        return filtered
    
    def rank_suggestions(self, suggestions: List[Dict[str, Any]], 
                        ranking_criteria: str = 'expected_value') -> List[Dict[str, Any]]:
        """Rank suggestions based on specified criteria."""
        if ranking_criteria == 'expected_value':
            return sorted(suggestions, key=lambda x: x['expected_value'], reverse=True)
        elif ranking_criteria == 'risk_reward_ratio':
            return sorted(suggestions, key=lambda x: x['risk_reward_ratio'], reverse=True)
        elif ranking_criteria == 'confidence':
            return sorted(suggestions, key=lambda x: x['confidence'], reverse=True)
        else:
            return suggestions 