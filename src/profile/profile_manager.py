"""
User Profile Management System

Handles user profile creation, risk assessment, investment goals,
watchlist configuration, and learning preferences.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from ..utils.database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class ProfileManager:
    """
    Comprehensive user profile management system.
    
    Features:
    - Risk tolerance assessment and management
    - Investment goals tracking
    - Smart watchlist configuration
    - Learning preferences and market interests
    - Personalized news and event filtering
    """
    
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize profile manager.
        
        Args:
            db_manager: Database manager instance
        """
        self.db = db_manager
        logger.info("Profile manager initialized")
    
    def create_user_profile(self, username: str, email: str = None, 
                          risk_profile: str = 'moderate') -> Optional[str]:
        """
        Create a new user profile.
        
        Args:
            username: Unique username
            email: User email
            risk_profile: Initial risk tolerance level
            
        Returns:
            User UID if successful, None otherwise
        """
        try:
            user_uid = self.db.create_user(username, email, risk_profile)
            if user_uid:
                logger.info(f"Created user profile: {username} ({user_uid})")
                return user_uid
            return None
        except Exception as e:
            logger.error(f"Failed to create user profile: {e}")
            return None
    
    def get_user_profile(self, user_uid: str) -> Optional[Dict[str, Any]]:
        """
        Get complete user profile data.
        
        Args:
            user_uid: User UID
            
        Returns:
            Complete user profile dictionary
        """
        try:
            user_data = self.db.get_user(uid=user_uid)
            if not user_data:
                return None
            
            # Get user watchlists
            watchlists = self.get_user_watchlists(user_uid)
            
            # Get user preferences
            preferences = self.get_user_preferences(user_uid)
            
            # Combine all profile data
            profile = {
                'user': user_data,
                'watchlists': watchlists,
                'preferences': preferences
            }
            
            return profile
        except Exception as e:
            logger.error(f"Failed to get user profile: {e}")
            return None
    
    def update_risk_profile(self, user_uid: str, risk_assessment: Dict[str, Any]) -> bool:
        """
        Update user risk profile based on assessment.
        
        Args:
            user_uid: User UID
            risk_assessment: Risk assessment data
            
        Returns:
            True if successful
        """
        try:
            # Calculate risk profile from assessment
            risk_score = self._calculate_risk_score(risk_assessment)
            risk_profile = self._determine_risk_profile(risk_score)
            
            # Update user profile
            success = self.db.update_user(user_uid, risk_profile=risk_profile)
            
            if success:
                logger.info(f"Updated risk profile for user {user_uid}: {risk_profile}")
            
            return success
        except Exception as e:
            logger.error(f"Failed to update risk profile: {e}")
            return False
    
    def _calculate_risk_score(self, assessment: Dict[str, Any]) -> int:
        """
        Calculate risk score from assessment answers.
        
        Args:
            assessment: Risk assessment data
            
        Returns:
            Risk score (0-100)
        """
        score = 0
        
        # Investment timeline
        timeline = assessment.get('investment_timeline', 'medium')
        timeline_scores = {'short': 20, 'medium': 50, 'long': 80}
        score += timeline_scores.get(timeline, 50)
        
        # Risk tolerance
        tolerance = assessment.get('risk_tolerance', 'medium')
        tolerance_scores = {'low': 20, 'medium': 50, 'high': 80}
        score += tolerance_scores.get(tolerance, 50)
        
        # Investment experience
        experience = assessment.get('experience', 'medium')
        experience_scores = {'beginner': 30, 'medium': 50, 'expert': 70}
        score += experience_scores.get(experience, 50)
        
        # Financial goals
        goals = assessment.get('goals', 'growth')
        goal_scores = {'income': 30, 'growth': 60, 'aggressive': 80}
        score += goal_scores.get(goals, 60)
        
        return min(score, 100)
    
    def _determine_risk_profile(self, score: int) -> str:
        """
        Determine risk profile from score.
        
        Args:
            score: Risk score (0-100)
            
        Returns:
            Risk profile string
        """
        if score < 30:
            return 'conservative'
        elif score < 70:
            return 'moderate'
        else:
            return 'aggressive'
    
    def create_watchlist(self, user_uid: str, name: str, 
                        description: str = None, is_default: bool = False) -> Optional[str]:
        """
        Create a new watchlist for user.
        
        Args:
            user_uid: User UID
            name: Watchlist name
            description: Watchlist description
            is_default: Whether this is the default watchlist
            
        Returns:
            Watchlist UID if successful, None otherwise
        """
        try:
            # Get user ID
            user_data = self.db.get_user(uid=user_uid)
            if not user_data:
                return None
            
            user_id = user_data['id']
            
            # Create watchlist
            watchlist_uid = self.db.market_data.create_watchlist(
                user_id, name, description, is_default
            )
            
            if watchlist_uid:
                logger.info(f"Created watchlist '{name}' for user {user_uid}")
            
            return watchlist_uid
        except Exception as e:
            logger.error(f"Failed to create watchlist: {e}")
            return None
    
    def add_symbol_to_watchlist(self, watchlist_uid: str, symbol: str, 
                               priority: int = 0, notes: str = None) -> bool:
        """
        Add symbol to watchlist.
        
        Args:
            watchlist_uid: Watchlist UID
            symbol: Stock symbol
            priority: User-defined priority (0-10)
            notes: User notes about symbol
            
        Returns:
            True if successful
        """
        try:
            # Get or create symbol
            symbol_uid = self.db.get_or_create_symbol(symbol)
            if not symbol_uid:
                return False
            
            # Add to watchlist
            success = self.db.market_data.add_symbol_to_watchlist(
                watchlist_uid, symbol_uid, priority, notes
            )
            
            if success:
                logger.info(f"Added {symbol} to watchlist {watchlist_uid}")
            
            return success
        except Exception as e:
            logger.error(f"Failed to add symbol to watchlist: {e}")
            return False
    
    def get_user_watchlists(self, user_uid: str) -> List[Dict[str, Any]]:
        """
        Get all watchlists for user with symbols included.
        
        Args:
            user_uid: User UID
            
        Returns:
            List of watchlist data with symbols included
        """
        try:
            user_data = self.db.get_user(uid=user_uid)
            if not user_data:
                return []
            
            user_id = user_data['id']
            watchlists = self.db.market_data.get_user_watchlists(user_id)
            
            # Add symbols to each watchlist
            for watchlist in watchlists:
                watchlist_uid = watchlist['uid']
                symbols = self.db.market_data.get_watchlist_symbols(watchlist_uid)
                watchlist['symbols'] = symbols
            
            return watchlists
        except Exception as e:
            logger.error(f"Failed to get user watchlists: {e}")
            return []
    
    def update_user_preferences(self, user_uid: str, preferences: Dict[str, Any]) -> bool:
        """
        Update user preferences and learning settings.
        
        Args:
            user_uid: User UID
            preferences: User preferences data
            
        Returns:
            True if successful
        """
        try:
            # Update user profile with preferences
            update_data = {}
            
            # Risk management preferences
            if 'max_position_pct' in preferences:
                update_data['max_position_pct'] = preferences['max_position_pct']
            if 'stop_loss_pct' in preferences:
                update_data['stop_loss_pct'] = preferences['stop_loss_pct']
            if 'take_profit_pct' in preferences:
                update_data['take_profit_pct'] = preferences['take_profit_pct']
            
            # Update user
            success = self.db.update_user(user_uid, **update_data)
            
            if success:
                logger.info(f"Updated preferences for user {user_uid}")
            
            return success
        except Exception as e:
            logger.error(f"Failed to update user preferences: {e}")
            return False
    
    def get_user_preferences(self, user_uid: str) -> Dict[str, Any]:
        """
        Get user preferences and settings.
        
        Args:
            user_uid: User UID
            
        Returns:
            User preferences dictionary
        """
        try:
            user_data = self.db.get_user(uid=user_uid)
            if not user_data:
                return {}
            
            # Extract preferences from user data
            preferences = {
                'risk_profile': user_data.get('risk_profile', 'moderate'),
                'max_position_pct': user_data.get('max_position_pct', 0.1),
                'stop_loss_pct': user_data.get('stop_loss_pct', 0.05),
                'take_profit_pct': user_data.get('take_profit_pct', 0.15),
                'investment_goals': user_data.get('investment_goals', ''),
                'market_interests': user_data.get('market_interests', ''),
                'news_preferences': user_data.get('news_preferences', '')
            }
            
            return preferences
        except Exception as e:
            logger.error(f"Failed to get user preferences: {e}")
            return {}
    
    def get_risk_assessment_questions(self) -> List[Dict[str, Any]]:
        """
        Get risk assessment questions.
        
        Returns:
            List of assessment questions
        """
        return [
            {
                'id': 'investment_timeline',
                'question': 'What is your investment timeline?',
                'type': 'choice',
                'options': [
                    {'value': 'short', 'label': 'Less than 3 years'},
                    {'value': 'medium', 'label': '3-10 years'},
                    {'value': 'long', 'label': 'More than 10 years'}
                ]
            },
            {
                'id': 'risk_tolerance',
                'question': 'How do you feel about investment risk?',
                'type': 'choice',
                'options': [
                    {'value': 'low', 'label': 'I prefer stable, low-risk investments'},
                    {'value': 'medium', 'label': 'I can handle moderate ups and downs'},
                    {'value': 'high', 'label': 'I\'m comfortable with significant volatility'}
                ]
            },
            {
                'id': 'experience',
                'question': 'What is your investment experience level?',
                'type': 'choice',
                'options': [
                    {'value': 'beginner', 'label': 'New to investing'},
                    {'value': 'medium', 'label': 'Some experience'},
                    {'value': 'expert', 'label': 'Experienced investor'}
                ]
            },
            {
                'id': 'goals',
                'question': 'What are your primary investment goals?',
                'type': 'choice',
                'options': [
                    {'value': 'income', 'label': 'Generate regular income'},
                    {'value': 'growth', 'label': 'Long-term growth'},
                    {'value': 'aggressive', 'label': 'Maximum growth potential'}
                ]
            }
        ]
    
    def validate_profile_data(self, profile_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate user profile data.
        
        Args:
            profile_data: Profile data to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Validate username
        username = profile_data.get('username', '').strip()
        if not username:
            errors.append("Username is required")
        elif len(username) < 3:
            errors.append("Username must be at least 3 characters")
        
        # Validate email (optional but if provided, must be valid)
        email = profile_data.get('email', '').strip()
        if email and '@' not in email:
            errors.append("Invalid email format")
        
        # Validate risk profile
        risk_profile = profile_data.get('risk_profile', '')
        valid_risk_profiles = ['conservative', 'moderate', 'aggressive']
        if risk_profile and risk_profile not in valid_risk_profiles:
            errors.append(f"Invalid risk profile. Must be one of: {', '.join(valid_risk_profiles)}")
        
        # Validate position percentages
        max_position = profile_data.get('max_position_pct', 0.1)
        if not (0 < max_position <= 1):
            errors.append("Max position percentage must be between 0 and 1")
        
        return len(errors) == 0, errors
    
    def get_user_profile_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile by username.
        
        Args:
            username: Username to search for
            
        Returns:
            User profile dictionary or None if not found
        """
        try:
            user_data = self.db.get_user(username=username)
            if not user_data:
                return None
            
            # Get user watchlists
            watchlists = self.get_user_watchlists(user_data['uid'])
            
            # Get user preferences
            preferences = self.get_user_preferences(user_data['uid'])
            
            # Combine all profile data
            profile = {
                'user': user_data,
                'watchlists': watchlists,
                'preferences': preferences
            }
            
            return profile
        except Exception as e:
            logger.error(f"Failed to get user profile by username: {e}")
            return None
    
    def update_user_profile(self, user_uid: str, profile_data: Dict[str, Any]) -> bool:
        """
        Update user profile data.
        
        Args:
            user_uid: User UID
            profile_data: Updated profile data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate the data first
            is_valid, errors = self.validate_profile_data(profile_data)
            if not is_valid:
                logger.error(f"Invalid profile data: {errors}")
                return False
            
            # Update user data
            success = self.db.update_user(
                uid=user_uid,
                username=profile_data.get('username'),
                email=profile_data.get('email'),
                risk_profile=profile_data.get('risk_profile')
            )
            
            if success:
                logger.info(f"Updated user profile: {user_uid}")
                return True
            else:
                logger.error(f"Failed to update user profile: {user_uid}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update user profile: {e}")
            return False 