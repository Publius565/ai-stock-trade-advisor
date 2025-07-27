"""
Signal Generator - Coordinates trading engine and rules engine
Handles signal generation, validation, and management
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json

from .trading_engine import TradingEngine, TradingSignal, SignalType, SignalStrength
from .rules_engine import RulesEngine
from ..utils.database_manager import DatabaseManager
from ..data_layer.market_data import MarketDataManager


@dataclass
class SignalMetrics:
    """Signal performance metrics"""
    total_signals: int
    successful_signals: int
    accuracy_rate: float
    avg_confidence: float
    best_performing_rules: List[str]
    last_updated: datetime


class SignalGenerator:
    """
    Coordinates trading engine and rules engine for signal generation
    """
    
    def __init__(self, db_manager: DatabaseManager, trading_engine: TradingEngine):
        self.db_manager = db_manager
        self.trading_engine = trading_engine
        self.rules_engine = RulesEngine()
        cache_dir = getattr(db_manager, 'get_cache_dir', lambda: "data/cache")()
        self.market_data_manager = MarketDataManager(cache_dir)
        self.logger = logging.getLogger(__name__)
        
        # Signal tracking
        self.signal_history: List[TradingSignal] = []
        self.signal_metrics = SignalMetrics(
            total_signals=0,
            successful_signals=0,
            accuracy_rate=0.0,
            avg_confidence=0.0,
            best_performing_rules=[],
            last_updated=datetime.now()
        )
        
        self.logger.info("Signal Generator initialized")
    
    def generate_signals_for_watchlist(self, watchlist_symbols: List[str]) -> List[TradingSignal]:
        """
        Generate signals for symbols in the watchlist
        """
        signals = []
        
        for symbol in watchlist_symbols:
            try:
                signal = self.generate_signal_for_symbol(symbol)
                if signal:
                    signals.append(signal)
                    
            except Exception as e:
                self.logger.error(f"Error generating signal for {symbol}: {e}")
        
        self.logger.info(f"Generated {len(signals)} signals for watchlist")
        return signals
    
    def generate_signal_for_symbol(self, symbol: str) -> Optional[TradingSignal]:
        """
        Generate a comprehensive trading signal for a single symbol
        """
        try:
            # Get market data
            market_data = self.market_data_manager.get_market_data(symbol)
            if not market_data:
                self.logger.warning(f"No market data available for {symbol}")
                return None
            
            # Use rules engine to evaluate symbol
            signal = self.rules_engine.evaluate_symbol(symbol, market_data)
            if not signal:
                return None
            
            # Enhance signal with additional analysis
            enhanced_signal = self._enhance_signal(signal, market_data)
            
            # Store in history
            self.signal_history.append(enhanced_signal)
            
            # Update metrics
            self._update_metrics()
            
            return enhanced_signal
            
        except Exception as e:
            self.logger.error(f"Error generating signal for {symbol}: {e}")
            return None
    
    def _enhance_signal(self, signal: TradingSignal, market_data: Dict) -> TradingSignal:
        """
        Enhance signal with additional analysis and context
        """
        # Add market context
        market_context = self._analyze_market_context(market_data)
        
        # Adjust confidence based on market conditions
        adjusted_confidence = self._adjust_confidence(signal.confidence, market_context)
        
        # Add trend analysis
        trend_analysis = self._analyze_trend(market_data)
        
        # Enhance reasoning
        enhanced_reasoning = f"{signal.reasoning}; {market_context}; {trend_analysis}"
        
        # Create enhanced signal
        enhanced_signal = TradingSignal(
            symbol=signal.symbol,
            signal_type=signal.signal_type,
            strength=signal.strength,
            price=signal.price,
            timestamp=signal.timestamp,
            confidence=adjusted_confidence,
            reasoning=enhanced_reasoning,
            indicators=signal.indicators,
            risk_level=signal.risk_level
        )
        
        return enhanced_signal
    
    def _analyze_market_context(self, market_data: Dict) -> str:
        """Analyze broader market context"""
        context_parts = []
        
        # Volume analysis
        volume = market_data.get('volume', 0)
        avg_volume = market_data.get('avg_volume_20', 0)
        if volume and avg_volume:
            volume_ratio = volume / avg_volume
            if volume_ratio > 2.0:
                context_parts.append("Very high volume")
            elif volume_ratio > 1.5:
                context_parts.append("High volume")
            elif volume_ratio < 0.5:
                context_parts.append("Low volume")
        
        # Price momentum
        price_change = market_data.get('price_change_pct', 0)
        if abs(price_change) > 0.05:
            direction = "strong upward" if price_change > 0 else "strong downward"
            context_parts.append(f"{direction} momentum")
        
        # Volatility context
        volatility = market_data.get('volatility_20', 0)
        if volatility > 0.05:
            context_parts.append("High volatility environment")
        elif volatility < 0.02:
            context_parts.append("Low volatility environment")
        
        return "; ".join(context_parts) if context_parts else "Normal market conditions"
    
    def _adjust_confidence(self, base_confidence: float, market_context: str) -> float:
        """Adjust confidence based on market context"""
        adjusted = base_confidence
        
        # Adjust based on market conditions
        if "Very high volume" in market_context:
            adjusted += 0.1
        elif "Low volume" in market_context:
            adjusted -= 0.1
        
        if "High volatility environment" in market_context:
            adjusted -= 0.05
        
        # Ensure confidence stays within bounds
        return max(0.0, min(1.0, adjusted))
    
    def _analyze_trend(self, market_data: Dict) -> str:
        """Analyze price trend"""
        sma_20 = market_data.get('sma_20', 0)
        sma_50 = market_data.get('sma_50', 0)
        current_price = market_data.get('price', 0)
        
        if not all([sma_20, sma_50, current_price]):
            return "Insufficient data for trend analysis"
        
        # Trend analysis
        if current_price > sma_20 > sma_50:
            return "Strong uptrend"
        elif current_price > sma_20 and sma_20 < sma_50:
            return "Potential trend reversal"
        elif current_price < sma_20 < sma_50:
            return "Strong downtrend"
        elif current_price < sma_20 and sma_20 > sma_50:
            return "Potential trend reversal"
        else:
            return "Sideways trend"
    
    def get_signal_recommendations(self, signals: List[TradingSignal]) -> List[Dict]:
        """
        Get actionable recommendations from signals
        """
        recommendations = []
        
        for signal in signals:
            if signal.signal_type == SignalType.HOLD:
                continue
            
            # Check if signal meets execution criteria
            if self._should_execute_signal(signal):
                recommendation = {
                    'symbol': signal.symbol,
                    'action': signal.signal_type.value,
                    'price': signal.price,
                    'confidence': signal.confidence,
                    'strength': signal.strength.value,
                    'reasoning': signal.reasoning,
                    'risk_level': signal.risk_level,
                    'timestamp': signal.timestamp.isoformat(),
                    'priority': self._calculate_priority(signal)
                }
                recommendations.append(recommendation)
        
        # Sort by priority
        recommendations.sort(key=lambda x: x['priority'], reverse=True)
        
        return recommendations
    
    def _should_execute_signal(self, signal: TradingSignal) -> bool:
        """Determine if signal should be executed"""
        # Minimum confidence threshold
        if signal.confidence < 0.6:
            return False
        
        # Minimum strength threshold
        if signal.strength.value < SignalStrength.MODERATE.value:
            return False
        
        # Risk level check
        if signal.risk_level == "HIGH":
            # Require higher confidence for high-risk signals
            if signal.confidence < 0.8:
                return False
        
        return True
    
    def _calculate_priority(self, signal: TradingSignal) -> float:
        """Calculate signal priority score"""
        priority = 0.0
        
        # Base priority from confidence
        priority += signal.confidence * 0.4
        
        # Strength bonus
        priority += signal.strength.value * 0.2
        
        # Signal type bonus
        if signal.signal_type in [SignalType.STRONG_BUY, SignalType.STRONG_SELL]:
            priority += 0.2
        elif signal.signal_type in [SignalType.BUY, SignalType.SELL]:
            priority += 0.1
        
        # Risk adjustment
        if signal.risk_level == "LOW":
            priority += 0.1
        elif signal.risk_level == "HIGH":
            priority -= 0.1
        
        return priority
    
    def get_signal_summary(self) -> Dict:
        """Get summary of recent signals"""
        recent_signals = [
            s for s in self.signal_history 
            if s.timestamp > datetime.now() - timedelta(days=7)
        ]
        
        if not recent_signals:
            return {
                'total_signals': 0,
                'buy_signals': 0,
                'sell_signals': 0,
                'hold_signals': 0,
                'avg_confidence': 0.0,
                'high_confidence_signals': 0
            }
        
        buy_signals = len([s for s in recent_signals if s.signal_type in [SignalType.BUY, SignalType.STRONG_BUY]])
        sell_signals = len([s for s in recent_signals if s.signal_type in [SignalType.SELL, SignalType.STRONG_SELL]])
        hold_signals = len([s for s in recent_signals if s.signal_type == SignalType.HOLD])
        
        avg_confidence = sum(s.confidence for s in recent_signals) / len(recent_signals)
        high_confidence_signals = len([s for s in recent_signals if s.confidence > 0.8])
        
        return {
            'total_signals': len(recent_signals),
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'hold_signals': hold_signals,
            'avg_confidence': round(avg_confidence, 3),
            'high_confidence_signals': high_confidence_signals
        }
    
    def _update_metrics(self) -> None:
        """Update signal performance metrics"""
        if not self.signal_history:
            return
        
        self.signal_metrics.total_signals = len(self.signal_history)
        self.signal_metrics.avg_confidence = sum(s.confidence for s in self.signal_history) / len(self.signal_history)
        self.signal_metrics.last_updated = datetime.now()
        
        # Calculate accuracy (simplified - would need actual trade results)
        # For now, assume signals with confidence > 0.8 are "successful"
        high_confidence_signals = [s for s in self.signal_history if s.confidence > 0.8]
        self.signal_metrics.successful_signals = len(high_confidence_signals)
        
        if self.signal_metrics.total_signals > 0:
            self.signal_metrics.accuracy_rate = self.signal_metrics.successful_signals / self.signal_metrics.total_signals
    
    def get_rules_summary(self) -> Dict:
        """Get summary of trading rules"""
        return self.rules_engine.get_rule_summary()
    
    def enable_rule(self, rule_name: str, enabled: bool = True) -> None:
        """Enable or disable a trading rule"""
        self.rules_engine.enable_rule(rule_name, enabled)
    
    def add_custom_rule(self, rule_name: str, rule_type: str, parameters: Dict, weight: float) -> None:
        """Add a custom trading rule"""
        from .rules_engine import TradingRule, RuleType
        
        rule = TradingRule(
            name=rule_name,
            rule_type=RuleType(rule_type),
            description=f"Custom rule: {rule_name}",
            parameters=parameters,
            weight=weight
        )
        
        self.rules_engine.add_rule(rule)
        self.logger.info(f"Added custom rule: {rule_name}")
    
    def export_signals(self, filename: str = None) -> str:
        """Export signal history to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"signals_export_{timestamp}.json"
        
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'total_signals': len(self.signal_history),
            'signals': [
                {
                    'symbol': s.symbol,
                    'signal_type': s.signal_type.value,
                    'strength': s.strength.value,
                    'price': s.price,
                    'timestamp': s.timestamp.isoformat(),
                    'confidence': s.confidence,
                    'reasoning': s.reasoning,
                    'risk_level': s.risk_level
                }
                for s in self.signal_history
            ]
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            self.logger.info(f"Exported {len(self.signal_history)} signals to {filename}")
            return filename
            
        except Exception as e:
            self.logger.error(f"Error exporting signals: {e}")
            return "" 