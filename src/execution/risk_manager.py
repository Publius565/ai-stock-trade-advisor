"""
Risk Management System
Advanced risk management for the AI-Driven Stock Trade Advisor.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk tolerance levels."""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


@dataclass
class PositionRisk:
    """Position risk metrics."""
    symbol: str
    current_price: float
    position_size: int
    position_value: float
    unrealized_pnl: float
    stop_loss_price: float
    take_profit_price: float
    risk_per_share: float
    total_risk: float
    risk_percentage: float
    max_position_size: int
    suggested_position_size: int


@dataclass
class PortfolioRisk:
    """Portfolio risk metrics."""
    total_portfolio_value: float
    total_unrealized_pnl: float
    total_risk: float
    portfolio_risk_percentage: float
    max_portfolio_risk: float
    current_risk_utilization: float
    largest_position_risk: float
    concentration_risk: float
    correlation_risk: float
    sector_exposure: Dict[str, float]
    position_count: int
    risk_alerts: List[str]


class RiskManager:
    """
    Advanced risk management system.
    
    Provides position sizing, stop-loss management, portfolio risk controls,
    and risk monitoring capabilities.
    """
    
    def __init__(self, 
                 max_portfolio_risk: float = 0.02,
                 max_position_risk: float = 0.01,
                 max_sector_exposure: float = 0.25,
                 risk_level: RiskLevel = RiskLevel.MODERATE):
        """
        Initialize risk manager.
        
        Args:
            max_portfolio_risk: Maximum portfolio risk (default: 2%)
            max_position_risk: Maximum position risk (default: 1%)
            max_sector_exposure: Maximum sector exposure (default: 25%)
            risk_level: Risk tolerance level
        """
        self.max_portfolio_risk = max_portfolio_risk
        self.max_position_risk = max_position_risk
        self.max_sector_exposure = max_sector_exposure
        self.risk_level = risk_level
        self.logger = logging.getLogger(__name__)
        
        # Risk level multipliers
        self.risk_multipliers = {
            RiskLevel.CONSERVATIVE: 0.5,
            RiskLevel.MODERATE: 1.0,
            RiskLevel.AGGRESSIVE: 1.5
        }
        
    def calculate_position_size(self,
                              symbol: str,
                              current_price: float,
                              stop_loss_price: float,
                              portfolio_value: float,
                              volatility: Optional[float] = None) -> int:
        """
        Calculate optimal position size based on risk parameters.
        
        Args:
            symbol: Stock symbol
            current_price: Current stock price
            stop_loss_price: Stop loss price
            portfolio_value: Total portfolio value
            volatility: Stock volatility (optional)
            
        Returns:
            Suggested position size in shares
        """
        try:
            # Calculate risk per share
            risk_per_share = abs(current_price - stop_loss_price)
            
            if risk_per_share <= 0:
                self.logger.warning(f"Invalid stop loss for {symbol}: risk per share is zero")
                return 0
            
            # Calculate maximum risk amount
            max_risk_amount = portfolio_value * self.max_position_risk * self.risk_multipliers[self.risk_level]
            
            # Adjust for volatility if provided
            if volatility is not None:
                volatility_adjustment = min(1.0, 0.2 / volatility)  # Reduce size for high volatility
                max_risk_amount *= volatility_adjustment
            
            # Calculate position size
            position_size = int(max_risk_amount / risk_per_share)
            
            # Ensure minimum position size
            min_position_value = portfolio_value * 0.001  # Minimum 0.1% of portfolio
            min_shares = int(min_position_value / current_price)
            
            if position_size < min_shares:
                position_size = min_shares
            
            # Ensure maximum position size
            max_position_value = portfolio_value * 0.05  # Maximum 5% of portfolio
            max_shares = int(max_position_value / current_price)
            
            if position_size > max_shares:
                position_size = max_shares
            
            self.logger.info(f"Calculated position size for {symbol}: {position_size} shares")
            return position_size
            
        except Exception as e:
            self.logger.error(f"Error calculating position size for {symbol}: {e}")
            return 0
    
    def calculate_stop_loss(self,
                           entry_price: float,
                           atr: float,
                           risk_level: RiskLevel = None) -> float:
        """
        Calculate dynamic stop loss based on ATR.
        
        Args:
            entry_price: Entry price
            atr: Average True Range
            risk_level: Risk level for stop loss calculation
            
        Returns:
            Stop loss price
        """
        if risk_level is None:
            risk_level = self.risk_level
            
        # ATR multiplier based on risk level
        atr_multipliers = {
            RiskLevel.CONSERVATIVE: 1.5,
            RiskLevel.MODERATE: 2.0,
            RiskLevel.AGGRESSIVE: 2.5
        }
        
        atr_multiplier = atr_multipliers[risk_level]
        stop_loss_distance = atr * atr_multiplier
        
        return entry_price - stop_loss_distance
    
    def calculate_take_profit(self,
                             entry_price: float,
                             stop_loss_price: float,
                             risk_reward_ratio: float = 2.0) -> float:
        """
        Calculate take profit based on risk-reward ratio.
        
        Args:
            entry_price: Entry price
            stop_loss_price: Stop loss price
            risk_reward_ratio: Desired risk-reward ratio
            
        Returns:
            Take profit price
        """
        risk_distance = entry_price - stop_loss_price
        reward_distance = risk_distance * risk_reward_ratio
        
        return entry_price + reward_distance
    
    def analyze_position_risk(self,
                             symbol: str,
                             current_price: float,
                             position_size: int,
                             stop_loss_price: float,
                             portfolio_value: float) -> PositionRisk:
        """
        Analyze risk for a specific position.
        
        Args:
            symbol: Stock symbol
            current_price: Current stock price
            position_size: Current position size
            stop_loss_price: Stop loss price
            portfolio_value: Total portfolio value
            
        Returns:
            PositionRisk object with risk metrics
        """
        try:
            position_value = current_price * position_size
            risk_per_share = abs(current_price - stop_loss_price)
            total_risk = risk_per_share * position_size
            risk_percentage = total_risk / portfolio_value
            
            # Calculate unrealized P&L (assuming long position)
            unrealized_pnl = (current_price - stop_loss_price) * position_size
            
            # Calculate take profit
            take_profit_price = self.calculate_take_profit(current_price, stop_loss_price)
            
            # Calculate maximum position size
            max_position_size = self.calculate_position_size(
                symbol, current_price, stop_loss_price, portfolio_value
            )
            
            return PositionRisk(
                symbol=symbol,
                current_price=current_price,
                position_size=position_size,
                position_value=position_value,
                unrealized_pnl=unrealized_pnl,
                stop_loss_price=stop_loss_price,
                take_profit_price=take_profit_price,
                risk_per_share=risk_per_share,
                total_risk=total_risk,
                risk_percentage=risk_percentage,
                max_position_size=max_position_size,
                suggested_position_size=max_position_size
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing position risk for {symbol}: {e}")
            raise
    
    def analyze_portfolio_risk(self,
                              positions: List[PositionRisk],
                              portfolio_value: float,
                              sector_data: Optional[Dict[str, str]] = None) -> PortfolioRisk:
        """
        Analyze overall portfolio risk.
        
        Args:
            positions: List of PositionRisk objects
            portfolio_value: Total portfolio value
            sector_data: Dictionary mapping symbols to sectors
            
        Returns:
            PortfolioRisk object with portfolio risk metrics
        """
        try:
            total_unrealized_pnl = sum(pos.unrealized_pnl for pos in positions)
            total_risk = sum(pos.total_risk for pos in positions)
            portfolio_risk_percentage = total_risk / portfolio_value
            current_risk_utilization = portfolio_risk_percentage / self.max_portfolio_risk
            
            # Calculate largest position risk
            largest_position_risk = max(pos.risk_percentage for pos in positions) if positions else 0.0
            
            # Calculate concentration risk (Herfindahl index)
            position_values = [pos.position_value for pos in positions]
            total_position_value = sum(position_values)
            
            if total_position_value > 0:
                concentration_risk = sum((value / total_position_value) ** 2 for value in position_values)
            else:
                concentration_risk = 0.0
            
            # Calculate sector exposure
            sector_exposure = {}
            if sector_data:
                sector_values = {}
                for pos in positions:
                    sector = sector_data.get(pos.symbol, "Unknown")
                    sector_values[sector] = sector_values.get(sector, 0) + pos.position_value
                
                for sector, value in sector_values.items():
                    sector_exposure[sector] = value / portfolio_value
            
            # Calculate correlation risk (simplified)
            correlation_risk = self._calculate_correlation_risk(positions)
            
            # Generate risk alerts
            risk_alerts = self._generate_risk_alerts(
                portfolio_risk_percentage, largest_position_risk, 
                concentration_risk, sector_exposure
            )
            
            return PortfolioRisk(
                total_portfolio_value=portfolio_value,
                total_unrealized_pnl=total_unrealized_pnl,
                total_risk=total_risk,
                portfolio_risk_percentage=portfolio_risk_percentage,
                max_portfolio_risk=self.max_portfolio_risk,
                current_risk_utilization=current_risk_utilization,
                largest_position_risk=largest_position_risk,
                concentration_risk=concentration_risk,
                correlation_risk=correlation_risk,
                sector_exposure=sector_exposure,
                position_count=len(positions),
                risk_alerts=risk_alerts
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing portfolio risk: {e}")
            raise
    
    def _calculate_correlation_risk(self, positions: List[PositionRisk]) -> float:
        """
        Calculate simplified correlation risk.
        
        Args:
            positions: List of PositionRisk objects
            
        Returns:
            Correlation risk score (0-1)
        """
        if len(positions) <= 1:
            return 0.0
        
        # Simplified correlation risk based on position size distribution
        position_values = [pos.position_value for pos in positions]
        total_value = sum(position_values)
        
        if total_value == 0:
            return 0.0
        
        # Calculate Gini coefficient as a measure of concentration
        sorted_values = sorted(position_values)
        n = len(sorted_values)
        cumsum = np.cumsum(sorted_values)
        gini = (n + 1 - 2 * np.sum(cumsum) / cumsum[-1]) / n
        
        return gini
    
    def _generate_risk_alerts(self,
                             portfolio_risk_percentage: float,
                             largest_position_risk: float,
                             concentration_risk: float,
                             sector_exposure: Dict[str, float]) -> List[str]:
        """
        Generate risk alerts based on portfolio metrics.
        
        Args:
            portfolio_risk_percentage: Portfolio risk percentage
            largest_position_risk: Largest position risk
            concentration_risk: Concentration risk
            sector_exposure: Sector exposure dictionary
            
        Returns:
            List of risk alert messages
        """
        alerts = []
        
        if portfolio_risk_percentage > self.max_portfolio_risk:
            alerts.append(f"Portfolio risk ({portfolio_risk_percentage:.2%}) exceeds maximum ({self.max_portfolio_risk:.2%})")
        
        if largest_position_risk > self.max_position_risk:
            alerts.append(f"Largest position risk ({largest_position_risk:.2%}) exceeds maximum ({self.max_position_risk:.2%})")
        
        if concentration_risk > 0.5:
            alerts.append(f"High portfolio concentration risk ({concentration_risk:.2%})")
        
        for sector, exposure in sector_exposure.items():
            if exposure > self.max_sector_exposure:
                alerts.append(f"Sector {sector} exposure ({exposure:.2%}) exceeds maximum ({self.max_sector_exposure:.2%})")
        
        return alerts
    
    def should_close_position(self,
                             position_risk: PositionRisk,
                             portfolio_risk: PortfolioRisk) -> bool:
        """
        Determine if a position should be closed based on risk metrics.
        
        Args:
            position_risk: PositionRisk object
            portfolio_risk: PortfolioRisk object
            
        Returns:
            True if position should be closed
        """
        # Close if position risk exceeds maximum
        if position_risk.risk_percentage > self.max_position_risk:
            return True
        
        # Close if portfolio risk is too high and this is a large position
        if (portfolio_risk.portfolio_risk_percentage > self.max_portfolio_risk and 
            position_risk.risk_percentage > self.max_position_risk * 0.5):
            return True
        
        # Close if stop loss is hit
        if position_risk.current_price <= position_risk.stop_loss_price:
            return True
        
        return False
    
    def get_risk_summary(self, portfolio_risk: PortfolioRisk) -> Dict[str, any]:
        """
        Generate risk summary report.
        
        Args:
            portfolio_risk: PortfolioRisk object
            
        Returns:
            Dictionary with risk summary
        """
        return {
            "portfolio_risk": {
                "total_risk": f"${portfolio_risk.total_risk:,.2f}",
                "risk_percentage": f"{portfolio_risk.portfolio_risk_percentage:.2%}",
                "max_risk": f"{portfolio_risk.max_portfolio_risk:.2%}",
                "utilization": f"{portfolio_risk.current_risk_utilization:.1%}"
            },
            "concentration_metrics": {
                "largest_position_risk": f"{portfolio_risk.largest_position_risk:.2%}",
                "concentration_risk": f"{portfolio_risk.concentration_risk:.2%}",
                "correlation_risk": f"{portfolio_risk.correlation_risk:.2%}",
                "position_count": portfolio_risk.position_count
            },
            "sector_exposure": portfolio_risk.sector_exposure,
            "risk_alerts": portfolio_risk.risk_alerts,
            "risk_level": self.risk_level.value
        } 