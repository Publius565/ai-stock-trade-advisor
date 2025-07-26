"""
Database Manager Factory for AI-Driven Stock Trade Advisor

Provides a factory pattern for accessing specialized database managers.
Maintains backward compatibility while using modular design.
"""

import logging
from typing import Optional
from .base_manager import BaseDatabaseManager
from .user_manager import UserManager
from .market_data_manager import MarketDataManager
from .signal_manager import SignalManager

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Factory for specialized database managers.
    
    Provides access to:
    - UserManager: User profiles and authentication
    - MarketDataManager: Market data and symbols
    - SignalManager: Trading signals and portfolio
    
    Maintains backward compatibility with legacy code.
    """
    
    def __init__(self, db_path: str = "data/trading_advisor.db"):
        """
        Initialize database manager factory.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        
        # Initialize specialized managers
        self.users = UserManager(db_path)
        self.market_data = MarketDataManager(db_path)
        self.signals = SignalManager(db_path)
        
        logger.info(f"Database manager factory initialized: {db_path}")
    
    def close(self):
        """Close all manager connections."""
        self.users.close()
        self.market_data.close()
        self.signals.close()
        logger.info("All database connections closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    # ============================================================================
    # LEGACY COMPATIBILITY METHODS
    # ============================================================================
    
    def generate_uid(self, prefix: str = "obj") -> str:
        """Generate UID using base manager method."""
        return self.users.generate_uid(prefix)
    
    # User management (delegate to UserManager)
    def create_user(self, username: str, email: str = None, 
                   risk_profile: str = 'moderate') -> Optional[str]:
        """Create user - delegates to UserManager."""
        return self.users.create_user(username, email, risk_profile)
    
    def get_user(self, uid: str = None, username: str = None):
        """Get user - delegates to UserManager."""
        return self.users.get_user(uid, username)
    
    def update_user(self, uid: str, **kwargs) -> bool:
        """Update user - delegates to UserManager."""
        return self.users.update_user(uid, **kwargs)
    
    # Symbol management (delegate to MarketDataManager)
    def get_or_create_symbol(self, symbol: str, name: str = None, 
                           sector: str = None) -> Optional[str]:
        """Get or create symbol - delegates to MarketDataManager."""
        return self.market_data.get_or_create_symbol(symbol, name, sector)
    
    def get_symbol(self, symbol: str):
        """Get symbol - delegates to MarketDataManager."""
        return self.market_data.get_symbol(symbol)
    
    # Market data management (delegate to MarketDataManager)
    def store_market_data(self, symbol: str, data_points: list) -> bool:
        """Store market data - delegates to MarketDataManager."""
        return self.market_data.store_market_data(symbol, data_points)
    
    def get_market_data(self, symbol: str, days: int = 30):
        """Get market data - delegates to MarketDataManager."""
        return self.market_data.get_market_data(symbol, days)
    
    # Signal management (delegate to SignalManager)
    def create_signal(self, user_uid: str, symbol: str, signal_type: str,
                     risk_level: str, confidence: float = None,
                     price_target: float = None, rationale: str = None) -> Optional[str]:
        """Create signal - delegates to SignalManager."""
        return self.signals.create_signal(user_uid, symbol, signal_type, 
                                         risk_level, confidence, price_target, rationale)
    
    def get_user_signals(self, user_uid: str, active_only: bool = True):
        """Get user signals - delegates to SignalManager."""
        return self.signals.get_user_signals(user_uid, active_only)
    
    # Portfolio management (delegate to SignalManager)
    def get_user_positions(self, user_uid: str):
        """Get user positions - delegates to SignalManager."""
        return self.signals.get_user_positions(user_uid)
    
    def get_portfolio_summary(self, user_uid: str):
        """Get portfolio summary - delegates to SignalManager."""
        return self.signals.get_portfolio_summary(user_uid)
 