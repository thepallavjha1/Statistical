"""
Unit tests for Statistical Arbitrage Platform.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Mock tests for core modules
class TestDataIngestion:
    """Tests for data ingestion module."""
    
    def test_data_manager_initialization(self):
        """Test data manager initialization."""
        from src.data_ingestion import DataIngestionManager
        manager = DataIngestionManager()
        assert manager is not None
    
    def test_load_universe(self):
        """Test loading universe from CSV."""
        from src.data_ingestion import DataIngestionManager
        import os
        
        manager = DataIngestionManager()
        config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
        universe_file = os.path.join(config_dir, 'nifty50.csv')
        
        symbols = manager.load_universe(universe_file)
        assert len(symbols) > 0
        assert 'RELIANCE' in symbols


class TestPairSelection:
    """Tests for pair selection module."""
    
    def test_pair_selection_engine_initialization(self):
        """Test pair selection engine initialization."""
        from src.pair_selection import PairSelectionEngine
        engine = PairSelectionEngine(correlation_threshold=0.7)
        assert engine.correlation_threshold == 0.7


class TestCointegration:
    """Tests for cointegration module."""
    
    def test_cointegration_analyzer_initialization(self):
        """Test cointegration analyzer initialization."""
        from src.cointegration import CointegrationAnalyzer
        analyzer = CointegrationAnalyzer(p_value_threshold=0.05)
        assert analyzer.p_value_threshold == 0.05
    
    def test_hedge_ratio_calculation(self):
        """Test hedge ratio calculation."""
        from src.cointegration import CointegrationAnalyzer
        
        analyzer = CointegrationAnalyzer()
        
        # Create synthetic data
        prices_b = np.linspace(100, 150, 100)
        prices_a = 2.0 * prices_b + np.random.normal(0, 5, 100)
        
        beta = analyzer.calculate_hedge_ratio(prices_a, prices_b)
        
        # Beta should be close to 2.0
        assert 1.5 < beta < 2.5


class TestSignalEngine:
    """Tests for signal engine module."""
    
    def test_signal_engine_initialization(self):
        """Test signal engine initialization."""
        from src.signal_engine import SignalEngine
        engine = SignalEngine(long_threshold=-2.0, short_threshold=2.0)
        assert engine.long_threshold == -2.0
        assert engine.short_threshold == 2.0
    
    def test_z_score_calculation(self):
        """Test Z-score calculation."""
        from src.signal_engine import SignalEngine
        
        engine = SignalEngine()
        
        # Create synthetic data
        prices_a = np.array([100, 101, 102, 103, 104])
        prices_b = np.array([50, 50.5, 51, 51.5, 52])
        hedge_ratio = 2.0
        
        z_score = engine.calculate_z_score(prices_a, prices_b, hedge_ratio, window=3)
        
        assert not np.isnan(z_score)
    
    def test_signal_determination(self):
        """Test signal determination logic."""
        from src.signal_engine import SignalEngine
        
        engine = SignalEngine()
        
        # Test long signal
        signal = engine._determine_signal(-2.5, -2.0, -1.8)
        assert signal == 'LONG'
        
        # Test short signal
        signal = engine._determine_signal(2.5, 2.0, 1.8)
        assert signal == 'SHORT'
        
        # Test exit signal
        signal = engine._determine_signal(0.2, 0.3, 0.4)
        assert signal == 'EXIT'
        
        # Test hold signal
        signal = engine._determine_signal(0.8, 0.9, 1.0)
        assert signal == 'HOLD'


class TestBacktesting:
    """Tests for backtesting module."""
    
    def test_backtest_engine_initialization(self):
        """Test backtesting engine initialization."""
        from src.backtesting import BacktestingEngine
        engine = BacktestingEngine()
        assert engine is not None


class TestDatabase:
    """Tests for database module."""
    
    def test_database_initialization(self):
        """Test database initialization."""
        from src.database import init_db
        db = init_db(':memory:')
        assert db is not None
    
    def test_database_operations(self):
        """Test database operations."""
        from src.database import DatabaseOperations
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=True) as tmp:
            db_ops = DatabaseOperations(tmp.name)
            
            # Test adding a stock
            stock = db_ops.add_stock('TEST', 'Test Company', 'Test Sector', 'NIFTY50')
            assert stock.symbol == 'TEST'
            
            # Test getting a stock
            retrieved = db_ops.get_stock('TEST')
            assert retrieved is not None
            assert retrieved.symbol == 'TEST'


class TestUtilities:
    """Tests for utility modules."""
    
    def test_opportunity_ranker(self):
        """Test opportunity ranking."""
        from src.utils import OpportunityRanker
        
        signal = {
            'signal_strength': 0.8,
            'z_score_30': -2.5,
            'sharpe_ratio': 1.5,
            'p_value': 0.01
        }
        
        score = OpportunityRanker.calculate_opportunity_score(signal)
        assert 0 <= score <= 1
    
    def test_data_validator(self):
        """Test data validation."""
        from src.utils import DataValidator
        
        # Create valid data
        data = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=100),
            'open': np.random.rand(100) * 100 + 100,
            'high': np.random.rand(100) * 100 + 105,
            'low': np.random.rand(100) * 100 + 95,
            'close': np.random.rand(100) * 100 + 100,
            'volume': np.random.rand(100) * 1e7 + 1e6
        })
        
        checks = DataValidator.check_price_data(data)
        assert 'total_records' in checks
        assert checks['total_records'] == 100


class TestPipeline:
    """Tests for main pipeline."""
    
    def test_pipeline_initialization(self):
        """Test pipeline initialization."""
        from src.pipeline import StatArbPipeline
        pipeline = StatArbPipeline()
        assert pipeline is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
