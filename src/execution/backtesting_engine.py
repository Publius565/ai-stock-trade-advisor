"""
Backtesting Engine
Historical strategy testing framework for the AI-Driven Stock Trade Advisor.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Callable, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from enum import Enum

from .portfolio_analytics import PortfolioAnalytics, PortfolioMetrics
from .risk_manager import RiskManager, RiskLevel, PositionRisk, PortfolioRisk

logger = logging.getLogger(__name__)


class OrderType(Enum):
    """Order types for backtesting."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


@dataclass
class BacktestOrder:
    """Backtest order representation."""
    symbol: str
    order_type: OrderType
    side: str  # "buy" or "sell"
    quantity: int
    price: float
    timestamp: datetime
    filled: bool = False
    fill_price: Optional[float] = None
    fill_timestamp: Optional[datetime] = None
    commission: float = 0.0


@dataclass
class BacktestPosition:
    """Backtest position representation."""
    symbol: str
    quantity: int
    entry_price: float
    entry_timestamp: datetime
    current_price: float
    unrealized_pnl: float
    realized_pnl: float = 0.0
    total_pnl: float = 0.0


@dataclass
class BacktestResult:
    """Backtest results container."""
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_return: float
    annualized_return: float
    max_drawdown: float
    sharpe_ratio: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    equity_curve: pd.Series
    trade_history: List[Dict[str, Any]]
    portfolio_metrics: PortfolioMetrics


