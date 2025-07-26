"""
Market Scanner Tab Component

Handles market scanning UI and functionality.
"""

import logging
from typing import Dict, List, Optional, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout,
    QPushButton, QLabel, QComboBox, QSpinBox,
    QGroupBox, QTableWidget, QTableWidgetItem, QMessageBox,
    QProgressBar
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt

logger = logging.getLogger(__name__)


class ScannerWorker(QThread):
    """Background worker for market scanning operations."""
    
    scan_complete = pyqtSignal(dict)
    scan_error = pyqtSignal(str)
    
    def __init__(self, scanner, scan_type: str, **kwargs):
        super().__init__()
        self.scanner = scanner
        self.scan_type = scan_type
        self.kwargs = kwargs
    
    def run(self):
        try:
            if self.scan_type == "top_movers":
                result = self.scanner.scan_top_movers(**self.kwargs)
            elif self.scan_type == "watchlist":
                result = self.scanner.scan_user_watchlists(**self.kwargs)
            elif self.scan_type == "intelligent":
                result = self.scanner.get_intelligent_symbols(**self.kwargs)
            else:
                raise ValueError(f"Unknown scan type: {self.scan_type}")
            
            self.scan_complete.emit(result)
        except Exception as e:
            self.scan_error.emit(str(e))


