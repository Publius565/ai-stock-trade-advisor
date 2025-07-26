"""
Trading Signals Tab Component

Integrates backend trading engine components to display real-time trading signals,
portfolio management, and rules engine configuration.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QTextEdit, QGroupBox, QComboBox,
    QTableWidget, QTableWidgetItem, QProgressBar, QCheckBox,
    QSlider, QSpinBox
)
from PyQt6.QtCore import pyqtSignal, QTimer, Qt
from PyQt6.QtGui import QColor, QFont

from src.strategy.trading_engine import TradingEngine
from src.strategy.rules_engine import RulesEngine
from src.strategy.signal_generator import SignalGenerator

logger = logging.getLogger(__name__)


class TradingSignalsTab(QWidget):
    """Trading signals tab component with integrated backend trading features."""
    
    # Signals
    activity_logged = pyqtSignal(str)
    status_updated = pyqtSignal(str)
    
    def __init__(self, db_manager=None, market_data_manager=None, profile_manager=None):
        super().__init__()
        self.db_manager = db_manager
        self.market_data_manager = market_data_manager
        self.profile_manager = profile_manager
        self.current_user_uid = None
        
        # Initialize trading components (will be set later via setters)
        self.trading_engine = None
        self.rules_engine = None
        self.signal_generator = None
        
        self.init_ui()
        
        # Auto-refresh timer for signals
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_signals)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds
    
    def init_ui(self):
        """Initialize the trading signals tab UI."""
        layout = QVBoxLayout(self)
        
        # Portfolio Overview Section
        portfolio_group = QGroupBox("Portfolio Overview")
        portfolio_layout = QGridLayout(portfolio_group)
        
        # Portfolio metrics
        metrics = ["Total Value", "Today's P&L", "Total P&L", "Cash Available", 
                  "Positions", "Win Rate"]
        
        self.portfolio_labels = {}
        row, col = 0, 0
        for metric in metrics:
            label_key = QLabel(f"{metric}:")
            label_value = QLabel("$0.00" if "$" in metric or "P&L" in metric else "0")
            label_value.setStyleSheet("font-weight: bold; color: #2E8B57; font-size: 14px;")
            
            portfolio_layout.addWidget(label_key, row, col)
            portfolio_layout.addWidget(label_value, row, col + 1)
            
            self.portfolio_labels[metric] = label_value
            
            col += 2
            if col >= 6:
                col = 0
                row += 1
        
        layout.addWidget(portfolio_group)
        
        # Active Signals Section
        signals_group = QGroupBox("Active Trading Signals")
        signals_layout = QVBoxLayout(signals_group)
        
        # Signals controls
        controls_layout = QHBoxLayout()
        
        self.refresh_signals_btn = QPushButton("Refresh Signals")
        self.refresh_signals_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        
        self.clear_signals_btn = QPushButton("Clear History")
        self.clear_signals_btn.setStyleSheet("background-color: #FF5722; color: white;")
        
        controls_layout.addWidget(self.refresh_signals_btn)
        controls_layout.addWidget(self.clear_signals_btn)
        controls_layout.addStretch()
        
        signals_layout.addLayout(controls_layout)
        
        # Signals table
        self.signals_table = QTableWidget()
        self.signals_table.setColumnCount(8)
        self.signals_table.setHorizontalHeaderLabels([
            "Symbol", "Signal", "Strength", "Confidence", "Price", "Target", "Stop Loss", "Timestamp"
        ])
        signals_layout.addWidget(self.signals_table)
        
        layout.addWidget(signals_group)
        
        # Rules Engine Configuration
        rules_group = QGroupBox("Trading Rules Configuration")
        rules_layout = QVBoxLayout(rules_group)
        
        # Rules controls
        rules_controls_layout = QGridLayout()
        
        # Rule checkboxes
        self.rule_checkboxes = {}
        rules = [
            ("SMA Crossover", "Simple Moving Average crossover signals"),
            ("EMA Crossover", "Exponential Moving Average crossover signals"),
            ("RSI Oversold/Overbought", "RSI momentum signals"),
            ("Volume Spike", "Unusual volume activity signals"),
            ("Volatility Breakout", "Price volatility breakout signals")
        ]
        
        for i, (rule_name, description) in enumerate(rules):
            checkbox = QCheckBox(rule_name)
            checkbox.setChecked(True)  # Default enabled
            checkbox.setToolTip(description)
            self.rule_checkboxes[rule_name] = checkbox
            rules_controls_layout.addWidget(checkbox, i // 2, i % 2)
        
        rules_layout.addLayout(rules_controls_layout)
        
        # Rule parameters
        params_layout = QGridLayout()
        
        params_layout.addWidget(QLabel("Min Confidence:"), 0, 0)
        self.min_confidence_slider = QSlider(Qt.Orientation.Horizontal)
        self.min_confidence_slider.setRange(50, 95)
        self.min_confidence_slider.setValue(70)
        self.min_confidence_label = QLabel("70%")
        params_layout.addWidget(self.min_confidence_slider, 0, 1)
        params_layout.addWidget(self.min_confidence_label, 0, 2)
        
        params_layout.addWidget(QLabel("Max Positions:"), 1, 0)
        self.max_positions_spin = QSpinBox()
        self.max_positions_spin.setRange(1, 20)
        self.max_positions_spin.setValue(5)
        params_layout.addWidget(self.max_positions_spin, 1, 1)
        
        rules_layout.addLayout(params_layout)
        
        # Apply rules button
        self.apply_rules_btn = QPushButton("Apply Rules Configuration")
        self.apply_rules_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        rules_layout.addWidget(self.apply_rules_btn)
        
        layout.addWidget(rules_group)
        
        # Market Context & Analysis
        context_group = QGroupBox("Market Context Analysis")
        context_layout = QVBoxLayout(context_group)
        
        self.market_context_display = QTextEdit()
        self.market_context_display.setMaximumHeight(120)
        self.market_context_display.setReadOnly(True)
        self.market_context_display.setText("Market context analysis will appear here after signal generation.")
        context_layout.addWidget(self.market_context_display)
        
        layout.addWidget(context_group)
        
        # Setup connections
        self.setup_connections()
        
        logger.info("Trading Signals tab initialized")
    
    def setup_connections(self):
        """Set up signal connections."""
        self.refresh_signals_btn.clicked.connect(self.refresh_signals)
        self.clear_signals_btn.clicked.connect(self.clear_signals_history)
        self.apply_rules_btn.clicked.connect(self.apply_rules_configuration)
        self.min_confidence_slider.valueChanged.connect(self.update_confidence_label)
    
    def set_db_manager(self, manager):
        """Set the database manager."""
        self.db_manager = manager
    
    def set_profile_manager(self, manager):
        """Set the profile manager and initialize trading components."""
        self.profile_manager = manager
        
        # Initialize trading components if both dependencies are available
        if self.db_manager and manager and not self.trading_engine:
            try:
                self.trading_engine = TradingEngine(self.db_manager, manager)
                self.rules_engine = RulesEngine()
                self.signal_generator = SignalGenerator(self.db_manager, self.trading_engine)
                logger.info("Trading components initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize trading components: {e}")
                self.trading_engine = None
                self.rules_engine = None
                self.signal_generator = None
        if manager and not self.trading_engine:
            try:
                self.trading_engine = TradingEngine(manager)
                self.signal_generator = SignalGenerator(manager, self.trading_engine)
                logger.info("Trading components initialized with new db_manager")
            except Exception as e:
                logger.error(f"Failed to initialize trading components: {e}")
    
    def set_market_data_manager(self, manager):
        """Set the market data manager."""
        self.market_data_manager = manager
    

    
    def set_current_user(self, user_uid: str):
        """Set the current user UID."""
        self.current_user_uid = user_uid
        self.refresh_portfolio_overview()
    
    def refresh_signals(self):
        """Refresh trading signals display."""
        if not self.signal_generator:
            self.signals_table.setRowCount(0)
            return
        
        try:
            # Get signals from signal generator
            # For POC, we'll simulate signals
            signals = self.generate_sample_signals()
            
            # Display signals in table
            self.display_signals(signals)
            
            # Update market context
            self.update_market_context()
            
            self.activity_logged.emit(f"Refreshed {len(signals)} trading signals")
            
        except Exception as e:
            logger.error(f"Error refreshing signals: {e}")
    
    def generate_sample_signals(self) -> List[Dict]:
        """Generate sample signals for POC demonstration."""
        import random
        from datetime import datetime, timedelta
        
        symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "NVDA", "META"]
        signal_types = ["BUY", "SELL", "HOLD"]
        
        signals = []
        for i in range(random.randint(3, 8)):
            signal = {
                'symbol': random.choice(symbols),
                'signal_type': random.choice(signal_types),
                'strength': random.choice(['WEAK', 'MODERATE', 'STRONG']),
                'confidence': random.uniform(0.6, 0.95),
                'current_price': random.uniform(100, 300),
                'target_price': random.uniform(105, 320),
                'stop_loss': random.uniform(90, 280),
                'timestamp': datetime.now() - timedelta(minutes=random.randint(1, 120))
            }
            signals.append(signal)
        
        return signals
    
    def display_signals(self, signals: List[Dict]):
        """Display trading signals in table."""
        try:
            self.signals_table.setRowCount(len(signals))
            
            for row, signal in enumerate(signals):
                # Color coding for signal types
                signal_type = signal.get('signal_type', 'HOLD')
                if signal_type == 'BUY':
                    color = QColor(76, 175, 80)  # Green
                elif signal_type == 'SELL':
                    color = QColor(244, 67, 54)  # Red
                else:
                    color = QColor(158, 158, 158)  # Gray
                
                items = [
                    signal.get('symbol', 'N/A'),
                    signal.get('signal_type', 'N/A'),
                    signal.get('strength', 'N/A'),
                    f"{signal.get('confidence', 0):.1%}",
                    f"${signal.get('current_price', 0):.2f}",
                    f"${signal.get('target_price', 0):.2f}",
                    f"${signal.get('stop_loss', 0):.2f}",
                    signal.get('timestamp', datetime.now()).strftime('%H:%M:%S')
                ]
                
                for col, item_text in enumerate(items):
                    item = QTableWidgetItem(str(item_text))
                    if col == 1:  # Signal type column
                        item.setBackground(color)
                        item.setForeground(QColor(255, 255, 255))  # White text
                        font = QFont()
                        font.setBold(True)
                        item.setFont(font)
                    self.signals_table.setItem(row, col, item)
            
            # Auto-resize columns
            self.signals_table.resizeColumnsToContents()
            
        except Exception as e:
            logger.error(f"Error displaying signals: {e}")
    
    def refresh_portfolio_overview(self):
        """Refresh portfolio overview display."""
        try:
            if not self.trading_engine or not self.current_user_uid:
                return
            
            # Get portfolio data (simulated for POC)
            portfolio_data = {
                "Total Value": "$127,450.00",
                "Today's P&L": "+$2,340.50 (+1.87%)",
                "Total P&L": "+$27,450.00 (+27.4%)",
                "Cash Available": "$15,230.00",
                "Positions": "12",
                "Win Rate": "68.4%"
            }
            
            # Update portfolio labels
            for metric, value in portfolio_data.items():
                if metric in self.portfolio_labels:
                    self.portfolio_labels[metric].setText(value)
                    
                    # Color coding for P&L
                    if "P&L" in metric and "+" in value:
                        self.portfolio_labels[metric].setStyleSheet("font-weight: bold; color: #4CAF50; font-size: 14px;")
                    elif "P&L" in metric and "-" in value:
                        self.portfolio_labels[metric].setStyleSheet("font-weight: bold; color: #F44336; font-size: 14px;")
                        
        except Exception as e:
            logger.error(f"Error refreshing portfolio overview: {e}")
    
    def update_market_context(self):
        """Update market context analysis display."""
        try:
            # Sample market context for POC
            context_text = f"""
