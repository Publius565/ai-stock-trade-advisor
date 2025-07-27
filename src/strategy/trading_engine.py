"""
Trading Engine - Core orchestration for rule-based expert system
Handles trading decisions, signal processing, and portfolio management
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ..utils.database_manager import DatabaseManager
from ..data_layer.market_data import MarketDataManager
from ..profile.profile_manager import ProfileManager


class SignalType(Enum):
    """Trading signal types"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    STRONG_BUY = "STRONG_BUY"
    STRONG_SELL = "STRONG_SELL"


class SignalStrength(Enum):
    """Signal strength levels"""
    WEAK = 1
    MODERATE = 2
    STRONG = 3
    VERY_STRONG = 4


@dataclass
class TradingSignal:
    """Trading signal data structure"""
    symbol: str
    signal_type: SignalType
    strength: SignalStrength
    price: float
    timestamp: datetime
    confidence: float  # 0.0 to 1.0
    reasoning: str
    indicators: Dict[str, float]
    risk_level: str


@dataclass
class PortfolioPosition:
    """Portfolio position tracking"""
    symbol: str
    shares: int
    avg_price: float
    current_price: float
    unrealized_pnl: float
    entry_date: datetime
    last_updated: datetime


class TradingEngine:
    """
    Core trading engine that orchestrates the rule-based expert system
    """
    
    def __init__(self, db_manager: DatabaseManager, profile_manager: ProfileManager):
        self.db_manager = db_manager
        self.profile_manager = profile_manager
        cache_dir = getattr(db_manager, 'get_cache_dir', lambda: "data/cache")()
        self.market_data_manager = MarketDataManager(cache_dir)
        self.logger = logging.getLogger(__name__)
        
        # Trading state
        self.active_signals: Dict[str, TradingSignal] = {}
        self.portfolio_positions: Dict[str, PortfolioPosition] = {}
        self.trading_enabled = False
        self.max_positions = 10
        self.max_risk_per_trade = 0.02  # 2% max risk per trade
        
        self.logger.info("Trading Engine initialized")
    
    def enable_trading(self, enabled: bool = True) -> None:
        """Enable or disable trading operations"""
        self.trading_enabled = enabled
        self.logger.info(f"Trading {'enabled' if enabled else 'disabled'}")
    
    def set_risk_parameters(self, max_positions: int, max_risk_per_trade: float) -> None:
        """Set risk management parameters"""
        self.max_positions = max_positions
        self.max_risk_per_trade = max_risk_per_trade
        self.logger.info(f"Risk parameters updated: max_positions={max_positions}, max_risk={max_risk_per_trade}")
    
    def generate_signals(self, symbols: List[str]) -> List[TradingSignal]:
        """
        Generate trading signals for given symbols
        """
        signals = []
        
        for symbol in symbols:
            try:
                # Get market data
                market_data = self.market_data_manager.get_market_data(symbol)
                if not market_data:
                    continue
                
                # Generate signal using rules engine
                signal = self._apply_trading_rules(symbol, market_data)
                if signal:
                    signals.append(signal)
                    self.active_signals[symbol] = signal
                    
            except Exception as e:
                self.logger.error(f"Error generating signal for {symbol}: {e}")
        
        self.logger.info(f"Generated {len(signals)} trading signals")
        return signals
    
    def _apply_trading_rules(self, symbol: str, market_data: Dict) -> Optional[TradingSignal]:
        """
        Apply trading rules to generate signals
        Basic implementation - will be enhanced with RulesEngine
        """
        try:
            # Basic moving average crossover rule
            current_price = market_data.get('price', 0)
            sma_20 = market_data.get('sma_20', 0)
            sma_50 = market_data.get('sma_50', 0)
            volume = market_data.get('volume', 0)
            avg_volume = market_data.get('avg_volume', 0)
            
            if not all([current_price, sma_20, sma_50]):
                return None
            
            # Simple moving average crossover
            signal_type = SignalType.HOLD
            strength = SignalStrength.WEAK
            confidence = 0.5
            reasoning = []
            
            # Price above both moving averages - bullish
            if current_price > sma_20 > sma_50:
                signal_type = SignalType.BUY
                strength = SignalStrength.MODERATE
                confidence = 0.7
                reasoning.append("Price above both moving averages")
            
            # Price below both moving averages - bearish
            elif current_price < sma_20 < sma_50:
                signal_type = SignalType.SELL
                strength = SignalStrength.MODERATE
                confidence = 0.7
                reasoning.append("Price below both moving averages")
            
            # Volume confirmation
            if volume > avg_volume * 1.5:
                strength = SignalStrength.STRONG
                confidence += 0.1
                reasoning.append("High volume confirmation")
            
            # Create signal
            signal = TradingSignal(
                symbol=symbol,
                signal_type=signal_type,
                strength=strength,
                price=current_price,
                timestamp=datetime.now(),
                confidence=min(confidence, 1.0),
                reasoning="; ".join(reasoning),
                indicators={
                    'sma_20': sma_20,
                    'sma_50': sma_50,
                    'volume': volume,
                    'avg_volume': avg_volume
                },
                risk_level=self._assess_risk_level(symbol, market_data)
            )
            
            return signal
            
        except Exception as e:
            self.logger.error(f"Error applying trading rules for {symbol}: {e}")
            return None
    
    def _assess_risk_level(self, symbol: str, market_data: Dict) -> str:
        """Assess risk level for a symbol"""
        volatility = market_data.get('volatility', 0)
        
        if volatility > 0.05:  # 5% daily volatility
            return "HIGH"
        elif volatility > 0.03:  # 3% daily volatility
            return "MEDIUM"
        else:
            return "LOW"
    
    def process_signals(self, signals: List[TradingSignal]) -> List[Dict]:
        """
        Process trading signals and generate trade recommendations
        """
        recommendations = []
        
        for signal in signals:
            if signal.signal_type == SignalType.HOLD:
                continue
                
            # Check if we should act on this signal
            should_trade = self._should_execute_signal(signal)
            
            if should_trade:
                recommendation = {
                    'symbol': signal.symbol,
                    'action': signal.signal_type.value,
                    'price': signal.price,
                    'confidence': signal.confidence,
                    'reasoning': signal.reasoning,
                    'risk_level': signal.risk_level,
                    'timestamp': signal.timestamp.isoformat()
                }
                recommendations.append(recommendation)
        
        self.logger.info(f"Generated {len(recommendations)} trade recommendations")
        return recommendations
    
    def _should_execute_signal(self, signal: TradingSignal) -> bool:
        """
        Determine if a signal should be executed based on risk management
        """
        # Check if trading is enabled
        if not self.trading_enabled:
            return False
        
        # Check confidence threshold
        if signal.confidence < 0.6:
            return False
        
        # Check if we already have a position
        if signal.symbol in self.portfolio_positions:
            return False
        
        # Check position limit
        if len(self.portfolio_positions) >= self.max_positions:
            return False
        
        # Check risk level against user profile
        user_profile = self.profile_manager.get_current_profile()
        if user_profile:
            risk_tolerance = user_profile.get('risk_tolerance', 'MODERATE')
            if signal.risk_level == "HIGH" and risk_tolerance == "CONSERVATIVE":
                return False
        
        return True
    
    def get_portfolio_summary(self) -> Dict:
        """Get current portfolio summary"""
        total_value = 0
        total_pnl = 0
        position_count = len(self.portfolio_positions)
        
        for position in self.portfolio_positions.values():
            position_value = position.shares * position.current_price
            total_value += position_value
            total_pnl += position.unrealized_pnl
        
        return {
            'total_positions': position_count,
            'total_value': total_value,
            'total_unrealized_pnl': total_pnl,
            'max_positions': self.max_positions,
            'trading_enabled': self.trading_enabled
        }
    
    def get_active_signals(self) -> List[Dict]:
        """Get currently active trading signals"""
        return [
            {
                'symbol': signal.symbol,
                'type': signal.signal_type.value,
                'strength': signal.strength.value,
                'price': signal.price,
                'confidence': signal.confidence,
                'timestamp': signal.timestamp.isoformat()
            }
            for signal in self.active_signals.values()
        ] 