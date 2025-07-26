"""
Profile Tab Component

Handles user profile management UI and functionality.
"""

import logging
from typing import Optional
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox,
    QGroupBox, QMessageBox
)
from PyQt6.QtCore import pyqtSignal

logger = logging.getLogger(__name__)


class ProfileTab(QWidget):
    """User profile management tab component."""
    
    # Signals for communication with parent
    profile_created = pyqtSignal(str)  # user_uid
    profile_loaded = pyqtSignal(str)   # user_uid
    activity_logged = pyqtSignal(str)  # activity message
    status_updated = pyqtSignal(str)   # status message
    
    def __init__(self, profile_manager=None):
        super().__init__()
        self.profile_manager = profile_manager
        self.current_user_uid = None
        self.init_ui()
    
    def init_ui(self):
        """Initialize the profile tab UI."""
        layout = QVBoxLayout(self)
        
        # User Profile Section
        profile_group = QGroupBox("User Profile Management")
        profile_layout = QGridLayout(profile_group)
        
        # Profile creation inputs
        profile_layout.addWidget(QLabel("Username:"), 0, 0)
        self.username_input = QLineEdit()
        profile_layout.addWidget(self.username_input, 0, 1)
        
        profile_layout.addWidget(QLabel("Email:"), 1, 0)
        self.email_input = QLineEdit()
        profile_layout.addWidget(self.email_input, 1, 1)
        
        profile_layout.addWidget(QLabel("Risk Profile:"), 2, 0)
        self.risk_profile_combo = QComboBox()
        self.risk_profile_combo.addItems(["conservative", "moderate", "aggressive"])
        profile_layout.addWidget(self.risk_profile_combo, 2, 1)
        
        # Profile action buttons
        button_layout = QHBoxLayout()
        self.create_profile_btn = QPushButton("Create Profile")
        self.load_profile_btn = QPushButton("Load Profile")
        self.update_profile_btn = QPushButton("Update Profile")
        
        button_layout.addWidget(self.create_profile_btn)
        button_layout.addWidget(self.load_profile_btn)
        button_layout.addWidget(self.update_profile_btn)
        profile_layout.addLayout(button_layout, 3, 0, 1, 2)
        
        layout.addWidget(profile_group)
        
        # Risk Assessment Section
        risk_group = QGroupBox("Risk Assessment")
        risk_layout = QGridLayout(risk_group)
        
        risk_layout.addWidget(QLabel("Investment Timeline:"), 0, 0)
        self.timeline_combo = QComboBox()
        self.timeline_combo.addItems(["short", "medium", "long"])
        risk_layout.addWidget(self.timeline_combo, 0, 1)
        
        risk_layout.addWidget(QLabel("Risk Tolerance:"), 1, 0)
        self.tolerance_combo = QComboBox()
        self.tolerance_combo.addItems(["low", "medium", "high"])
        risk_layout.addWidget(self.tolerance_combo, 1, 1)
        
        risk_layout.addWidget(QLabel("Experience Level:"), 2, 0)
        self.experience_combo = QComboBox()
        self.experience_combo.addItems(["beginner", "intermediate", "expert"])
        risk_layout.addWidget(self.experience_combo, 2, 1)
        
        risk_layout.addWidget(QLabel("Investment Goals:"), 3, 0)
        self.goals_combo = QComboBox()
        self.goals_combo.addItems(["conservative", "balanced", "aggressive"])
        risk_layout.addWidget(self.goals_combo, 3, 1)
        
        self.update_risk_btn = QPushButton("Update Risk Assessment")
        risk_layout.addWidget(self.update_risk_btn, 4, 0, 1, 2)
        
        layout.addWidget(risk_group)
        
        # Profile Display
        self.profile_display = QTextEdit()
        self.profile_display.setReadOnly(True)
        self.profile_display.setMaximumHeight(200)
        layout.addWidget(QLabel("Profile Information:"))
        layout.addWidget(self.profile_display)
        
        layout.addStretch()
        
        # Connect signals
        self.setup_connections()
    
    def setup_connections(self):
        """Set up signal connections."""
        self.create_profile_btn.clicked.connect(self.create_profile)
        self.load_profile_btn.clicked.connect(self.load_profile)
        self.update_profile_btn.clicked.connect(self.update_profile)
        self.update_risk_btn.clicked.connect(self.update_risk_assessment)
    
    def set_profile_manager(self, profile_manager):
        """Set the profile manager instance."""
        self.profile_manager = profile_manager
    
    def create_profile(self):
        """Create a new user profile."""
        try:
            username = self.username_input.text().strip()
            email = self.email_input.text().strip()
            risk_profile = self.risk_profile_combo.currentText()
            
            if not username or not email:
                QMessageBox.warning(self, "Warning", "Please enter username and email")
                return
            
            if not self.profile_manager:
                QMessageBox.critical(self, "Error", "Profile manager not initialized")
                return
            
            # Create user profile
            user_uid = self.profile_manager.create_user_profile(
                username=username,
                email=email,
                risk_profile=risk_profile
            )
            
            if user_uid:
                self.current_user_uid = user_uid
                QMessageBox.information(self, "Success", f"Profile created successfully!\nUser ID: {user_uid}")
                self.activity_logged.emit(f"Created profile for {username}")
                self.status_updated.emit(f"Profile created: {username}")
                self.profile_created.emit(user_uid)
                self.refresh_profile_display()
                
                # Clear inputs
                self.username_input.clear()
                self.email_input.clear()
            else:
                QMessageBox.critical(self, "Error", "Failed to create profile")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create profile: {e}")
            logger.error(f"Profile creation failed: {e}")
    
    def load_profile(self):
        """Load an existing user profile."""
        try:
            username = self.username_input.text().strip()
            
            if not username:
                QMessageBox.warning(self, "Warning", "Please enter username to load")
                return
            
            if not self.profile_manager:
                QMessageBox.critical(self, "Error", "Profile manager not initialized")
                return
            
            # Load user profile
            profile = self.profile_manager.get_user_profile_by_username(username=username)
            
            if profile and 'user' in profile:
                user_data = profile['user']
                self.current_user_uid = user_data['uid']
                self.email_input.setText(user_data.get('email', ''))
                self.risk_profile_combo.setCurrentText(user_data.get('risk_profile', 'moderate'))
                
                QMessageBox.information(self, "Success", f"Profile loaded successfully!")
                self.activity_logged.emit(f"Loaded profile for {username}")
                self.status_updated.emit(f"Profile loaded: {username}")
                self.profile_loaded.emit(self.current_user_uid)
                self.refresh_profile_display()
            else:
                QMessageBox.warning(self, "Warning", f"Profile not found for username: {username}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load profile: {e}")
            logger.error(f"Profile loading failed: {e}")
    
    def update_profile(self):
        """Update the current user profile."""
        try:
            if not self.current_user_uid:
                QMessageBox.warning(self, "Warning", "No profile loaded")
                return
            
            username = self.username_input.text().strip()
            email = self.email_input.text().strip()
            risk_profile = self.risk_profile_combo.currentText()
            
            if not username or not email:
                QMessageBox.warning(self, "Warning", "Please enter username and email")
                return
            
            # Update profile
            profile_data = {
                'username': username,
                'email': email,
                'risk_profile': risk_profile
            }
            
            success = self.profile_manager.update_user_profile(
                user_uid=self.current_user_uid,
                profile_data=profile_data
            )
            
            if success:
                QMessageBox.information(self, "Success", "Profile updated successfully!")
                self.activity_logged.emit(f"Updated profile for {username}")
                self.status_updated.emit(f"Profile updated: {username}")
                self.refresh_profile_display()
            else:
                QMessageBox.critical(self, "Error", "Failed to update profile")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update profile: {e}")
            logger.error(f"Profile update failed: {e}")
    
    def update_risk_assessment(self):
        """Update risk assessment for the current user."""
        try:
            if not self.current_user_uid:
                QMessageBox.warning(self, "Warning", "No profile loaded")
                return
            
            risk_data = {
                'investment_timeline': self.timeline_combo.currentText(),
                'risk_tolerance': self.tolerance_combo.currentText(),
                'experience_level': self.experience_combo.currentText(),
                'investment_goals': self.goals_combo.currentText()
            }
            
            success = self.profile_manager.update_risk_assessment(
                self.current_user_uid, risk_data
            )
            
            if success:
                QMessageBox.information(self, "Success", "Risk assessment updated!")
                self.activity_logged.emit("Updated risk assessment")
                self.status_updated.emit("Risk assessment updated")
                self.refresh_profile_display()
            else:
                QMessageBox.critical(self, "Error", "Failed to update risk assessment")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update risk assessment: {e}")
            logger.error(f"Risk assessment update failed: {e}")
    
    def refresh_profile_display(self):
        """Refresh the profile information display."""
        try:
            if not self.current_user_uid or not self.profile_manager:
                self.profile_display.clear()
                return
            
            profile = self.profile_manager.get_user_profile(user_uid=self.current_user_uid)
            if profile and 'user' in profile:
                user_data = profile['user']
                info_text = f"""
User ID: {user_data['uid']}
Username: {user_data['username']}
Email: {user_data.get('email', 'N/A')}
Risk Profile: {user_data.get('risk_profile', 'N/A')}
Created: {user_data.get('created_at', 'N/A')}
Last Updated: {user_data.get('updated_at', 'N/A')}
                """.strip()
                
                self.profile_display.setText(info_text)
            else:
                self.profile_display.setText("No profile information available")
                
        except Exception as e:
            self.profile_display.setText(f"Error loading profile: {e}")
            logger.error(f"Profile display refresh failed: {e}")
    
    def set_current_user(self, user_uid: str):
        """Set the current user UID."""
        self.current_user_uid = user_uid
        self.refresh_profile_display() 