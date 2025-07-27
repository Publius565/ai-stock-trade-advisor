"""
Backtesting Tab
Historical strategy testing and analysis component.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
from typing import Dict, List, Optional, Callable
import logging
from datetime import datetime, timedelta
import numpy as np

from ..execution import BacktestingEngine, BacktestResult, RiskLevel

logger = logging.getLogger(__name__)


class BacktestingTab(ttk.Frame):
    """
    Backtesting Tab Component.
    
    Provides historical strategy testing with comprehensive results analysis
    and performance visualization.
    """
    
    def __init__(self, parent, **kwargs):
        """Initialize the Backtesting Tab."""
        super().__init__(parent, **kwargs)
        self.parent = parent
        
        # Initialize backtesting engine
        self.backtesting_engine = BacktestingEngine()
        
        # Data storage
        self.market_data = {}
        self.backtest_result = None
        self.strategy_function = None
        
        # Create UI components
        self._create_widgets()
        self._setup_layout()
        
        logger.info("Backtesting Tab initialized")
    
    def _create_widgets(self):
        """Create all UI widgets."""
        # Main container
        self.main_frame = ttk.Frame(self)
        
        # Title
        self.title_label = ttk.Label(
            self.main_frame,
            text="Strategy Backtesting",
            font=("Arial", 16, "bold")
        )
        
        # Configuration panel
        self.config_frame = ttk.LabelFrame(self.main_frame, text="Backtest Configuration", padding=10)
        
        # Initial capital
        self.capital_label = ttk.Label(self.config_frame, text="Initial Capital ($):")
        self.capital_var = tk.StringVar(value="100000")
        self.capital_entry = ttk.Entry(self.config_frame, textvariable=self.capital_var, width=15)
        
        # Commission rate
        self.commission_label = ttk.Label(self.config_frame, text="Commission Rate (%):")
        self.commission_var = tk.StringVar(value="0.5")
        self.commission_entry = ttk.Entry(self.config_frame, textvariable=self.commission_var, width=15)
        
        # Slippage rate
        self.slippage_label = ttk.Label(self.config_frame, text="Slippage Rate (%):")
        self.slippage_var = tk.StringVar(value="0.1")
        self.slippage_entry = ttk.Entry(self.config_frame, textvariable=self.slippage_var, width=15)
        
        # Risk level
        self.risk_label = ttk.Label(self.config_frame, text="Risk Level:")
        self.risk_var = tk.StringVar(value="moderate")
        self.risk_combo = ttk.Combobox(
            self.config_frame,
            textvariable=self.risk_var,
            values=["conservative", "moderate", "aggressive"],
            state="readonly",
            width=15
        )
        
        # Date range
        self.date_frame = ttk.LabelFrame(self.config_frame, text="Date Range", padding=5)
        
        self.start_date_label = ttk.Label(self.date_frame, text="Start Date:")
        self.start_date_var = tk.StringVar(value="2024-01-01")
        self.start_date_entry = ttk.Entry(self.date_frame, textvariable=self.start_date_var, width=12)
        
        self.end_date_label = ttk.Label(self.date_frame, text="End Date:")
        self.end_date_var = tk.StringVar(value="2024-12-31")
        self.end_date_entry = ttk.Entry(self.date_frame, textvariable=self.end_date_var, width=12)
        
        # Data loading
        self.data_frame = ttk.LabelFrame(self.main_frame, text="Market Data", padding=10)
        
        self.load_data_button = ttk.Button(
            self.data_frame,
            text="Load Market Data",
            command=self._load_market_data
        )
        
        self.data_status_label = ttk.Label(self.data_frame, text="No data loaded")
        
        # Strategy selection
        self.strategy_frame = ttk.LabelFrame(self.main_frame, text="Strategy", padding=10)
        
        self.strategy_label = ttk.Label(self.strategy_frame, text="Strategy:")
        self.strategy_var = tk.StringVar(value="Simple Moving Average")
        self.strategy_combo = ttk.Combobox(
            self.strategy_frame,
            textvariable=self.strategy_var,
            values=["Simple Moving Average", "RSI Strategy", "MACD Strategy", "Custom Strategy"],
            state="readonly",
            width=20
        )
        self.strategy_combo.bind("<<ComboboxSelected>>", self._on_strategy_change)
        
        # Run backtest button
        self.run_button = ttk.Button(
            self.main_frame,
            text="Run Backtest",
            command=self._run_backtest,
            style="Accent.TButton"
        )
        
        # Results notebook
        self.results_notebook = ttk.Notebook(self.main_frame)
        
        # Summary tab
        self.summary_frame = ttk.Frame(self.results_notebook)
        self._create_summary_widgets()
        
        # Performance tab
        self.performance_frame = ttk.Frame(self.results_notebook)
        self._create_performance_widgets()
        
        # Trades tab
        self.trades_frame = ttk.Frame(self.results_notebook)
        self._create_trades_widgets()
        
        # Equity curve tab
        self.equity_frame = ttk.Frame(self.results_notebook)
        self._create_equity_widgets()
        
        # Add tabs to notebook
        self.results_notebook.add(self.summary_frame, text="Summary")
        self.results_notebook.add(self.performance_frame, text="Performance")
        self.results_notebook.add(self.trades_frame, text="Trades")
        self.results_notebook.add(self.equity_frame, text="Equity Curve")
    
    def _create_summary_widgets(self):
        """Create summary widgets."""
        # Summary metrics
        self.summary_metrics_frame = ttk.LabelFrame(self.summary_frame, text="Summary Metrics", padding=10)
        
        # Total return
        self.total_return_label = ttk.Label(self.summary_metrics_frame, text="Total Return:")
        self.total_return_value = ttk.Label(self.summary_metrics_frame, text="--", font=("Arial", 12, "bold"))
        
        # Annualized return
        self.annual_return_label = ttk.Label(self.summary_metrics_frame, text="Annualized Return:")
        self.annual_return_value = ttk.Label(self.summary_metrics_frame, text="--", font=("Arial", 12, "bold"))
        
        # Final capital
        self.final_capital_label = ttk.Label(self.summary_metrics_frame, text="Final Capital:")
        self.final_capital_value = ttk.Label(self.summary_metrics_frame, text="--", font=("Arial", 12, "bold"))
        
        # Max drawdown
        self.max_drawdown_label = ttk.Label(self.summary_metrics_frame, text="Max Drawdown:")
        self.max_drawdown_value = ttk.Label(self.summary_metrics_frame, text="--", font=("Arial", 12, "bold"))
        
        # Sharpe ratio
        self.sharpe_label = ttk.Label(self.summary_metrics_frame, text="Sharpe Ratio:")
        self.sharpe_value = ttk.Label(self.summary_metrics_frame, text="--", font=("Arial", 12, "bold"))
        
        # Trading statistics
        self.trading_stats_frame = ttk.LabelFrame(self.summary_frame, text="Trading Statistics", padding=10)
        
        # Total trades
        self.total_trades_label = ttk.Label(self.trading_stats_frame, text="Total Trades:")
        self.total_trades_value = ttk.Label(self.trading_stats_frame, text="--", font=("Arial", 12, "bold"))
        
        # Win rate
        self.win_rate_label = ttk.Label(self.trading_stats_frame, text="Win Rate:")
        self.win_rate_value = ttk.Label(self.trading_stats_frame, text="--", font=("Arial", 12, "bold"))
        
        # Profit factor
        self.profit_factor_label = ttk.Label(self.trading_stats_frame, text="Profit Factor:")
        self.profit_factor_value = ttk.Label(self.trading_stats_frame, text="--", font=("Arial", 12, "bold"))
        
        # Average win/loss
        self.avg_win_label = ttk.Label(self.trading_stats_frame, text="Avg Win:")
        self.avg_win_value = ttk.Label(self.trading_stats_frame, text="--", font=("Arial", 12, "bold"))
        
        self.avg_loss_label = ttk.Label(self.trading_stats_frame, text="Avg Loss:")
        self.avg_loss_value = ttk.Label(self.trading_stats_frame, text="--", font=("Arial", 12, "bold"))
    
    def _create_performance_widgets(self):
        """Create performance widgets."""
        # Performance metrics
        self.perf_metrics_frame = ttk.LabelFrame(self.performance_frame, text="Performance Metrics", padding=10)
        
        # Volatility
        self.volatility_label = ttk.Label(self.perf_metrics_frame, text="Volatility:")
        self.volatility_value = ttk.Label(self.perf_metrics_frame, text="--", font=("Arial", 12, "bold"))
        
        # Sortino ratio
        self.sortino_label = ttk.Label(self.perf_metrics_frame, text="Sortino Ratio:")
        self.sortino_value = ttk.Label(self.perf_metrics_frame, text="--", font=("Arial", 12, "bold"))
        
        # Calmar ratio
        self.calmar_label = ttk.Label(self.perf_metrics_frame, text="Calmar Ratio:")
        self.calmar_value = ttk.Label(self.perf_metrics_frame, text="--", font=("Arial", 12, "bold"))
        
        # Information ratio
        self.info_ratio_label = ttk.Label(self.perf_metrics_frame, text="Information Ratio:")
        self.info_ratio_value = ttk.Label(self.perf_metrics_frame, text="--", font=("Arial", 12, "bold"))
        
        # Beta and Alpha
        self.beta_label = ttk.Label(self.perf_metrics_frame, text="Beta:")
        self.beta_value = ttk.Label(self.perf_metrics_frame, text="--", font=("Arial", 12, "bold"))
        
        self.alpha_label = ttk.Label(self.perf_metrics_frame, text="Alpha:")
        self.alpha_value = ttk.Label(self.perf_metrics_frame, text="--", font=("Arial", 12, "bold"))
        
        # Risk metrics
        self.risk_metrics_frame = ttk.LabelFrame(self.performance_frame, text="Risk Metrics", padding=10)
        
        # VaR
        self.var_label = ttk.Label(self.risk_metrics_frame, text="VaR (95%):")
        self.var_value = ttk.Label(self.risk_metrics_frame, text="--", font=("Arial", 12, "bold"))
        
        # CVaR
        self.cvar_label = ttk.Label(self.risk_metrics_frame, text="CVaR (95%):")
        self.cvar_value = ttk.Label(self.risk_metrics_frame, text="--", font=("Arial", 12, "bold"))
        
        # Max consecutive wins/losses
        self.max_wins_label = ttk.Label(self.risk_metrics_frame, text="Max Consecutive Wins:")
        self.max_wins_value = ttk.Label(self.risk_metrics_frame, text="--", font=("Arial", 12, "bold"))
        
        self.max_losses_label = ttk.Label(self.risk_metrics_frame, text="Max Consecutive Losses:")
        self.max_losses_value = ttk.Label(self.risk_metrics_frame, text="--", font=("Arial", 12, "bold"))
    
    def _create_trades_widgets(self):
        """Create trades widgets."""
        # Trades table
        self.trades_frame_inner = ttk.Frame(self.trades_frame)
        
        # Create treeview for trades
        self.trades_tree = ttk.Treeview(
            self.trades_frame_inner,
            columns=("date", "symbol", "side", "quantity", "price", "commission", "total"),
            show="tree headings",
            height=15
        )
        
        # Configure columns
        self.trades_tree.heading("#0", text="Trade #")
        self.trades_tree.heading("date", text="Date")
        self.trades_tree.heading("symbol", text="Symbol")
        self.trades_tree.heading("side", text="Side")
        self.trades_tree.heading("quantity", text="Quantity")
        self.trades_tree.heading("price", text="Price")
        self.trades_tree.heading("commission", text="Commission")
        self.trades_tree.heading("total", text="Total")
        
        self.trades_tree.column("#0", width=80)
        self.trades_tree.column("date", width=100)
        self.trades_tree.column("symbol", width=80)
        self.trades_tree.column("side", width=60)
        self.trades_tree.column("quantity", width=80)
        self.trades_tree.column("price", width=80)
        self.trades_tree.column("commission", width=80)
        self.trades_tree.column("total", width=100)
        
        # Scrollbar
        self.trades_scrollbar = ttk.Scrollbar(self.trades_frame_inner, orient="vertical", command=self.trades_tree.yview)
        self.trades_tree.configure(yscrollcommand=self.trades_scrollbar.set)
    
    def _create_equity_widgets(self):
        """Create equity curve widgets."""
        # Equity curve display
        self.equity_frame_inner = ttk.Frame(self.equity_frame)
        
        # Canvas for equity curve (simplified - would use matplotlib in full implementation)
        self.equity_canvas = tk.Canvas(self.equity_frame_inner, bg="white", height=300)
        
        # Equity curve info
        self.equity_info_frame = ttk.LabelFrame(self.equity_frame_inner, text="Equity Curve Information", padding=10)
        
        self.equity_start_label = ttk.Label(self.equity_info_frame, text="Starting Value:")
        self.equity_start_value = ttk.Label(self.equity_info_frame, text="--", font=("Arial", 12, "bold"))
        
        self.equity_end_label = ttk.Label(self.equity_info_frame, text="Ending Value:")
        self.equity_end_value = ttk.Label(self.equity_info_frame, text="--", font=("Arial", 12, "bold"))
        
        self.equity_peak_label = ttk.Label(self.equity_info_frame, text="Peak Value:")
        self.equity_peak_value = ttk.Label(self.equity_info_frame, text="--", font=("Arial", 12, "bold"))
        
        self.equity_trough_label = ttk.Label(self.equity_info_frame, text="Trough Value:")
        self.equity_trough_value = ttk.Label(self.equity_info_frame, text="--", font=("Arial", 12, "bold"))
    
    def _setup_layout(self):
        """Setup the layout of all widgets."""
        # Main layout
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        self.title_label.pack(pady=(0, 20))
        
        # Configuration panel
        self.config_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Capital and rates row
        self.capital_label.grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.capital_entry.grid(row=0, column=1, padx=5, pady=2)
        
        self.commission_label.grid(row=0, column=2, sticky="w", padx=5, pady=2)
        self.commission_entry.grid(row=0, column=3, padx=5, pady=2)
        
        self.slippage_label.grid(row=0, column=4, sticky="w", padx=5, pady=2)
        self.slippage_entry.grid(row=0, column=5, padx=5, pady=2)
        
        # Risk level row
        self.risk_label.grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.risk_combo.grid(row=1, column=1, padx=5, pady=2)
        
        # Date range
        self.date_frame.grid(row=1, column=2, columnspan=4, padx=20, pady=2)
        
        self.start_date_label.grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.start_date_entry.grid(row=0, column=1, padx=5, pady=2)
        
        self.end_date_label.grid(row=0, column=2, sticky="w", padx=5, pady=2)
        self.end_date_entry.grid(row=0, column=3, padx=5, pady=2)
        
        # Data loading
        self.data_frame.pack(fill=tk.X, pady=(0, 10))
        self.load_data_button.pack(side=tk.LEFT, padx=5)
        self.data_status_label.pack(side=tk.LEFT, padx=20)
        
        # Strategy selection
        self.strategy_frame.pack(fill=tk.X, pady=(0, 10))
        self.strategy_label.pack(side=tk.LEFT, padx=5)
        self.strategy_combo.pack(side=tk.LEFT, padx=5)
        
        # Run button
        self.run_button.pack(pady=10)
        
        # Results notebook
        self.results_notebook.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Setup individual tab layouts
        self._setup_summary_layout()
        self._setup_performance_layout()
        self._setup_trades_layout()
        self._setup_equity_layout()
    
    def _setup_summary_layout(self):
        """Setup summary tab layout."""
        # Summary metrics
        self.summary_metrics_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.total_return_label.grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.total_return_value.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        
        self.annual_return_label.grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.annual_return_value.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        
        self.final_capital_label.grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.final_capital_value.grid(row=2, column=1, sticky="w", padx=5, pady=2)
        
        self.max_drawdown_label.grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.max_drawdown_value.grid(row=3, column=1, sticky="w", padx=5, pady=2)
        
        self.sharpe_label.grid(row=4, column=0, sticky="w", padx=5, pady=2)
        self.sharpe_value.grid(row=4, column=1, sticky="w", padx=5, pady=2)
        
        # Trading statistics
        self.trading_stats_frame.pack(fill=tk.X)
        
        self.total_trades_label.grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.total_trades_value.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        
        self.win_rate_label.grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.win_rate_value.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        
        self.profit_factor_label.grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.profit_factor_value.grid(row=2, column=1, sticky="w", padx=5, pady=2)
        
        self.avg_win_label.grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.avg_win_value.grid(row=3, column=1, sticky="w", padx=5, pady=2)
        
        self.avg_loss_label.grid(row=4, column=0, sticky="w", padx=5, pady=2)
        self.avg_loss_value.grid(row=4, column=1, sticky="w", padx=5, pady=2)
    
    def _setup_performance_layout(self):
        """Setup performance tab layout."""
        # Performance metrics
        self.perf_metrics_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.volatility_label.grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.volatility_value.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        
        self.sortino_label.grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.sortino_value.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        
        self.calmar_label.grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.calmar_value.grid(row=2, column=1, sticky="w", padx=5, pady=2)
        
        self.info_ratio_label.grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.info_ratio_value.grid(row=3, column=1, sticky="w", padx=5, pady=2)
        
        self.beta_label.grid(row=4, column=0, sticky="w", padx=5, pady=2)
        self.beta_value.grid(row=4, column=1, sticky="w", padx=5, pady=2)
        
        self.alpha_label.grid(row=5, column=0, sticky="w", padx=5, pady=2)
        self.alpha_value.grid(row=5, column=1, sticky="w", padx=5, pady=2)
        
        # Risk metrics
        self.risk_metrics_frame.pack(fill=tk.X)
        
        self.var_label.grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.var_value.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        
        self.cvar_label.grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.cvar_value.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        
        self.max_wins_label.grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.max_wins_value.grid(row=2, column=1, sticky="w", padx=5, pady=2)
        
        self.max_losses_label.grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.max_losses_value.grid(row=3, column=1, sticky="w", padx=5, pady=2)
    
    def _setup_trades_layout(self):
        """Setup trades tab layout."""
        self.trades_frame_inner.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.trades_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.trades_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _setup_equity_layout(self):
        """Setup equity tab layout."""
        self.equity_frame_inner.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.equity_canvas.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.equity_info_frame.pack(fill=tk.X)
        
        self.equity_start_label.grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.equity_start_value.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        
        self.equity_end_label.grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.equity_end_value.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        
        self.equity_peak_label.grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.equity_peak_value.grid(row=2, column=1, sticky="w", padx=5, pady=2)
        
        self.equity_trough_label.grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.equity_trough_value.grid(row=3, column=1, sticky="w", padx=5, pady=2)
    
    def _load_market_data(self):
        """Load market data for backtesting."""
        try:
            # For now, generate mock data
            self._generate_mock_market_data()
            self.data_status_label.config(text=f"Loaded data for {len(self.market_data)} symbols")
            logger.info(f"Loaded market data for {len(self.market_data)} symbols")
        except Exception as e:
            logger.error(f"Error loading market data: {e}")
            messagebox.showerror("Error", f"Failed to load market data: {e}")
    
    def _generate_mock_market_data(self):
        """Generate mock market data for demonstration."""
        symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        self.market_data = {}
        
        for symbol in symbols:
            # Generate realistic price data
            np.random.seed(hash(symbol) % 1000)
            returns = np.random.normal(0.0005, 0.02, len(dates))
            prices = 100 * np.exp(np.cumsum(returns))
            
            data = pd.DataFrame({
                'date': dates,
                'open': prices * (1 + np.random.normal(0, 0.01, len(dates))),
                'high': prices * (1 + np.abs(np.random.normal(0, 0.02, len(dates)))),
                'low': prices * (1 - np.abs(np.random.normal(0, 0.02, len(dates)))),
                'close': prices,
                'volume': np.random.randint(1000000, 10000000, len(dates))
            })
            
            self.market_data[symbol] = data
    
    def _on_strategy_change(self, event=None):
        """Handle strategy selection change."""
        strategy = self.strategy_var.get()
        logger.info(f"Strategy changed to: {strategy}")
        
        # Set strategy function based on selection
        if strategy == "Simple Moving Average":
            self.strategy_function = self._sma_strategy
        elif strategy == "RSI Strategy":
            self.strategy_function = self._rsi_strategy
        elif strategy == "MACD Strategy":
            self.strategy_function = self._macd_strategy
        else:
            self.strategy_function = None
    
    def _sma_strategy(self, current_date, market_data, positions, **params):
        """Simple Moving Average strategy."""
        signals = []
        short_window = params.get('short_window', 20)
        long_window = params.get('long_window', 50)
        
        for symbol, data in market_data.items():
            if len(data) < long_window:
                continue
                
            current_data = data[data['date'] <= current_date].tail(long_window)
            if len(current_data) < long_window:
                continue
            
            short_sma = current_data['close'].tail(short_window).mean()
            long_sma = current_data['close'].mean()
            current_price = current_data['close'].iloc[-1]
            
            # Generate signals
            if short_sma > long_sma and symbol not in positions:
                signals.append({
                    'symbol': symbol,
                    'action': 'buy',
                    'quantity': 100,
                    'price': current_price
                })
            elif short_sma < long_sma and symbol in positions:
                signals.append({
                    'symbol': symbol,
                    'action': 'sell',
                    'quantity': positions[symbol].quantity,
                    'price': current_price
                })
        
        return signals
    
    def _rsi_strategy(self, current_date, market_data, positions, **params):
        """RSI strategy."""
        signals = []
        rsi_period = params.get('rsi_period', 14)
        oversold = params.get('oversold', 30)
        overbought = params.get('overbought', 70)
        
        for symbol, data in market_data.items():
            if len(data) < rsi_period + 1:
                continue
                
            current_data = data[data['date'] <= current_date].tail(rsi_period + 1)
            if len(current_data) < rsi_period + 1:
                continue
            
            # Calculate RSI
            delta = current_data['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]
            current_price = current_data['close'].iloc[-1]
            
            # Generate signals
            if current_rsi < oversold and symbol not in positions:
                signals.append({
                    'symbol': symbol,
                    'action': 'buy',
                    'quantity': 100,
                    'price': current_price
                })
            elif current_rsi > overbought and symbol in positions:
                signals.append({
                    'symbol': symbol,
                    'action': 'sell',
                    'quantity': positions[symbol].quantity,
                    'price': current_price
                })
        
        return signals
    
    def _macd_strategy(self, current_date, market_data, positions, **params):
        """MACD strategy."""
        signals = []
        fast_period = params.get('fast_period', 12)
        slow_period = params.get('slow_period', 26)
        signal_period = params.get('signal_period', 9)
        
        for symbol, data in market_data.items():
            if len(data) < slow_period + signal_period:
                continue
                
            current_data = data[data['date'] <= current_date].tail(slow_period + signal_period)
            if len(current_data) < slow_period + signal_period:
                continue
            
            # Calculate MACD
            ema_fast = current_data['close'].ewm(span=fast_period).mean()
            ema_slow = current_data['close'].ewm(span=slow_period).mean()
            macd = ema_fast - ema_slow
            signal = macd.ewm(span=signal_period).mean()
            histogram = macd - signal
            
            current_price = current_data['close'].iloc[-1]
            
            # Generate signals
            if histogram.iloc[-1] > 0 and histogram.iloc[-2] <= 0 and symbol not in positions:
                signals.append({
                    'symbol': symbol,
                    'action': 'buy',
                    'quantity': 100,
                    'price': current_price
                })
            elif histogram.iloc[-1] < 0 and histogram.iloc[-2] >= 0 and symbol in positions:
                signals.append({
                    'symbol': symbol,
                    'action': 'sell',
                    'quantity': positions[symbol].quantity,
                    'price': current_price
                })
        
        return signals
    
    def _run_backtest(self):
        """Run the backtest."""
        try:
            if not self.market_data:
                messagebox.showwarning("Warning", "Please load market data first.")
                return
            
            if not self.strategy_function:
                messagebox.showwarning("Warning", "Please select a strategy first.")
                return
            
            # Get configuration
            initial_capital = float(self.capital_var.get())
            commission_rate = float(self.commission_var.get()) / 100
            slippage_rate = float(self.slippage_var.get()) / 100
            risk_level = RiskLevel(self.risk_var.get())
            start_date = datetime.strptime(self.start_date_var.get(), "%Y-%m-%d")
            end_date = datetime.strptime(self.end_date_var.get(), "%Y-%m-%d")
            
            # Update backtesting engine
            self.backtesting_engine = BacktestingEngine(
                initial_capital=initial_capital,
                commission_rate=commission_rate,
                slippage_rate=slippage_rate,
                risk_level=risk_level
            )
            
            # Run backtest
            self.backtest_result = self.backtesting_engine.run_backtest(
                strategy_function=self.strategy_function,
                market_data=self.market_data,
                start_date=start_date,
                end_date=end_date
            )
            
            # Update displays
            self._update_results_display()
            
            logger.info("Backtest completed successfully")
            messagebox.showinfo("Success", "Backtest completed successfully!")
            
        except Exception as e:
            logger.error(f"Error running backtest: {e}")
            messagebox.showerror("Error", f"Failed to run backtest: {e}")
    
    def _update_results_display(self):
        """Update all result displays."""
        if not self.backtest_result:
            return
        
        # Update summary
        self._update_summary_display()
        
        # Update performance
        self._update_performance_display()
        
        # Update trades
        self._update_trades_display()
        
        # Update equity curve
        self._update_equity_display()
    
    def _update_summary_display(self):
        """Update summary display."""
        result = self.backtest_result
        
        self.total_return_value.config(text=f"{result.total_return:.2%}")
        self.annual_return_value.config(text=f"{result.annualized_return:.2%}")
        self.final_capital_value.config(text=f"${result.final_capital:,.2f}")
        self.max_drawdown_value.config(text=f"{result.max_drawdown:.2%}")
        self.sharpe_value.config(text=f"{result.sharpe_ratio:.3f}")
        
        self.total_trades_value.config(text=str(result.total_trades))
        self.win_rate_value.config(text=f"{result.win_rate:.2%}")
        self.profit_factor_value.config(text=f"{result.profit_factor:.3f}")
        self.avg_win_value.config(text=f"${result.avg_win:,.2f}")
        self.avg_loss_value.config(text=f"${result.avg_loss:,.2f}")
    
    def _update_performance_display(self):
        """Update performance display."""
        result = self.backtest_result
        metrics = result.portfolio_metrics
        
        self.volatility_value.config(text=f"{metrics.volatility:.2%}")
        self.sortino_value.config(text=f"{metrics.sortino_ratio:.3f}")
        self.calmar_value.config(text=f"{metrics.calmar_ratio:.3f}")
        self.info_ratio_value.config(text=f"{metrics.information_ratio:.3f}")
        self.beta_value.config(text=f"{metrics.beta:.3f}")
        self.alpha_value.config(text=f"{metrics.alpha:.2%}")
        
        self.var_value.config(text=f"{metrics.var_95:.2%}")
        self.cvar_value.config(text=f"{metrics.cvar_95:.2%}")
        self.max_wins_value.config(text=str(metrics.max_consecutive_wins))
        self.max_losses_value.config(text=str(metrics.max_consecutive_losses))
    
    def _update_trades_display(self):
        """Update trades display."""
        # Clear existing trades
        for item in self.trades_tree.get_children():
            self.trades_tree.delete(item)
        
        # Add trades
        for i, trade in enumerate(self.backtest_result.trade_history):
            self.trades_tree.insert("", "end", text=f"{i+1}", values=(
                trade['timestamp'].strftime("%Y-%m-%d"),
                trade['symbol'],
                trade['side'],
                trade['quantity'],
                f"${trade['fill_price']:.2f}",
                f"${trade['commission']:.2f}",
                f"${trade['total_cost']:.2f}"
            ))
    
    def _update_equity_display(self):
        """Update equity curve display."""
        result = self.backtest_result
        
        # Update equity info
        equity_curve = result.equity_curve
        if len(equity_curve) > 0:
            self.equity_start_value.config(text=f"${equity_curve.iloc[0]:,.2f}")
            self.equity_end_value.config(text=f"${equity_curve.iloc[-1]:,.2f}")
            self.equity_peak_value.config(text=f"${equity_curve.max():,.2f}")
            self.equity_trough_value.config(text=f"${equity_curve.min():,.2f}")
        
        # Clear canvas and draw simple equity curve (would use matplotlib in full implementation)
        self.equity_canvas.delete("all")
        if len(equity_curve) > 1:
            # Draw simple line chart
            canvas_width = self.equity_canvas.winfo_width()
            canvas_height = self.equity_canvas.winfo_height()
            
            if canvas_width > 1 and canvas_height > 1:
                x_scale = canvas_width / (len(equity_curve) - 1)
                y_scale = canvas_height / (equity_curve.max() - equity_curve.min())
                
                points = []
                for i, value in enumerate(equity_curve):
                    x = i * x_scale
                    y = canvas_height - (value - equity_curve.min()) * y_scale
                    points.extend([x, y])
                
                if len(points) >= 4:
                    self.equity_canvas.create_line(points, fill="blue", width=2) 