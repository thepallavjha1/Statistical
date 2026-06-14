"""
Test data generation for development and testing.
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from src.data_ingestion import get_data_manager


def generate_test_data():
    """Generate test OHLCV data for development."""
    
    print("Generating test data for development...")
    
    data_mgr = get_data_manager()
    
    # Test symbols
    symbols = ['TEST_A', 'TEST_B', 'TEST_C']
    
    for symbol in symbols:
        print(f"Generating data for {symbol}...")
        
        # Generate 3 years of daily data
        dates = pd.date_range(end=datetime.now(), periods=756, freq='D')
        
        # Generate correlated price series
        base_price = np.random.uniform(100, 500)
        daily_returns = np.random.normal(0.0005, 0.02, len(dates))
        prices = base_price * np.exp(np.cumsum(daily_returns))
        
        data = pd.DataFrame({
            'date': dates,
            'open': prices * (1 + np.random.normal(0, 0.01, len(dates))),
            'high': prices * (1 + abs(np.random.normal(0, 0.015, len(dates)))),
            'low': prices * (1 - abs(np.random.normal(0, 0.015, len(dates)))),
            'close': prices,
            'volume': np.random.uniform(1e6, 10e6, len(dates))
        })
        
        # Ensure OHLC logic
        data['high'] = data[['open', 'high', 'close']].max(axis=1)
        data['low'] = data[['open', 'low', 'close']].min(axis=1)
        
        # Save
        data_mgr.save_to_parquet(data, symbol)
        print(f"  ✓ {len(data)} records saved")
    
    print("\n✓ Test data generated successfully!")


if __name__ == '__main__':
    generate_test_data()
