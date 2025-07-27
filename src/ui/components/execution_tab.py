"""
Trade Execution Tab Component

Integrates backend execution layer components to display trade execution,
order management, and broker integration status.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QTextEdit, QGroupBox, QComboBox,
    QTableWidget, QTableWidgetItem, QProgressBar, QCheckBox,
    QSpinBox, QDoubleSpinBox
)
from PyQt6.QtCore import pyqtSignal, QTimer, Qt
from PyQt6.QtGui import QColor, QFont

from src.execution.trade_executor import TradeExecutor, TradeOrder, OrderType, OrderStatus
from src.execution.alpaca_broker import AlpacaBroker

logger = logging.getLogger(__name__)


class ExecutionTab(QWidget):
    """Trade execution tab component with integrated backend execution features."""
    
    # Signals
    activity_logged = pyqtSignal(str)
    status_updated = pyqtSignal(str)
    
    def __init__(self, db_manager=None, market_data_manager=None, profile_manager=None):
        super().__init__()
        self.db_manager = db_manager
        self.market_data_manager = market_data_manager
        self.profile_manager = profile_manager
        self.current_user_uid = None
        
        # Initialize execution components (will be set later via setters)
        self.trade_executor = None
        self.alpaca_broker = None
        
        self.init_ui()
        
        # Auto-refresh timer for execution status
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_execution_status)
        self.refresh_timer.start(10000)  # Refresh every 10 seconds
    
    def init_ui(self):
        """Initialize the trade execution tab UI."""
        layout = QVBoxLayout(self)
        
        # Broker Connection Section
        broker_group = QGroupBox("Broker Connection")
        broker_layout = QGridLayout(broker_group)
        
        # Connection status
        self.connection_status = QLabel("Disconnected")
        self.connection_status.setStyleSheet("color: red; font-weight: bold;")
        broker_layout.addWidget(QLabel("Status:"), 0, 0)
        broker_layout.addWidget(self.connection_status, 0, 1)
        
        # Account info
        self.account_value = QLabel("$0.00")
        self.account_value.setStyleSheet("font-weight: bold; color: #2E8B57;")
        broker_layout.addWidget(QLabel("Account Value:"), 0, 2)
        broker_layout.addWidget(self.account_value, 0, 3)
        
        self.cash_available = QLabel("$0.00")
        self.cash_available.setStyleSheet("font-weight: bold; color: #2E8B57;")
        broker_layout.addWidget(QLabel("Cash Available:"), 1, 0)
        broker_layout.addWidget(self.cash_available, 1, 1)
        
        # Connection controls
        self.connect_btn = QPushButton("Connect to Alpaca")
        self.connect_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        broker_layout.addWidget(self.connect_btn, 1, 2)
        
        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.setStyleSheet("background-color: #FF5722; color: white;")
        self.disconnect_btn.setEnabled(False)
        broker_layout.addWidget(self.disconnect_btn, 1, 3)
        
        layout.addWidget(broker_group)
        
        # Order Management Section
        order_group = QGroupBox("Order Management")
        order_layout = QVBoxLayout(order_group)
        
        # Order creation controls
        controls_layout = QGridLayout()
        
        controls_layout.addWidget(QLabel("Symbol:"), 0, 0)
        self.symbol_input = QComboBox()
        self.symbol_input.setEditable(True)
        self.symbol_input.addItems(["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"])
        controls_layout.addWidget(self.symbol_input, 0, 1)
        
        controls_layout.addWidget(QLabel("Order Type:"), 0, 2)
        self.order_type_combo = QComboBox()
        self.order_type_combo.addItems(["Market", "Limit", "Stop", "Stop Limit"])
        controls_layout.addWidget(self.order_type_combo, 0, 3)
        
        controls_layout.addWidget(QLabel("Action:"), 1, 0)
        self.action_combo = QComboBox()
        self.action_combo.addItems(["Buy", "Sell"])
        controls_layout.addWidget(self.action_combo, 1, 1)
        
        controls_layout.addWidget(QLabel("Quantity:"), 1, 2)
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 10000)
        self.quantity_spin.setValue(100)
        controls_layout.addWidget(self.quantity_spin, 1, 3)
        
        controls_layout.addWidget(QLabel("Price:"), 2, 0)
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0.01, 10000.00)
        self.price_spin.setDecimals(2)
        self.price_spin.setValue(100.00)
        controls_layout.addWidget(self.price_spin, 2, 1)
        
        # Order buttons
        self.place_order_btn = QPushButton("Place Order")
        self.place_order_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        controls_layout.addWidget(self.place_order_btn, 2, 2)
        
        self.cancel_all_btn = QPushButton("Cancel All Orders")
        self.cancel_all_btn.setStyleSheet("background-color: #FF9800; color: white;")
        controls_layout.addWidget(self.cancel_all_btn, 2, 3)
        
        order_layout.addLayout(controls_layout)
        
        # Orders table
        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(8)
        self.orders_table.setHorizontalHeaderLabels([
            "Order ID", "Symbol", "Type", "Action", "Quantity", "Price", "Status", "Time"
        ])
        order_layout.addWidget(self.orders_table)
        
        layout.addWidget(order_group)
        
        # Execution Status Section
        status_group = QGroupBox("Execution Status")
        status_layout = QVBoxLayout(status_group)
        
        # Status metrics
        metrics_layout = QGridLayout()
        
        self.orders_pending = QLabel("0")
        self.orders_pending.setStyleSheet("font-weight: bold; color: #FF9800;")
        metrics_layout.addWidget(QLabel("Pending Orders:"), 0, 0)
        metrics_layout.addWidget(self.orders_pending, 0, 1)
        
        self.orders_filled = QLabel("0")
        self.orders_filled.setStyleSheet("font-weight: bold; color: #4CAF50;")
        metrics_layout.addWidget(QLabel("Filled Orders:"), 0, 2)
        metrics_layout.addWidget(self.orders_filled, 0, 3)
        
        self.orders_cancelled = QLabel("0")
        self.orders_cancelled.setStyleSheet("font-weight: bold; color: #F44336;")
        metrics_layout.addWidget(QLabel("Cancelled Orders:"), 1, 0)
        metrics_layout.addWidget(self.orders_cancelled, 1, 1)
        
        self.execution_time = QLabel("0.00s")
        self.execution_time.setStyleSheet("font-weight: bold; color: #2196F3;")
        metrics_layout.addWidget(QLabel("Avg Execution Time:"), 1, 2)
        metrics_layout.addWidget(self.execution_time, 1, 3)
        
        status_layout.addLayout(metrics_layout)
        
        # Execution log
        self.execution_log = QTextEdit()
        self.execution_log.setMaximumHeight(150)
        self.execution_log.setReadOnly(True)
        self.execution_log.setText("Execution log will appear here...")
        status_layout.addWidget(self.execution_log)
        
        layout.addWidget(status_group)
        
        # Setup connections
        self.setup_connections()
        
        logger.info("Execution tab initialized")
    
    def setup_connections(self):
        """Setup signal connections."""
        self.connect_btn.clicked.connect(self.connect_broker)
        self.disconnect_btn.clicked.connect(self.disconnect_broker)
        self.place_order_btn.clicked.connect(self.place_order)
        self.cancel_all_btn.clicked.connect(self.cancel_all_orders)
    
    def set_db_manager(self, manager):
        """Set database manager."""
        self.db_manager = manager
    
    def set_profile_manager(self, manager):
        """Set profile manager."""
        self.profile_manager = manager
    
    def set_market_data_manager(self, manager):
        """Set market data manager."""
        self.market_data_manager = manager
    
    def set_trade_executor(self, executor):
        """Set trade executor."""
        self.trade_executor = executor
        logger.info("Trade executor set in ExecutionTab")
    
    def set_alpaca_broker(self, broker):
        """Set Alpaca broker."""
        self.alpaca_broker = broker
        logger.info("Alpaca broker set in ExecutionTab")
    
    def set_current_user(self, user_uid: str):
        """Set current user."""
        self.current_user_uid = user_uid
        self.refresh_execution_status()
    
    def connect_broker(self):
        """Connect to Alpaca broker."""
        try:
            if self.alpaca_broker:
                success = self.alpaca_broker.connect()
                if success:
                    self.connection_status.setText("Connected")
                    self.connection_status.setStyleSheet("color: green; font-weight: bold;")
                    self.connect_btn.setEnabled(False)
                    self.disconnect_btn.setEnabled(True)
                    self.place_order_btn.setEnabled(True)
                    self.log_activity("Connected to Alpaca broker")
                    self.update_status("Connected to Alpaca broker")
                else:
                    self.log_activity("Failed to connect to Alpaca broker")
                    self.update_status("Connection failed")
            else:
                self.log_activity("Alpaca broker not available")
        except Exception as e:
            logger.error(f"Error connecting to broker: {e}")
            self.log_activity(f"Connection error: {e}")
    
    def disconnect_broker(self):
        """Disconnect from Alpaca broker."""
        try:
            if self.alpaca_broker:
                self.alpaca_broker.disconnect()
                self.connection_status.setText("Disconnected")
                self.connection_status.setStyleSheet("color: red; font-weight: bold;")
                self.connect_btn.setEnabled(True)
                self.disconnect_btn.setEnabled(False)
                self.place_order_btn.setEnabled(False)
                self.log_activity("Disconnected from Alpaca broker")
                self.update_status("Disconnected from broker")
        except Exception as e:
            logger.error(f"Error disconnecting from broker: {e}")
    
    def place_order(self):
        """Place a new order."""
        try:
            if not self.alpaca_broker or not self.alpaca_broker.is_connected():
                self.log_activity("Cannot place order - broker not connected")
                return
            
            symbol = self.symbol_input.currentText().upper()
            order_type = self.order_type_combo.currentText().upper()
            action = self.action_combo.currentText().upper()
            quantity = self.quantity_spin.value()
            price = self.price_spin.value()
            
            # Create order
            order = TradeOrder(
                symbol=symbol,
                order_type=OrderType[order_type],
                side=action,
                quantity=quantity,
                price=price,
                user_id=1  # TODO: Get actual user ID
            )
            
            # Execute order
            if self.trade_executor:
                result = self.trade_executor.execute_order(order)
                if result:
                    self.log_activity(f"Order placed: {symbol} {action} {quantity} @ ${price}")
                    self.update_status(f"Order placed successfully")
                    self.refresh_orders_table()
                else:
                    self.log_activity("Order placement failed")
                    self.update_status("Order placement failed")
            else:
                self.log_activity("Trade executor not available")
                
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            self.log_activity(f"Order error: {e}")
    
    def cancel_all_orders(self):
        """Cancel all pending orders."""
        try:
            if self.alpaca_broker and self.alpaca_broker.is_connected():
                cancelled = self.alpaca_broker.cancel_all_orders()
                self.log_activity(f"Cancelled {cancelled} orders")
                self.update_status(f"Cancelled {cancelled} orders")
                self.refresh_orders_table()
            else:
                self.log_activity("Cannot cancel orders - broker not connected")
        except Exception as e:
            logger.error(f"Error cancelling orders: {e}")
            self.log_activity(f"Cancel error: {e}")
    
    def refresh_execution_status(self):
        """Refresh execution status and metrics."""
        try:
            if self.alpaca_broker and self.alpaca_broker.is_connected():
                # Update account info
                account = self.alpaca_broker.get_account()
                if account:
                    self.account_value.setText(f"${account.get('equity', 0):,.2f}")
                    self.cash_available.setText(f"${account.get('cash', 0):,.2f}")
                
                # Update order metrics
                self.refresh_order_metrics()
                self.refresh_orders_table()
                
        except Exception as e:
            logger.error(f"Error refreshing execution status: {e}")
    
    def refresh_order_metrics(self):
        """Refresh order metrics."""
        try:
            if self.alpaca_broker:
                orders = self.alpaca_broker.get_orders()
                pending = len([o for o in orders if o.get('status') == 'pending'])
                filled = len([o for o in orders if o.get('status') == 'filled'])
                cancelled = len([o for o in orders if o.get('status') == 'cancelled'])
                
                self.orders_pending.setText(str(pending))
                self.orders_filled.setText(str(filled))
                self.orders_cancelled.setText(str(cancelled))
                
        except Exception as e:
            logger.error(f"Error refreshing order metrics: {e}")
    
    def refresh_orders_table(self):
        """Refresh orders table."""
        try:
            if self.alpaca_broker:
                orders = self.alpaca_broker.get_orders()
                
                self.orders_table.setRowCount(len(orders))
                
                for row, order in enumerate(orders):
                    self.orders_table.setItem(row, 0, QTableWidgetItem(str(order.get('id', ''))))
                    self.orders_table.setItem(row, 1, QTableWidgetItem(order.get('symbol', '')))
                    self.orders_table.setItem(row, 2, QTableWidgetItem(order.get('type', '')))
                    self.orders_table.setItem(row, 3, QTableWidgetItem(order.get('side', '')))
                    self.orders_table.setItem(row, 4, QTableWidgetItem(str(order.get('quantity', ''))))
                    self.orders_table.setItem(row, 5, QTableWidgetItem(f"${order.get('price', 0):.2f}"))
                    
                    status = order.get('status', '')
                    status_item = QTableWidgetItem(status)
                    if status == 'filled':
                        status_item.setBackground(QColor(76, 175, 80, 100))  # Green
                    elif status == 'cancelled':
                        status_item.setBackground(QColor(244, 67, 54, 100))  # Red
                    elif status == 'pending':
                        status_item.setBackground(QColor(255, 152, 0, 100))  # Orange
                    self.orders_table.setItem(row, 6, status_item)
                    
                    # Format timestamp
                    timestamp = order.get('created_at', '')
                    if timestamp:
                        try:
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            formatted_time = dt.strftime('%H:%M:%S')
                        except:
                            formatted_time = timestamp
                    else:
                        formatted_time = ''
                    self.orders_table.setItem(row, 7, QTableWidgetItem(formatted_time))
                
        except Exception as e:
            logger.error(f"Error refreshing orders table: {e}")
    
    def log_activity(self, message: str):
        """Log activity message."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.execution_log.append(f"[{timestamp}] {message}")
        self.activity_logged.emit(message)
    
    def update_status(self, message: str):
        """Update status message."""
        self.status_updated.emit(message) 