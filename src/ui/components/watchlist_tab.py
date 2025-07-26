"""
Watchlist Tab Component

Handles watchlist management UI and functionality.
"""

import logging
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout,
    QPushButton, QLabel, QLineEdit, QSpinBox,
    QGroupBox, QTableWidget, QTableWidgetItem, QMessageBox
)
from PyQt6.QtCore import pyqtSignal

logger = logging.getLogger(__name__)


class WatchlistTab(QWidget):
    """Watchlist management tab component."""
    
    # Signals for communication with parent
    activity_logged = pyqtSignal(str)  # activity message
    status_updated = pyqtSignal(str)   # status message
    
    def __init__(self, profile_manager=None):
        super().__init__()
        self.profile_manager = profile_manager
        self.current_user_uid = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize the watchlist tab UI."""
        layout = QVBoxLayout(self)
        
        # Watchlist Creation
        create_group = QGroupBox("Create Watchlist")
        create_layout = QGridLayout(create_group)
        
        create_layout.addWidget(QLabel("Watchlist Name:"), 0, 0)
        self.watchlist_name_input = QLineEdit()
        create_layout.addWidget(self.watchlist_name_input, 0, 1)
        
        create_layout.addWidget(QLabel("Description:"), 1, 0)
        self.watchlist_desc_input = QLineEdit()
        create_layout.addWidget(self.watchlist_desc_input, 1, 1)
        
        self.create_watchlist_btn = QPushButton("Create Watchlist")
        create_layout.addWidget(self.create_watchlist_btn, 2, 0, 1, 2)
        
        layout.addWidget(create_group)
        
        # Add Symbols
        symbols_group = QGroupBox("Add Symbols to Watchlist")
        symbols_layout = QGridLayout(symbols_group)
        
        symbols_layout.addWidget(QLabel("Symbol:"), 0, 0)
        self.symbol_input = QLineEdit()
        symbols_layout.addWidget(self.symbol_input, 0, 1)
        
        symbols_layout.addWidget(QLabel("Priority:"), 1, 0)
        self.priority_spin = QSpinBox()
        self.priority_spin.setRange(1, 10)
        self.priority_spin.setValue(5)
        symbols_layout.addWidget(self.priority_spin, 1, 1)
        
        symbols_layout.addWidget(QLabel("Notes:"), 2, 0)
        self.notes_input = QLineEdit()
        symbols_layout.addWidget(self.notes_input, 2, 1)
        
        self.add_symbol_btn = QPushButton("Add Symbol")
        symbols_layout.addWidget(self.add_symbol_btn, 3, 0, 1, 2)
        
        layout.addWidget(symbols_group)
        
        # Watchlist Display
        self.watchlist_table = QTableWidget()
        self.watchlist_table.setColumnCount(5)
        self.watchlist_table.setHorizontalHeaderLabels([
            "Symbol", "Priority", "Notes", "Added Date", "Actions"
        ])
        layout.addWidget(QLabel("Current Watchlist:"))
        layout.addWidget(self.watchlist_table)
        
        layout.addStretch()
        
        # Connect signals
        self.setup_connections()
    
    def setup_connections(self):
        """Set up signal connections."""
        self.create_watchlist_btn.clicked.connect(self.create_watchlist)
        self.add_symbol_btn.clicked.connect(self.add_symbol_to_watchlist)
    
    def set_profile_manager(self, profile_manager):
        """Set the profile manager instance."""
        self.profile_manager = profile_manager
    
    def set_current_user(self, user_uid: str):
        """Set the current user UID."""
        self.current_user_uid = user_uid
        self.refresh_watchlist_display()
    
    def create_watchlist(self):
        """Create a new watchlist."""
        try:
            if not self.current_user_uid:
                QMessageBox.warning(self, "Warning", "No profile loaded")
                return
            
            name = self.watchlist_name_input.text().strip()
            description = self.watchlist_desc_input.text().strip()
            
            if not name:
                QMessageBox.warning(self, "Warning", "Please enter watchlist name")
                return
            
            if not self.profile_manager:
                QMessageBox.critical(self, "Error", "Profile manager not initialized")
                return
            
            # Create watchlist
            watchlist_uid = self.profile_manager.create_watchlist(
                user_uid=self.current_user_uid,
                name=name,
                description=description
            )
            
            if watchlist_uid:
                QMessageBox.information(self, "Success", f"Watchlist '{name}' created successfully!")
                self.activity_logged.emit(f"Created watchlist '{name}'")
                self.status_updated.emit(f"Created watchlist: {name}")
                
                # Clear inputs
                self.watchlist_name_input.clear()
                self.watchlist_desc_input.clear()
                
                # Refresh display
                self.refresh_watchlist_display()
            else:
                QMessageBox.critical(self, "Error", "Failed to create watchlist")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create watchlist: {e}")
            logger.error(f"Watchlist creation failed: {e}")
    
    def add_symbol_to_watchlist(self):
        """Add a symbol to the current watchlist."""
        try:
            if not self.current_user_uid:
                QMessageBox.warning(self, "Warning", "No profile loaded")
                return
            
            symbol = self.symbol_input.text().strip().upper()
            priority = self.priority_spin.value()
            notes = self.notes_input.text().strip()
            
            if not symbol:
                QMessageBox.warning(self, "Warning", "Please enter a symbol")
                return
            
            if not self.profile_manager:
                QMessageBox.critical(self, "Error", "Profile manager not initialized")
                return
            
            # Get user's watchlists
            watchlists = self.profile_manager.get_user_watchlists(self.current_user_uid)
            if not watchlists:
                QMessageBox.warning(self, "Warning", "No watchlist found. Please create a watchlist first.")
                return
            
            # Use the first watchlist (or could let user select)
            watchlist_uid = watchlists[0]['uid']
            
            # Add symbol to watchlist
            success = self.profile_manager.add_symbol_to_watchlist(
                watchlist_uid=watchlist_uid,
                symbol=symbol,
                priority=priority,
                notes=notes
            )
            
            if success:
                QMessageBox.information(self, "Success", f"Added {symbol} to watchlist")
                self.activity_logged.emit(f"Added {symbol} to watchlist")
                self.status_updated.emit(f"Added symbol: {symbol}")
                
                # Clear inputs
                self.symbol_input.clear()
                self.notes_input.clear()
                
                # Refresh display
                self.refresh_watchlist_display()
            else:
                QMessageBox.critical(self, "Error", f"Failed to add {symbol} to watchlist")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add symbol: {e}")
            logger.error(f"Symbol addition failed: {e}")
    
    def remove_symbol_from_watchlist(self, symbol: str):
        """Remove a symbol from the watchlist."""
        try:
            if not self.current_user_uid:
                return
            
            watchlists = self.profile_manager.get_user_watchlists(self.current_user_uid)
            if watchlists:
                watchlist_uid = watchlists[0]['uid']
                success = self.profile_manager.remove_symbol_from_watchlist(watchlist_uid, symbol)
                
                if success:
                    self.activity_logged.emit(f"Removed {symbol} from watchlist")
                    self.status_updated.emit(f"Removed {symbol} from watchlist")
                    self.refresh_watchlist_display()
                else:
                    QMessageBox.warning(self, "Error", f"Failed to remove {symbol}")
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to remove symbol: {e}")
            logger.error(f"Symbol removal failed: {e}")
    
    def refresh_watchlist_display(self):
        """Refresh the watchlist display."""
        if not self.current_user_uid or not self.profile_manager:
            self.watchlist_table.setRowCount(0)
            return
        
        try:
            watchlists = self.profile_manager.get_user_watchlists(self.current_user_uid)
            if not watchlists:
                self.watchlist_table.setRowCount(0)
                return
            
            # Get symbols from first watchlist
            watchlist_uid = watchlists[0]['uid']
            symbols = self.profile_manager.get_watchlist_symbols(watchlist_uid)
            
            self.watchlist_table.setRowCount(len(symbols))
            
            for row, symbol_data in enumerate(symbols):
                self.watchlist_table.setItem(row, 0, QTableWidgetItem(symbol_data.get('symbol', '')))
                self.watchlist_table.setItem(row, 1, QTableWidgetItem(str(symbol_data.get('priority', ''))))
                self.watchlist_table.setItem(row, 2, QTableWidgetItem(symbol_data.get('notes', '')))
                self.watchlist_table.setItem(row, 3, QTableWidgetItem(symbol_data.get('added_at', '')))
                
                # Add remove button
                remove_btn = QPushButton("Remove")
                remove_btn.clicked.connect(lambda checked, s=symbol_data['symbol']: self.remove_symbol_from_watchlist(s))
                self.watchlist_table.setCellWidget(row, 4, remove_btn)
            
        except Exception as e:
            logger.error(f"Failed to refresh watchlist display: {e}")
    
    def get_watchlist_count(self) -> int:
        """Get the number of user watchlists."""
        if not self.current_user_uid or not self.profile_manager:
            return 0
        
        try:
            watchlists = self.profile_manager.get_user_watchlists(self.current_user_uid)
            return len(watchlists)
        except Exception:
            return 0
    
    def get_symbols_count(self) -> int:
        """Get the total number of symbols tracked."""
        if not self.current_user_uid or not self.profile_manager:
            return 0
        
        try:
            watchlists = self.profile_manager.get_user_watchlists(self.current_user_uid)
            total_symbols = 0
            for watchlist in watchlists:
                symbols = self.profile_manager.get_watchlist_symbols(watchlist['uid'])
                total_symbols += len(symbols)
            return total_symbols
        except Exception:
            return 0 