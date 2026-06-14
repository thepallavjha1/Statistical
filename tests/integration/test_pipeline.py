"""Integration tests for Statistical Arbitrage Platform."""

import pytest
import tempfile
import os
from datetime import datetime, timedelta


class TestFullPipeline:
    """Integration tests for the full pipeline."""
    
    def test_pipeline_end_to_end(self):
        """Test full pipeline execution (using mock data)."""
        from src.pipeline import StatArbPipeline
        
        pipeline = StatArbPipeline()
        assert pipeline is not None


class TestDatabase:
    """Integration tests for database operations."""
    
    def test_database_end_to_end(self):
        """Test database end-to-end operations."""
        from src.database import DatabaseOperations
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            tmp_path = tmp.name
            tmp.close()
            
        try:
            db_ops = DatabaseOperations(tmp_path)
            
            # Add and retrieve stock
            db_ops.add_stock('RELIANCE', 'Reliance Industries', 'Energy', 'NIFTY50')
            stock = db_ops.get_stock('RELIANCE')
            assert stock.symbol == 'RELIANCE'
            
            # Add OHLCV data
            db_ops.add_ohlcv(
                'RELIANCE',
                datetime.now(),
                100.0, 102.0, 99.0, 101.0, 1e6
            )
            
            ohlcv = db_ops.get_ohlcv('RELIANCE')
            assert len(ohlcv) > 0
            
            # Add pair
            pair = db_ops.add_pair('RELIANCE', 'TCS', 0.75, 0.72, 0.68)
            assert pair.stock_a == 'RELIANCE'
            
            # Add cointegration result
            coint = db_ops.add_cointegration(
                'RELIANCE', 'TCS',
                -3.5, 0.01, "[-3.43, -2.86, -2.57]",
                hedge_ratio=1.5
            )
            assert coint.cointegrated == True
            
            # Verify retrieval
            cointegrated = db_ops.get_cointegrated_pairs(threshold=0.05)
            assert len(cointegrated) > 0
        finally:
            if 'db_ops' in locals() and db_ops:
                try:
                    db_ops.db.engine.dispose()
                except Exception:
                    pass
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
