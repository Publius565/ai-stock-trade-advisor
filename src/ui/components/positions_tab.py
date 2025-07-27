"""
Positions Tab Component

Integrates backend position monitoring components to display real-time portfolio
positions, P&L tracking, and position management.
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

from src.execution.position_monitor import PositionMonitor, Position, PositionStatus

logger = logging.getLogger(__name__)


class PositionsTab(QWidget):
    """Positions tab component with integrated backend position monitoring features."""
    
    # Signals
    activity_logged = pyqtSignal(str)
    status_updated = pyqtSignal(str)
    
    def __init__(self, db_manager=None, market_data_manager=None, profile_manager=None):
        super().__init__()
        self.db_manager = db_manager
        self.market_data_manager = market_data_manager
        self.profile_manager = profile_manager
        self.current_user_uid = None
        
        # Initialize position monitoring component (will be set later via setters)
        self.position_monitor = None
        
        self.init_ui()
        
        # Auto-refresh timer for positions
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_positions)
        self.refresh_timer.start(15000)  # Refresh every 15 seconds
    
    def init_ui(self):
        """Initialize the positions tab UI."""
        layout = QVBoxLayout(self)
        
        # Portfolio Summary Section
        portfolio_group = QGroupBox("Portfolio Summary")
        portfolio_layout = QGridLayout(portfolio_group)
        
        # Portfolio metrics
        metrics = [
            ("Total Positions", "0"),
            ("Total Market Value", "$0.00"),
            ("Total Unrealized P&L", "$0.00"),
            ("Total Realized P&L", "$0.00"),
            ("Total P&L", "$0.00"),
            ("Avg P&L %", "0.00%"),
            ("Top Performer", "N/A"),
            ("Worst Performer", "N/A")
        ]
        
        self.portfolio_labels = {}
        row, col = 0, 0
        for metric_name, default_value in metrics:
            label_key = QLabel(f"{metric_name}:")
            label_value = QLabel(default_value)
            if "$" in default_value:
                label_value.setStyleSheet("font-weight: bold; color: #2E8B57; font-size: 14px;")
            elif "%" in default_value:
                label_value.setStyleSheet("font-weight: bold; color: #2196F3; font-size: 14px;")
            else:
                label_value.setStyleSheet("font-weight: bold; color: #2E8B57; font-size: 14px;")
            
            portfolio_layout.addWidget(label_key, row, col)
            portfolio_layout.addWidget(label_value, row, col + 1)
            
            self.portfolio_labels[metric_name] = label_value
            
            col += 2
            if col >= 4:
                col = 0
                row += 1
        
        layout.addWidget(portfolio_group)
        
        # Position Management Section
        positions_group = QGroupBox("Position Management")
        positions_layout = QVBoxLayout(positions_group)
        
        # Position controls
        controls_layout = QHBoxLayout()
        
        self.refresh_positions_btn = QPushButton("Refresh Positions")
        self.refresh_positions_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        
        self.close_position_btn = QPushButton("Close Position")
        self.close_position_btn.setStyleSheet("background-color: #FF5722; color: white;")
        self.close_position_btn.setEnabled(False)
        
        self.add_position_btn = QPushButton("Add Position")
        self.add_position_btn.setStyleSheet("background-color: #2196F3; color: white;")
        
        controls_layout.addWidget(self.refresh_positions_btn)
        controls_layout.addWidget(self.close_position_btn)
        controls_layout.addWidget(self.add_position_btn)
        controls_layout.addStretch()
        
        positions_layout.addLayout(controls_layout)
        
        # Positions table
        self.positions_table = QTableWidget()
        self.positions_table.setColumnCount(10)
        self.positions_table.setHorizontalHeaderLabels([
            "Symbol", "Quantity", "Avg Price", "Current Price", "Market Value", 
            "Unrealized P&L", "P&L %", "Entry Date", "Status", "Actions"
        ])
        self.positions_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.positions_table.itemSelectionChanged.connect(self.on_position_selected)
        positions_layout.addWidget(self.positions_table)
        
        layout.addWidget(positions_group)
        
        # Position Details Section
        details_group = QGroupBox("Position Details")
        details_layout = QVBoxLayout(details_group)
        
        # Details grid
        details_grid = QGridLayout()
        
        self.detail_symbol = QLabel("N/A")
        self.detail_symbol.setStyleSheet("font-weight: bold; font-size: 16px;")
        details_grid.addWidget(QLabel("Symbol:"), 0, 0)
        details_grid.addWidget(self.detail_symbol, 0, 1)
        
        self.detail_quantity = QLabel("0")
        details_grid.addWidget(QLabel("Quantity:"), 0, 2)
        details_grid.addWidget(self.detail_quantity, 0, 3)
        
        self.detail_avg_price = QLabel("$0.00")
        details_grid.addWidget(QLabel("Average Price:"), 1, 0)
        details_grid.addWidget(self.detail_avg_price, 1, 1)
        
        self.detail_current_price = QLabel("$0.00")
        details_grid.addWidget(QLabel("Current Price:"), 1, 2)
        details_grid.addWidget(self.detail_current_price, 1, 3)
        
        self.detail_market_value = QLabel("$0.00")
        details_grid.addWidget(QLabel("Market Value:"), 2, 0)
        details_grid.addWidget(self.detail_market_value, 2, 1)
        
        self.detail_unrealized_pnl = QLabel("$0.00")
        details_grid.addWidget(QLabel("Unrealized P&L:"), 2, 2)
        details_grid.addWidget(self.detail_unrealized_pnl, 2, 3)
        
        self.detail_pnl_percentage = QLabel("0.00%")
        details_grid.addWidget(QLabel("P&L %:"), 3, 0)
        details_grid.addWidget(self.detail_pnl_percentage, 3, 1)
        
        self.detail_entry_date = QLabel("N/A")
        details_grid.addWidget(QLabel("Entry Date:"), 3, 2)
        details_grid.addWidget(self.detail_entry_date, 3, 3)
        
        details_layout.addLayout(details_grid)
        
        # Position actions
        actions_layout = QHBoxLayout()
        
        self.buy_more_btn = QPushButton("Buy More")
        self.buy_more_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        self.buy_more_btn.setEnabled(False)
        
        self.sell_some_btn = QPushButton("Sell Some")
        self.sell_some_btn.setStyleSheet("background-color: #FF9800; color: white;")
        self.sell_some_btn.setEnabled(False)
        
        self.close_all_btn = QPushButton("Close All")
        self.close_all_btn.setStyleSheet("background-color: #F44336; color: white;")
        self.close_all_btn.setEnabled(False)
        
        actions_layout.addWidget(self.buy_more_btn)
        actions_layout.addWidget(self.sell_some_btn)
        actions_layout.addWidget(self.close_all_btn)
        actions_layout.addStretch()
        
        details_layout.addLayout(actions_layout)
        
        layout.addWidget(details_group)
        
        # Recent Activity Section
        activity_group = QGroupBox("Recent Position Activity")
        activity_layout = QVBoxLayout(activity_group)
        
        self.activity_log = QTextEdit()
        self.activity_log.setMaximumHeight(120)
        self.activity_log.setReadOnly(True)
        self.activity_log.setText("Position activity will appear here...")
        activity_layout.addWidget(self.activity_log)
        
        layout.addWidget(activity_group)
        
        # Setup connections
        self.setup_connections()
        
        logger.info("Positions tab initialized")
    
    def setup_connections(self):
        """Setup signal connections."""
        self.refresh_positions_btn.clicked.connect(self.refresh_positions)
        self.close_position_btn.clicked.connect(self.close_selected_position)
        self.add_position_btn.clicked.connect(self.add_position)
        self.buy_more_btn.clicked.connect(self.buy_more)
        self.sell_some_btn.clicked.connect(self.sell_some)
        self.close_all_btn.clicked.connect(self.close_all_positions)
    
    def set_db_manager(self, manager):
        """Set database manager."""
        self.db_manager = manager
    
    def set_profile_manager(self, manager):
        """Set profile manager."""
        self.profile_manager = manager
    
    def set_market_data_manager(self, manager):
        """Set market data manager."""
        self.market_data_manager = manager
    
    def set_position_monitor(self, monitor):
        """Set position monitor."""
        self.position_monitor = monitor
        logger.info("Position monitor set in PositionsTab")
    
    def set_current_user(self, user_uid: str):
        """Set current user."""
        self.current_user_uid = user_uid
        self.refresh_positions()
    
    def refresh_positions(self):
        """Refresh all positions and portfolio summary."""
        try:
            if self.position_monitor and self.current_user_uid:
                # Get user ID from UID
                user_id = self._get_user_id_from_uid(self.current_user_uid)
                if user_id:
                    # Update positions
                    self.position_monitor.update_positions(user_id)
                    
                    # Get portfolio summary
                    summary = self.position_monitor.get_portfolio_summary(user_id)
                    self._update_portfolio_summary(summary)
                    
                    # Refresh positions table
                    self._refresh_positions_table(user_id)
                    
                    self.log_activity("Positions refreshed")
                    self.update_status("Positions updated")
                    
        except Exception as e:
            logger.error(f"Error refreshing positions: {e}")
            self.log_activity(f"Error refreshing positions: {e}")
    
    def _update_portfolio_summary(self, summary: Dict):
        """Update portfolio summary display."""
        try:
            if not summary:
                return
            
            # Update portfolio metrics
            self.portfolio_labels["Total Positions"].setText(str(summary.get('total_positions', 0)))
            self.portfolio_labels["Total Market Value"].setText(f"${summary.get('total_market_value', 0):,.2f}")
            
            unrealized_pnl = summary.get('total_unrealized_pnl', 0)
            realized_pnl = summary.get('total_realized_pnl', 0)
            total_pnl = unrealized_pnl + realized_pnl
            
            # Color code P&L values
            self.portfolio_labels["Total Unrealized P&L"].setText(f"${unrealized_pnl:,.2f}")
            self.portfolio_labels["Total Realized P&L"].setText(f"${realized_pnl:,.2f}")
            self.portfolio_labels["Total P&L"].setText(f"${total_pnl:,.2f}")
            
            # Color code P&L
            if unrealized_pnl > 0:
                self.portfolio_labels["Total Unrealized P&L"].setStyleSheet("font-weight: bold; color: #4CAF50; font-size: 14px;")
            elif unrealized_pnl < 0:
                self.portfolio_labels["Total Unrealized P&L"].setStyleSheet("font-weight: bold; color: #F44336; font-size: 14px;")
            
            if total_pnl > 0:
                self.portfolio_labels["Total P&L"].setStyleSheet("font-weight: bold; color: #4CAF50; font-size: 14px;")
            elif total_pnl < 0:
                self.portfolio_labels["Total P&L"].setStyleSheet("font-weight: bold; color: #F44336; font-size: 14px;")
            
            # Update percentage
            avg_pnl_percentage = summary.get('avg_pnl_percentage', 0)
            self.portfolio_labels["Avg P&L %"].setText(f"{avg_pnl_percentage:.2f}%")
            
            if avg_pnl_percentage > 0:
                self.portfolio_labels["Avg P&L %"].setStyleSheet("font-weight: bold; color: #4CAF50; font-size: 14px;")
            elif avg_pnl_percentage < 0:
                self.portfolio_labels["Avg P&L %"].setStyleSheet("font-weight: bold; color: #F44336; font-size: 14px;")
            
            # Update top performers
            top_performers = summary.get('top_performers', [])
            if top_performers:
                self.portfolio_labels["Top Performer"].setText(f"{top_performers[0].get('symbol', 'N/A')} ({top_performers[0].get('pnl_percentage', 0):.2f}%)")
                self.portfolio_labels["Worst Performer"].setText(f"{top_performers[-1].get('symbol', 'N/A')} ({top_performers[-1].get('pnl_percentage', 0):.2f}%)")
            
        except Exception as e:
            logger.error(f"Error updating portfolio summary: {e}")
    
    def _refresh_positions_table(self, user_id: int):
        """Refresh positions table."""
        try:
            if not self.position_monitor:
                return
            
            # Get user positions
            positions = self.position_monitor.get_user_positions(user_id)
            
            self.positions_table.setRowCount(len(positions))
            
            for row, position in enumerate(positions):
                # Symbol
                self.positions_table.setItem(row, 0, QTableWidgetItem(position.get('symbol', '')))
                
                # Quantity
                self.positions_table.setItem(row, 1, QTableWidgetItem(str(position.get('quantity', 0))))
                
                # Average price
                self.positions_table.setItem(row, 2, QTableWidgetItem(f"${position.get('avg_price', 0):.2f}"))
                
                # Current price
                current_price = position.get('current_price', 0)
                self.positions_table.setItem(row, 3, QTableWidgetItem(f"${current_price:.2f}"))
                
                # Market value
                market_value = position.get('market_value', 0)
                self.positions_table.setItem(row, 4, QTableWidgetItem(f"${market_value:.2f}"))
                
                # Unrealized P&L
                unrealized_pnl = position.get('unrealized_pnl', 0)
                pnl_item = QTableWidgetItem(f"${unrealized_pnl:.2f}")
                if unrealized_pnl > 0:
                    pnl_item.setBackground(QColor(76, 175, 80, 100))  # Green
                elif unrealized_pnl < 0:
                    pnl_item.setBackground(QColor(244, 67, 54, 100))  # Red
                self.positions_table.setItem(row, 5, pnl_item)
                
                # P&L percentage
                pnl_percentage = position.get('pnl_percentage', 0)
                pnl_pct_item = QTableWidgetItem(f"{pnl_percentage:.2f}%")
                if pnl_percentage > 0:
                    pnl_pct_item.setBackground(QColor(76, 175, 80, 100))  # Green
                elif pnl_percentage < 0:
                    pnl_pct_item.setBackground(QColor(244, 67, 54, 100))  # Red
                self.positions_table.setItem(row, 6, pnl_pct_item)
                
                # Entry date
                entry_date = position.get('entry_date', '')
                if entry_date:
                    try:
                        dt = datetime.fromtimestamp(entry_date)
                        formatted_date = dt.strftime('%Y-%m-%d')
                    except:
                        formatted_date = str(entry_date)
                else:
                    formatted_date = 'N/A'
                self.positions_table.setItem(row, 7, QTableWidgetItem(formatted_date))
                
                # Status
                status = position.get('status', 'active')
                status_item = QTableWidgetItem(status.title())
                if status == 'active':
                    status_item.setBackground(QColor(76, 175, 80, 100))  # Green
                elif status == 'closed':
                    status_item.setBackground(QColor(158, 158, 158, 100))  # Gray
                self.positions_table.setItem(row, 8, status_item)
                
                # Actions button
                actions_btn = QPushButton("Actions")
                actions_btn.setStyleSheet("background-color: #2196F3; color: white;")
                self.positions_table.setCellWidget(row, 9, actions_btn)
                
        except Exception as e:
            logger.error(f"Error refreshing positions table: {e}")
    
    def on_position_selected(self):
        """Handle position selection."""
        try:
            current_row = self.positions_table.currentRow()
            if current_row >= 0:
                # Enable position action buttons
                self.close_position_btn.setEnabled(True)
                self.buy_more_btn.setEnabled(True)
                self.sell_some_btn.setEnabled(True)
                self.close_all_btn.setEnabled(True)
                
                # Update position details
                self._update_position_details(current_row)
            else:
                # Disable position action buttons
                self.close_position_btn.setEnabled(False)
                self.buy_more_btn.setEnabled(False)
                self.sell_some_btn.setEnabled(False)
                self.close_all_btn.setEnabled(False)
                
                # Clear position details
                self._clear_position_details()
                
        except Exception as e:
            logger.error(f"Error handling position selection: {e}")
    
    def _update_position_details(self, row: int):
        """Update position details display."""
        try:
            # Get position data from table
            symbol = self.positions_table.item(row, 0).text()
            quantity = int(self.positions_table.item(row, 1).text())
            avg_price = float(self.positions_table.item(row, 2).text().replace('$', ''))
            current_price = float(self.positions_table.item(row, 3).text().replace('$', ''))
            market_value = float(self.positions_table.item(row, 4).text().replace('$', ''))
            unrealized_pnl = float(self.positions_table.item(row, 5).text().replace('$', ''))
            pnl_percentage = float(self.positions_table.item(row, 6).text().replace('%', ''))
            entry_date = self.positions_table.item(row, 7).text()
            
            # Update detail labels
            self.detail_symbol.setText(symbol)
            self.detail_quantity.setText(str(quantity))
            self.detail_avg_price.setText(f"${avg_price:.2f}")
            self.detail_current_price.setText(f"${current_price:.2f}")
            self.detail_market_value.setText(f"${market_value:.2f}")
            self.detail_unrealized_pnl.setText(f"${unrealized_pnl:.2f}")
            self.detail_pnl_percentage.setText(f"{pnl_percentage:.2f}%")
            self.detail_entry_date.setText(entry_date)
            
            # Color code P&L
            if unrealized_pnl > 0:
                self.detail_unrealized_pnl.setStyleSheet("font-weight: bold; color: #4CAF50;")
                self.detail_pnl_percentage.setStyleSheet("font-weight: bold; color: #4CAF50;")
            elif unrealized_pnl < 0:
                self.detail_unrealized_pnl.setStyleSheet("font-weight: bold; color: #F44336;")
                self.detail_pnl_percentage.setStyleSheet("font-weight: bold; color: #F44336;")
            
        except Exception as e:
            logger.error(f"Error updating position details: {e}")
    
    def _clear_position_details(self):
        """Clear position details display."""
        self.detail_symbol.setText("N/A")
        self.detail_quantity.setText("0")
        self.detail_avg_price.setText("$0.00")
        self.detail_current_price.setText("$0.00")
        self.detail_market_value.setText("$0.00")
        self.detail_unrealized_pnl.setText("$0.00")
        self.detail_pnl_percentage.setText("0.00%")
        self.detail_entry_date.setText("N/A")
    
    def close_selected_position(self):
        """Close the selected position."""
        try:
            current_row = self.positions_table.currentRow()
            if current_row >= 0:
                symbol = self.positions_table.item(current_row, 0).text()
                self.log_activity(f"Closing position: {symbol}")
                # TODO: Implement position closing logic
                self.update_status(f"Closing position: {symbol}")
        except Exception as e:
            logger.error(f"Error closing position: {e}")
            self.log_activity(f"Error closing position: {e}")
    
    def add_position(self):
        """Add a new position."""
        try:
            self.log_activity("Adding new position")
            # TODO: Implement position adding logic
            self.update_status("Adding new position")
        except Exception as e:
            logger.error(f"Error adding position: {e}")
            self.log_activity(f"Error adding position: {e}")
    
    def buy_more(self):
        """Buy more of the selected position."""
        try:
            current_row = self.positions_table.currentRow()
            if current_row >= 0:
                symbol = self.positions_table.item(current_row, 0).text()
                self.log_activity(f"Buying more: {symbol}")
                # TODO: Implement buy more logic
                self.update_status(f"Buying more: {symbol}")
        except Exception as e:
            logger.error(f"Error buying more: {e}")
            self.log_activity(f"Error buying more: {e}")
    
    def sell_some(self):
        """Sell some of the selected position."""
        try:
            current_row = self.positions_table.currentRow()
            if current_row >= 0:
                symbol = self.positions_table.item(current_row, 0).text()
                self.log_activity(f"Selling some: {symbol}")
                # TODO: Implement sell some logic
                self.update_status(f"Selling some: {symbol}")
        except Exception as e:
            logger.error(f"Error selling some: {e}")
            self.log_activity(f"Error selling some: {e}")
    
    def close_all_positions(self):
        """Close all positions."""
        try:
            self.log_activity("Closing all positions")
            # TODO: Implement close all positions logic
            self.update_status("Closing all positions")
        except Exception as e:
            logger.error(f"Error closing all positions: {e}")
            self.log_activity(f"Error closing all positions: {e}")
    
    def _get_user_id_from_uid(self, user_uid: str) -> Optional[int]:
        """Get user ID from UID."""
        try:
            if self.db_manager:
                query = "SELECT id FROM users WHERE uid = ?"
                result = self.db_manager.fetch_one(query, (user_uid,))
                return result[0] if result else None
        except Exception as e:
            logger.error(f"Error getting user ID from UID: {e}")
        return None
    
    def log_activity(self, message: str):
        """Log activity message."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.activity_log.append(f"[{timestamp}] {message}")
        self.activity_logged.emit(message)
    
    def update_status(self, message: str):
        """Update status message."""
        self.status_updated.emit(message) 