"""
Cointegration testing and analysis module.
"""

import pandas as pd
import numpy as np
from statsmodels.tsa.stattools import coint
from sklearn.linear_model import LinearRegression
from typing import Dict, Tuple, Optional
import logging

from src.data_ingestion import get_data_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CointegrationAnalyzer:
    """Analyzes cointegration between pairs."""
    
    def __init__(self, p_value_threshold: float = 0.05):
        """Initialize cointegration analyzer."""
        self.p_value_threshold = p_value_threshold
        self.data_manager = get_data_manager()
    
    def test_cointegration(self, symbol_a: str, symbol_b: str) -> Dict:
        """Test cointegration between two stocks."""
        try:
            prices_a = self.data_manager.get_price_series(symbol_a)
            prices_b = self.data_manager.get_price_series(symbol_b)
            
            if prices_a is None or prices_b is None:
                return {
                    'stock_a': symbol_a,
                    'stock_b': symbol_b,
                    'cointegrated': False,
                    'p_value': np.nan,
                    'test_statistic': np.nan
                }
            
            # Align dates
            common_dates = prices_a.index.intersection(prices_b.index)
            prices_a = prices_a[common_dates]
            prices_b = prices_b[common_dates]
            
            if len(prices_a) < 100:
                return {
                    'stock_a': symbol_a,
                    'stock_b': symbol_b,
                    'cointegrated': False,
                    'p_value': np.nan,
                    'test_statistic': np.nan
                }
            
            # Perform cointegration test
            test_statistic, p_value, critical_values = coint(prices_a.values, prices_b.values)
            
            # Calculate hedge ratio
            hedge_ratio = self.calculate_hedge_ratio(prices_a.values, prices_b.values)
            
            cointegrated = p_value < self.p_value_threshold
            
            result = {
                'stock_a': symbol_a,
                'stock_b': symbol_b,
                'test_statistic': test_statistic,
                'p_value': p_value,
                'critical_values': critical_values,
                'cointegrated': cointegrated,
                'hedge_ratio': hedge_ratio,
                'n_observations': len(prices_a)
            }
            
            if cointegrated:
                logger.info(f"Cointegrated: {symbol_a}-{symbol_b} (p={p_value:.4f}, beta={hedge_ratio:.4f})")
            
            return result
        
        except Exception as e:
            logger.error(f"Error testing cointegration {symbol_a}-{symbol_b}: {str(e)}")
            return {
                'stock_a': symbol_a,
                'stock_b': symbol_b,
                'cointegrated': False,
                'p_value': np.nan,
                'test_statistic': np.nan
            }
    
    def calculate_hedge_ratio(self, prices_a: np.ndarray, 
                             prices_b: np.ndarray) -> float:
        """Calculate OLS hedge ratio (beta)."""
        try:
            # Use OLS regression: Price_A = alpha + beta * Price_B
            X = prices_b.reshape(-1, 1)
            y = prices_a.reshape(-1, 1)
            
            model = LinearRegression()
            model.fit(X, y)
            
            beta = model.coef_[0, 0]
            return beta
        except Exception as e:
            logger.error(f"Error calculating hedge ratio: {str(e)}")
            return np.nan
    
    def calculate_spread(self, prices_a: np.ndarray, prices_b: np.ndarray,
                        hedge_ratio: float) -> np.ndarray:
        """Calculate spread: Price_A - Beta * Price_B"""
        spread = prices_a - hedge_ratio * prices_b
        return spread
    
    def analyze_spread(self, symbol_a: str, symbol_b: str,
                      hedge_ratio: float = None) -> Dict:
        """Analyze spread statistics."""
        try:
            prices_a = self.data_manager.get_price_series(symbol_a)
            prices_b = self.data_manager.get_price_series(symbol_b)
            
            if prices_a is None or prices_b is None:
                return {}
            
            # Align dates
            common_dates = prices_a.index.intersection(prices_b.index)
            prices_a = prices_a[common_dates].values
            prices_b = prices_b[common_dates].values
            
            # Calculate hedge ratio if not provided
            if hedge_ratio is None:
                hedge_ratio = self.calculate_hedge_ratio(prices_a, prices_b)
            
            # Calculate spread
            spread = self.calculate_spread(prices_a, prices_b, hedge_ratio)
            
            # Calculate statistics
            stats = {
                'stock_a': symbol_a,
                'stock_b': symbol_b,
                'hedge_ratio': hedge_ratio,
                'mean_spread': np.mean(spread),
                'std_spread': np.std(spread),
                'median_spread': np.median(spread),
                'min_spread': np.min(spread),
                'max_spread': np.max(spread),
                'current_spread': spread[-1],
                'half_life': self.estimate_half_life(spread)
            }
            
            return stats
        
        except Exception as e:
            logger.error(f"Error analyzing spread {symbol_a}-{symbol_b}: {str(e)}")
            return {}
    
    def estimate_half_life(self, spread: np.ndarray) -> float:
        """Estimate mean reversion half-life using Ornstein-Uhlenbeck approximation."""
        try:
            # Fit Ornstein-Uhlenbeck: dX = -kX dt + sigma dW
            # Half-life = ln(2) / k
            
            # Calculate lag-1 autocorrelation
            spread = spread - np.mean(spread)
            
            # Autocorrelation approximation
            numerator = np.sum(spread[:-1] * spread[1:])
            denominator = np.sum(spread**2)
            
            if denominator == 0:
                return np.nan
            
            rho = numerator / denominator
            
            # Bound rho to (-1, 1) for stability
            rho = np.clip(rho, -0.999, 0.999)
            
            # Mean reversion speed
            k = -np.log(rho)
            
            # Half-life in periods (days)
            half_life = np.log(2) / k if k > 0 else np.nan
            
            return max(0.5, half_life)  # At least 0.5 days
        
        except Exception as e:
            logger.error(f"Error estimating half-life: {str(e)}")
            return np.nan
    
    def test_pairs_batch(self, pairs: list) -> list:
        """Test cointegration for multiple pairs."""
        results = []
        
        for pair in pairs:
            symbol_a = pair['stock_a']
            symbol_b = pair['stock_b']
            
            result = self.test_cointegration(symbol_a, symbol_b)
            
            if result['cointegrated']:
                spread_stats = self.analyze_spread(symbol_a, symbol_b, result['hedge_ratio'])
                result.update(spread_stats)
                results.append(result)
        
        # Sort by p-value
        results.sort(key=lambda x: x['p_value'])
        
        logger.info(f"Cointegrated {len(results)} pairs out of {len(pairs)}")
        return results


# Global instance
_coint_analyzer = None


def get_cointegration_analyzer(p_value_threshold: float = 0.05) -> CointegrationAnalyzer:
    """Get or create cointegration analyzer."""
    global _coint_analyzer
    if _coint_analyzer is None:
        _coint_analyzer = CointegrationAnalyzer(p_value_threshold)
    return _coint_analyzer
