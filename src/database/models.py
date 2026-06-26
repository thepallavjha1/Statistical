"""
Database models for Statistical Arbitrage Platform.
"""

from datetime import datetime
from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import threading

Base = declarative_base()


class Stock(Base):
    """Stores information about individual stocks."""
    __tablename__ = 'stocks'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    company_name = Column(String(255))
    sector = Column(String(100))
    nifty_index = Column(String(50))  # NIFTY50, NIFTY100, etc.
    active = Column(Boolean, default=True)
    last_price = Column(Float)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Stock {self.symbol}>"


class OHLCVData(Base):
    """Stores OHLCV data for stocks."""
    __tablename__ = 'ohlcv_data'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    
    def __repr__(self):
        return f"<OHLCVData {self.symbol} {self.date}>"


class Pair(Base):
    """Stores pair information."""
    __tablename__ = 'pairs'
    
    id = Column(Integer, primary_key=True)
    stock_a = Column(String(20), nullable=False, index=True)
    stock_b = Column(String(20), nullable=False, index=True)
    correlation_1y = Column(Float)
    correlation_2y = Column(Float)
    correlation_3y = Column(Float)
    active = Column(Boolean, default=True)
    created_date = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Pair {self.stock_a}-{self.stock_b}>"


class CointegrationResult(Base):
    """Stores cointegration test results."""
    __tablename__ = 'cointegration_results'
    
    id = Column(Integer, primary_key=True)
    stock_a = Column(String(20), nullable=False, index=True)
    stock_b = Column(String(20), nullable=False, index=True)
    test_statistic = Column(Float)
    p_value = Column(Float)
    critical_values = Column(String(255))  # JSON string
    cointegrated = Column(Boolean)
    hedge_ratio = Column(Float)
    test_date = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<CointegrationResult {self.stock_a}-{self.stock_b} p={self.p_value:.4f}>"


class SpreadStatistics(Base):
    """Stores spread statistics for pairs."""
    __tablename__ = 'spread_statistics'
    
    id = Column(Integer, primary_key=True)
    stock_a = Column(String(20), nullable=False, index=True)
    stock_b = Column(String(20), nullable=False, index=True)
    mean_spread = Column(Float)
    std_spread = Column(Float)
    median_spread = Column(Float)
    min_spread = Column(Float)
    max_spread = Column(Float)
    half_life = Column(Float)  # Days to revert to mean
    period_days = Column(Integer)  # Lookback period
    calculated_date = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<SpreadStatistics {self.stock_a}-{self.stock_b}>"


class Signal(Base):
    """Stores trading signals."""
    __tablename__ = 'signals'
    
    id = Column(Integer, primary_key=True)
    stock_a = Column(String(20), nullable=False, index=True)
    stock_b = Column(String(20), nullable=False, index=True)
    signal_type = Column(String(20))  # BUY, SELL, EXIT, HOLD
    z_score_30d = Column(Float)
    z_score_60d = Column(Float)
    z_score_90d = Column(Float)
    current_spread = Column(Float)
    signal_strength = Column(Float)  # 0 to 1
    created_date = Column(DateTime, default=datetime.utcnow, index=True)
    
    @property
    def z_score_30(self):
        return self.z_score_30d

    @property
    def z_score_60(self):
        return self.z_score_60d

    @property
    def z_score_90(self):
        return self.z_score_90d

    def __repr__(self):
        return f"<Signal {self.stock_a}-{self.stock_b} {self.signal_type}>"


class SignalHistory(Base):
    """Stores historical signals for tracking changes."""
    __tablename__ = 'signal_history'
    
    id = Column(Integer, primary_key=True)
    stock_a = Column(String(20), nullable=False, index=True)
    stock_b = Column(String(20), nullable=False, index=True)
    signal_type = Column(String(20))
    z_score = Column(Float)
    spread = Column(Float)
    created_date = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<SignalHistory {self.stock_a}-{self.stock_b} {self.created_date}>"


