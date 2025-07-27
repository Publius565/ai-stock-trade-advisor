"""
Performance Tracker - Portfolio performance analytics and reporting
Part of Phase 4: Execution Layer implementation
"""

import logging
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ..utils.database_manager import DatabaseManager


class PerformanceMetric(Enum):
    """Performance metric types"""
    TOTAL_RETURN = "total_return"
    SHARPE_RATIO = "sharpe_ratio"
    MAX_DRAWDOWN = "max_drawdown"
    WIN_RATE = "win_rate"
    PROFIT_FACTOR = "profit_factor"
    CALMAR_RATIO = "calmar_ratio"


@dataclass
class PerformanceSnapshot:
    """Performance snapshot data structure"""
    date: datetime
    portfolio_value: float
    daily_return: float
    cumulative_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float


class PerformanceTracker:
    """
    Portfolio performance tracking and analytics system
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.logger = logging.getLogger(__name__)
        
        # Performance tracking
        self.risk_free_rate = 0.02  # 2% annual risk-free rate
        self.trading_days_per_year = 252
        
        self.logger.info("Performance Tracker initialized")
    
    def calculate_performance_metrics(self, user_id: int, start_date: Optional[datetime] = None, 
                                    end_date: Optional[datetime] = None) -> Dict:
        """
        Calculate comprehensive performance metrics for a user
        """
        try:
            # Get portfolio data
            portfolio_data = self._get_portfolio_data(user_id, start_date, end_date)
            if not portfolio_data:
                return {}
            
            # Calculate basic metrics
            total_return = self._calculate_total_return(portfolio_data)
            daily_returns = self._calculate_daily_returns(portfolio_data)
            
            # Calculate advanced metrics
            sharpe_ratio = self._calculate_sharpe_ratio(daily_returns)
            max_drawdown = self._calculate_max_drawdown(portfolio_data)
            win_rate = self._calculate_win_rate(user_id, start_date, end_date)
            profit_factor = self._calculate_profit_factor(user_id, start_date, end_date)
            calmar_ratio = self._calculate_calmar_ratio(total_return, max_drawdown)
            
            # Calculate volatility
            volatility = self._calculate_volatility(daily_returns)
            
            # Get performance breakdown
            performance_breakdown = self._get_performance_breakdown(user_id, start_date, end_date)
            
            return {
                'total_return': total_return,
                'annualized_return': self._annualize_return(total_return, len(portfolio_data)),
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'win_rate': win_rate,
                'profit_factor': profit_factor,
                'calmar_ratio': calmar_ratio,
                'volatility': volatility,
                'risk_adjusted_return': sharpe_ratio * volatility if volatility > 0 else 0,
                'performance_breakdown': performance_breakdown,
                'period_days': len(portfolio_data),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating performance metrics: {e}")
            return {}
    
    def _get_portfolio_data(self, user_id: int, start_date: Optional[datetime] = None, 
                           end_date: Optional[datetime] = None) -> List[Dict]:
        """Get portfolio value data over time"""
        try:
            query = """
                SELECT date, portfolio_value, daily_return, cumulative_return
                FROM performance
                WHERE user_id = ?
            """
            params = [user_id]
            
            if start_date:
                query += " AND date >= ?"
                params.append(int(start_date.timestamp()))
            
            if end_date:
                query += " AND date <= ?"
                params.append(int(end_date.timestamp()))
            
            query += " ORDER BY date ASC"
            
            results = self.db_manager.fetch_all(query, tuple(params))
            portfolio_data = []
            
            for row in results:
                portfolio_data.append({
                    'date': datetime.fromtimestamp(row[0]),
                    'portfolio_value': row[1],
                    'daily_return': row[2] or 0.0,
                    'cumulative_return': row[3] or 0.0
                })
            
            return portfolio_data
            
        except Exception as e:
            self.logger.error(f"Error getting portfolio data: {e}")
            return []
    
    def _calculate_total_return(self, portfolio_data: List[Dict]) -> float:
        """Calculate total return over the period"""
        if not portfolio_data:
            return 0.0
        
        initial_value = portfolio_data[0]['portfolio_value']
        final_value = portfolio_data[-1]['portfolio_value']
        
        if initial_value <= 0:
            return 0.0
        
        return (final_value - initial_value) / initial_value
    
    def _calculate_daily_returns(self, portfolio_data: List[Dict]) -> List[float]:
        """Calculate daily returns from portfolio data"""
        returns = []
        
        for i in range(1, len(portfolio_data)):
            prev_value = portfolio_data[i-1]['portfolio_value']
            curr_value = portfolio_data[i]['portfolio_value']
            
            if prev_value > 0:
                daily_return = (curr_value - prev_value) / prev_value
                returns.append(daily_return)
        
        return returns
    
    def _calculate_sharpe_ratio(self, daily_returns: List[float]) -> float:
        """Calculate Sharpe ratio"""
        if not daily_returns:
            return 0.0
        
        try:
            # Calculate average return
            avg_return = sum(daily_returns) / len(daily_returns)
            
            # Calculate standard deviation
            variance = sum((r - avg_return) ** 2 for r in daily_returns) / len(daily_returns)
            std_dev = math.sqrt(variance)
            
            if std_dev == 0:
                return 0.0
            
            # Annualize returns and volatility
            annualized_return = avg_return * self.trading_days_per_year
            annualized_volatility = std_dev * math.sqrt(self.trading_days_per_year)
            
            # Calculate Sharpe ratio
            sharpe_ratio = (annualized_return - self.risk_free_rate) / annualized_volatility
            
            return sharpe_ratio
            
        except Exception as e:
            self.logger.error(f"Error calculating Sharpe ratio: {e}")
            return 0.0
    
    def _calculate_max_drawdown(self, portfolio_data: List[Dict]) -> float:
        """Calculate maximum drawdown"""
        if not portfolio_data:
            return 0.0
        
        try:
            peak = portfolio_data[0]['portfolio_value']
            max_drawdown = 0.0
            
            for data in portfolio_data:
                value = data['portfolio_value']
                
                if value > peak:
                    peak = value
                else:
                    drawdown = (peak - value) / peak
                    max_drawdown = max(max_drawdown, drawdown)
            
            return max_drawdown
            
        except Exception as e:
            self.logger.error(f"Error calculating max drawdown: {e}")
            return 0.0
    
    def _calculate_win_rate(self, user_id: int, start_date: Optional[datetime] = None, 
                           end_date: Optional[datetime] = None) -> float:
        """Calculate win rate from trades"""
        try:
            query = """
                SELECT COUNT(*) as total_trades,
                       SUM(CASE WHEN (t.trade_type = 'buy' AND p.unrealized_pnl > 0) OR 
                                   (t.trade_type = 'sell' AND p.realized_pnl > 0) THEN 1 ELSE 0 END) as winning_trades
                FROM trades t
                LEFT JOIN positions p ON t.symbol_id = p.symbol_id AND t.user_id = p.user_id
                WHERE t.user_id = ? AND t.status = 'filled'
            """
            params = [user_id]
            
            if start_date:
                query += " AND t.trade_date >= ?"
                params.append(int(start_date.timestamp()))
            
            if end_date:
                query += " AND t.trade_date <= ?"
                params.append(int(end_date.timestamp()))
            
            result = self.db_manager.fetch_one(query, tuple(params))
            if result and result[0] > 0:
                return result[1] / result[0]
            
            return 0.0
            
        except Exception as e:
            self.logger.error(f"Error calculating win rate: {e}")
            return 0.0
    
    def _calculate_profit_factor(self, user_id: int, start_date: Optional[datetime] = None, 
                                end_date: Optional[datetime] = None) -> float:
        """Calculate profit factor (gross profit / gross loss)"""
        try:
            query = """
                SELECT 
                    SUM(CASE WHEN p.unrealized_pnl > 0 THEN p.unrealized_pnl ELSE 0 END) as gross_profit,
                    SUM(CASE WHEN p.unrealized_pnl < 0 THEN ABS(p.unrealized_pnl) ELSE 0 END) as gross_loss
                FROM positions p
                WHERE p.user_id = ? AND p.quantity > 0
            """
            params = [user_id]
            
            if start_date:
                query += " AND p.last_updated >= ?"
                params.append(int(start_date.timestamp()))
            
            if end_date:
                query += " AND p.last_updated <= ?"
                params.append(int(end_date.timestamp()))
            
            result = self.db_manager.fetch_one(query, tuple(params))
            if result and result[1] > 0:  # gross_loss > 0
                return result[0] / result[1]  # gross_profit / gross_loss
            
            return 0.0
            
        except Exception as e:
            self.logger.error(f"Error calculating profit factor: {e}")
            return 0.0
    
    def _calculate_calmar_ratio(self, total_return: float, max_drawdown: float) -> float:
        """Calculate Calmar ratio (annualized return / max drawdown)"""
        if max_drawdown == 0:
            return 0.0
        
        try:
            # Annualize the total return (assuming 1 year period)
            annualized_return = total_return
            
            return annualized_return / max_drawdown
            
        except Exception as e:
            self.logger.error(f"Error calculating Calmar ratio: {e}")
            return 0.0
    
    def _calculate_volatility(self, daily_returns: List[float]) -> float:
        """Calculate annualized volatility"""
        if not daily_returns:
            return 0.0
        
        try:
            avg_return = sum(daily_returns) / len(daily_returns)
            variance = sum((r - avg_return) ** 2 for r in daily_returns) / len(daily_returns)
            std_dev = math.sqrt(variance)
            
            # Annualize volatility
            annualized_volatility = std_dev * math.sqrt(self.trading_days_per_year)
            
            return annualized_volatility
            
        except Exception as e:
            self.logger.error(f"Error calculating volatility: {e}")
            return 0.0
    
    def _annualize_return(self, total_return: float, days: int) -> float:
        """Annualize return based on number of days"""
        if days <= 0:
            return 0.0
        
        try:
            # Convert to annualized return
            annualized_return = ((1 + total_return) ** (365 / days)) - 1
            return annualized_return
            
        except Exception as e:
            self.logger.error(f"Error annualizing return: {e}")
            return 0.0
    
    def _get_performance_breakdown(self, user_id: int, start_date: Optional[datetime] = None, 
                                  end_date: Optional[datetime] = None) -> Dict:
        """Get detailed performance breakdown"""
        try:
            # Get top performing symbols
            top_symbols = self._get_top_performing_symbols(user_id, start_date, end_date)
            
            # Get monthly performance
            monthly_performance = self._get_monthly_performance(user_id, start_date, end_date)
            
            # Get sector performance (if available)
            sector_performance = self._get_sector_performance(user_id, start_date, end_date)
            
            return {
                'top_symbols': top_symbols,
                'monthly_performance': monthly_performance,
                'sector_performance': sector_performance
            }
            
        except Exception as e:
            self.logger.error(f"Error getting performance breakdown: {e}")
            return {}
    
    def _get_top_performing_symbols(self, user_id: int, start_date: Optional[datetime] = None, 
                                   end_date: Optional[datetime] = None, limit: int = 10) -> List[Dict]:
        """Get top performing symbols"""
        try:
            query = """
                SELECT s.symbol, p.unrealized_pnl, p.realized_pnl, p.quantity, p.current_price
                FROM positions p
                JOIN symbols s ON p.symbol_id = s.id
                WHERE p.user_id = ? AND p.quantity > 0
            """
            params = [user_id]
            
            if start_date:
                query += " AND p.last_updated >= ?"
                params.append(int(start_date.timestamp()))
            
            if end_date:
                query += " AND p.last_updated <= ?"
                params.append(int(end_date.timestamp()))
            
            query += " ORDER BY (p.unrealized_pnl + p.realized_pnl) DESC LIMIT ?"
            params.append(limit)
            
            results = self.db_manager.fetch_all(query, tuple(params))
            symbols = []
            
            for row in results:
                total_pnl = (row[1] or 0.0) + (row[2] or 0.0)
                symbols.append({
                    'symbol': row[0],
                    'unrealized_pnl': row[1] or 0.0,
                    'realized_pnl': row[2] or 0.0,
                    'total_pnl': total_pnl,
                    'quantity': row[3],
                    'current_price': row[4] or 0.0
                })
            
            return symbols
            
        except Exception as e:
            self.logger.error(f"Error getting top performing symbols: {e}")
            return []
    
    def _get_monthly_performance(self, user_id: int, start_date: Optional[datetime] = None, 
                                end_date: Optional[datetime] = None) -> List[Dict]:
        """Get monthly performance breakdown"""
        try:
            query = """
                SELECT 
                    strftime('%Y-%m', datetime(date, 'unixepoch')) as month,
                    AVG(portfolio_value) as avg_value,
                    SUM(daily_return) as monthly_return,
                    MAX(portfolio_value) as peak_value
                FROM performance
                WHERE user_id = ?
            """
            params = [user_id]
            
            if start_date:
                query += " AND date >= ?"
                params.append(int(start_date.timestamp()))
            
            if end_date:
                query += " AND date <= ?"
                params.append(int(end_date.timestamp()))
            
            query += " GROUP BY month ORDER BY month"
            
            results = self.db_manager.fetch_all(query, tuple(params))
            monthly_data = []
            
            for row in results:
                monthly_data.append({
                    'month': row[0],
                    'avg_value': row[1] or 0.0,
                    'monthly_return': row[2] or 0.0,
                    'peak_value': row[3] or 0.0
                })
            
            return monthly_data
            
        except Exception as e:
            self.logger.error(f"Error getting monthly performance: {e}")
            return []
    
    def _get_sector_performance(self, user_id: int, start_date: Optional[datetime] = None, 
                               end_date: Optional[datetime] = None) -> List[Dict]:
        """Get sector performance breakdown"""
        try:
            query = """
                SELECT 
                    s.sector,
                    COUNT(*) as position_count,
                    SUM(p.unrealized_pnl) as sector_pnl,
                    AVG(p.unrealized_pnl) as avg_position_pnl
                FROM positions p
                JOIN symbols s ON p.symbol_id = s.id
                WHERE p.user_id = ? AND p.quantity > 0 AND s.sector IS NOT NULL
            """
            params = [user_id]
            
            if start_date:
                query += " AND p.last_updated >= ?"
                params.append(int(start_date.timestamp()))
            
            if end_date:
                query += " AND p.last_updated <= ?"
                params.append(int(end_date.timestamp()))
            
            query += " GROUP BY s.sector ORDER BY sector_pnl DESC"
            
            results = self.db_manager.fetch_all(query, tuple(params))
            sector_data = []
            
            for row in results:
                sector_data.append({
                    'sector': row[0],
                    'position_count': row[1],
                    'sector_pnl': row[2] or 0.0,
                    'avg_position_pnl': row[3] or 0.0
                })
            
            return sector_data
            
        except Exception as e:
            self.logger.error(f"Error getting sector performance: {e}")
            return []
    
    def create_performance_snapshot(self, user_id: int) -> bool:
        """
        Create a daily performance snapshot
        """
        try:
            # Get current portfolio value
            portfolio_summary = self._get_current_portfolio_summary(user_id)
            if not portfolio_summary:
                return False
            
            # Calculate daily return
            daily_return = self._calculate_daily_return(user_id)
            
            # Calculate cumulative return
            cumulative_return = self._calculate_cumulative_return(user_id)
            
            # Calculate metrics
            sharpe_ratio = self._calculate_daily_sharpe_ratio(user_id)
            max_drawdown = self._calculate_daily_max_drawdown(user_id)
            win_rate = self._calculate_daily_win_rate(user_id)
            profit_factor = self._calculate_daily_profit_factor(user_id)
            
            # Insert snapshot
            query = """
                INSERT INTO performance (uid, user_id, date, portfolio_value, daily_return, 
                                       cumulative_return, sharpe_ratio, max_drawdown, win_rate, profit_factor)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            import uuid
            params = (
                str(uuid.uuid4()),
                user_id,
                int(datetime.now().timestamp()),
                portfolio_summary['total_market_value'],
                daily_return,
                cumulative_return,
                sharpe_ratio,
                max_drawdown,
                win_rate,
                profit_factor
            )
            
            self.db_manager.execute_query(query, params)
            self.logger.info(f"Performance snapshot created for user {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating performance snapshot: {e}")
            return False
    
    def _get_current_portfolio_summary(self, user_id: int) -> Optional[Dict]:
        """Get current portfolio summary"""
        try:
            query = """
                SELECT SUM(market_value) as total_market_value
                FROM positions
                WHERE user_id = ? AND quantity > 0
            """
            
            result = self.db_manager.fetch_one(query, (user_id,))
            if result:
                return {'total_market_value': result[0] or 0.0}
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting portfolio summary: {e}")
            return None
    
    def _calculate_daily_return(self, user_id: int) -> float:
        """Calculate daily return"""
        try:
            # Get yesterday's portfolio value
            yesterday = datetime.now() - timedelta(days=1)
            query = """
                SELECT portfolio_value
                FROM performance
                WHERE user_id = ? AND date <= ?
                ORDER BY date DESC
                LIMIT 1
            """
            
            result = self.db_manager.fetch_one(query, (user_id, int(yesterday.timestamp())))
            if not result:
                return 0.0
            
            yesterday_value = result[0]
            
            # Get current portfolio value
            current_summary = self._get_current_portfolio_summary(user_id)
            if not current_summary:
                return 0.0
            
            current_value = current_summary['total_market_value']
            
            if yesterday_value > 0:
                return (current_value - yesterday_value) / yesterday_value
            
            return 0.0
            
        except Exception as e:
            self.logger.error(f"Error calculating daily return: {e}")
            return 0.0
    
    def _calculate_cumulative_return(self, user_id: int) -> float:
        """Calculate cumulative return from start"""
        try:
            # Get first performance record
            query = """
                SELECT portfolio_value
                FROM performance
                WHERE user_id = ?
                ORDER BY date ASC
                LIMIT 1
            """
            
            result = self.db_manager.fetch_one(query, (user_id,))
            if not result:
                return 0.0
            
            initial_value = result[0]
            
            # Get current portfolio value
            current_summary = self._get_current_portfolio_summary(user_id)
            if not current_summary:
                return 0.0
            
            current_value = current_summary['total_market_value']
            
            if initial_value > 0:
                return (current_value - initial_value) / initial_value
            
            return 0.0
            
        except Exception as e:
            self.logger.error(f"Error calculating cumulative return: {e}")
            return 0.0
    
    def _calculate_daily_sharpe_ratio(self, user_id: int) -> float:
        """Calculate daily Sharpe ratio"""
        # Simplified calculation for daily snapshot
        return 0.0
    
    def _calculate_daily_max_drawdown(self, user_id: int) -> float:
        """Calculate daily max drawdown"""
        # Simplified calculation for daily snapshot
        return 0.0
    
    def _calculate_daily_win_rate(self, user_id: int) -> float:
        """Calculate daily win rate"""
        # Simplified calculation for daily snapshot
        return 0.0
    
    def _calculate_daily_profit_factor(self, user_id: int) -> float:
        """Calculate daily profit factor"""
        # Simplified calculation for daily snapshot
        return 0.0
    
    def generate_performance_report(self, user_id: int, report_type: str = "comprehensive") -> Dict:
        """
        Generate a comprehensive performance report
        """
        try:
            if report_type == "comprehensive":
                return self._generate_comprehensive_report(user_id)
            elif report_type == "summary":
                return self._generate_summary_report(user_id)
            elif report_type == "monthly":
                return self._generate_monthly_report(user_id)
            else:
                self.logger.warning(f"Unknown report type: {report_type}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error generating performance report: {e}")
            return {}
    
    def _generate_comprehensive_report(self, user_id: int) -> Dict:
        """Generate comprehensive performance report"""
        # Get performance metrics for different time periods
        current_month = datetime.now().replace(day=1)
        three_months_ago = current_month - timedelta(days=90)
        six_months_ago = current_month - timedelta(days=180)
        one_year_ago = current_month - timedelta(days=365)
        
        return {
            'current_month': self.calculate_performance_metrics(user_id, current_month),
            'three_months': self.calculate_performance_metrics(user_id, three_months_ago),
            'six_months': self.calculate_performance_metrics(user_id, six_months_ago),
            'one_year': self.calculate_performance_metrics(user_id, one_year_ago),
            'all_time': self.calculate_performance_metrics(user_id),
            'report_generated': datetime.now().isoformat()
        }
    
    def _generate_summary_report(self, user_id: int) -> Dict:
        """Generate summary performance report"""
        return self.calculate_performance_metrics(user_id)
    
    def _generate_monthly_report(self, user_id: int) -> Dict:
        """Generate monthly performance report"""
        current_month = datetime.now().replace(day=1)
        return self.calculate_performance_metrics(user_id, current_month) 