"""
Backtesting engine for pair trading strategies.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

from src.data_ingestion import get_data_manager
from src.cointegration import get_cointegration_analyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BacktestingEngine:
    """Backtests pair trading strategies."""
    
    def __init__(self):
        """Initialize backtesting engine."""
        self.data_manager = get_data_manager()
        self.coint_analyzer = get_cointegration_analyzer()
    
    def backtest_pair(self, symbol_a: str, symbol_b: str,
                     start_date: datetime = None,
                     end_date: datetime = None,
                     entry_threshold: float = 2.0,
                     exit_threshold: float = 0.5,
                     initial_capital: float = 100000.0) -> Dict:
        """Backtest a pair trading strategy."""
        try:
            prices_a = self.data_manager.get_price_series(symbol_a)
            prices_b = self.data_manager.get_price_series(symbol_b)
            
            if prices_a is None or prices_b is None:
                return self._empty_backtest_result(symbol_a, symbol_b)
            
            # Filter by date range
            if start_date:
                prices_a = prices_a[prices_a.index >= start_date]
                prices_b = prices_b[prices_b.index >= start_date]
            if end_date:
                prices_a = prices_a[prices_a.index <= end_date]
                prices_b = prices_b[prices_b.index <= end_date]
            
            # Align dates
            common_dates = prices_a.index.intersection(prices_b.index)
            if len(common_dates) < 100:
                return self._empty_backtest_result(symbol_a, symbol_b)
            
            prices_a = prices_a[common_dates].values
            prices_b = prices_b[common_dates].values
            dates = common_dates
            
            # Calculate hedge ratio
            hedge_ratio = self.coint_analyzer.calculate_hedge_ratio(prices_a, prices_b)
            
            # Calculate spread
            spread = prices_a - hedge_ratio * prices_b
            
            # Backtest
            results = self._run_backtest(
                symbol_a, symbol_b, prices_a, prices_b, spread, dates,
                hedge_ratio, entry_threshold, exit_threshold, initial_capital
            )
            
            return results
        
        except Exception as e:
            logger.error(f"Error backtesting {symbol_a}-{symbol_b}: {str(e)}")
            return self._empty_backtest_result(symbol_a, symbol_b)
    
    def _run_backtest(self, symbol_a: str, symbol_b: str,
                     prices_a: np.ndarray, prices_b: np.ndarray,
                     spread: np.ndarray, dates,
                     hedge_ratio: float, entry_threshold: float,
                     exit_threshold: float, initial_capital: float) -> Dict:
        """Run backtest simulation."""
        
        # Calculate Z-scores (rolling 30-day)
        z_scores = []
        for i in range(len(spread)):
            if i < 30:
                window_start = 0
            else:
                window_start = i - 30
            
            window_spread = spread[window_start:i+1]
            mean_spread = np.mean(window_spread)
            std_spread = np.std(window_spread)
            
            if std_spread == 0:
                z_score = 0.0
            else:
                z_score = (spread[i] - mean_spread) / std_spread
            
            z_scores.append(z_score)
        
        z_scores = np.array(z_scores)
        
        # Run trading logic
        position = None  # None, 'LONG', 'SHORT'
        entry_price_a = None
        entry_price_b = None
        trades = []
        equity_curve = [initial_capital]
        cash = initial_capital
        shares_a = 0
        shares_b = 0
        
        for i in range(len(z_scores)):
            current_z = z_scores[i]
            
            # Entry logic
            if position is None:
                # LONG spread
                if current_z < -entry_threshold:
                    position = 'LONG'
                    entry_price_a = prices_a[i]
                    entry_price_b = prices_b[i]
                    # Buy A, Sell B
                    shares_a = (cash * 0.95) / entry_price_a
                    shares_b = -(shares_a * hedge_ratio) if hedge_ratio > 0 else 0
                    cash = cash - shares_a * entry_price_a - shares_b * entry_price_b
                    entry_date = dates[i]
                    entry_z = current_z
                
                # SHORT spread
                elif current_z > entry_threshold:
                    position = 'SHORT'
                    entry_price_a = prices_a[i]
                    entry_price_b = prices_b[i]
                    # Sell A, Buy B
                    shares_a = -(cash * 0.95) / entry_price_a
                    shares_b = -(shares_a * hedge_ratio) if hedge_ratio > 0 else 0
                    cash = cash - shares_a * entry_price_a - shares_b * entry_price_b
                    entry_date = dates[i]
                    entry_z = current_z
            
            # Exit logic
            elif position is not None:
                if abs(current_z) < exit_threshold:
                    # Close position
                    exit_price_a = prices_a[i]
                    exit_price_b = prices_b[i]
                    
                    # Calculate P&L
                    pnl = (shares_a * (exit_price_a - entry_price_a) +
                           shares_b * (exit_price_b - entry_price_b))
                    
                    trades.append({
                        'entry_date': entry_date,
                        'exit_date': dates[i],
                        'position_type': position,
                        'entry_z': entry_z,
                        'exit_z': current_z,
                        'pnl': pnl,
                        'return_pct': (pnl / initial_capital) * 100,
                        'holding_days': (dates[i] - entry_date).days
                    })
                    
                    cash = cash + shares_a * exit_price_a + shares_b * exit_price_b
                    shares_a = 0
                    shares_b = 0
                    position = None
            
            # Update equity
            current_equity = cash
            if position is not None:
                current_equity += shares_a * prices_a[i] + shares_b * prices_b[i]
            
            equity_curve.append(current_equity)
        
        # Calculate metrics
        metrics = self._calculate_metrics(
            symbol_a, symbol_b, equity_curve, trades,
            initial_capital, entry_threshold, exit_threshold,
            dates[0], dates[-1]
        )
        
        return metrics
    
    def _calculate_metrics(self, symbol_a: str, symbol_b: str,
                          equity_curve: List[float], trades: List[Dict],
                          initial_capital: float, entry_threshold: float,
                          exit_threshold: float, start_date, end_date) -> Dict:
        """Calculate performance metrics."""
        
        equity_curve = np.array(equity_curve)
        
        # Returns
        total_return = (equity_curve[-1] - initial_capital) / initial_capital
        total_return_pct = total_return * 100
        
        days = (end_date - start_date).days
        annualized_return = total_return * (365.0 / max(days, 1))
        
        # Drawdown
        running_max = np.maximum.accumulate(equity_curve)
        drawdown = (equity_curve - running_max) / running_max
        max_drawdown = np.min(drawdown)
        
        # Sharpe and Sortino
        daily_returns = np.diff(equity_curve) / equity_curve[:-1]
        
        if len(daily_returns) > 1:
            mean_daily_return = np.mean(daily_returns)
            std_daily_return = np.std(daily_returns)
            
            sharpe_ratio = (mean_daily_return * 252) / (std_daily_return * np.sqrt(252)) if std_daily_return > 0 else 0
            
            # Sortino (only penalize negative returns)
            negative_returns = daily_returns[daily_returns < 0]
            downside_std = np.std(negative_returns) if len(negative_returns) > 0 else 0
            sortino_ratio = (mean_daily_return * 252) / (downside_std * np.sqrt(252)) if downside_std > 0 else 0
        else:
            sharpe_ratio = 0.0
            sortino_ratio = 0.0
        
        # Trade statistics
        if trades:
            hit_rate = len([t for t in trades if t['pnl'] > 0]) / len(trades)
            
            winning_trades = [t for t in trades if t['pnl'] > 0]
            losing_trades = [t for t in trades if t['pnl'] < 0]
            
            avg_win = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0
            avg_loss = abs(np.mean([t['pnl'] for t in losing_trades])) if losing_trades else 0
            
            profit_factor = avg_win / avg_loss if avg_loss > 0 else 0
            avg_holding_days = np.mean([t['holding_days'] for t in trades])
        else:
            hit_rate = 0.0
            profit_factor = 0.0
            avg_holding_days = 0.0
        
        return {
            'stock_a': symbol_a,
            'stock_b': symbol_b,
            'start_date': start_date,
            'end_date': end_date,
            'entry_threshold': entry_threshold,
            'exit_threshold': exit_threshold,
            'total_return': total_return_pct,
            'annualized_return': annualized_return * 100,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'max_drawdown': max_drawdown * 100,
            'num_trades': len(trades),
            'hit_rate': hit_rate * 100,
            'profit_factor': profit_factor,
            'avg_holding_days': avg_holding_days,
            'final_equity': equity_curve[-1],
            'trades': trades
        }
    
    def _empty_backtest_result(self, symbol_a: str, symbol_b: str) -> Dict:
        """Return empty backtest result."""
        return {
            'stock_a': symbol_a,
            'stock_b': symbol_b,
            'total_return': 0.0,
            'annualized_return': 0.0,
            'sharpe_ratio': 0.0,
            'sortino_ratio': 0.0,
            'max_drawdown': 0.0,
            'num_trades': 0,
            'hit_rate': 0.0,
            'profit_factor': 0.0,
            'avg_holding_days': 0.0,
            'final_equity': 0.0,
            'trades': []
        }
    
    def backtest_pairs_batch(self, cointegrated_pairs: List[Dict],
                            start_date: datetime = None,
                            end_date: datetime = None) -> List[Dict]:
        """Backtest multiple pairs."""
        results = []
        
        for pair in cointegrated_pairs:
            result = self.backtest_pair(
                pair['stock_a'],
                pair['stock_b'],
                start_date,
                end_date
            )
            results.append(result)
        
        # Sort by Sharpe ratio
        results.sort(key=lambda x: x['sharpe_ratio'], reverse=True)
        
        logger.info(f"Completed backtests for {len(results)} pairs")
        return results


# Global instance
_backtest_engine = None


def get_backtest_engine() -> BacktestingEngine:
    """Get or create backtesting engine."""
    global _backtest_engine
    if _backtest_engine is None:
        _backtest_engine = BacktestingEngine()
    return _backtest_engine
