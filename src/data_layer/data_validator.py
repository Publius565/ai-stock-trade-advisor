"""
Data Validator Module

Provides data validation and quality checks for market data.
Ensures data consistency and identifies potential issues.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DataValidator:
    """
    Market data validation and quality assurance system.
    
    Features:
    - Data completeness checks
    - Price anomaly detection
    - Volume validation
    - Date consistency verification
    - Data source comparison
    """
    
    def __init__(self):
        """Initialize the data validator."""
        # Validation thresholds
        self.price_change_threshold = 0.50  # 50% price change threshold
        self.volume_spike_threshold = 10.0  # 10x volume spike threshold
        self.min_data_points = 5  # Minimum data points for validation
        self.max_gap_days = 7  # Maximum gap between data points
        
        logger.info("Data validator initialized")
    
    def validate_market_data(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate market data for quality and consistency.
        
        Args:
            data: Market data dictionary
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        if not data:
            return False, ["No data provided"]
        
        # Basic structure validation
        if 'symbol' not in data:
            issues.append("Missing symbol")
        
        if 'data' not in data or not data['data']:
            issues.append("No price data available")
            return False, issues
        
        price_data = data['data']
        
        # Data completeness check
        completeness_issues = self._check_data_completeness(price_data)
        issues.extend(completeness_issues)
        
        # Price validation
        price_issues = self._validate_prices(price_data)
        issues.extend(price_issues)
        
        # Volume validation
        volume_issues = self._validate_volumes(price_data)
        issues.extend(volume_issues)
        
        # Date consistency check
        date_issues = self._validate_dates(price_data)
        issues.extend(date_issues)
        
        # OHLC consistency check
        ohlc_issues = self._validate_ohlc_consistency(price_data)
        issues.extend(ohlc_issues)
        
        is_valid = len(issues) == 0
        
        if not is_valid:
            logger.warning(f"Data validation failed for {data.get('symbol', 'unknown')}: {issues}")
        else:
            logger.debug(f"Data validation passed for {data.get('symbol', 'unknown')}")
        
        return is_valid, issues
    
    def _check_data_completeness(self, price_data: List[Dict[str, Any]]) -> List[str]:
        """Check if data has required fields and sufficient data points."""
        issues = []
        
        if len(price_data) < self.min_data_points:
            issues.append(f"Insufficient data points: {len(price_data)} < {self.min_data_points}")
        
        required_fields = ['date', 'open', 'high', 'low', 'close', 'volume']
        
        for i, data_point in enumerate(price_data):
            missing_fields = []
            for field in required_fields:
                if field not in data_point or data_point[field] is None:
                    missing_fields.append(field)
            
            if missing_fields:
                issues.append(f"Data point {i} missing fields: {missing_fields}")
        
        return issues
    
    def _validate_prices(self, price_data: List[Dict[str, Any]]) -> List[str]:
        """Validate price data for anomalies and consistency."""
        issues = []
        
        if len(price_data) < 2:
            return issues
        
        for i in range(1, len(price_data)):
            prev_close = price_data[i-1]['close']
            curr_close = price_data[i]['close']
            
            if prev_close <= 0 or curr_close <= 0:
                issues.append(f"Invalid price at data point {i}: {curr_close}")
                continue
            
            # Check for extreme price changes
            price_change = abs(curr_close - prev_close) / prev_close
            
            if price_change > self.price_change_threshold:
                issues.append(f"Large price change at data point {i}: {price_change:.2%}")
            
            # Check OHLC consistency
            data_point = price_data[i]
            if data_point['high'] < data_point['low']:
                issues.append(f"High < Low at data point {i}")
            
            if data_point['open'] < 0 or data_point['close'] < 0:
                issues.append(f"Negative price at data point {i}")
        
        return issues
    
    def _validate_volumes(self, price_data: List[Dict[str, Any]]) -> List[str]:
        """Validate volume data for anomalies."""
        issues = []
        
        if len(price_data) < 2:
            return issues
        
        volumes = [point['volume'] for point in price_data if point['volume'] is not None]
        
        if not volumes:
            issues.append("No valid volume data")
            return issues
        
        # Check for zero or negative volumes
        for i, point in enumerate(price_data):
            if point['volume'] is not None and point['volume'] <= 0:
                issues.append(f"Invalid volume at data point {i}: {point['volume']}")
        
        # Check for volume spikes
        if len(volumes) >= 10:
            avg_volume = sum(volumes) / len(volumes)
            
            for i, volume in enumerate(volumes):
                if volume > avg_volume * self.volume_spike_threshold:
                    issues.append(f"Volume spike at data point {i}: {volume} vs avg {avg_volume:.0f}")
        
        return issues
    
    def _validate_dates(self, price_data: List[Dict[str, Any]]) -> List[str]:
        """Validate date consistency and gaps."""
        issues = []
        
        if len(price_data) < 2:
            return issues
        
        dates = []
        for point in price_data:
            try:
                if isinstance(point['date'], str):
                    date_obj = datetime.strptime(point['date'], '%Y-%m-%d')
                else:
                    date_obj = point['date']
                dates.append(date_obj)
            except (ValueError, TypeError) as e:
                issues.append(f"Invalid date format: {point['date']}")
                continue
        
        if len(dates) < 2:
            return issues
        
        # Check for date gaps
        for i in range(1, len(dates)):
            gap = (dates[i] - dates[i-1]).days
            
            if gap > self.max_gap_days:
                issues.append(f"Large date gap between {dates[i-1]} and {dates[i]}: {gap} days")
        
        # Check for duplicate dates
        unique_dates = set(dates)
        if len(unique_dates) != len(dates):
            issues.append("Duplicate dates found")
        
        return issues
    
    def _validate_ohlc_consistency(self, price_data: List[Dict[str, Any]]) -> List[str]:
        """Validate OHLC (Open, High, Low, Close) consistency."""
        issues = []
        
        for i, point in enumerate(price_data):
            open_price = point['open']
            high_price = point['high']
            low_price = point['low']
            close_price = point['close']
            
            # Check basic OHLC relationships
            if high_price < max(open_price, close_price):
                issues.append(f"High price too low at data point {i}")
            
            if low_price > min(open_price, close_price):
                issues.append(f"Low price too high at data point {i}")
            
            if high_price < low_price:
                issues.append(f"High < Low at data point {i}")
        
        return issues
    
    def compare_data_sources(self, data1: Dict[str, Any], data2: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare data from two different sources for consistency.
        
        Args:
            data1: First data source
            data2: Second data source
            
        Returns:
            Comparison results dictionary
        """
        comparison = {
            'symbol_match': data1.get('symbol') == data2.get('symbol'),
            'data_points_diff': 0,
            'price_differences': [],
            'source1': data1.get('source', 'unknown'),
            'source2': data2.get('source', 'unknown')
        }
        
        if not comparison['symbol_match']:
            return comparison
        
        data1_points = data1.get('data', [])
        data2_points = data2.get('data', [])
        
        comparison['data_points_diff'] = abs(len(data1_points) - len(data2_points))
        
        # Compare overlapping dates
        data1_dict = {point['date']: point for point in data1_points}
        data2_dict = {point['date']: point for point in data2_points}
        
        common_dates = set(data1_dict.keys()) & set(data2_dict.keys())
        
        for date in common_dates:
            point1 = data1_dict[date]
            point2 = data2_dict[date]
            
            close_diff = abs(point1['close'] - point2['close'])
            close_diff_pct = close_diff / point1['close'] if point1['close'] > 0 else 0
            
            if close_diff_pct > 0.01:  # 1% difference threshold
                comparison['price_differences'].append({
                    'date': date,
                    'difference': close_diff,
                    'difference_pct': close_diff_pct,
                    'source1_close': point1['close'],
                    'source2_close': point2['close']
                })
        
        return comparison
    
    def get_data_quality_score(self, data: Dict[str, Any]) -> float:
        """
        Calculate a data quality score (0.0 to 1.0).
        
        Args:
            data: Market data dictionary
            
        Returns:
            Quality score between 0.0 and 1.0
        """
        if not data or 'data' not in data:
            return 0.0
        
        price_data = data['data']
        if not price_data:
            return 0.0
        
        score = 1.0
        deductions = 0.0
        
        # Check data completeness
        required_fields = ['date', 'open', 'high', 'low', 'close', 'volume']
        for point in price_data:
            missing_fields = sum(1 for field in required_fields if field not in point or point[field] is None)
            if missing_fields > 0:
                deductions += 0.1 * (missing_fields / len(required_fields))
        
        # Check for price anomalies
        if len(price_data) >= 2:
            for i in range(1, len(price_data)):
                prev_close = price_data[i-1]['close']
                curr_close = price_data[i]['close']
                
                if prev_close > 0 and curr_close > 0:
                    price_change = abs(curr_close - prev_close) / prev_close
                    if price_change > self.price_change_threshold:
                        deductions += 0.05
        
        # Check for volume issues
        zero_volumes = sum(1 for point in price_data if point.get('volume', 0) <= 0)
        if zero_volumes > 0:
            deductions += 0.1 * (zero_volumes / len(price_data))
        
        # Check data recency
        if price_data:
            try:
                latest_date = datetime.strptime(price_data[-1]['date'], '%Y-%m-%d')
                days_old = (datetime.now() - latest_date).days
                if days_old > 30:
                    deductions += 0.2
                elif days_old > 7:
                    deductions += 0.1
            except (ValueError, TypeError):
                deductions += 0.1
        
        final_score = max(0.0, score - deductions)
        return round(final_score, 2)
    
    def suggest_data_improvements(self, data: Dict[str, Any]) -> List[str]:
        """
        Suggest improvements for data quality.
        
        Args:
            data: Market data dictionary
            
        Returns:
            List of improvement suggestions
        """
        suggestions = []
        
        if not data or 'data' not in data:
            suggestions.append("No data available for analysis")
            return suggestions
        
        price_data = data['data']
        
        # Check data recency
        if price_data:
            try:
                latest_date = datetime.strptime(price_data[-1]['date'], '%Y-%m-%d')
                days_old = (datetime.now() - latest_date).days
                
                if days_old > 7:
                    suggestions.append(f"Data is {days_old} days old - consider refreshing")
            except (ValueError, TypeError):
                suggestions.append("Date format issues detected")
        
        # Check data volume
        if len(price_data) < 30:
            suggestions.append(f"Limited historical data ({len(price_data)} points) - consider longer time period")
        
        # Check for missing fields
        required_fields = ['date', 'open', 'high', 'low', 'close', 'volume']
        for point in price_data:
            missing_fields = [field for field in required_fields if field not in point or point[field] is None]
            if missing_fields:
                suggestions.append(f"Missing fields detected: {missing_fields}")
                break
        
        # Check for price anomalies
        if len(price_data) >= 2:
            anomalies = 0
            for i in range(1, len(price_data)):
                prev_close = price_data[i-1]['close']
                curr_close = price_data[i]['close']
                
                if prev_close > 0 and curr_close > 0:
                    price_change = abs(curr_close - prev_close) / prev_close
                    if price_change > self.price_change_threshold:
                        anomalies += 1
            
            if anomalies > 0:
                suggestions.append(f"Detected {anomalies} price anomalies - verify data accuracy")
        
        return suggestions 