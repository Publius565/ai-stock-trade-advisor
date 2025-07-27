"""
Portfolio Analytics Tab
Advanced portfolio analysis and performance visualization component.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from typing import Dict, List, Optional
import logging
from datetime import datetime, timedelta
import numpy as np

from src.execution import PortfolioAnalytics, RiskManager, RiskLevel, PositionRisk, PortfolioRisk

logger = logging.getLogger(__name__)


class PortfolioAnalyticsTab(ttk.Frame):
    """
    Portfolio Analytics Tab Component.
    
    Provides comprehensive portfolio analysis including performance metrics,
    risk analysis, and portfolio insights with interactive visualizations.
    """
    
    def __init__(self, parent, **kwargs):
        """Initialize the Portfolio Analytics Tab."""
        super().__init__(parent, **kwargs)
        self.parent = parent
        
        # Initialize components
        self.portfolio_analytics = PortfolioAnalytics()
        self.risk_manager = RiskManager()
        
        # Data storage
        self.portfolio_data = None
        self.positions_data = None
        self.risk_data = None
        
        # Create UI components
        self._create_widgets()
        self._setup_layout()
        
        logger.info("Portfolio Analytics Tab initialized")
    
    def _create_widgets(self):
        """Create all UI widgets."""
        # Main container
        self.main_frame = ttk.Frame(self)
        
        # Title
        self.title_label = ttk.Label(
            self.main_frame,
            text="Portfolio Analytics & Risk Management",
            font=("Arial", 16, "bold")
        )
        
        # Control panel
        self.control_frame = ttk.LabelFrame(self.main_frame, text="Controls", padding=10)
        
        # Risk level selector
        self.risk_level_label = ttk.Label(self.control_frame, text="Risk Level:")
        self.risk_level_var = tk.StringVar(value="moderate")
        self.risk_level_combo = ttk.Combobox(
            self.control_frame,
            textvariable=self.risk_level_var,
            values=["conservative", "moderate", "aggressive"],
            state="readonly",
            width=15
        )
        self.risk_level_combo.bind("<<ComboboxSelected>>", self._on_risk_level_change)
        
        # Refresh button
        self.refresh_button = ttk.Button(
            self.control_frame,
            text="Refresh Analytics",
            command=self._refresh_analytics
        )
        
        # Notebook for different analytics sections
        self.notebook = ttk.Notebook(self.main_frame)
        
        # Performance Metrics Tab
        self.performance_frame = ttk.Frame(self.notebook)
        self._create_performance_widgets()
        
        # Risk Analysis Tab
        self.risk_frame = ttk.Frame(self.notebook)
        self._create_risk_widgets()
        
        # Portfolio Insights Tab
        self.insights_frame = ttk.Frame(self.notebook)
        self._create_insights_widgets()
        
        # Add tabs to notebook
        self.notebook.add(self.performance_frame, text="Performance Metrics")
        self.notebook.add(self.risk_frame, text="Risk Analysis")
        self.notebook.add(self.insights_frame, text="Portfolio Insights")
    
    def _create_performance_widgets(self):
        """Create performance metrics widgets."""
        # Summary metrics
        self.summary_frame = ttk.LabelFrame(self.performance_frame, text="Summary Metrics", padding=10)
        
        # Total return
        self.total_return_label = ttk.Label(self.summary_frame, text="Total Return:")
        self.total_return_value = ttk.Label(self.summary_frame, text="--", font=("Arial", 12, "bold"))
        
        # Annualized return
        self.annual_return_label = ttk.Label(self.summary_frame, text="Annualized Return:")
        self.annual_return_value = ttk.Label(self.summary_frame, text="--", font=("Arial", 12, "bold"))
        
        # Volatility
        self.volatility_label = ttk.Label(self.summary_frame, text="Volatility:")
        self.volatility_value = ttk.Label(self.summary_frame, text="--", font=("Arial", 12, "bold"))
        
        # Max drawdown
        self.drawdown_label = ttk.Label(self.summary_frame, text="Max Drawdown:")
        self.drawdown_value = ttk.Label(self.summary_frame, text="--", font=("Arial", 12, "bold"))
        
        # Risk-adjusted metrics
        self.risk_metrics_frame = ttk.LabelFrame(self.performance_frame, text="Risk-Adjusted Metrics", padding=10)
        
        # Sharpe ratio
        self.sharpe_label = ttk.Label(self.risk_metrics_frame, text="Sharpe Ratio:")
        self.sharpe_value = ttk.Label(self.risk_metrics_frame, text="--", font=("Arial", 12, "bold"))
        
        # Sortino ratio
        self.sortino_label = ttk.Label(self.risk_metrics_frame, text="Sortino Ratio:")
        self.sortino_value = ttk.Label(self.risk_metrics_frame, text="--", font=("Arial", 12, "bold"))
        
        # Calmar ratio
        self.calmar_label = ttk.Label(self.risk_metrics_frame, text="Calmar Ratio:")
        self.calmar_value = ttk.Label(self.risk_metrics_frame, text="--", font=("Arial", 12, "bold"))
        
        # Trading metrics
        self.trading_frame = ttk.LabelFrame(self.performance_frame, text="Trading Metrics", padding=10)
        
        # Win rate
        self.win_rate_label = ttk.Label(self.trading_frame, text="Win Rate:")
        self.win_rate_value = ttk.Label(self.trading_frame, text="--", font=("Arial", 12, "bold"))
        
        # Profit factor
        self.profit_factor_label = ttk.Label(self.trading_frame, text="Profit Factor:")
        self.profit_factor_value = ttk.Label(self.trading_frame, text="--", font=("Arial", 12, "bold"))
        
        # Average win/loss
        self.avg_win_label = ttk.Label(self.trading_frame, text="Avg Win:")
        self.avg_win_value = ttk.Label(self.trading_frame, text="--", font=("Arial", 12, "bold"))
        
        self.avg_loss_label = ttk.Label(self.trading_frame, text="Avg Loss:")
        self.avg_loss_value = ttk.Label(self.trading_frame, text="--", font=("Arial", 12, "bold"))
    
    def _create_risk_widgets(self):
        """Create risk analysis widgets."""
        # Portfolio risk summary
        self.portfolio_risk_frame = ttk.LabelFrame(self.risk_frame, text="Portfolio Risk Summary", padding=10)
        
        # Total risk
        self.total_risk_label = ttk.Label(self.portfolio_risk_frame, text="Total Risk:")
        self.total_risk_value = ttk.Label(self.portfolio_risk_frame, text="--", font=("Arial", 12, "bold"))
        
        # Risk percentage
        self.risk_percentage_label = ttk.Label(self.portfolio_risk_frame, text="Risk %:")
        self.risk_percentage_value = ttk.Label(self.portfolio_risk_frame, text="--", font=("Arial", 12, "bold"))
        
        # Risk utilization
        self.risk_utilization_label = ttk.Label(self.portfolio_risk_frame, text="Risk Utilization:")
        self.risk_utilization_value = ttk.Label(self.portfolio_risk_frame, text="--", font=("Arial", 12, "bold"))
        
        # Concentration metrics
        self.concentration_frame = ttk.LabelFrame(self.risk_frame, text="Concentration Metrics", padding=10)
        
        # Largest position risk
        self.largest_risk_label = ttk.Label(self.concentration_frame, text="Largest Position Risk:")
        self.largest_risk_value = ttk.Label(self.concentration_frame, text="--", font=("Arial", 12, "bold"))
        
        # Concentration risk
        self.concentration_risk_label = ttk.Label(self.concentration_frame, text="Concentration Risk:")
        self.concentration_risk_value = ttk.Label(self.concentration_frame, text="--", font=("Arial", 12, "bold"))
        
        # Correlation risk
        self.correlation_risk_label = ttk.Label(self.concentration_frame, text="Correlation Risk:")
        self.correlation_risk_value = ttk.Label(self.concentration_frame, text="--", font=("Arial", 12, "bold"))
        
        # Risk alerts
        self.alerts_frame = ttk.LabelFrame(self.risk_frame, text="Risk Alerts", padding=10)
        self.alerts_text = tk.Text(self.alerts_frame, height=8, width=60, wrap=tk.WORD)
        self.alerts_scrollbar = ttk.Scrollbar(self.alerts_frame, orient="vertical", command=self.alerts_text.yview)
        self.alerts_text.configure(yscrollcommand=self.alerts_scrollbar.set)
    
    def _create_insights_widgets(self):
        """Create portfolio insights widgets."""
        # Sector exposure
        self.sector_frame = ttk.LabelFrame(self.insights_frame, text="Sector Exposure", padding=10)
        self.sector_tree = ttk.Treeview(self.sector_frame, columns=("exposure", "status"), show="tree headings", height=8)
        self.sector_tree.heading("#0", text="Sector")
        self.sector_tree.heading("exposure", text="Exposure %")
        self.sector_tree.heading("status", text="Status")
        self.sector_tree.column("#0", width=150)
        self.sector_tree.column("exposure", width=100)
        self.sector_tree.column("status", width=100)
        
        # Position analysis
        self.position_frame = ttk.LabelFrame(self.insights_frame, text="Position Analysis", padding=10)
        self.position_tree = ttk.Treeview(
            self.position_frame, 
            columns=("symbol", "size", "value", "risk", "pnl"), 
            show="tree headings", 
            height=8
        )
        self.position_tree.heading("#0", text="Symbol")
        self.position_tree.heading("symbol", text="Symbol")
        self.position_tree.heading("size", text="Size")
        self.position_tree.heading("value", text="Value")
        self.position_tree.heading("risk", text="Risk %")
        self.position_tree.heading("pnl", text="P&L")
        self.position_tree.column("#0", width=80)
        self.position_tree.column("symbol", width=80)
        self.position_tree.column("size", width=80)
        self.position_tree.column("value", width=100)
        self.position_tree.column("risk", width=80)
        self.position_tree.column("pnl", width=100)
    
    def _setup_layout(self):
        """Setup the layout of all widgets."""
        # Main layout
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        self.title_label.pack(pady=(0, 20))
        
        # Control panel
        self.control_frame.pack(fill=tk.X, pady=(0, 20))
        self.risk_level_label.grid(row=0, column=0, padx=(0, 5), pady=5)
        self.risk_level_combo.grid(row=0, column=1, padx=(0, 20), pady=5)
        self.refresh_button.grid(row=0, column=2, padx=5, pady=5)
        
        # Notebook
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Performance metrics layout
        self._setup_performance_layout()
        
        # Risk analysis layout
        self._setup_risk_layout()
        
        # Insights layout
        self._setup_insights_layout()
    
    def _setup_performance_layout(self):
        """Setup performance metrics layout."""
        # Summary metrics
        self.summary_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.total_return_label.grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.total_return_value.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        
        self.annual_return_label.grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.annual_return_value.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        
        self.volatility_label.grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.volatility_value.grid(row=2, column=1, sticky="w", padx=5, pady=2)
        
        self.drawdown_label.grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.drawdown_value.grid(row=3, column=1, sticky="w", padx=5, pady=2)
        
        # Risk-adjusted metrics
        self.risk_metrics_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.sharpe_label.grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.sharpe_value.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        
        self.sortino_label.grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.sortino_value.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        
        self.calmar_label.grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.calmar_value.grid(row=2, column=1, sticky="w", padx=5, pady=2)
        
        # Trading metrics
        self.trading_frame.pack(fill=tk.X)
        
        self.win_rate_label.grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.win_rate_value.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        
        self.profit_factor_label.grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.profit_factor_value.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        
        self.avg_win_label.grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.avg_win_value.grid(row=2, column=1, sticky="w", padx=5, pady=2)
        
        self.avg_loss_label.grid(row=3, column=0, sticky="w", padx=5, pady=2)
        self.avg_loss_value.grid(row=3, column=1, sticky="w", padx=5, pady=2)
    
    def _setup_risk_layout(self):
        """Setup risk analysis layout."""
        # Portfolio risk summary
        self.portfolio_risk_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.total_risk_label.grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.total_risk_value.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        
        self.risk_percentage_label.grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.risk_percentage_value.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        
        self.risk_utilization_label.grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.risk_utilization_value.grid(row=2, column=1, sticky="w", padx=5, pady=2)
        
        # Concentration metrics
        self.concentration_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.largest_risk_label.grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.largest_risk_value.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        
        self.concentration_risk_label.grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.concentration_risk_value.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        
        self.correlation_risk_label.grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.correlation_risk_value.grid(row=2, column=1, sticky="w", padx=5, pady=2)
        
        # Risk alerts
        self.alerts_frame.pack(fill=tk.BOTH, expand=True)
        self.alerts_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.alerts_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _setup_insights_layout(self):
        """Setup insights layout."""
        # Sector exposure
        self.sector_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.sector_tree.pack(fill=tk.BOTH, expand=True)
        
        # Position analysis
        self.position_frame.pack(fill=tk.BOTH, expand=True)
        self.position_tree.pack(fill=tk.BOTH, expand=True)
    
    def _on_risk_level_change(self, event=None):
        """Handle risk level change."""
        try:
            risk_level = RiskLevel(self.risk_level_var.get())
            self.risk_manager = RiskManager(risk_level=risk_level)
            self._refresh_analytics()
            logger.info(f"Risk level changed to: {risk_level.value}")
        except Exception as e:
            logger.error(f"Error changing risk level: {e}")
            messagebox.showerror("Error", f"Failed to change risk level: {e}")
    
    def _refresh_analytics(self):
        """Refresh portfolio analytics."""
        try:
            # Get current portfolio data
            self._load_portfolio_data()
            
            # Update displays
            self._update_performance_display()
            self._update_risk_display()
            self._update_insights_display()
            
            logger.info("Portfolio analytics refreshed")
        except Exception as e:
            logger.error(f"Error refreshing analytics: {e}")
            messagebox.showerror("Error", f"Failed to refresh analytics: {e}")
    
    def _load_portfolio_data(self):
        """Load current portfolio data."""
        try:
            # This would typically get data from the main application
            # For now, we'll use mock data
            self._load_mock_data()
        except Exception as e:
            logger.error(f"Error loading portfolio data: {e}")
            raise
    
    def _load_mock_data(self):
        """Load mock portfolio data for demonstration."""
        # Mock portfolio returns (daily returns for the last year)
        np.random.seed(42)
        dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
        returns = pd.Series(np.random.normal(0.0005, 0.02, len(dates)), index=dates)
        
        # Mock positions
        self.positions_data = [
            PositionRisk(
                symbol="AAPL",
                current_price=150.0,
                position_size=100,
                position_value=15000.0,
                unrealized_pnl=500.0,
                stop_loss_price=140.0,
                take_profit_price=160.0,
                risk_per_share=10.0,
                total_risk=1000.0,
                risk_percentage=0.01,
                max_position_size=150,
                suggested_position_size=150
            ),
            PositionRisk(
                symbol="MSFT",
                current_price=300.0,
                position_size=50,
                position_value=15000.0,
                unrealized_pnl=750.0,
                stop_loss_price=280.0,
                take_profit_price=320.0,
                risk_per_share=20.0,
                total_risk=1000.0,
                risk_percentage=0.01,
                max_position_size=75,
                suggested_position_size=75
            )
        ]
        
        # Calculate portfolio metrics
        self.portfolio_data = self.portfolio_analytics.calculate_portfolio_metrics(returns)
        
        # Calculate risk metrics
        portfolio_value = 100000.0  # Mock portfolio value
        sector_data = {"AAPL": "Technology", "MSFT": "Technology"}
        self.risk_data = self.risk_manager.analyze_portfolio_risk(
            self.positions_data, portfolio_value, sector_data
        )
    
    def _update_performance_display(self):
        """Update performance metrics display."""
        if not self.portfolio_data:
            return
        
        # Summary metrics
        self.total_return_value.config(text=f"{self.portfolio_data.total_return:.2%}")
        self.annual_return_value.config(text=f"{self.portfolio_data.annualized_return:.2%}")
        self.volatility_value.config(text=f"{self.portfolio_data.volatility:.2%}")
        self.drawdown_value.config(text=f"{self.portfolio_data.max_drawdown:.2%}")
        
        # Risk-adjusted metrics
        self.sharpe_value.config(text=f"{self.portfolio_data.sharpe_ratio:.3f}")
        self.sortino_value.config(text=f"{self.portfolio_data.sortino_ratio:.3f}")
        self.calmar_value.config(text=f"{self.portfolio_data.calmar_ratio:.3f}")
        
        # Trading metrics
        self.win_rate_value.config(text=f"{self.portfolio_data.win_rate:.2%}")
        self.profit_factor_value.config(text=f"{self.portfolio_data.profit_factor:.3f}")
        self.avg_win_value.config(text=f"{self.portfolio_data.avg_win:.2%}")
        self.avg_loss_value.config(text=f"{self.portfolio_data.avg_loss:.2%}")
    
    def _update_risk_display(self):
        """Update risk analysis display."""
        if not self.risk_data:
            return
        
        # Portfolio risk
        self.total_risk_value.config(text=f"${self.risk_data.total_risk:,.2f}")
        self.risk_percentage_value.config(text=f"{self.risk_data.portfolio_risk_percentage:.2%}")
        self.risk_utilization_value.config(text=f"{self.risk_data.current_risk_utilization:.1%}")
        
        # Concentration metrics
        self.largest_risk_value.config(text=f"{self.risk_data.largest_position_risk:.2%}")
        self.concentration_risk_value.config(text=f"{self.risk_data.concentration_risk:.2%}")
        self.correlation_risk_value.config(text=f"{self.risk_data.correlation_risk:.2%}")
        
        # Risk alerts
        self.alerts_text.delete(1.0, tk.END)
        if self.risk_data.risk_alerts:
            for alert in self.risk_data.risk_alerts:
                self.alerts_text.insert(tk.END, f"• {alert}\n")
        else:
            self.alerts_text.insert(tk.END, "No risk alerts at this time.")
    
    def _update_insights_display(self):
        """Update portfolio insights display."""
        if not self.risk_data or not self.positions_data:
            return
        
        # Clear existing data
        for item in self.sector_tree.get_children():
            self.sector_tree.delete(item)
        
        for item in self.position_tree.get_children():
            self.position_tree.delete(item)
        
        # Sector exposure
        for sector, exposure in self.risk_data.sector_exposure.items():
            status = "Normal" if exposure <= 0.25 else "High"
            self.sector_tree.insert("", "end", text=sector, values=(f"{exposure:.2%}", status))
        
        # Position analysis
        for position in self.positions_data:
            pnl_color = "green" if position.unrealized_pnl >= 0 else "red"
            self.position_tree.insert("", "end", text=position.symbol, values=(
                position.symbol,
                position.position_size,
                f"${position.position_value:,.2f}",
                f"{position.risk_percentage:.2%}",
                f"${position.unrealized_pnl:,.2f}"
            ))
    
    def update_data(self, portfolio_data=None, positions_data=None, risk_data=None):
        """
        Update portfolio data from external source.
        
        Args:
            portfolio_data: PortfolioMetrics object
            positions_data: List of PositionRisk objects
            risk_data: PortfolioRisk object
        """
        try:
            if portfolio_data:
                self.portfolio_data = portfolio_data
            if positions_data:
                self.positions_data = positions_data
            if risk_data:
                self.risk_data = risk_data
            
            # Update displays
            self._update_performance_display()
            self._update_risk_display()
            self._update_insights_display()
            
            logger.info("Portfolio analytics data updated")
        except Exception as e:
            logger.error(f"Error updating portfolio data: {e}")
            messagebox.showerror("Error", f"Failed to update portfolio data: {e}") 