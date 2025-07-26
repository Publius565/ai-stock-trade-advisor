"""
Feature Engineering Pipeline

Extracts and creates features from market data for machine learning models.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Engineers features from raw market data for ML models."""
    
    def __init__(self):
        self.feature_columns: List[str] = []
        self.scaler = None
    
    def create_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create technical indicators from OHLCV data."""
        if df.empty:
            return df
        
        # Ensure we have required columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.warning(f"Missing columns for technical indicators: {missing_cols}")
            return df
        
        # Copy dataframe to avoid modifying original
        df_features = df.copy()
        
        # Price-based indicators
        df_features = self._add_price_indicators(df_features)
        
        # Volume-based indicators
        df_features = self._add_volume_indicators(df_features)
        
        # Momentum indicators
        df_features = self._add_momentum_indicators(df_features)
        
        # Volatility indicators
        df_features = self._add_volatility_indicators(df_features)
        
        # Trend indicators
        df_features = self._add_trend_indicators(df_features)
        
        # Remove any infinite or NaN values
        df_features = df_features.replace([np.inf, -np.inf], np.nan)
        df_features = df_features.ffill().bfill()
        
        logger.info(f"Created {len(df_features.columns)} features from {len(df)} data points")
        
        return df_features
    
    def _add_price_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add price-based technical indicators."""
        # Moving averages
        for period in [5, 10, 20, 50]:
            df[f'sma_{period}'] = df['close'].rolling(window=period).mean()
            df[f'ema_{period}'] = df['close'].ewm(span=period).mean()
        
        # Price changes
        df['price_change'] = df['close'].pct_change()
        df['price_change_5d'] = df['close'].pct_change(periods=5)
        df['price_change_10d'] = df['close'].pct_change(periods=10)
        
        # High-Low range
        df['hl_range'] = (df['high'] - df['low']) / df['close']
        df['hl_range_5d_avg'] = df['hl_range'].rolling(window=5).mean()
        
        # Price position within day's range
        df['price_position'] = (df['close'] - df['low']) / (df['high'] - df['low'])
        
        return df
    
    def _add_volume_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add volume-based technical indicators."""
        # Volume moving averages
        for period in [5, 10, 20]:
            df[f'volume_sma_{period}'] = df['volume'].rolling(window=period).mean()
        
        # Volume ratio
        df['volume_ratio'] = df['volume'] / df['volume'].rolling(window=20).mean()
        
        # Volume-price trend
        df['volume_price_trend'] = (df['close'] - df['close'].shift(1)) * df['volume']
        df['volume_price_trend_5d'] = df['volume_price_trend'].rolling(window=5).sum()
        
        # On-balance volume (simplified)
        df['obv'] = (np.sign(df['close'].diff()) * df['volume']).fillna(0).cumsum()
        
        return df
    
    def _add_momentum_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add momentum-based technical indicators."""
        # RSI
        for period in [14, 21]:
            df[f'rsi_{period}'] = self._calculate_rsi(df['close'], period)
        
        # MACD
        df['macd'], df['macd_signal'], df['macd_histogram'] = self._calculate_macd(df['close'])
        
        # Stochastic oscillator
        df['stoch_k'], df['stoch_d'] = self._calculate_stochastic(df, 14)
        
        # Williams %R
        df['williams_r'] = self._calculate_williams_r(df, 14)
        
        return df
    
    def _add_volatility_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add volatility-based technical indicators."""
        # Bollinger Bands
        for period in [20, 50]:
            bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(df['close'], period)
            df[f'bb_upper_{period}'] = bb_upper
            df[f'bb_middle_{period}'] = bb_middle
            df[f'bb_lower_{period}'] = bb_lower
            df[f'bb_width_{period}'] = (bb_upper - bb_lower) / bb_middle
            df[f'bb_position_{period}'] = (df['close'] - bb_lower) / (bb_upper - bb_lower)
        
        # Average True Range (ATR)
        df['atr'] = self._calculate_atr(df, 14)
        df['atr_ratio'] = df['atr'] / df['close']
        
        return df
    
    def _add_trend_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add trend-based technical indicators."""
        # ADX (Average Directional Index)
        df['adx'] = self._calculate_adx(df, 14)
        
        # Parabolic SAR
        df['psar'] = self._calculate_psar(df)
        
        # Price channels
        for period in [20, 50]:
            df[f'highest_{period}'] = df['high'].rolling(window=period).max()
            df[f'lowest_{period}'] = df['low'].rolling(window=period).min()
            df[f'channel_position_{period}'] = (df['close'] - df[f'lowest_{period}']) / (df[f'highest_{period}'] - df[f'lowest_{period}'])
        
        return df
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate MACD (Moving Average Convergence Divergence)."""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        macd_signal = macd.ewm(span=signal).mean()
        macd_histogram = macd - macd_signal
        return macd, macd_signal, macd_histogram
    
    def _calculate_stochastic(self, df: pd.DataFrame, period: int = 14) -> Tuple[pd.Series, pd.Series]:
        """Calculate Stochastic Oscillator."""
        lowest_low = df['low'].rolling(window=period).min()
        highest_high = df['high'].rolling(window=period).max()
        k = 100 * ((df['close'] - lowest_low) / (highest_high - lowest_low))
        d = k.rolling(window=3).mean()
        return k, d
    
    def _calculate_williams_r(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Williams %R."""
        highest_high = df['high'].rolling(window=period).max()
        lowest_low = df['low'].rolling(window=period).min()
        williams_r = -100 * ((highest_high - df['close']) / (highest_high - lowest_low))
        return williams_r
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: float = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands."""
        middle = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        return upper, middle, lower
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range."""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        atr = true_range.rolling(window=period).mean()
        return atr
    
    def _calculate_adx(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average Directional Index (simplified)."""
        # Simplified ADX calculation
        high_diff = df['high'].diff()
        low_diff = df['low'].diff()
        
        plus_dm = np.where((high_diff > low_diff) & (high_diff > 0), high_diff, 0)
        minus_dm = np.where((low_diff > high_diff) & (low_diff > 0), low_diff, 0)
        
        tr = self._calculate_atr(df, period)
        plus_di = 100 * pd.Series(plus_dm).rolling(window=period).mean() / tr
        minus_di = 100 * pd.Series(minus_dm).rolling(window=period).mean() / tr
        
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = pd.Series(dx).rolling(window=period).mean()
        
        return adx
    
    def _calculate_psar(self, df: pd.DataFrame, acceleration: float = 0.02, maximum: float = 0.2) -> pd.Series:
        """Calculate Parabolic SAR (simplified)."""
        # Simplified PSAR calculation
        psar = df['close'].copy()
        psar.iloc[0] = df['low'].iloc[0]
        
        for i in range(1, len(df)):
            if df['close'].iloc[i] > psar.iloc[i-1]:
                psar.iloc[i] = psar.iloc[i-1] + acceleration * (df['high'].iloc[i] - psar.iloc[i-1])
            else:
                psar.iloc[i] = psar.iloc[i-1] - acceleration * (psar.iloc[i-1] - df['low'].iloc[i])
        
        return psar
    
    def create_target_variable(self, df: pd.DataFrame, target_period: int = 5) -> pd.Series:
        """Create target variable for prediction (future price change)."""
        if df.empty:
            return pd.Series()
        
        # Future price change
        future_price = df['close'].shift(-target_period)
        target = (future_price - df['close']) / df['close']
        
        return target
    
    def get_feature_columns(self, exclude_target: bool = True) -> List[str]:
        """Get list of feature columns."""
        if not self.feature_columns:
            # Default technical indicator columns
            self.feature_columns = [
                'sma_5', 'sma_10', 'sma_20', 'sma_50',
                'ema_5', 'ema_10', 'ema_20', 'ema_50',
                'price_change', 'price_change_5d', 'price_change_10d',
                'hl_range', 'hl_range_5d_avg', 'price_position',
                'volume_sma_5', 'volume_sma_10', 'volume_sma_20',
                'volume_ratio', 'volume_price_trend', 'volume_price_trend_5d', 'obv',
                'rsi_14', 'rsi_21', 'macd', 'macd_signal', 'macd_histogram',
                'stoch_k', 'stoch_d', 'williams_r',
                'bb_upper_20', 'bb_middle_20', 'bb_lower_20', 'bb_width_20', 'bb_position_20',
                'bb_upper_50', 'bb_middle_50', 'bb_lower_50', 'bb_width_50', 'bb_position_50',
                'atr', 'atr_ratio', 'adx', 'psar',
                'highest_20', 'lowest_20', 'channel_position_20',
                'highest_50', 'lowest_50', 'channel_position_50'
            ]
        
        if exclude_target:
            return [col for col in self.feature_columns if col != 'target']
        
        return self.feature_columns.copy()
    
    def prepare_features(self, df: pd.DataFrame, target_period: int = 5) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare features and target for ML model training."""
        # Create technical indicators
        df_features = self.create_technical_indicators(df)
        
        # Create target variable
        target = self.create_target_variable(df_features, target_period)
        
        # Get feature columns
        feature_cols = self.get_feature_columns()
        
        # Select only available features
        available_features = [col for col in feature_cols if col in df_features.columns]
        
        # Prepare feature matrix
        X = df_features[available_features].copy()
        y = target.copy()
        
        # Remove rows with NaN values
        valid_indices = ~(X.isna().any(axis=1) | y.isna())
        X = X[valid_indices]
        y = y[valid_indices]
        
        logger.info(f"Prepared {len(X)} samples with {len(X.columns)} features")
        
        return X, y 