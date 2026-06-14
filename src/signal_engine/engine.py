"""
Signal generation engine for pair trading.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List
from datetime import datetime
import logging

from src.data_ingestion import get_data_manager
from src.cointegration import get_cointegration_analyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SignalEngine:
    """Generates trading signals based on spread statistics."""
    
    def __init__(self, long_threshold: float = -2.0, 
                 short_threshold: float = 2.0,
                 exit_threshold: float = 0.5):
        """Initialize signal engine."""
        self.long_threshold = long_threshold  # Z-score < -2 = Long spread (BUY A, SELL B)
        self.short_threshold = short_threshold  # Z-score > +2 = Short spread (SELL A, BUY B)
        self.exit_threshold = exit_threshold  # |Z| < 0.5 = EXIT
        self.data_manager = get_data_manager()
        self.coint_analyzer = get_cointegration_analyzer()
    
    def calculate_z_score(self, prices_a: np.ndarray, prices_b: np.ndarray,
                         hedge_ratio: float, window: int = 30) -> float:
        """Calculate Z-score of spread for the latest observation."""
        try:
            spread = prices_a - hedge_ratio * prices_b
            
            if len(spread) < window:
                return np.nan
            
            # Use rolling window
            rolling_mean = np.mean(spread[-window:])
            rolling_std = np.std(spread[-window:])
            
            if rolling_std == 0:
                return 0.0
            
            current_spread = spread[-1]
            z_score = (current_spread - rolling_mean) / rolling_std
            
            return z_score
        except Exception as e:
            logger.error(f"Error calculating z-score: {str(e)}")
            return np.nan
    
    def get_price_data(self, symbol_a: str, symbol_b: str) -> Optional[Dict]:
        """Get price data for a pair."""
        try:
            prices_a = self.data_manager.get_price_series(symbol_a)
            prices_b = self.data_manager.get_price_series(symbol_b)
            
            if prices_a is None or prices_b is None:
                return None
            
            # Align dates
            common_dates = prices_a.index.intersection(prices_b.index)
            
            if len(common_dates) < 100:
                return None
            
            prices_a = prices_a[common_dates].values
            prices_b = prices_b[common_dates].values
            
            return {
                'prices_a': prices_a,
                'prices_b': prices_b,
                'dates': common_dates
            }
        except Exception as e:
            logger.error(f"Error getting price data: {str(e)}")
            return None
    
    def generate_signal(self, symbol_a: str, symbol_b: str,
                       hedge_ratio: float = None) -> Dict:
        """Generate trading signal for a pair."""
        try:
            price_data = self.get_price_data(symbol_a, symbol_b)
            
            if price_data is None:
                return {
                    'stock_a': symbol_a,
                    'stock_b': symbol_b,
                    'signal': 'HOLD',
                    'z_score_30': np.nan,
                    'z_score_60': np.nan,
                    'z_score_90': np.nan,
                    'current_spread': np.nan
                }
            
            prices_a = price_data['prices_a']
            prices_b = price_data['prices_b']
            
            # Calculate hedge ratio if not provided
            if hedge_ratio is None:
                hedge_ratio = self.coint_analyzer.calculate_hedge_ratio(prices_a, prices_b)
            
            # Calculate spread
            spread = prices_a - hedge_ratio * prices_b
            current_spread = spread[-1]
            
            # Calculate Z-scores for different windows
            z_30 = self.calculate_z_score(prices_a, prices_b, hedge_ratio, window=30)
            z_60 = self.calculate_z_score(prices_a, prices_b, hedge_ratio, window=60)
            z_90 = self.calculate_z_score(prices_a, prices_b, hedge_ratio, window=90)
            
            # Determine signal
            signal = self._determine_signal(z_30, z_60, z_90)
            signal_strength = self._calculate_signal_strength(z_30, z_60, z_90)
            
            result = {
                'stock_a': symbol_a,
                'stock_b': symbol_b,
                'signal': signal,
                'z_score_30': z_30,
                'z_score_60': z_60,
                'z_score_90': z_90,
                'current_spread': current_spread,
                'hedge_ratio': hedge_ratio,
                'signal_strength': signal_strength,
                'timestamp': datetime.utcnow()
            }
            
            return result
        
        except Exception as e:
            logger.error(f"Error generating signal for {symbol_a}-{symbol_b}: {str(e)}")
            return {
                'stock_a': symbol_a,
                'stock_b': symbol_b,
                'signal': 'HOLD',
                'z_score_30': np.nan,
                'z_score_60': np.nan,
                'z_score_90': np.nan,
                'current_spread': np.nan
            }
    
    def _determine_signal(self, z_30: float, z_60: float, z_90: float) -> str:
        """Determine trading signal from Z-scores."""
        
        # Use 30-day Z-score as primary signal
        if np.isnan(z_30):
            return 'HOLD'
        
        # Exit signal
        if abs(z_30) < self.exit_threshold:
            return 'EXIT'
        
        # Long spread (Z < -2): BUY A, SELL B
        if z_30 < self.long_threshold:
            return 'LONG'
        
        # Short spread (Z > +2): SELL A, BUY B
        if z_30 > self.short_threshold:
            return 'SHORT'
        
        return 'HOLD'
    
    def _calculate_signal_strength(self, z_30: float, z_60: float, z_90: float) -> float:
        """Calculate signal strength (0 to 1)."""
        if np.isnan(z_30):
            return 0.0
        
        # Signal strength based on how extreme the Z-score is
        extreme_z = abs(z_30)
        
        # Normalized strength: 0 to 3 sigma becomes 0 to 1
        strength = min(extreme_z / 3.0, 1.0)
        
        # Boost if multi-period agreement
        z_values = [z for z in [z_30, z_60, z_90] if not np.isnan(z)]
        
        if len(z_values) > 1:
            # Check if signs agree
            mean_z = np.mean(z_values)
            if (mean_z < 0 and z_30 < 0) or (mean_z > 0 and z_30 > 0):
                strength = min(strength * 1.2, 1.0)
        
        return strength
    
    def generate_signals_batch(self, cointegrated_pairs: List[Dict]) -> List[Dict]:
        """Generate signals for multiple pairs."""
        signals = []
        
        for pair in cointegrated_pairs:
            signal = self.generate_signal(
                pair['stock_a'],
                pair['stock_b'],
                pair.get('hedge_ratio')
            )
            
            if signal['signal'] != 'HOLD':
                signals.append(signal)
        
        # Sort by signal strength
        signals.sort(key=lambda x: x['signal_strength'], reverse=True)
        
        logger.info(f"Generated {len(signals)} active signals from {len(cointegrated_pairs)} pairs")
        
        return signals
    
    def set_thresholds(self, long_threshold: float = None,
                      short_threshold: float = None,
                      exit_threshold: float = None):
        """Update signal thresholds."""
        if long_threshold is not None:
            self.long_threshold = long_threshold
        if short_threshold is not None:
            self.short_threshold = short_threshold
        if exit_threshold is not None:
            self.exit_threshold = exit_threshold
        
        logger.info(f"Updated thresholds: long={self.long_threshold}, short={self.short_threshold}, exit={self.exit_threshold}")


# Global instance
_signal_engine = None


def get_signal_engine(long_threshold: float = -2.0,
                     short_threshold: float = 2.0,
                     exit_threshold: float = 0.5) -> SignalEngine:
    """Get or create signal engine."""
    global _signal_engine
    if _signal_engine is None:
        _signal_engine = SignalEngine(long_threshold, short_threshold, exit_threshold)
    return _signal_engine
