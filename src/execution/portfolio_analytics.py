"""
Portfolio Analytics Module
Advanced portfolio analysis and performance metrics for the AI-Driven Stock Trade Advisor.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class RiskMetric(Enum):
    """Risk metrics enumeration."""
    SHARPE_RATIO = "sharpe_ratio"
    SORTINO_RATIO = "sortino_ratio"
    MAX_DRAWDOWN = "max_drawdown"
    VAR_95 = "var_95"
    CVAR_95 = "cvar_95"
    BETA = "beta"
    ALPHA = "alpha"
    VOLATILITY = "volatility"


@dataclass
class PortfolioMetrics:
    """Portfolio performance metrics container."""
    total_return: float
    annualized_return: float
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    var_95: float
    cvar_95: float
    beta: float
    alpha: float
    win_rate: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    max_consecutive_wins: int
    max_consecutive_losses: int
    calmar_ratio: float
    information_ratio: float


class PortfolioAnalytics:
    """
    Advanced portfolio analytics and performance analysis.
    
    Provides comprehensive portfolio metrics including risk analysis,
    performance attribution, and statistical measures.
    """
    
    def __init__(self, risk_free_rate: float = 0.02):
        """
        Initialize portfolio analytics.
        
        Args:
            risk_free_rate: Annual risk-free rate (default: 2%)
        """
        self.risk_free_rate = risk_free_rate
        self.logger = logging.getLogger(__name__)
        
    def calculate_portfolio_metrics(self, 
                                  returns: pd.Series,
                                  benchmark_returns: Optional[pd.Series] = None) -> PortfolioMetrics:
        """
        Calculate comprehensive portfolio performance metrics.
        
        Args:
            returns: Portfolio returns series
            benchmark_returns: Benchmark returns series for relative metrics
            
        Returns:
            PortfolioMetrics object with all calculated metrics
        """
        try:
            # Basic return metrics
            total_return = (1 + returns).prod() - 1
            annualized_return = self._calculate_annualized_return(returns)
            volatility = returns.std() * np.sqrt(252)  # Annualized volatility
            
            # Risk-adjusted metrics
            sharpe_ratio = self._calculate_sharpe_ratio(returns)
            sortino_ratio = self._calculate_sortino_ratio(returns)
            max_drawdown = self._calculate_max_drawdown(returns)
            
            # Risk metrics
            var_95 = self._calculate_var(returns, 0.05)
            cvar_95 = self._calculate_cvar(returns, 0.05)
            
            # Relative metrics (if benchmark provided)
            beta = 1.0
            alpha = 0.0
            if benchmark_returns is not None:
                beta = self._calculate_beta(returns, benchmark_returns)
                alpha = self._calculate_alpha(returns, benchmark_returns, beta)
            
            # Trading metrics
            win_rate, profit_factor, avg_win, avg_loss = self._calculate_trading_metrics(returns)
            max_consecutive_wins, max_consecutive_losses = self._calculate_consecutive_trades(returns)
            
            # Additional ratios
            calmar_ratio = self._calculate_calmar_ratio(annualized_return, max_drawdown)
            information_ratio = self._calculate_information_ratio(returns, benchmark_returns) if benchmark_returns is not None else 0.0
            
            return PortfolioMetrics(
                total_return=total_return,
                annualized_return=annualized_return,
                volatility=volatility,
                sharpe_ratio=sharpe_ratio,
                sortino_ratio=sortino_ratio,
                max_drawdown=max_drawdown,
                var_95=var_95,
                cvar_95=cvar_95,
                beta=beta,
                alpha=alpha,
                win_rate=win_rate,
                profit_factor=profit_factor,
                avg_win=avg_win,
                avg_loss=avg_loss,
                max_consecutive_wins=max_consecutive_wins,
                max_consecutive_losses=max_consecutive_losses,
                calmar_ratio=calmar_ratio,
                information_ratio=information_ratio
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating portfolio metrics: {e}")
            raise
    
    def _calculate_annualized_return(self, returns: pd.Series) -> float:
        """Calculate annualized return."""
        total_days = len(returns)
        total_return = (1 + returns).prod() - 1
        return (1 + total_return) ** (252 / total_days) - 1
    
    def _calculate_sharpe_ratio(self, returns: pd.Series) -> float:
        """Calculate Sharpe ratio."""
        excess_returns = returns - self.risk_free_rate / 252
        if returns.std() == 0:
            return 0.0
        return excess_returns.mean() / returns.std() * np.sqrt(252)
    
    def _calculate_sortino_ratio(self, returns: pd.Series) -> float:
        """Calculate Sortino ratio."""
        excess_returns = returns - self.risk_free_rate / 252
        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0.0
        return excess_returns.mean() / downside_returns.std() * np.sqrt(252)
    
    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """Calculate maximum drawdown."""
        cumulative_returns = (1 + returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        return drawdown.min()
    
    def _calculate_var(self, returns: pd.Series, confidence_level: float) -> float:
        """Calculate Value at Risk."""
        return np.percentile(returns, confidence_level * 100)
    
    def _calculate_cvar(self, returns: pd.Series, confidence_level: float) -> float:
        """Calculate Conditional Value at Risk (Expected Shortfall)."""
        var = self._calculate_var(returns, confidence_level)
        return returns[returns <= var].mean()
    
    def _calculate_beta(self, returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """Calculate beta relative to benchmark."""
        covariance = returns.cov(benchmark_returns)
        benchmark_variance = benchmark_returns.var()
        return covariance / benchmark_variance if benchmark_variance != 0 else 1.0
    
    def _calculate_alpha(self, returns: pd.Series, benchmark_returns: pd.Series, beta: float) -> float:
        """Calculate alpha relative to benchmark."""
        return returns.mean() - beta * benchmark_returns.mean()
    
    def _calculate_trading_metrics(self, returns: pd.Series) -> Tuple[float, float, float, float]:
        """Calculate trading performance metrics."""
        positive_returns = returns[returns > 0]
        negative_returns = returns[returns < 0]
        
        win_rate = len(positive_returns) / len(returns) if len(returns) > 0 else 0.0
        profit_factor = abs(positive_returns.sum() / negative_returns.sum()) if negative_returns.sum() != 0 else float('inf')
        avg_win = positive_returns.mean() if len(positive_returns) > 0 else 0.0
        avg_loss = negative_returns.mean() if len(negative_returns) > 0 else 0.0
        
        return win_rate, profit_factor, avg_win, avg_loss
    
    def _calculate_consecutive_trades(self, returns: pd.Series) -> Tuple[int, int]:
        """Calculate maximum consecutive wins and losses."""
        wins = returns > 0
        losses = returns < 0
        
        max_consecutive_wins = self._max_consecutive_ones(wins)
        max_consecutive_losses = self._max_consecutive_ones(losses)
        
        return max_consecutive_wins, max_consecutive_losses
    
    def _max_consecutive_ones(self, series: pd.Series) -> int:
        """Calculate maximum consecutive True values."""
        max_count = 0
        current_count = 0
        
        for value in series:
            if value:
                current_count += 1
                max_count = max(max_count, current_count)
            else:
                current_count = 0
                
        return max_count
    
    def _calculate_calmar_ratio(self, annualized_return: float, max_drawdown: float) -> float:
        """Calculate Calmar ratio."""
        return annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0.0
    
    def _calculate_information_ratio(self, returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """Calculate information ratio."""
        active_returns = returns - benchmark_returns
        tracking_error = active_returns.std()
        return active_returns.mean() / tracking_error if tracking_error != 0 else 0.0
    
    def generate_performance_report(self, metrics: PortfolioMetrics) -> Dict[str, any]:
        """
        Generate comprehensive performance report.
        
        Args:
            metrics: PortfolioMetrics object
            
        Returns:
            Dictionary containing formatted performance report
        """
        return {
            "summary": {
                "total_return": f"{metrics.total_return:.2%}",
                "annualized_return": f"{metrics.annualized_return:.2%}",
                "volatility": f"{metrics.volatility:.2%}",
                "max_drawdown": f"{metrics.max_drawdown:.2%}"
            },
            "risk_metrics": {
                "sharpe_ratio": f"{metrics.sharpe_ratio:.3f}",
                "sortino_ratio": f"{metrics.sortino_ratio:.3f}",
                "calmar_ratio": f"{metrics.calmar_ratio:.3f}",
                "var_95": f"{metrics.var_95:.2%}",
                "cvar_95": f"{metrics.cvar_95:.2%}"
            },
            "relative_metrics": {
                "beta": f"{metrics.beta:.3f}",
                "alpha": f"{metrics.alpha:.2%}",
                "information_ratio": f"{metrics.information_ratio:.3f}"
            },
            "trading_metrics": {
                "win_rate": f"{metrics.win_rate:.2%}",
                "profit_factor": f"{metrics.profit_factor:.3f}",
                "avg_win": f"{metrics.avg_win:.2%}",
                "avg_loss": f"{metrics.avg_loss:.2%}",
                "max_consecutive_wins": metrics.max_consecutive_wins,
                "max_consecutive_losses": metrics.max_consecutive_losses
            }
        }
    
    def calculate_rolling_metrics(self, 
                                returns: pd.Series, 
                                window: int = 252) -> pd.DataFrame:
        """
        Calculate rolling portfolio metrics.
        
        Args:
            returns: Portfolio returns series
            window: Rolling window size in days
            
        Returns:
            DataFrame with rolling metrics
        """
        rolling_metrics = pd.DataFrame()
        
        rolling_metrics['rolling_return'] = returns.rolling(window).apply(
            lambda x: (1 + x).prod() - 1
        )
        rolling_metrics['rolling_volatility'] = returns.rolling(window).std() * np.sqrt(252)
        rolling_metrics['rolling_sharpe'] = returns.rolling(window).apply(
            lambda x: self._calculate_sharpe_ratio(x)
        )
        rolling_metrics['rolling_max_drawdown'] = returns.rolling(window).apply(
            lambda x: self._calculate_max_drawdown(x)
        )
        
        return rolling_metrics 