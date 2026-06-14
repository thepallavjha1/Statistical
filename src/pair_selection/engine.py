"""
Pair selection module for finding correlated stock pairs.
"""

import pandas as pd
import numpy as np
from itertools import combinations
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
import logging

from src.data_ingestion import get_data_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PairSelectionEngine:
    """Selects pairs based on correlation."""
    
    def __init__(self, correlation_threshold: float = 0.7):
        """Initialize pair selection engine."""
        self.correlation_threshold = correlation_threshold
        self.data_manager = get_data_manager()
    
    def calculate_correlation(self, symbol_a: str, symbol_b: str,
                            lookback_days: int = 252) -> float:
        """Calculate Pearson correlation between two stocks."""
        try:
            prices_a = self.data_manager.get_price_series(symbol_a)
            prices_b = self.data_manager.get_price_series(symbol_b)
            
            if prices_a is None or prices_b is None:
                return np.nan
            
            # Use last N days
            prices_a = prices_a.tail(lookback_days)
            prices_b = prices_b.tail(lookback_days)
            
            # Calculate returns
            returns_a = prices_a.pct_change().dropna()
            returns_b = prices_b.pct_change().dropna()
            
            # Align dates
            common_dates = returns_a.index.intersection(returns_b.index)
            
            if len(common_dates) < 20:
                return np.nan
            
            returns_a = returns_a[common_dates]
            returns_b = returns_b[common_dates]
            
            correlation = returns_a.corr(returns_b)
            return correlation
        except Exception as e:
            logger.error(f"Error calculating correlation {symbol_a}-{symbol_b}: {str(e)}")
            return np.nan
    
    def find_correlated_pairs(self, symbols: List[str],
                             lookback_days: int = 252) -> List[Dict]:
        """Find all correlated pairs."""
        if len(symbols) > 50:
            return self._find_correlated_pairs_matrix(symbols, lookback_days)

        pairs = []
        n = len(symbols)

        logger.info(f"Finding correlated pairs from {n} stocks (threshold={self.correlation_threshold})")

        total_combinations = len(list(combinations(symbols, 2)))
        count = 0

        for symbol_a, symbol_b in combinations(symbols, 2):
            count += 1
            if count % 100 == 0:
                logger.info(f"Processed {count}/{total_combinations} combinations")

            correlation = self.calculate_correlation(symbol_a, symbol_b, lookback_days)

            if not np.isnan(correlation) and abs(correlation) >= self.correlation_threshold:
                pairs.append({
                    'stock_a': symbol_a,
                    'stock_b': symbol_b,
                    'correlation': correlation
                })

        pairs.sort(key=lambda x: abs(x['correlation']), reverse=True)
        logger.info(f"Found {len(pairs)} correlated pairs")

        return pairs

    def _find_correlated_pairs_matrix(self, symbols: List[str],
                                      lookback_days: int = 252) -> List[Dict]:
        """Fast pair scan using a single correlation matrix (for large universes)."""
        logger.info(
            f"Matrix scan for {len(symbols)} stocks (threshold={self.correlation_threshold})"
        )

        returns = {}
        for symbol in symbols:
            prices = self.data_manager.get_price_series(symbol)
            if prices is None or prices.empty:
                continue
            series = prices.tail(lookback_days).pct_change().dropna()
            if len(series) >= 20:
                returns[symbol] = series

        if len(returns) < 2:
            logger.warning("Not enough price data for correlation matrix")
            return []

        returns_df = pd.DataFrame(returns).dropna(how='any')
        if returns_df.shape[0] < 20:
            logger.warning("Not enough overlapping dates for correlation matrix")
            return []

        corr_matrix = returns_df.corr()
        pairs = []

        for i, symbol_a in enumerate(corr_matrix.columns):
            for j in range(i + 1, len(corr_matrix.columns)):
                symbol_b = corr_matrix.columns[j]
                correlation = corr_matrix.iloc[i, j]
                if not np.isnan(correlation) and abs(correlation) >= self.correlation_threshold:
                    pairs.append({
                        'stock_a': symbol_a,
                        'stock_b': symbol_b,
                        'correlation': correlation
                    })

        pairs.sort(key=lambda x: abs(x['correlation']), reverse=True)
        logger.info(f"Found {len(pairs)} correlated pairs")
        return pairs
    
    def find_pairs_for_symbol(self, symbol: str, symbols: List[str],
                            lookback_days: int = 252) -> List[Dict]:
        """Find all correlated pairs for a specific symbol."""
        pairs = []
        
        for other_symbol in symbols:
            if symbol == other_symbol:
                continue
            
            correlation = self.calculate_correlation(symbol, other_symbol, lookback_days)
            
            if not np.isnan(correlation) and abs(correlation) >= self.correlation_threshold:
                pairs.append({
                    'stock_a': symbol,
                    'stock_b': other_symbol,
                    'correlation': correlation
                })
        
        pairs.sort(key=lambda x: abs(x['correlation']), reverse=True)
        return pairs
    
    def calculate_multi_period_correlation(self, symbol_a: str, symbol_b: str) -> Dict[str, float]:
        """Calculate correlation for multiple time periods."""
        correlations = {}
        
        for period, days in [('1Y', 252), ('2Y', 504), ('3Y', 756)]:
            corr = self.calculate_correlation(symbol_a, symbol_b, lookback_days=days)
            correlations[f'correlation_{period.lower()}'] = corr
        
        return correlations
    
    def filter_by_liquidity(self, symbols: List[str],
                           min_avg_volume: float = 1e6) -> List[str]:
        """Filter symbols by minimum average daily volume."""
        liquid_symbols = []
        
        for symbol in symbols:
            try:
                data = self.data_manager.load_from_parquet(symbol)
                if data is not None and not data.empty:
                    avg_volume = data['volume'].tail(20).mean()
                    if avg_volume >= min_avg_volume:
                        liquid_symbols.append(symbol)
            except Exception as e:
                logger.warning(f"Error checking liquidity for {symbol}: {str(e)}")
        
        return liquid_symbols
    
    def get_pair_metrics(self, symbol_a: str, symbol_b: str) -> Dict:
        """Get comprehensive metrics for a pair."""
        try:
            correlations = self.calculate_multi_period_correlation(symbol_a, symbol_b)
            
            prices_a = self.data_manager.get_price_series(symbol_a)
            prices_b = self.data_manager.get_price_series(symbol_b)
            
            metrics = {
                'stock_a': symbol_a,
                'stock_b': symbol_b,
                **correlations,
                'price_a_current': prices_a.iloc[-1] if prices_a is not None else None,
                'price_b_current': prices_b.iloc[-1] if prices_b is not None else None,
                'ratio_ab': prices_a.iloc[-1] / prices_b.iloc[-1] if prices_a is not None and prices_b is not None else None
            }
            
            return metrics
        except Exception as e:
            logger.error(f"Error getting pair metrics {symbol_a}-{symbol_b}: {str(e)}")
            return {}


# Global instance
_pair_engine = None


def get_pair_selection_engine(correlation_threshold: float = 0.7) -> PairSelectionEngine:
    """Get or create pair selection engine."""
    global _pair_engine
    if _pair_engine is None:
        _pair_engine = PairSelectionEngine(correlation_threshold)
    return _pair_engine
