"""
Utility functions for statistical calculations and helpers.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Any
import logging

logger = logging.getLogger(__name__)


class OpportunityRanker:
    """Ranks opportunities based on multiple criteria."""
    
    @staticmethod
    def calculate_opportunity_score(signal_dict: Dict) -> float:
        """Calculate composite opportunity score (0 to 1)."""
        
        score = 0.0
        weight_sum = 0.0
        
        # Signal strength (40%)
        if 'signal_strength' in signal_dict:
            signal_strength = signal_dict['signal_strength']
            score += signal_strength * 0.40
            weight_sum += 0.40
        
        # Z-score extremeness (30%)
        if 'z_score_30' in signal_dict:
            z_score = signal_dict['z_score_30']
            if not np.isnan(z_score):
                extremeness = min(abs(z_score) / 3.0, 1.0)
                score += extremeness * 0.30
                weight_sum += 0.30
        
        # Backtest Sharpe (20%)
        if 'sharpe_ratio' in signal_dict:
            sharpe = signal_dict['sharpe_ratio']
            if not np.isnan(sharpe) and sharpe > 0:
                normalized_sharpe = min(sharpe / 2.0, 1.0)
                score += normalized_sharpe * 0.20
                weight_sum += 0.20
        
        # Cointegration strength (10%)
        if 'p_value' in signal_dict:
            p_value = signal_dict['p_value']
            if not np.isnan(p_value):
                coint_strength = 1.0 - min(p_value / 0.05, 1.0)
                score += coint_strength * 0.10
                weight_sum += 0.10
        
        # Normalize
        if weight_sum > 0:
            score = score / weight_sum
        
        return min(score, 1.0)
    
    @staticmethod
    def rank_opportunities(signals: List[Dict]) -> List[Dict]:
        """Rank opportunities by score."""
        
        for signal in signals:
            signal['opportunity_score'] = OpportunityRanker.calculate_opportunity_score(signal)
        
        # Sort by score
        signals.sort(key=lambda x: x['opportunity_score'], reverse=True)
        
        return signals


class DataValidator:
    """Validates data quality."""
    
    @staticmethod
    def check_price_data(data: pd.DataFrame) -> Dict[str, Any]:
        """Check for common data issues."""
        
        checks = {
            'total_records': len(data),
            'date_range': (data['date'].min(), data['date'].max()),
            'missing_ohlcv': data[['open', 'high', 'low', 'close']].isna().sum().sum(),
            'missing_volume': data['volume'].isna().sum(),
            'zero_volume': (data['volume'] == 0).sum(),
            'negative_prices': (data[['open', 'high', 'low', 'close']] < 0).sum().sum(),
            'invalid_ohlc': (
                ((data['high'] < data['low']).sum()) +
                ((data['high'] < data['close']).sum()) +
                ((data['high'] < data['open']).sum())
            ),
            'duplicate_dates': data['date'].duplicated().sum(),
            'price_spikes': DataValidator._detect_price_spikes(data)
        }
        
        return checks
    
    @staticmethod
    def _detect_price_spikes(data: pd.DataFrame, threshold: float = 0.20) -> int:
        """Detect price spikes (>20% daily move)."""
        data = data.sort_values('date')
        returns = data['close'].pct_change().abs()
        spikes = (returns > threshold).sum()
        return spikes
    
    @staticmethod
    def is_data_valid(data: pd.DataFrame, min_records: int = 100) -> bool:
        """Check if data is valid for analysis."""
        
        if len(data) < min_records:
            return False
        
        if data[['open', 'high', 'low', 'close']].isna().sum().sum() > len(data) * 0.05:
            return False
        
        if (data['volume'] == 0).sum() > len(data) * 0.10:
            return False
        
        return True


class SpreadNormalizer:
    """Utilities for spread normalization."""
    
    @staticmethod
    def normalize_spread(spread: np.ndarray) -> np.ndarray:
        """Normalize spread to 0-1 range."""
        min_spread = np.min(spread)
        max_spread = np.max(spread)
        
        if max_spread == min_spread:
            return np.ones_like(spread) * 0.5
        
        normalized = (spread - min_spread) / (max_spread - min_spread)
        return normalized
    
    @staticmethod
    def smooth_spread(spread: np.ndarray, window: int = 5) -> np.ndarray:
        """Apply moving average smoothing."""
        if len(spread) < window:
            return spread
        
        smoothed = pd.Series(spread).rolling(window=window, center=True).mean().values
        
        # Fill NaN values at edges
        for i in range(len(smoothed)):
            if np.isnan(smoothed[i]):
                smoothed[i] = spread[i]
        
        return smoothed


class StatisticalTests:
    """Additional statistical test utilities."""
    
    @staticmethod
    def calculate_autocorrelation(series: np.ndarray, lag: int = 1) -> float:
        """Calculate autocorrelation at specified lag."""
        if len(series) < lag + 1:
            return np.nan
        
        series = series - np.mean(series)
        variance = np.var(series)
        
        if variance == 0:
            return 0.0
        
        autocov = np.mean(series[:-lag] * series[lag:])
        return autocov / variance
    
    @staticmethod
    def calculate_rolling_correlation(series_a: np.ndarray, series_b: np.ndarray,
                                     window: int = 30) -> np.ndarray:
        """Calculate rolling correlation."""
        df_a = pd.Series(series_a)
        df_b = pd.Series(series_b)
        
        rolling_corr = df_a.rolling(window).corr(df_b).values
        return rolling_corr
    
    @staticmethod
    def calculate_rolling_zscore(series: np.ndarray, window: int = 30) -> np.ndarray:
        """Calculate rolling Z-score."""
        df = pd.Series(series)
        rolling_mean = df.rolling(window).mean()
        rolling_std = df.rolling(window).std()
        
        z_scores = (df - rolling_mean) / rolling_std
        return z_scores.values


def log_performance_metrics(metrics: Dict):
    """Log backtest performance metrics."""
    logger.info(f"Backtest Results:")
    logger.info(f"  Total Return: {metrics['total_return']:.2f}%")
    logger.info(f"  Annualized Return: {metrics['annualized_return']:.2f}%")
    logger.info(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    logger.info(f"  Max Drawdown: {metrics['max_drawdown']:.2f}%")
    logger.info(f"  Number of Trades: {metrics['num_trades']}")
    logger.info(f"  Hit Rate: {metrics['hit_rate']:.2f}%")
    logger.info(f"  Profit Factor: {metrics['profit_factor']:.2f}")
