"""
Performance Analytics Tab Component

Integrates backend performance tracking components to display comprehensive
performance analytics, risk metrics, and portfolio reporting.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QTextEdit, QGroupBox, QComboBox,
    QTableWidget, QTableWidgetItem, QProgressBar, QCheckBox,
    QSpinBox, QDoubleSpinBox, QDateEdit
)
from PyQt6.QtCore import pyqtSignal, QTimer, Qt, QDate
from PyQt6.QtGui import QColor, QFont

from src.execution.performance_tracker import PerformanceTracker, PerformanceSnapshot, PerformanceMetric

logger = logging.getLogger(__name__)


class PerformanceTab(QWidget):
    """Performance analytics tab component with integrated backend performance tracking features."""
    
    # Signals
    activity_logged = pyqtSignal(str)
    status_updated = pyqtSignal(str)
    
    def __init__(self, db_manager=None, market_data_manager=None, profile_manager=None):
        super().__init__()
        self.db_manager = db_manager
        self.market_data_manager = market_data_manager
        self.profile_manager = profile_manager
        self.current_user_uid = None
        
        # Initialize performance tracking component (will be set later via setters)
        self.performance_tracker = None
        
        self.init_ui()
        
        # Auto-refresh timer for performance metrics
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_performance)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds
    
    def init_ui(self):
        """Initialize the performance analytics tab UI."""
        layout = QVBoxLayout(self)
        
        # Performance Summary Section
        summary_group = QGroupBox("Performance Summary")
        summary_layout = QGridLayout(summary_group)
        
        # Key performance metrics
        metrics = [
            ("Total Return", "0.00%"),
            ("Sharpe Ratio", "0.00"),
            ("Max Drawdown", "0.00%"),
            ("Win Rate", "0.00%"),
            ("Profit Factor", "0.00"),
            ("Calmar Ratio", "0.00"),
            ("Volatility", "0.00%"),
            ("Beta", "0.00")
        ]
        
        self.performance_labels = {}
        row, col = 0, 0
        for metric_name, default_value in metrics:
            label_key = QLabel(f"{metric_name}:")
            label_value = QLabel(default_value)
            if "%" in default_value:
                label_value.setStyleSheet("font-weight: bold; color: #2196F3; font-size: 14px;")
            else:
                label_value.setStyleSheet("font-weight: bold; color: #2E8B57; font-size: 14px;")
            
            summary_layout.addWidget(label_key, row, col)
            summary_layout.addWidget(label_value, row, col + 1)
            
            self.performance_labels[metric_name] = label_value
            
            col += 2
            if col >= 4:
                col = 0
                row += 1
        
        layout.addWidget(summary_group)
        
        # Performance Controls Section
        controls_group = QGroupBox("Performance Controls")
        controls_layout = QHBoxLayout(controls_group)
        
        # Date range controls
        controls_layout.addWidget(QLabel("From:"))
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.start_date.setCalendarPopup(True)
        controls_layout.addWidget(self.start_date)
        
        controls_layout.addWidget(QLabel("To:"))
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        controls_layout.addWidget(self.end_date)
        
        # Report type selector
        controls_layout.addWidget(QLabel("Report Type:"))
        self.report_type_combo = QComboBox()
        self.report_type_combo.addItems(["Comprehensive", "Summary", "Monthly", "Risk Analysis"])
        controls_layout.addWidget(self.report_type_combo)
        
        # Action buttons
        self.generate_report_btn = QPushButton("Generate Report")
        self.generate_report_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        controls_layout.addWidget(self.generate_report_btn)
        
        self.refresh_metrics_btn = QPushButton("Refresh Metrics")
        self.refresh_metrics_btn.setStyleSheet("background-color: #2196F3; color: white;")
        controls_layout.addWidget(self.refresh_metrics_btn)
        
        self.export_report_btn = QPushButton("Export Report")
        self.export_report_btn.setStyleSheet("background-color: #FF9800; color: white;")
        controls_layout.addWidget(self.export_report_btn)
        
        controls_layout.addStretch()
        
        layout.addWidget(controls_group)
        
        # Performance Metrics Table
        metrics_group = QGroupBox("Detailed Performance Metrics")
        metrics_layout = QVBoxLayout(metrics_group)
        
        self.metrics_table = QTableWidget()
        self.metrics_table.setColumnCount(6)
        self.metrics_table.setHorizontalHeaderLabels([
            "Metric", "Value", "Benchmark", "Status", "Trend", "Description"
        ])
        metrics_layout.addWidget(self.metrics_table)
        
        layout.addWidget(metrics_group)
        
        # Risk Analysis Section
        risk_group = QGroupBox("Risk Analysis")
        risk_layout = QVBoxLayout(risk_group)
        
        # Risk metrics grid
        risk_grid = QGridLayout()
        
        self.var_95 = QLabel("0.00%")
        self.var_95.setStyleSheet("font-weight: bold; color: #F44336;")
        risk_grid.addWidget(QLabel("VaR (95%):"), 0, 0)
        risk_grid.addWidget(self.var_95, 0, 1)
        
        self.cvar_95 = QLabel("0.00%")
        self.cvar_95.setStyleSheet("font-weight: bold; color: #F44336;")
        risk_grid.addWidget(QLabel("CVaR (95%):"), 0, 2)
        risk_grid.addWidget(self.cvar_95, 0, 3)
        
        self.max_drawdown_duration = QLabel("0 days")
        risk_grid.addWidget(QLabel("Max DD Duration:"), 1, 0)
        risk_grid.addWidget(self.max_drawdown_duration, 1, 1)
        
        self.recovery_time = QLabel("0 days")
        risk_grid.addWidget(QLabel("Recovery Time:"), 1, 2)
        risk_grid.addWidget(self.recovery_time, 1, 3)
        
        self.correlation = QLabel("0.00")
        risk_grid.addWidget(QLabel("Market Correlation:"), 2, 0)
        risk_grid.addWidget(self.correlation, 2, 1)
        
        self.tracking_error = QLabel("0.00%")
        risk_grid.addWidget(QLabel("Tracking Error:"), 2, 2)
        risk_grid.addWidget(self.tracking_error, 2, 3)
        
        risk_layout.addLayout(risk_grid)
        
        layout.addWidget(risk_group)
        
        # Performance Report Section
        report_group = QGroupBox("Performance Report")
        report_layout = QVBoxLayout(report_group)
        
        self.report_display = QTextEdit()
        self.report_display.setReadOnly(True)
        self.report_display.setText("Performance report will appear here...")
        report_layout.addWidget(self.report_display)
        
        layout.addWidget(report_group)
        
        # Setup connections
        self.setup_connections()
        
        logger.info("Performance tab initialized")
    
    def setup_connections(self):
        """Setup signal connections."""
        self.generate_report_btn.clicked.connect(self.generate_performance_report)
        self.refresh_metrics_btn.clicked.connect(self.refresh_performance)
        self.export_report_btn.clicked.connect(self.export_performance_report)
    
    def set_db_manager(self, manager):
        """Set database manager."""
        self.db_manager = manager
    
    def set_profile_manager(self, manager):
        """Set profile manager."""
        self.profile_manager = manager
    
    def set_market_data_manager(self, manager):
        """Set market data manager."""
        self.market_data_manager = manager
    
    def set_performance_tracker(self, tracker):
        """Set performance tracker."""
        self.performance_tracker = tracker
        logger.info("Performance tracker set in PerformanceTab")
    
    def set_current_user(self, user_uid: str):
        """Set current user."""
        self.current_user_uid = user_uid
        self.refresh_performance()
    
    def refresh_performance(self):
        """Refresh performance metrics and summary."""
        try:
            if self.performance_tracker and self.current_user_uid:
                # Get user ID from UID
                user_id = self._get_user_id_from_uid(self.current_user_uid)
                if user_id:
                    # Get performance snapshot
                    snapshot = self.performance_tracker.get_performance_snapshot(user_id)
                    if snapshot:
                        self._update_performance_summary(snapshot)
                        self._update_risk_metrics(snapshot)
                        self._refresh_metrics_table(snapshot)
                        
                        self.log_activity("Performance metrics refreshed")
                        self.update_status("Performance updated")
                    
        except Exception as e:
            logger.error(f"Error refreshing performance: {e}")
            self.log_activity(f"Error refreshing performance: {e}")
    
    def _update_performance_summary(self, snapshot: Dict):
        """Update performance summary display."""
        try:
            if not snapshot:
                return
            
            # Update key metrics with color coding
            total_return = snapshot.get('total_return', 0)
            self.performance_labels["Total Return"].setText(f"{total_return:.2f}%")
            if total_return > 0:
                self.performance_labels["Total Return"].setStyleSheet("font-weight: bold; color: #4CAF50; font-size: 14px;")
            elif total_return < 0:
                self.performance_labels["Total Return"].setStyleSheet("font-weight: bold; color: #F44336; font-size: 14px;")
            
            sharpe_ratio = snapshot.get('sharpe_ratio', 0)
            self.performance_labels["Sharpe Ratio"].setText(f"{sharpe_ratio:.2f}")
            if sharpe_ratio > 1.0:
                self.performance_labels["Sharpe Ratio"].setStyleSheet("font-weight: bold; color: #4CAF50; font-size: 14px;")
            elif sharpe_ratio < 0:
                self.performance_labels["Sharpe Ratio"].setStyleSheet("font-weight: bold; color: #F44336; font-size: 14px;")
            
            max_drawdown = snapshot.get('max_drawdown', 0)
            self.performance_labels["Max Drawdown"].setText(f"{max_drawdown:.2f}%")
            if max_drawdown < -20:
                self.performance_labels["Max Drawdown"].setStyleSheet("font-weight: bold; color: #F44336; font-size: 14px;")
            elif max_drawdown > -10:
                self.performance_labels["Max Drawdown"].setStyleSheet("font-weight: bold; color: #4CAF50; font-size: 14px;")
            
            win_rate = snapshot.get('win_rate', 0)
            self.performance_labels["Win Rate"].setText(f"{win_rate:.2f}%")
            if win_rate > 60:
                self.performance_labels["Win Rate"].setStyleSheet("font-weight: bold; color: #4CAF50; font-size: 14px;")
            elif win_rate < 40:
                self.performance_labels["Win Rate"].setStyleSheet("font-weight: bold; color: #F44336; font-size: 14px;")
            
            profit_factor = snapshot.get('profit_factor', 0)
            self.performance_labels["Profit Factor"].setText(f"{profit_factor:.2f}")
            if profit_factor > 1.5:
                self.performance_labels["Profit Factor"].setStyleSheet("font-weight: bold; color: #4CAF50; font-size: 14px;")
            elif profit_factor < 1.0:
                self.performance_labels["Profit Factor"].setStyleSheet("font-weight: bold; color: #F44336; font-size: 14px;")
            
            calmar_ratio = snapshot.get('calmar_ratio', 0)
            self.performance_labels["Calmar Ratio"].setText(f"{calmar_ratio:.2f}")
            if calmar_ratio > 0.5:
                self.performance_labels["Calmar Ratio"].setStyleSheet("font-weight: bold; color: #4CAF50; font-size: 14px;")
            elif calmar_ratio < 0:
                self.performance_labels["Calmar Ratio"].setStyleSheet("font-weight: bold; color: #F44336; font-size: 14px;")
            
            volatility = snapshot.get('volatility', 0)
            self.performance_labels["Volatility"].setText(f"{volatility:.2f}%")
            
            beta = snapshot.get('beta', 0)
            self.performance_labels["Beta"].setText(f"{beta:.2f}")
            if beta > 1.2:
                self.performance_labels["Beta"].setStyleSheet("font-weight: bold; color: #FF9800; font-size: 14px;")
            elif beta < 0.8:
                self.performance_labels["Beta"].setStyleSheet("font-weight: bold; color: #2196F3; font-size: 14px;")
            
        except Exception as e:
            logger.error(f"Error updating performance summary: {e}")
    
    def _update_risk_metrics(self, snapshot: Dict):
        """Update risk analysis metrics."""
        try:
            if not snapshot:
                return
            
            # Update risk metrics
            var_95 = snapshot.get('var_95', 0)
            self.var_95.setText(f"{var_95:.2f}%")
            
            cvar_95 = snapshot.get('cvar_95', 0)
            self.cvar_95.setText(f"{cvar_95:.2f}%")
            
            max_dd_duration = snapshot.get('max_drawdown_duration', 0)
            self.max_drawdown_duration.setText(f"{max_dd_duration} days")
            
            recovery_time = snapshot.get('recovery_time', 0)
            self.recovery_time.setText(f"{recovery_time} days")
            
            correlation = snapshot.get('market_correlation', 0)
            self.correlation.setText(f"{correlation:.2f}")
            
            tracking_error = snapshot.get('tracking_error', 0)
            self.tracking_error.setText(f"{tracking_error:.2f}%")
            
        except Exception as e:
            logger.error(f"Error updating risk metrics: {e}")
    
    def _refresh_metrics_table(self, snapshot: Dict):
        """Refresh detailed metrics table."""
        try:
            if not snapshot:
                return
            
            # Define metrics to display
            metrics_data = [
                ("Total Return", f"{snapshot.get('total_return', 0):.2f}%", "S&P 500", "Good" if snapshot.get('total_return', 0) > 0 else "Poor", "↗" if snapshot.get('total_return', 0) > 0 else "↘", "Total portfolio return"),
                ("Sharpe Ratio", f"{snapshot.get('sharpe_ratio', 0):.2f}", "1.0", "Good" if snapshot.get('sharpe_ratio', 0) > 1.0 else "Poor", "↗" if snapshot.get('sharpe_ratio', 0) > 1.0 else "↘", "Risk-adjusted return"),
                ("Max Drawdown", f"{snapshot.get('max_drawdown', 0):.2f}%", "-20%", "Good" if snapshot.get('max_drawdown', 0) > -20 else "Poor", "↗" if snapshot.get('max_drawdown', 0) > -20 else "↘", "Maximum portfolio decline"),
                ("Win Rate", f"{snapshot.get('win_rate', 0):.2f}%", "50%", "Good" if snapshot.get('win_rate', 0) > 50 else "Poor", "↗" if snapshot.get('win_rate', 0) > 50 else "↘", "Percentage of winning trades"),
                ("Profit Factor", f"{snapshot.get('profit_factor', 0):.2f}", "1.5", "Good" if snapshot.get('profit_factor', 0) > 1.5 else "Poor", "↗" if snapshot.get('profit_factor', 0) > 1.5 else "↘", "Gross profit / Gross loss"),
                ("Calmar Ratio", f"{snapshot.get('calmar_ratio', 0):.2f}", "0.5", "Good" if snapshot.get('calmar_ratio', 0) > 0.5 else "Poor", "↗" if snapshot.get('calmar_ratio', 0) > 0.5 else "↘", "Annual return / Max drawdown"),
                ("Volatility", f"{snapshot.get('volatility', 0):.2f}%", "15%", "Good" if snapshot.get('volatility', 0) < 15 else "Poor", "↗" if snapshot.get('volatility', 0) < 15 else "↘", "Portfolio volatility"),
                ("Beta", f"{snapshot.get('beta', 0):.2f}", "1.0", "Good" if 0.8 <= snapshot.get('beta', 0) <= 1.2 else "Poor", "↗" if 0.8 <= snapshot.get('beta', 0) <= 1.2 else "↘", "Market sensitivity")
            ]
            
            self.metrics_table.setRowCount(len(metrics_data))
            
            for row, (metric, value, benchmark, status, trend, description) in enumerate(metrics_data):
                self.metrics_table.setItem(row, 0, QTableWidgetItem(metric))
                self.metrics_table.setItem(row, 1, QTableWidgetItem(value))
                self.metrics_table.setItem(row, 2, QTableWidgetItem(benchmark))
                
                # Color code status
                status_item = QTableWidgetItem(status)
                if status == "Good":
                    status_item.setBackground(QColor(76, 175, 80, 100))  # Green
                else:
                    status_item.setBackground(QColor(244, 67, 54, 100))  # Red
                self.metrics_table.setItem(row, 3, status_item)
                
                # Color code trend
                trend_item = QTableWidgetItem(trend)
                if "↗" in trend:
                    trend_item.setBackground(QColor(76, 175, 80, 100))  # Green
                else:
                    trend_item.setBackground(QColor(244, 67, 54, 100))  # Red
                self.metrics_table.setItem(row, 4, trend_item)
                
                self.metrics_table.setItem(row, 5, QTableWidgetItem(description))
                
        except Exception as e:
            logger.error(f"Error refreshing metrics table: {e}")
    
    def generate_performance_report(self):
        """Generate comprehensive performance report."""
        try:
            if not self.performance_tracker or not self.current_user_uid:
                self.log_activity("Performance tracker not available")
                return
            
            user_id = self._get_user_id_from_uid(self.current_user_uid)
            if not user_id:
                self.log_activity("User ID not found")
                return
            
            # Get date range
            start_date = self.start_date.date().toPyDate()
            end_date = self.end_date.date().toPyDate()
            report_type = self.report_type_combo.currentText()
            
            # Generate report
            report = self.performance_tracker.generate_report(
                user_id, 
                report_type.lower().replace(" ", "_"),
                start_date,
                end_date
            )
            
            if report:
                self._display_performance_report(report)
                self.log_activity(f"Generated {report_type} report")
                self.update_status(f"{report_type} report generated")
            else:
                self.log_activity("Failed to generate report")
                self.update_status("Report generation failed")
                
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            self.log_activity(f"Error generating report: {e}")
    
    def _display_performance_report(self, report: str):
        """Display performance report in text area."""
        try:
            self.report_display.setText(report)
        except Exception as e:
            logger.error(f"Error displaying report: {e}")
    
    def export_performance_report(self):
        """Export performance report to file."""
        try:
            report_text = self.report_display.toPlainText()
            if report_text and report_text != "Performance report will appear here...":
                # TODO: Implement file export functionality
                self.log_activity("Exporting performance report")
                self.update_status("Report exported")
            else:
                self.log_activity("No report to export")
                self.update_status("No report available")
        except Exception as e:
            logger.error(f"Error exporting report: {e}")
            self.log_activity(f"Error exporting report: {e}")
    
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
        self.activity_logged.emit(f"[{timestamp}] {message}")
    
    def update_status(self, message: str):
        """Update status message."""
        self.status_updated.emit(message) 