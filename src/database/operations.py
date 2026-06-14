"""
Database operations for Statistical Arbitrage Platform.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from .models import (
    Stock, OHLCVData, Pair, CointegrationResult, SpreadStatistics,
    Signal, SignalHistory, BacktestResult, init_db
)

# Import configuration
try:
    from config import DB_PATH
except ImportError:
    DB_PATH = None


class DatabaseOperations:
    """Handles all database operations."""
    
    def __init__(self, db_path: str = None):
        # Use config DB_PATH if not provided
        if db_path is None:
            db_path = DB_PATH
        self.db = init_db(db_path)
    
    # Stock operations
    def add_stock(self, symbol: str, company_name: str = None, 
                  sector: str = None, nifty_index: str = None) -> Stock:
        """Add a new stock."""
        session = self.db.get_session()
        stock = Stock(
            symbol=symbol, 
            company_name=company_name,
            sector=sector, 
            nifty_index=nifty_index
        )
        session.add(stock)
        session.commit()
        session.close()
        return stock
    
    def get_stock(self, symbol: str) -> Optional[Stock]:
        """Get stock by symbol."""
        session = self.db.get_session()
        stock = session.query(Stock).filter_by(symbol=symbol).first()
        session.close()
        return stock
    
    def get_all_stocks(self, nifty_index: str = None, active_only: bool = True) -> List[Stock]:
        """Get all stocks, optionally filtered."""
        session = self.db.get_session()
        query = session.query(Stock)
        if active_only:
            query = query.filter_by(active=True)
        if nifty_index:
            query = query.filter_by(nifty_index=nifty_index)
        stocks = query.all()
        session.close()
        return stocks
    
    # OHLCV operations
    def add_ohlcv(self, symbol: str, date: datetime, open: float, high: float,
                  low: float, close: float, volume: float):
        """Add OHLCV data."""
        session = self.db.get_session()
        data = OHLCVData(
            symbol=symbol, date=date, open=open, high=high,
            low=low, close=close, volume=volume
        )
        session.add(data)
        session.commit()
        session.close()
    
    def get_ohlcv(self, symbol: str, start_date: datetime = None, 
                  end_date: datetime = None) -> List[OHLCVData]:
        """Get OHLCV data for a symbol."""
        session = self.db.get_session()
        query = session.query(OHLCVData).filter_by(symbol=symbol).order_by(OHLCVData.date)
        if start_date:
            query = query.filter(OHLCVData.date >= start_date)
        if end_date:
            query = query.filter(OHLCVData.date <= end_date)
        data = query.all()
        session.close()
        return data
    
    # Pair operations
    def add_pair(self, stock_a: str, stock_b: str, 
                 correlation_1y: float = None, correlation_2y: float = None,
                 correlation_3y: float = None) -> Pair:
        """Add a pair."""
        session = self.db.get_session()
        pair = Pair(
            stock_a=stock_a, stock_b=stock_b,
            correlation_1y=correlation_1y, correlation_2y=correlation_2y,
            correlation_3y=correlation_3y
        )
        session.add(pair)
        session.commit()
        session.close()
        return pair
    
    def get_pair(self, stock_a: str, stock_b: str) -> Optional[Pair]:
        """Get pair correlation data."""
        session = self.db.get_session()
        pair = session.query(Pair).filter(
            ((Pair.stock_a == stock_a) & (Pair.stock_b == stock_b)) |
            ((Pair.stock_a == stock_b) & (Pair.stock_b == stock_a))
        ).first()
        session.close()
        return pair
    
    # Cointegration operations
    def add_cointegration(self, stock_a: str, stock_b: str, test_statistic: float,
                         p_value: float, critical_values: str, hedge_ratio: float = None):
        """Add cointegration test result."""
        session = self.db.get_session()
        result = CointegrationResult(
            stock_a=stock_a, stock_b=stock_b, test_statistic=test_statistic,
            p_value=p_value, critical_values=critical_values,
            cointegrated=(p_value < 0.05), hedge_ratio=hedge_ratio
        )
        session.add(result)
        session.commit()
        session.close()
        return result
    
    def get_cointegrated_pairs(self, threshold: float = 0.05) -> List[CointegrationResult]:
        """Get all cointegrated pairs."""
        session = self.db.get_session()
        results = session.query(CointegrationResult).filter(
            CointegrationResult.p_value < threshold
        ).order_by(CointegrationResult.test_date.desc()).all()
        session.close()
        return results
    
    # Spread statistics operations
    def add_spread_stats(self, stock_a: str, stock_b: str, mean_spread: float,
                        std_spread: float, median_spread: float, min_spread: float,
                        max_spread: float, half_life: float = None, period_days: int = 252):
        """Add spread statistics."""
        session = self.db.get_session()
        stats = SpreadStatistics(
            stock_a=stock_a, stock_b=stock_b, mean_spread=mean_spread,
            std_spread=std_spread, median_spread=median_spread,
            min_spread=min_spread, max_spread=max_spread,
            half_life=half_life, period_days=period_days
        )
        session.add(stats)
        session.commit()
        session.close()
        return stats
    
    # Signal operations
    def add_signal(self, stock_a: str, stock_b: str, signal_type: str,
                  z_score_30d: float = None, z_score_60d: float = None,
                  z_score_90d: float = None, current_spread: float = None,
                  signal_strength: float = None):
        """Add a signal."""
        session = self.db.get_session()
        signal = Signal(
            stock_a=stock_a, stock_b=stock_b, signal_type=signal_type,
            z_score_30d=z_score_30d, z_score_60d=z_score_60d,
            z_score_90d=z_score_90d, current_spread=current_spread,
            signal_strength=signal_strength
        )
        session.add(signal)
        session.commit()
        
        # Also add to history
        history = SignalHistory(
            stock_a=stock_a, stock_b=stock_b, signal_type=signal_type,
            z_score=z_score_90d, spread=current_spread
        )
        session.add(history)
        session.commit()
        session.close()
        return signal
    
    def get_latest_signals(self, hours: int = 24) -> List[Signal]:
        """Get latest signals."""
        session = self.db.get_session()
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        signals = session.query(Signal).filter(
            Signal.created_date >= cutoff
        ).order_by(Signal.created_date.desc()).all()
        session.close()
        return signals
    
    # Backtest operations
    def add_backtest_result(self, stock_a: str, stock_b: str, start_date: datetime,
                           end_date: datetime, entry_threshold: float,
                           exit_threshold: float, total_return: float,
                           annualized_return: float, sharpe_ratio: float,
                           sortino_ratio: float, max_drawdown: float,
                           hit_rate: float, profit_factor: float,
                           num_trades: int, avg_holding_days: float) -> BacktestResult:
        """Add backtest result."""
        session = self.db.get_session()
        result = BacktestResult(
            stock_a=stock_a, stock_b=stock_b, start_date=start_date,
            end_date=end_date, entry_threshold=entry_threshold,
            exit_threshold=exit_threshold, total_return=total_return,
            annualized_return=annualized_return, sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio, max_drawdown=max_drawdown,
            hit_rate=hit_rate, profit_factor=profit_factor,
            num_trades=num_trades, avg_holding_days=avg_holding_days
        )
        session.add(result)
        session.commit()
        session.close()
        return result
    
    def get_backtest_result(self, stock_a: str, stock_b: str) -> Optional[BacktestResult]:
        """Get latest backtest result for a pair."""
        session = self.db.get_session()
        result = session.query(BacktestResult).filter(
            (BacktestResult.stock_a == stock_a) & (BacktestResult.stock_b == stock_b)
        ).order_by(BacktestResult.backtest_date.desc()).first()
        session.close()
        return result


# Global database operations instance
_db_ops = None


def get_db_ops(db_path: str = None) -> DatabaseOperations:
    """Get or create database operations instance."""
    global _db_ops
    if _db_ops is None:
        _db_ops = DatabaseOperations(db_path)
    return _db_ops
