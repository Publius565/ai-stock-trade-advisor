"""
Rules Engine - Advanced trading rule evaluation and signal generation
Handles complex technical analysis and pattern recognition
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import math

from .trading_engine import SignalType, SignalStrength, TradingSignal


class RuleType(Enum):
    """Types of trading rules"""
    TECHNICAL_INDICATOR = "technical_indicator"
    PATTERN_RECOGNITION = "pattern_recognition"
    VOLUME_ANALYSIS = "volume_analysis"
    MOMENTUM_ANALYSIS = "momentum_analysis"
    RISK_MANAGEMENT = "risk_management"


@dataclass
class TradingRule:
    """Trading rule definition"""
    name: str
    rule_type: RuleType
    description: str
    parameters: Dict[str, Any]
    weight: float  # 0.0 to 1.0
    enabled: bool = True


class RulesEngine:
    """
    Advanced rules engine for evaluating trading signals
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.rules: Dict[str, TradingRule] = {}
        self._initialize_default_rules()
        
    def _initialize_default_rules(self):
        """Initialize default trading rules"""
        
        # Moving Average Rules
        self.add_rule(TradingRule(
            name="SMA_Crossover_20_50",
            rule_type=RuleType.TECHNICAL_INDICATOR,
            description="Simple Moving Average 20/50 crossover",
            parameters={"short_period": 20, "long_period": 50},
            weight=0.3
        ))
        
        self.add_rule(TradingRule(
            name="EMA_Crossover_12_26",
            rule_type=RuleType.TECHNICAL_INDICATOR,
            description="Exponential Moving Average 12/26 crossover",
            parameters={"short_period": 12, "long_period": 26},
            weight=0.25
        ))
        
        # Volume Rules
        self.add_rule(TradingRule(
            name="Volume_Spike",
            rule_type=RuleType.VOLUME_ANALYSIS,
            description="Volume spike detection",
            parameters={"threshold": 1.5, "period": 20},
            weight=0.2
        ))
        
        # Momentum Rules
        self.add_rule(TradingRule(
            name="RSI_Overbought_Oversold",
            rule_type=RuleType.MOMENTUM_ANALYSIS,
            description="RSI overbought/oversold conditions",
            parameters={"overbought": 70, "oversold": 30, "period": 14},
            weight=0.15
        ))
        
        # Risk Management Rules
        self.add_rule(TradingRule(
            name="Volatility_Check",
            rule_type=RuleType.RISK_MANAGEMENT,
            description="Volatility-based risk assessment",
            parameters={"max_volatility": 0.05, "period": 20},
            weight=0.1
        ))
        
        self.logger.info(f"Initialized {len(self.rules)} default trading rules")
    
    def add_rule(self, rule: TradingRule) -> None:
        """Add a new trading rule"""
        self.rules[rule.name] = rule
        self.logger.info(f"Added rule: {rule.name}")
    
    def remove_rule(self, rule_name: str) -> None:
        """Remove a trading rule"""
        if rule_name in self.rules:
            del self.rules[rule_name]
            self.logger.info(f"Removed rule: {rule_name}")
    
    def enable_rule(self, rule_name: str, enabled: bool = True) -> None:
        """Enable or disable a trading rule"""
        if rule_name in self.rules:
            self.rules[rule_name].enabled = enabled
            self.logger.info(f"{'Enabled' if enabled else 'Disabled'} rule: {rule_name}")
    
    def evaluate_symbol(self, symbol: str, market_data: Dict) -> Optional[TradingSignal]:
        """
        Evaluate a symbol using all enabled rules
        """
        if not market_data:
            return None
        
        rule_results = []
        total_weight = 0
        
        # Evaluate each enabled rule
        for rule in self.rules.values():
            if not rule.enabled:
                continue
                
            result = self._evaluate_rule(rule, market_data)
            if result:
                rule_results.append((rule, result))
                total_weight += rule.weight
        
        if not rule_results:
            return None
        
        # Aggregate results into final signal
        signal = self._aggregate_results(symbol, rule_results, total_weight, market_data)
        return signal
    
    def _evaluate_rule(self, rule: TradingRule, market_data: Dict) -> Optional[Dict]:
        """
        Evaluate a single trading rule
        """
        try:
            if rule.rule_type == RuleType.TECHNICAL_INDICATOR:
                return self._evaluate_technical_indicator(rule, market_data)
            elif rule.rule_type == RuleType.VOLUME_ANALYSIS:
                return self._evaluate_volume_analysis(rule, market_data)
            elif rule.rule_type == RuleType.MOMENTUM_ANALYSIS:
                return self._evaluate_momentum_analysis(rule, market_data)
            elif rule.rule_type == RuleType.RISK_MANAGEMENT:
                return self._evaluate_risk_management(rule, market_data)
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Error evaluating rule {rule.name}: {e}")
            return None
    
    def _evaluate_technical_indicator(self, rule: TradingRule, market_data: Dict) -> Optional[Dict]:
        """Evaluate technical indicator rules"""
        
        if rule.name == "SMA_Crossover_20_50":
            return self._evaluate_sma_crossover(rule, market_data)
        elif rule.name == "EMA_Crossover_12_26":
            return self._evaluate_ema_crossover(rule, market_data)
        
        return None
    
    def _evaluate_sma_crossover(self, rule: TradingRule, market_data: Dict) -> Optional[Dict]:
        """Evaluate SMA crossover rule"""
        short_period = rule.parameters["short_period"]
        long_period = rule.parameters["long_period"]
        
        sma_short = market_data.get(f'sma_{short_period}', 0)
        sma_long = market_data.get(f'sma_{long_period}', 0)
        current_price = market_data.get('price', 0)
        
        if not all([sma_short, sma_long, current_price]):
            return None
        
        # Bullish crossover
        if current_price > sma_short > sma_long:
            return {
                'signal': SignalType.BUY,
                'strength': SignalStrength.MODERATE,
                'confidence': 0.7,
                'reasoning': f"Price above SMA{short_period} and SMA{long_period}"
            }
        
        # Bearish crossover
        elif current_price < sma_short < sma_long:
            return {
                'signal': SignalType.SELL,
                'strength': SignalStrength.MODERATE,
                'confidence': 0.7,
                'reasoning': f"Price below SMA{short_period} and SMA{long_period}"
            }
        
        return None
    
    def _evaluate_ema_crossover(self, rule: TradingRule, market_data: Dict) -> Optional[Dict]:
        """Evaluate EMA crossover rule"""
        short_period = rule.parameters["short_period"]
        long_period = rule.parameters["long_period"]
        
        ema_short = market_data.get(f'ema_{short_period}', 0)
        ema_long = market_data.get(f'ema_{long_period}', 0)
        current_price = market_data.get('price', 0)
        
        if not all([ema_short, ema_long, current_price]):
            return None
        
        # Bullish crossover
        if current_price > ema_short > ema_long:
            return {
                'signal': SignalType.BUY,
                'strength': SignalStrength.MODERATE,
                'confidence': 0.75,
                'reasoning': f"Price above EMA{short_period} and EMA{long_period}"
            }
        
        # Bearish crossover
        elif current_price < ema_short < ema_long:
            return {
                'signal': SignalType.SELL,
                'strength': SignalStrength.MODERATE,
                'confidence': 0.75,
                'reasoning': f"Price below EMA{short_period} and EMA{long_period}"
            }
        
        return None
    
    def _evaluate_volume_analysis(self, rule: TradingRule, market_data: Dict) -> Optional[Dict]:
        """Evaluate volume analysis rules"""
        
        if rule.name == "Volume_Spike":
            return self._evaluate_volume_spike(rule, market_data)
        
        return None
    
    def _evaluate_volume_spike(self, rule: TradingRule, market_data: Dict) -> Optional[Dict]:
        """Evaluate volume spike rule"""
        threshold = rule.parameters["threshold"]
        period = rule.parameters["period"]
        
        current_volume = market_data.get('volume', 0)
        avg_volume = market_data.get(f'avg_volume_{period}', 0)
        
        if not all([current_volume, avg_volume]):
            return None
        
        volume_ratio = current_volume / avg_volume
        
        if volume_ratio > threshold:
            # Determine if volume spike is bullish or bearish based on price action
            price_change = market_data.get('price_change_pct', 0)
            
            if price_change > 0:
                return {
                    'signal': SignalType.BUY,
                    'strength': SignalStrength.STRONG,
                    'confidence': 0.8,
                    'reasoning': f"High volume ({volume_ratio:.1f}x avg) with positive price action"
                }
            elif price_change < 0:
                return {
                    'signal': SignalType.SELL,
                    'strength': SignalStrength.STRONG,
                    'confidence': 0.8,
                    'reasoning': f"High volume ({volume_ratio:.1f}x avg) with negative price action"
                }
        
        return None
    
    def _evaluate_momentum_analysis(self, rule: TradingRule, market_data: Dict) -> Optional[Dict]:
        """Evaluate momentum analysis rules"""
        
        if rule.name == "RSI_Overbought_Oversold":
            return self._evaluate_rsi_conditions(rule, market_data)
        
        return None
    
    def _evaluate_rsi_conditions(self, rule: TradingRule, market_data: Dict) -> Optional[Dict]:
        """Evaluate RSI overbought/oversold conditions"""
        overbought = rule.parameters["overbought"]
        oversold = rule.parameters["oversold"]
        period = rule.parameters["period"]
        
        rsi = market_data.get(f'rsi_{period}', 50)
        
        if rsi > overbought:
            return {
                'signal': SignalType.SELL,
                'strength': SignalStrength.MODERATE,
                'confidence': 0.6,
                'reasoning': f"RSI overbought ({rsi:.1f})"
            }
        elif rsi < oversold:
            return {
                'signal': SignalType.BUY,
                'strength': SignalStrength.MODERATE,
                'confidence': 0.6,
                'reasoning': f"RSI oversold ({rsi:.1f})"
            }
        
        return None
    
    def _evaluate_risk_management(self, rule: TradingRule, market_data: Dict) -> Optional[Dict]:
        """Evaluate risk management rules"""
        
        if rule.name == "Volatility_Check":
            return self._evaluate_volatility_check(rule, market_data)
        
        return None
    
    def _evaluate_volatility_check(self, rule: TradingRule, market_data: Dict) -> Optional[Dict]:
        """Evaluate volatility-based risk assessment"""
        max_volatility = rule.parameters["max_volatility"]
        period = rule.parameters["period"]
        
        volatility = market_data.get(f'volatility_{period}', 0)
        
        if volatility > max_volatility:
            return {
                'signal': SignalType.HOLD,
                'strength': SignalStrength.STRONG,
                'confidence': 0.9,
                'reasoning': f"High volatility ({volatility:.3f}) - risk management"
            }
        
        return None
    
    def _aggregate_results(self, symbol: str, rule_results: List[Tuple[TradingRule, Dict]], 
                          total_weight: float, market_data: Dict) -> TradingSignal:
        """
        Aggregate rule results into final trading signal
        """
        # Count signal types
        signal_counts = {SignalType.BUY: 0, SignalType.SELL: 0, SignalType.HOLD: 0}
        weighted_confidence = {SignalType.BUY: 0, SignalType.SELL: 0, SignalType.HOLD: 0}
        reasoning_list = []
        
        for rule, result in rule_results:
            signal_type = result['signal']
            signal_counts[signal_type] += 1
            weighted_confidence[signal_type] += result['confidence'] * rule.weight
            reasoning_list.append(f"{rule.name}: {result['reasoning']}")
        
        # Determine final signal type
        final_signal_type = max(signal_counts.items(), key=lambda x: x[1])[0]
        
        # Calculate weighted confidence
        if total_weight > 0:
            final_confidence = weighted_confidence[final_signal_type] / total_weight
        else:
            final_confidence = 0.5
        
        # Determine signal strength based on confidence and rule agreement
        if final_confidence > 0.8 and signal_counts[final_signal_type] >= 3:
            strength = SignalStrength.VERY_STRONG
        elif final_confidence > 0.7 and signal_counts[final_signal_type] >= 2:
            strength = SignalStrength.STRONG
        elif final_confidence > 0.6:
            strength = SignalStrength.MODERATE
        else:
            strength = SignalStrength.WEAK
        
        # Create final signal
        signal = TradingSignal(
            symbol=symbol,
            signal_type=final_signal_type,
            strength=strength,
            price=market_data.get('price', 0),
            timestamp=datetime.now(),
            confidence=final_confidence,
            reasoning="; ".join(reasoning_list),
            indicators=self._extract_indicators(market_data),
            risk_level=self._assess_risk_level(market_data)
        )
        
        return signal
    
    def _extract_indicators(self, market_data: Dict) -> Dict[str, float]:
        """Extract key indicators from market data"""
        indicators = {}
        
        # Moving averages
        for period in [12, 20, 26, 50]:
            if f'sma_{period}' in market_data:
                indicators[f'sma_{period}'] = market_data[f'sma_{period}']
            if f'ema_{period}' in market_data:
                indicators[f'ema_{period}'] = market_data[f'ema_{period}']
        
        # Volume
        if 'volume' in market_data:
            indicators['volume'] = market_data['volume']
        if 'avg_volume_20' in market_data:
            indicators['avg_volume_20'] = market_data['avg_volume_20']
        
        # RSI
        if 'rsi_14' in market_data:
            indicators['rsi_14'] = market_data['rsi_14']
        
        # Volatility
        if 'volatility_20' in market_data:
            indicators['volatility_20'] = market_data['volatility_20']
        
        return indicators
    
    def _assess_risk_level(self, market_data: Dict) -> str:
        """Assess overall risk level"""
        volatility = market_data.get('volatility_20', 0)
        
        if volatility > 0.05:
            return "HIGH"
        elif volatility > 0.03:
            return "MEDIUM"
        else:
            return "LOW"
    
    def get_rule_summary(self) -> Dict:
        """Get summary of all rules"""
        return {
            'total_rules': len(self.rules),
            'enabled_rules': len([r for r in self.rules.values() if r.enabled]),
            'rules': [
                {
                    'name': rule.name,
                    'type': rule.rule_type.value,
                    'enabled': rule.enabled,
                    'weight': rule.weight
                }
                for rule in self.rules.values()
            ]
        } 