"""
User Database Manager

Handles all user-related database operations including profiles, 
authentication, and user preferences.
"""

import sqlite3
import logging
from typing import Dict, List, Optional, Any
from .base_manager import BaseDatabaseManager

logger = logging.getLogger(__name__)


class UserManager(BaseDatabaseManager):
    """
    Specialized manager for user operations.
    
    Features:
    - User creation and management
    - Risk profile management
    - User preferences and settings
    - Authentication support
    """
    
    def get_manager_type(self) -> str:
        """Return the type of manager for logging."""
        return "UserManager"
    
    def create_user(self, username: str, email: str = None, 
                   risk_profile: str = 'moderate') -> Optional[str]:
        """
        Create a new user.
        
        Args:
            username: Unique username
            email: User email
            risk_profile: Risk tolerance level
            
        Returns:
            User UID if successful, None otherwise
        """
        uid = self.generate_uid('user')
        
        # Get next available ID
        id_query = "SELECT COALESCE(MAX(id), 0) + 1 as next_id FROM users"
        id_result = self.execute_query(id_query)
        next_id = id_result[0]['next_id'] if id_result else 1
        
        query = """
        INSERT INTO users (uid, id, username, email, risk_profile)
        VALUES (?, ?, ?, ?, ?)
        """
        
        try:
            self.execute_update(query, (uid, next_id, username, email, risk_profile))
            logger.info(f"Created user: {username} ({uid})")
            return uid
        except sqlite3.IntegrityError as e:
            logger.error(f"Failed to create user {username}: {e}")
            return None
    
    def get_user(self, uid: str = None, username: str = None) -> Optional[Dict[str, Any]]:
        """
        Get user by UID or username.
        
        Args:
            uid: User UID
            username: Username
            
        Returns:
            User data dictionary or None
        """
        if uid:
            query = "SELECT * FROM users WHERE uid = ?"
            params = (uid,)
        elif username:
            query = "SELECT * FROM users WHERE username = ?"
            params = (username,)
        else:
            return None
        
        results = self.execute_query(query, params)
        return results[0] if results else None
    
    def update_user(self, uid: str, **kwargs) -> bool:
        """
        Update user data.
        
        Args:
            uid: User UID
            **kwargs: Fields to update
            
        Returns:
            True if successful
        """
        if not kwargs:
            return False
        
        # Build dynamic update query
        fields = []
        values = []
        for key, value in kwargs.items():
            if key in ['risk_profile', 'max_position_pct', 'stop_loss_pct', 
                      'take_profit_pct', 'is_active', 'email']:
                fields.append(f"{key} = ?")
                values.append(value)
        
        if not fields:
            return False
        
        values.append(uid)
        
        query = f"""
        UPDATE users 
        SET {', '.join(fields)}, updated_at = unixepoch()
        WHERE uid = ?
        """
        
        return self.execute_update(query, tuple(values)) > 0
    
    def delete_user(self, uid: str) -> bool:
        """
        Soft delete a user (set is_active = 0).
        
        Args:
            uid: User UID
            
        Returns:
            True if successful
        """
        query = "UPDATE users SET is_active = 0 WHERE uid = ?"
        return self.execute_update(query, (uid,)) > 0
    
    def get_all_users(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """
        Get all users.
        
        Args:
            active_only: Only return active users
            
        Returns:
            List of user data dictionaries
        """
        if active_only:
            query = "SELECT * FROM users WHERE is_active = 1 ORDER BY created_at DESC"
        else:
            query = "SELECT * FROM users ORDER BY created_at DESC"
        
        return self.execute_query(query)
    
    def validate_user_credentials(self, username: str, password_hash: str = None) -> Optional[str]:
        """
        Validate user credentials (placeholder for future authentication).
        
        Args:
            username: Username
            password_hash: Hashed password (not implemented yet)
            
        Returns:
            User UID if valid, None otherwise
        """
        user = self.get_user(username=username)
        if user and user['is_active']:
            return user['uid']
        return None
    
    def get_user_statistics(self) -> Dict[str, Any]:
        """
        Get user statistics.
        
        Returns:
            Dictionary with user statistics
        """
        stats = {}
        
        # Total users
        total_query = "SELECT COUNT(*) as total FROM users"
        total_result = self.execute_query(total_query)
        stats['total_users'] = total_result[0]['total'] if total_result else 0
        
        # Active users
        active_query = "SELECT COUNT(*) as active FROM users WHERE is_active = 1"
        active_result = self.execute_query(active_query)
        stats['active_users'] = active_result[0]['active'] if active_result else 0
        
        # Risk profile distribution
        risk_query = """
        SELECT risk_profile, COUNT(*) as count 
        FROM users 
        WHERE is_active = 1 
        GROUP BY risk_profile
        """
        risk_results = self.execute_query(risk_query)
        stats['risk_distribution'] = {row['risk_profile']: row['count'] for row in risk_results}
        
        return stats 