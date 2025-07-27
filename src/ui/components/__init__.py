"""
UI Components Package

Contains modular UI components for the AI-Driven Stock Trade Advisor.
"""

from .profile_tab import ProfileTab
from .market_scanner_tab import MarketScannerTab
from .watchlist_tab import WatchlistTab
from .dashboard_tab import DashboardTab
from .ml_predictions_tab import MLPredictionsTab
from .trading_signals_tab import TradingSignalsTab
from .execution_tab import ExecutionTab
from .positions_tab import PositionsTab
from .performance_tab import PerformanceTab

__all__ = [
    'ProfileTab',
    'MarketScannerTab', 
    'WatchlistTab',
    'DashboardTab',
    'MLPredictionsTab',
    'TradingSignalsTab',
    'ExecutionTab',
    'PositionsTab',
    'PerformanceTab'
] 