class MarketScannerTab(QWidget):
    """Market scanner tab component."""
    
    # Signals for communication with parent
    activity_logged = pyqtSignal(str)  # activity message
    status_updated = pyqtSignal(str)   # status message
    
    def __init__(self, market_scanner=None):
        super().__init__()
        self.market_scanner = market_scanner
        self.scanner_worker = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize the market scanner tab UI."""
        layout = QVBoxLayout(self)
        
        # Scanner Controls
        controls_group = QGroupBox("Market Scanner Controls")
        controls_layout = QGridLayout(controls_group)
        
        controls_layout.addWidget(QLabel("Scan Type:"), 0, 0)
        self.scan_type_combo = QComboBox()
        self.scan_type_combo.addItems(["Top Movers", "Intelligent Suggestions"])
        controls_layout.addWidget(self.scan_type_combo, 0, 1)
        
        controls_layout.addWidget(QLabel("Limit:"), 1, 0)
        self.scan_limit_spin = QSpinBox()
        self.scan_limit_spin.setRange(5, 100)
        self.scan_limit_spin.setValue(20)
        controls_layout.addWidget(self.scan_limit_spin, 1, 1)
        
        self.scan_btn = QPushButton("Start Scan")
        controls_layout.addWidget(self.scan_btn, 2, 0, 1, 2)
        
        layout.addWidget(controls_group)
        
        # Progress bar
        self.scan_progress = QProgressBar()
        self.scan_progress.setVisible(False)
        layout.addWidget(self.scan_progress)
        
        # Results display
        results_group = QGroupBox("Scan Results")
        results_layout = QVBoxLayout(results_group)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels([
            "Symbol", "Change %", "Price", "Volume", "Sector", "Category"
        ])
        
        # Set table properties for better visibility
        self.results_table.setAlternatingRowColors(True)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.results_table.setSortingEnabled(True)
        self.results_table.setMinimumHeight(300)
        
        results_layout.addWidget(self.results_table)
        layout.addWidget(results_group)
        
        layout.addStretch()
        
        # Connect signals
        self.setup_connections()
    
    def setup_connections(self):
        """Set up signal connections."""
        self.scan_btn.clicked.connect(self.start_market_scan)
    
    def set_market_scanner(self, market_scanner):
        """Set the market scanner instance."""
        self.market_scanner = market_scanner
    
    def start_market_scan(self):
        """Start a market scan operation."""
        try:
            if not self.market_scanner:
                QMessageBox.critical(self, "Error", "Market scanner not initialized")
                return
            
            # Get scan parameters
            scan_type = self.scan_type_combo.currentText()
            limit = self.scan_limit_spin.value()
            
            # Show progress
            self.scan_progress.setVisible(True)
            self.scan_progress.setRange(0, 0)  # Indeterminate progress
            self.scan_btn.setEnabled(False)
            
            # Start background scan
            if scan_type == "Top Movers":
                self.scanner_worker = ScannerWorker(
                    self.market_scanner, "top_movers", limit=limit
                )
            else:  # Intelligent Suggestions
                self.scanner_worker = ScannerWorker(
                    self.market_scanner, "intelligent", limit=limit
                )
            
            # Connect worker signals
            self.scanner_worker.scan_complete.connect(self.on_scan_complete)
            self.scanner_worker.scan_error.connect(self.on_scan_error)
            
            # Start the worker
            self.scanner_worker.start()
            
            self.activity_logged.emit(f"Started {scan_type} scan (limit: {limit})")
            self.status_updated.emit("Scanning market...")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start scan: {e}")
            self.reset_scan_ui()
            logger.error(f"Market scan failed: {e}")
    
    def on_scan_complete(self, results: Dict[str, Any]):
        """Handle scan completion."""
        try:
            self.reset_scan_ui()
            
            # Process results based on scan type
            scan_type = self.scan_type_combo.currentText()
            
            if scan_type == "Top Movers":
                self.display_top_movers_results(results)
            else:  # Intelligent Suggestions
                self.display_intelligent_results(results)
            
            self.activity_logged.emit(f"Completed {scan_type} scan")
            self.status_updated.emit("Scan completed successfully")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process scan results: {e}")
            logger.error(f"Scan result processing failed: {e}")
    
    def on_scan_error(self, error_message: str):
        """Handle scan error."""
        self.reset_scan_ui()
        QMessageBox.critical(self, "Scan Error", f"Scan failed: {error_message}")
        self.activity_logged.emit(f"Scan failed: {error_message}")
        self.status_updated.emit("Scan failed")
        logger.error(f"Market scan error: {error_message}")
    
    def display_top_movers_results(self, results: Dict[str, List[Dict[str, Any]]]):
        """Display top movers scan results."""
        try:
            gainers = results.get('gainers', [])
            losers = results.get('losers', [])
            all_movers = gainers + losers
            
            self.results_table.setRowCount(len(all_movers))
            
            for row, mover in enumerate(all_movers):
                symbol = mover.get('symbol', 'N/A')
                change_pct = mover.get('change_percent', 0)
                price = mover.get('price', 0)
                volume = mover.get('volume', 0)
                sector = mover.get('sector', 'N/A')
                
                # Determine category (gainer/loser)
                category = "Gainer" if change_pct > 0 else "Loser"
                
                # Set table items
                self.results_table.setItem(row, 0, QTableWidgetItem(symbol))
                self.results_table.setItem(row, 1, QTableWidgetItem(f"{change_pct:.2f}%"))
                self.results_table.setItem(row, 2, QTableWidgetItem(f"${price:.2f}"))
                self.results_table.setItem(row, 3, QTableWidgetItem(f"{volume:,}"))
                self.results_table.setItem(row, 4, QTableWidgetItem(sector))
                self.results_table.setItem(row, 5, QTableWidgetItem(category))
                
                # Color code based on change
                if change_pct > 0:
                    # Green for gainers
                    for col in range(6):
                        item = self.results_table.item(row, col)
                        if item:
                            item.setBackground(Qt.GlobalColor.green)
                else:
                    # Red for losers
                    for col in range(6):
                        item = self.results_table.item(row, col)
                        if item:
                            item.setBackground(Qt.GlobalColor.red)
            
            # Resize columns to content
            self.results_table.resizeColumnsToContents()
            
        except Exception as e:
            logger.error(f"Failed to display top movers results: {e}")
            raise
    
    def display_intelligent_results(self, results: Dict[str, Any]):
        """Display intelligent suggestions results."""
        try:
            suggestions = results.get('suggestions', [])
            
            self.results_table.setRowCount(len(suggestions))
            
            for row, suggestion in enumerate(suggestions):
                symbol = suggestion.get('symbol', 'N/A')
                score = suggestion.get('score', 0)
                price = suggestion.get('price', 0)
                volume = suggestion.get('volume', 0)
                sector = suggestion.get('sector', 'N/A')
                reason = suggestion.get('reason', 'N/A')
                
                # Set table items
                self.results_table.setItem(row, 0, QTableWidgetItem(symbol))
                self.results_table.setItem(row, 1, QTableWidgetItem(f"{score:.2f}"))
                self.results_table.setItem(row, 2, QTableWidgetItem(f"${price:.2f}"))
                self.results_table.setItem(row, 3, QTableWidgetItem(f"{volume:,}"))
                self.results_table.setItem(row, 4, QTableWidgetItem(sector))
                self.results_table.setItem(row, 5, QTableWidgetItem(reason))
            
            # Update headers for intelligent suggestions
            self.results_table.setHorizontalHeaderLabels([
                "Symbol", "Score", "Price", "Volume", "Sector", "Reason"
            ])
            
            # Resize columns to content
            self.results_table.resizeColumnsToContents()
            
        except Exception as e:
            logger.error(f"Failed to display intelligent results: {e}")
            raise
    
    def reset_scan_ui(self):
        """Reset the scan UI to default state."""
        self.scan_progress.setVisible(False)
        self.scan_btn.setEnabled(True)
        
        if self.scanner_worker:
            self.scanner_worker.quit()
            self.scanner_worker.wait()
            self.scanner_worker = None
    
    def get_scan_limit(self):
        """Get the current scan limit value."""
        return self.scan_limit_spin.value()
    
    def set_scan_limit(self, limit: int):
        """Set the scan limit value."""
        self.scan_limit_spin.setValue(limit)
    
    def get_scan_type(self):
        """Get the current scan type."""
        return self.scan_type_combo.currentText()
    
    def set_scan_type(self, scan_type: str):
        """Set the scan type."""
        index = self.scan_type_combo.findText(scan_type)
        if index >= 0:
            self.scan_type_combo.setCurrentIndex(index) 