class BacktestResult(Base):
    """Stores backtesting results."""
    __tablename__ = 'backtest_results'
    
    id = Column(Integer, primary_key=True)
    stock_a = Column(String(20), nullable=False, index=True)
    stock_b = Column(String(20), nullable=False, index=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    entry_threshold = Column(Float)
    exit_threshold = Column(Float)
    total_return = Column(Float)
    annualized_return = Column(Float)
    sharpe_ratio = Column(Float)
    sortino_ratio = Column(Float)
    max_drawdown = Column(Float)
    hit_rate = Column(Float)
    profit_factor = Column(Float)
    num_trades = Column(Integer)
    avg_holding_days = Column(Float)
    backtest_date = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<BacktestResult {self.stock_a}-{self.stock_b} return={self.total_return:.2f}%>"


class VirtualPortfolio(Base):
    """Stores status of the virtual portfolio."""
    __tablename__ = 'virtual_portfolio'
    
    id = Column(Integer, primary_key=True)
    initial_capital = Column(Float, default=10000000.0) # 1 Crore INR
    cash = Column(Float, default=10000000.0)
    equity = Column(Float, default=10000000.0)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<VirtualPortfolio cash={self.cash:.2f} equity={self.equity:.2f}>"


class VirtualPosition(Base):
    """Stores open virtual trade positions."""
    __tablename__ = 'virtual_positions'
    
    id = Column(Integer, primary_key=True)
    stock_a = Column(String(20), nullable=False, index=True)
    stock_b = Column(String(20), nullable=False, index=True)
    position_type = Column(String(20), nullable=False) # LONG or SHORT
    hedge_ratio = Column(Float, nullable=False)
    shares_a = Column(Float, nullable=False)
    shares_b = Column(Float, nullable=False)
    entry_price_a = Column(Float, nullable=False)
    entry_price_b = Column(Float, nullable=False)
    entry_date = Column(DateTime, default=datetime.utcnow, index=True)
    entry_z_score = Column(Float)
    
    def __repr__(self):
        return f"<VirtualPosition {self.stock_a}-{self.stock_b} {self.position_type}>"


class VirtualTradeHistory(Base):
    """Stores completed virtual trades."""
    __tablename__ = 'virtual_trade_history'
    
    id = Column(Integer, primary_key=True)
    stock_a = Column(String(20), nullable=False, index=True)
    stock_b = Column(String(20), nullable=False, index=True)
    position_type = Column(String(20), nullable=False)
    entry_date = Column(DateTime, nullable=False)
    exit_date = Column(DateTime, default=datetime.utcnow, index=True)
    entry_price_a = Column(Float, nullable=False)
    entry_price_b = Column(Float, nullable=False)
    exit_price_a = Column(Float, nullable=False)
    exit_price_b = Column(Float, nullable=False)
    shares_a = Column(Float, nullable=False)
    shares_b = Column(Float, nullable=False)
    pnl = Column(Float)
    return_pct = Column(Float)
    
    def __repr__(self):
        return f"<VirtualTradeHistory {self.stock_a}-{self.stock_b} pnl={self.pnl:.2f}>"


class DatabaseManager:
    """Manages database connections and sessions."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, db_path: str = None):
        with cls._lock:
            if db_path is not None:
                normalized_path = f"sqlite:///{db_path}"
                if cls._instance is not None and cls._instance.db_path != normalized_path:
                    # Create a separate, non-singleton instance for a different database path
                    db_dir = os.path.dirname(db_path)
                    if db_dir:
                        os.makedirs(db_dir, exist_ok=True)
                    instance = super(DatabaseManager, cls).__new__(cls)
                    instance.db_path = normalized_path
                    instance.engine = create_engine(normalized_path)
                    instance.SessionLocal = sessionmaker(
                        bind=instance.engine,
                        expire_on_commit=False
                    )
                    Base.metadata.create_all(instance.engine)
                    return instance

            if cls._instance is None:
                if db_path is None:
                    try:
                        from config import DB_PATH
                        db_path = DB_PATH
                    except ImportError:
                        db_path = os.path.join(
                            os.path.dirname(__file__),
                            '..', '..', 'data', 'statarb.db'
                        )
                
                # Ensure directory exists
                db_dir = os.path.dirname(db_path)
                if db_dir:
                    os.makedirs(db_dir, exist_ok=True)
                    
                instance = super(DatabaseManager, cls).__new__(cls)
                instance.db_path = f"sqlite:///{db_path}"
                instance.engine = create_engine(instance.db_path)
                instance.SessionLocal = sessionmaker(
                    bind=instance.engine,
                    expire_on_commit=False
                )
                Base.metadata.create_all(instance.engine)
                cls._instance = instance
                
            return cls._instance
    
    def get_session(self):
        """Get a new database session."""
        return self.SessionLocal()
    
    def create_tables(self):
        """Create all tables."""
        Base.metadata.create_all(self.engine)
    
    def drop_tables(self):
        """Drop all tables (use with caution)."""
        Base.metadata.drop_all(self.engine)


def init_db(db_path: str = None) -> DatabaseManager:
    """Initialize database."""
    return DatabaseManager(db_path)