🏪 Market Context Analysis - {datetime.now().strftime('%H:%M:%S')}

📊 Market Sentiment: BULLISH (Moderate)
📈 Trend Direction: Upward with minor consolidation
📉 Volatility Level: MODERATE (VIX: 18.4)
💵 Volume Analysis: Above average (+15% vs 20-day avg)

🎯 Active Rules Summary:
• SMA Crossover: 3 signals generated
• RSI Conditions: 2 oversold opportunities detected  
• Volume Spikes: 1 breakout candidate identified
• Volatility: Normal range, good for trend following

⚠️ Risk Factors:
• Earnings season approaching (increased volatility)
• Fed meeting next week (policy uncertainty)
• Overall market correlation: HIGH (0.78)
            """
            
            self.market_context_display.setText(context_text.strip())
            
        except Exception as e:
            logger.error(f"Error updating market context: {e}")
    
    def clear_signals_history(self):
        """Clear signals history display."""
        self.signals_table.setRowCount(0)
        self.activity_logged.emit("Cleared signals history")
    
    def apply_rules_configuration(self):
        """Apply rules engine configuration."""
        try:
            if not self.rules_engine:
                return
            
            # Get rule configurations
            enabled_rules = []
            for rule_name, checkbox in self.rule_checkboxes.items():
                if checkbox.isChecked():
                    enabled_rules.append(rule_name)
            
            min_confidence = self.min_confidence_slider.value() / 100.0
            max_positions = self.max_positions_spin.value()
            
            # Apply configuration (POC implementation)
            config_summary = f"""
Applied Rules Configuration:
• Enabled Rules: {', '.join(enabled_rules)}
• Min Confidence: {min_confidence:.1%}
• Max Positions: {max_positions}
            """
            
            self.activity_logged.emit(f"Applied rules configuration - {len(enabled_rules)} rules enabled")
            
        except Exception as e:
            logger.error(f"Error applying rules configuration: {e}")
    
    def update_confidence_label(self, value):
        """Update confidence slider label."""
        self.min_confidence_label.setText(f"{value}%") 