class BacktestingEngine:
    """
    Comprehensive backtesting engine for strategy validation.
    
    Provides historical strategy testing with realistic market conditions,
    transaction costs, and comprehensive performance analysis.
    """
    
    def __init__(self,
                 initial_capital: float = 100000.0,
                 commission_rate: float = 0.005,
                 slippage_rate: float = 0.001,
                 risk_level: RiskLevel = RiskLevel.MODERATE):
        """
        Initialize backtesting engine.
        
        Args:
            initial_capital: Starting capital
            commission_rate: Commission rate per trade (default: 0.5%)
            slippage_rate: Slippage rate per trade (default: 0.1%)
            risk_level: Risk tolerance level
        """
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        self.risk_level = risk_level
        
        # Initialize components
        self.portfolio_analytics = PortfolioAnalytics()
        self.risk_manager = RiskManager(risk_level=risk_level)
        
        # Backtest state
        self.current_capital = initial_capital
        self.positions: Dict[str, BacktestPosition] = {}
        self.orders: List[BacktestOrder] = []
        self.trade_history: List[Dict[str, Any]] = []
        self.equity_curve: List[float] = []
        self.equity_dates: List[datetime] = []
        
        self.logger = logging.getLogger(__name__)
    
    def run_backtest(self,
                    strategy_function: Callable,
                    market_data: Dict[str, pd.DataFrame],
                    start_date: datetime,
                    end_date: datetime,
                    **strategy_params) -> BacktestResult:
        """
        Run backtest with given strategy and market data.
        
        Args:
            strategy_function: Function that generates trading signals
            market_data: Dictionary of market data DataFrames by symbol
            start_date: Backtest start date
            end_date: Backtest end date
            **strategy_params: Additional parameters for strategy function
            
        Returns:
            BacktestResult object with comprehensive results
        """
        try:
            self.logger.info(f"Starting backtest from {start_date} to {end_date}")
            
            # Reset backtest state
            self._reset_backtest_state()
            
            # Get all trading dates
            trading_dates = self._get_trading_dates(market_data, start_date, end_date)
            
            # Run backtest day by day
            for current_date in trading_dates:
                self._process_day(current_date, strategy_function, market_data, **strategy_params)
                self._update_equity_curve(current_date)
            
            # Calculate final results
            return self._calculate_backtest_results(start_date, end_date)
            
        except Exception as e:
            self.logger.error(f"Error running backtest: {e}")
            raise
    
    def _reset_backtest_state(self):
        """Reset backtest state for new run."""
        self.current_capital = self.initial_capital
        self.positions = {}
        self.orders = []
        self.trade_history = []
        self.equity_curve = []
        self.equity_dates = []
    
    def _get_trading_dates(self,
                          market_data: Dict[str, pd.DataFrame],
                          start_date: datetime,
                          end_date: datetime) -> List[datetime]:
        """Get sorted list of trading dates."""
        all_dates = set()
        for symbol, data in market_data.items():
            if 'date' in data.columns:
                symbol_dates = data[(data['date'] >= start_date) & (data['date'] <= end_date)]['date']
                all_dates.update(symbol_dates)
        
        return sorted(list(all_dates))
    
    def _process_day(self,
                    current_date: datetime,
                    strategy_function: Callable,
                    market_data: Dict[str, pd.DataFrame],
                    **strategy_params):
        """Process a single trading day."""
        # Update current prices
        self._update_positions(current_date, market_data)
        
        # Generate strategy signals
        signals = strategy_function(current_date, market_data, self.positions, **strategy_params)
        
        # Execute signals
        if signals:
            self._execute_signals(signals, current_date, market_data)
        
        # Process pending orders
        self._process_orders(current_date, market_data)
    
    def _update_positions(self, current_date: datetime, market_data: Dict[str, pd.DataFrame]):
        """Update position prices and P&L."""
        for symbol, position in self.positions.items():
            if symbol in market_data:
                data = market_data[symbol]
                current_data = data[data['date'] == current_date]
                
                if not current_data.empty:
                    current_price = current_data.iloc[0]['close']
                    position.current_price = current_price
                    position.unrealized_pnl = (current_price - position.entry_price) * position.quantity
                    position.total_pnl = position.realized_pnl + position.unrealized_pnl
    
    def _execute_signals(self,
                        signals: List[Dict[str, Any]],
                        current_date: datetime,
                        market_data: Dict[str, pd.DataFrame]):
        """Execute trading signals."""
        for signal in signals:
            symbol = signal.get('symbol')
            action = signal.get('action')  # 'buy' or 'sell'
            quantity = signal.get('quantity')
            price = signal.get('price')
            
            if not all([symbol, action, quantity, price]):
                continue
            
            # Create order
            order = BacktestOrder(
                symbol=symbol,
                order_type=OrderType.MARKET,
                side=action,
                quantity=quantity,
                price=price,
                timestamp=current_date
            )
            
            # Check if order can be filled
            if self._can_fill_order(order):
                self._fill_order(order, current_date, market_data)
    
    def _can_fill_order(self, order: BacktestOrder) -> bool:
        """Check if order can be filled."""
        if order.side == "buy":
            required_capital = order.quantity * order.price * (1 + self.commission_rate + self.slippage_rate)
            return self.current_capital >= required_capital
        elif order.side == "sell":
            return order.symbol in self.positions and self.positions[order.symbol].quantity >= order.quantity
        
        return False
    
    def _fill_order(self,
                   order: BacktestOrder,
                   current_date: datetime,
                   market_data: Dict[str, pd.DataFrame]):
        """Fill an order and update positions."""
        # Calculate fill price with slippage
        if order.side == "buy":
            fill_price = order.price * (1 + self.slippage_rate)
        else:
            fill_price = order.price * (1 - self.slippage_rate)
        
        # Calculate commission
        commission = order.quantity * fill_price * self.commission_rate
        
        # Update capital
        if order.side == "buy":
            total_cost = order.quantity * fill_price + commission
            self.current_capital -= total_cost
        else:
            total_proceeds = order.quantity * fill_price - commission
            self.current_capital += total_proceeds
        
        # Update positions
        self._update_position_from_order(order, fill_price, current_date)
        
        # Record trade
        self._record_trade(order, fill_price, commission, current_date)
        
        # Mark order as filled
        order.filled = True
        order.fill_price = fill_price
        order.fill_timestamp = current_date
        order.commission = commission
    
    def _update_position_from_order(self,
                                   order: BacktestOrder,
                                   fill_price: float,
                                   current_date: datetime):
        """Update position based on filled order."""
        symbol = order.symbol
        
        if order.side == "buy":
            if symbol in self.positions:
                # Add to existing position
                position = self.positions[symbol]
                total_quantity = position.quantity + order.quantity
                total_cost = (position.quantity * position.entry_price + 
                             order.quantity * fill_price)
                position.entry_price = total_cost / total_quantity
                position.quantity = total_quantity
            else:
                # Create new position
                self.positions[symbol] = BacktestPosition(
                    symbol=symbol,
                    quantity=order.quantity,
                    entry_price=fill_price,
                    entry_timestamp=current_date,
                    current_price=fill_price,
                    unrealized_pnl=0.0
                )
        
        elif order.side == "sell":
            if symbol in self.positions:
                position = self.positions[symbol]
                
                # Calculate realized P&L
                realized_pnl = (fill_price - position.entry_price) * order.quantity
                position.realized_pnl += realized_pnl
                
                # Update quantity
                position.quantity -= order.quantity
                
                # Remove position if quantity is zero
                if position.quantity <= 0:
                    del self.positions[symbol]
    
    def _record_trade(self,
                     order: BacktestOrder,
                     fill_price: float,
                     commission: float,
                     current_date: datetime):
        """Record trade in history."""
        trade = {
            'timestamp': current_date,
            'symbol': order.symbol,
            'side': order.side,
            'quantity': order.quantity,
            'fill_price': fill_price,
            'commission': commission,
            'total_cost': order.quantity * fill_price + commission if order.side == "buy" else order.quantity * fill_price - commission
        }
        
        self.trade_history.append(trade)
    
    def _process_orders(self, current_date: datetime, market_data: Dict[str, pd.DataFrame]):
        """Process pending orders (for limit/stop orders)."""
        # This is a simplified implementation
        # In a full implementation, you would check limit/stop conditions
        pass
    
    def _update_equity_curve(self, current_date: datetime):
        """Update equity curve with current portfolio value."""
        total_value = self.current_capital
        
        for position in self.positions.values():
            total_value += position.quantity * position.current_price
        
        self.equity_curve.append(total_value)
        self.equity_dates.append(current_date)
    
    def _calculate_backtest_results(self, start_date: datetime, end_date: datetime) -> BacktestResult:
        """Calculate comprehensive backtest results."""
        # Calculate returns
        equity_series = pd.Series(self.equity_curve, index=self.equity_dates)
        returns = equity_series.pct_change().dropna()
        
        # Calculate portfolio metrics
        portfolio_metrics = self.portfolio_analytics.calculate_portfolio_metrics(returns)
        
        # Calculate trade statistics
        total_trades = len(self.trade_history)
        winning_trades = len([t for t in self.trade_history if t['side'] == 'sell' and t['fill_price'] > 0])
        losing_trades = total_trades - winning_trades
        win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
        
        # Calculate average win/loss
        buy_trades = [t for t in self.trade_history if t['side'] == 'buy']
        sell_trades = [t for t in self.trade_history if t['side'] == 'sell']
        
        avg_win = 0.0
        avg_loss = 0.0
        profit_factor = 0.0
        
        if buy_trades and sell_trades:
            # Match buy and sell trades to calculate P&L
            trades_pnl = []
            for i in range(min(len(buy_trades), len(sell_trades))):
                buy_trade = buy_trades[i]
                sell_trade = sell_trades[i]
                pnl = (sell_trade['fill_price'] - buy_trade['fill_price']) * buy_trade['quantity']
                trades_pnl.append(pnl)
            
            if trades_pnl:
                winning_pnls = [pnl for pnl in trades_pnl if pnl > 0]
                losing_pnls = [pnl for pnl in trades_pnl if pnl < 0]
                
                avg_win = np.mean(winning_pnls) if winning_pnls else 0.0
                avg_loss = abs(np.mean(losing_pnls)) if losing_pnls else 0.0
                profit_factor = sum(winning_pnls) / abs(sum(losing_pnls)) if losing_pnls else float('inf')
        
        return BacktestResult(
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.initial_capital,
            final_capital=equity_series.iloc[-1] if len(equity_series) > 0 else self.initial_capital,
            total_return=portfolio_metrics.total_return,
            annualized_return=portfolio_metrics.annualized_return,
            max_drawdown=portfolio_metrics.max_drawdown,
            sharpe_ratio=portfolio_metrics.sharpe_ratio,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            equity_curve=equity_series,
            trade_history=self.trade_history,
            portfolio_metrics=portfolio_metrics
        )
    
    def generate_backtest_report(self, result: BacktestResult) -> Dict[str, Any]:
        """
        Generate comprehensive backtest report.
        
        Args:
            result: BacktestResult object
            
        Returns:
            Dictionary with formatted backtest report
        """
        return {
            "summary": {
                "start_date": result.start_date.strftime("%Y-%m-%d"),
                "end_date": result.end_date.strftime("%Y-%m-%d"),
                "initial_capital": f"${result.initial_capital:,.2f}",
                "final_capital": f"${result.final_capital:,.2f}",
                "total_return": f"{result.total_return:.2%}",
                "annualized_return": f"{result.annualized_return:.2%}"
            },
            "risk_metrics": {
                "max_drawdown": f"{result.max_drawdown:.2%}",
                "sharpe_ratio": f"{result.sharpe_ratio:.3f}",
                "volatility": f"{result.portfolio_metrics.volatility:.2%}"
            },
            "trading_metrics": {
                "total_trades": result.total_trades,
                "winning_trades": result.winning_trades,
                "losing_trades": result.losing_trades,
                "win_rate": f"{result.win_rate:.2%}",
                "avg_win": f"${result.avg_win:,.2f}",
                "avg_loss": f"${result.avg_loss:,.2f}",
                "profit_factor": f"{result.profit_factor:.3f}"
            },
            "portfolio_metrics": self.portfolio_analytics.generate_performance_report(result.portfolio_metrics)
        } 