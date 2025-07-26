"""
Market Scanner System

Provides market scanning capabilities including Top 50 movers,
watchlist management, and news monitoring for ticker relevance.
"""

import logging
import threading
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from .api_client import APIClient
from .market_data import MarketDataManager
from ..utils.database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class MarketScanner:
    """
    Comprehensive market scanner system.
    
    Features:
    - Top 50 movers scanner (gainers and losers)
    - Market-wide data filtering and analysis
    - User watchlist management and monitoring
    - News and events monitoring for ticker relevance
    - Sentiment analysis integration
    - Intelligent symbol selection and prioritization
    """
    
    def __init__(self, db_manager: DatabaseManager, max_workers: int = 4):
        """
        Initialize market scanner.
        
        Args:
            db_manager: Database manager instance
            max_workers: Maximum number of worker threads
        """
        self.db = db_manager
        self.api_client = APIClient()
        self.market_data = MarketDataManager()
        self.max_workers = max_workers
        
        # Scanner state
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._scan_thread = None
        
        # Statistics
        self.stats = {
            'scans_completed': 0,
            'symbols_scanned': 0,
            'api_calls': 0,
            'cache_hits': 0,
            'last_scan': None,
            'scan_duration': 0
        }
        
        logger.info("Market scanner initialized")
    
    def scan_top_movers(self, limit: int = 50, include_volume: bool = True) -> Dict[str, List[Dict[str, Any]]]:
        """
        Scan for top gainers and losers in the market.
        
        Args:
            limit: Number of movers to return (default 50)
            include_volume: Whether to include volume data
            
        Returns:
            Dictionary with 'gainers' and 'losers' lists
        """
        try:
            start_time = time.time()
            logger.info(f"Starting top {limit} movers scan")
            
            # Get market movers from API
            movers_data = self.api_client.get_market_movers(limit=limit)
            
            if not movers_data:
                logger.warning("No market movers data received")
                return {'gainers': [], 'losers': []}
            
            # Process and categorize movers
            gainers = []
            losers = []
            
            for mover in movers_data:
                symbol = mover.get('symbol', '')
                change_pct = mover.get('change_percent', 0)
                volume = mover.get('volume', 0)
                price = mover.get('price', 0)
                
                mover_info = {
                    'symbol': symbol,
                    'change_percent': change_pct,
                    'price': price,
                    'volume': volume if include_volume else None,
                    'market_cap': mover.get('market_cap'),
                    'sector': mover.get('sector'),
                    'scanned_at': datetime.now().isoformat()
                }
                
                if change_pct > 0:
                    gainers.append(mover_info)
                else:
                    losers.append(mover_info)
            
            # Sort by absolute change percentage
            gainers.sort(key=lambda x: abs(x['change_percent']), reverse=True)
            losers.sort(key=lambda x: abs(x['change_percent']), reverse=True)
            
            # Limit results
            gainers = gainers[:limit]
            losers = losers[:limit]
            
            # Store in database for tracking
            self._store_market_movers(gainers + losers)
            
            # Update statistics
            scan_duration = time.time() - start_time
            self.stats['scans_completed'] += 1
            self.stats['symbols_scanned'] += len(gainers) + len(losers)
            self.stats['last_scan'] = datetime.now()
            self.stats['scan_duration'] = scan_duration
            
            logger.info(f"Top movers scan completed: {len(gainers)} gainers, {len(losers)} losers in {scan_duration:.2f}s")
            
            return {
                'gainers': gainers,
                'losers': losers,
                'scan_metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'duration': scan_duration,
                    'total_symbols': len(gainers) + len(losers)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to scan top movers: {e}")
            return {'gainers': [], 'losers': []}
    
    def _store_market_movers(self, movers: List[Dict[str, Any]]) -> bool:
        """
        Store market movers data in database.
        
        Args:
            movers: List of market mover data
            
        Returns:
            True if successful
        """
        try:
            for mover in movers:
                symbol = mover['symbol']
                
                # Get or create symbol
                symbol_uid = self.db.get_or_create_symbol(symbol)
                if not symbol_uid:
                    continue
                
                # Store market mover data
                self.db.market_data.store_market_mover(
                    symbol_uid=symbol_uid,
                    change_percent=mover['change_percent'],
                    volume=mover.get('volume'),
                    price=mover['price'],
                    market_cap=mover.get('market_cap'),
                    sector=mover.get('sector')
                )
            
            return True
        except Exception as e:
            logger.error(f"Failed to store market movers: {e}")
            return False
    
    def scan_user_watchlists(self, user_uid: str) -> Dict[str, Any]:
        """
        Scan symbols in user watchlists for updates.
        
        Args:
            user_uid: User UID
            
        Returns:
            Watchlist scan results
        """
        try:
            # Get user watchlists
            watchlists = self.db.market_data.get_user_watchlists(user_uid)
            
            if not watchlists:
                return {'watchlists': [], 'updates': []}
            
            updates = []
            
            for watchlist in watchlists:
                watchlist_uid = watchlist['uid']
                symbols = self.db.market_data.get_watchlist_symbols(watchlist_uid)
                
                watchlist_updates = {
                    'watchlist_name': watchlist['name'],
                    'watchlist_uid': watchlist_uid,
                    'symbols': []
                }
                
                for symbol_data in symbols:
                    symbol = symbol_data['symbol']
                    
                    # Get latest market data
                    market_data = self.api_client.get_stock_data(symbol, days=1)
                    
                    if market_data:
                        latest_data = market_data[0] if market_data else {}
                        
                        symbol_update = {
                            'symbol': symbol,
                            'current_price': latest_data.get('close', 0),
                            'change_percent': latest_data.get('change_percent', 0),
                            'volume': latest_data.get('volume', 0),
                            'last_updated': datetime.now().isoformat(),
                            'user_priority': symbol_data.get('priority', 0),
                            'user_notes': symbol_data.get('notes', '')
                        }
                        
                        watchlist_updates['symbols'].append(symbol_update)
                
                updates.append(watchlist_updates)
            
            return {
                'watchlists': watchlists,
                'updates': updates,
                'scan_metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'total_watchlists': len(watchlists),
                    'total_symbols': sum(len(u['symbols']) for u in updates)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to scan user watchlists: {e}")
            return {'watchlists': [], 'updates': []}
    
    def scan_news_for_symbols(self, symbols: List[str], hours_back: int = 24) -> Dict[str, List[Dict[str, Any]]]:
        """
        Scan news for specific symbols.
        
        Args:
            symbols: List of symbols to scan news for
            hours_back: Hours of news history to retrieve
            
        Returns:
            News data organized by symbol
        """
        try:
            news_results = {}
            
            for symbol in symbols:
                # Get news for symbol
                news_data = self.api_client.get_news_for_symbol(symbol, hours_back=hours_back)
                
                if news_data:
                    # Process and categorize news
                    processed_news = []
                    
                    for article in news_data:
                        processed_article = {
                            'title': article.get('title', ''),
                            'summary': article.get('summary', ''),
                            'url': article.get('url', ''),
                            'published_at': article.get('published_at', ''),
                            'source': article.get('source', ''),
                            'sentiment': article.get('sentiment', 'neutral'),
                            'relevance_score': article.get('relevance_score', 0.5)
                        }
                        
                        processed_news.append(processed_article)
                    
                    # Sort by relevance and recency
                    processed_news.sort(key=lambda x: (x['relevance_score'], x['published_at']), reverse=True)
                    
                    news_results[symbol] = processed_news
                else:
                    news_results[symbol] = []
            
            # Store news data in database
            self._store_news_data(news_results)
            
            return news_results
            
        except Exception as e:
            logger.error(f"Failed to scan news for symbols: {e}")
            return {}
    
    def _store_news_data(self, news_data: Dict[str, List[Dict[str, Any]]]) -> bool:
        """
        Store news data in database.
        
        Args:
            news_data: News data organized by symbol
            
        Returns:
            True if successful
        """
        try:
            for symbol, articles in news_data.items():
                # Get symbol UID
                symbol_uid = self.db.get_or_create_symbol(symbol)
                if not symbol_uid:
                    continue
                
                for article in articles:
                    # Store news article
                    self.db.market_data.store_news_article(
                        symbol_uid=symbol_uid,
                        title=article['title'],
                        summary=article['summary'],
                        url=article['url'],
                        published_at=article['published_at'],
                        source=article['source'],
                        sentiment=article['sentiment'],
                        relevance_score=article['relevance_score']
                    )
            
            return True
        except Exception as e:
            logger.error(f"Failed to store news data: {e}")
            return False
    
    def get_intelligent_symbols(self, user_uid: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get intelligent symbol suggestions based on user preferences.
        
        Args:
            user_uid: User UID
            limit: Maximum number of symbols to return
            
        Returns:
            List of suggested symbols with reasoning
        """
        try:
            # Get user profile and preferences
            user_data = self.db.get_user(uid=user_uid)
            if not user_data:
                return []
            
            risk_profile = user_data.get('risk_profile', 'moderate')
            
            # Get top movers
            movers = self.scan_top_movers(limit=100)
            
            # Filter based on user preferences
            filtered_symbols = []
            
            # Process gainers and losers
            for category in ['gainers', 'losers']:
                symbols = movers.get(category, [])
                for symbol_data in symbols:
                    symbol = symbol_data['symbol']
                    change_pct = symbol_data['change_percent']
                    
                    # Apply risk-based filtering
                    if self._is_symbol_suitable_for_risk(symbol_data, risk_profile):
                        filtered_symbols.append({
                            'symbol': symbol,
                            'change_percent': change_pct,
                            'price': symbol_data['price'],
                            'volume': symbol_data.get('volume'),
                            'sector': symbol_data.get('sector'),
                            'category': category,
                            'reasoning': self._generate_symbol_reasoning(symbol_data, risk_profile),
                            'risk_score': self._calculate_symbol_risk_score(symbol_data)
                        })
            
            # Sort by relevance and limit results
            filtered_symbols.sort(key=lambda x: abs(x['change_percent']), reverse=True)
            filtered_symbols = filtered_symbols[:limit]
            
            return filtered_symbols
            
        except Exception as e:
            logger.error(f"Failed to get intelligent symbols: {e}")
            return []
    
    def _is_symbol_suitable_for_risk(self, symbol_data: Dict[str, Any], risk_profile: str) -> bool:
        """
        Check if symbol is suitable for user's risk profile.
        
        Args:
            symbol_data: Symbol market data
            risk_profile: User's risk profile
            
        Returns:
            True if suitable
        """
        change_pct = abs(symbol_data.get('change_percent', 0))
        volume = symbol_data.get('volume', 0)
        market_cap = symbol_data.get('market_cap', 0)
        
        if risk_profile == 'conservative':
            # Conservative: Low volatility, high volume, large cap
            return change_pct < 5 and volume > 1000000 and market_cap > 1000000000
        elif risk_profile == 'moderate':
            # Moderate: Medium volatility, reasonable volume
            return change_pct < 15 and volume > 500000
        else:
            # Aggressive: Higher volatility acceptable
            return change_pct < 30 and volume > 100000
    
    def _generate_symbol_reasoning(self, symbol_data: Dict[str, Any], risk_profile: str) -> str:
        """
        Generate reasoning for symbol suggestion.
        
        Args:
            symbol_data: Symbol market data
            risk_profile: User's risk profile
            
        Returns:
            Reasoning string
        """
        change_pct = symbol_data.get('change_percent', 0)
        volume = symbol_data.get('volume', 0)
        sector = symbol_data.get('sector', 'Unknown')
        
        if change_pct > 0:
            direction = "gaining"
        else:
            direction = "declining"
        
        reasoning = f"{symbol_data['symbol']} is {direction} {abs(change_pct):.1f}% "
        reasoning += f"with strong volume ({volume:,}) in {sector} sector. "
        
        if risk_profile == 'conservative':
            reasoning += "Suitable for conservative investors due to moderate volatility."
        elif risk_profile == 'moderate':
            reasoning += "Good balance of risk and potential for moderate investors."
        else:
            reasoning += "High potential for aggressive investors seeking growth."
        
        return reasoning
    
    def _calculate_symbol_risk_score(self, symbol_data: Dict[str, Any]) -> float:
        """
        Calculate risk score for symbol (0-1, higher = more risky).
        
        Args:
            symbol_data: Symbol market data
            
        Returns:
            Risk score
        """
        change_pct = abs(symbol_data.get('change_percent', 0))
        volume = symbol_data.get('volume', 0)
        market_cap = symbol_data.get('market_cap', 0)
        
        # Normalize factors
        volatility_score = min(change_pct / 50, 1.0)  # 50% change = max volatility
        volume_score = max(0, 1 - (volume / 10000000))  # Higher volume = lower risk
        cap_score = max(0, 1 - (market_cap / 100000000000))  # Higher cap = lower risk
        
        # Weighted average
        risk_score = (volatility_score * 0.5 + volume_score * 0.3 + cap_score * 0.2)
        
        return min(risk_score, 1.0)
    
    def start_continuous_scanning(self, interval_minutes: int = 15):
        """
        Start continuous market scanning in background thread.
        
        Args:
            interval_minutes: Scan interval in minutes
        """
        if self._scan_thread and self._scan_thread.is_alive():
            logger.warning("Continuous scanning already running")
            return
        
        self._stop_event.clear()
        self._scan_thread = threading.Thread(
            target=self._continuous_scan_worker,
            args=(interval_minutes,),
            daemon=True
        )
        self._scan_thread.start()
        logger.info(f"Started continuous scanning with {interval_minutes} minute interval")
    
    def stop_continuous_scanning(self):
        """Stop continuous market scanning."""
        self._stop_event.set()
        if self._scan_thread:
            self._scan_thread.join(timeout=5)
        logger.info("Stopped continuous scanning")
    
    def _continuous_scan_worker(self, interval_minutes: int):
        """Background worker for continuous scanning."""
        while not self._stop_event.is_set():
            try:
                # Perform scan
                self.scan_top_movers()
                
                # Wait for next scan
                self._stop_event.wait(interval_minutes * 60)
                
            except Exception as e:
                logger.error(f"Error in continuous scan worker: {e}")
                self._stop_event.wait(60)  # Wait 1 minute on error
    
    def get_scan_statistics(self) -> Dict[str, Any]:
        """
        Get scanner statistics.
        
        Returns:
            Scanner statistics dictionary
        """
        return {
            'scans_completed': self.stats['scans_completed'],
            'symbols_scanned': self.stats['symbols_scanned'],
            'api_calls': self.stats['api_calls'],
            'cache_hits': self.stats['cache_hits'],
            'last_scan': self.stats['last_scan'].isoformat() if self.stats['last_scan'] else None,
            'average_scan_duration': self.stats['scan_duration'],
            'is_continuous_scanning': self._scan_thread and self._scan_thread.is_alive()
        } 