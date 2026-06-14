"""
Initialize database with sample data for testing.
"""

import sys
import os
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

from src.database import get_db_ops
from src.data_ingestion import get_data_manager


def init_sample_data():
    """Initialize database with sample stocks and data."""
    
    print("Initializing database with sample data...")
    
    db_ops = get_db_ops()
    data_manager = get_data_manager()
    
    # Sample stocks
    stocks = [
        ('RELIANCE', 'Reliance Industries', 'Energy', 'NIFTY50'),
        ('TCS', 'Tata Consultancy Services', 'IT', 'NIFTY50'),
        ('INFY', 'Infosys', 'IT', 'NIFTY50'),
        ('HDFCBANK', 'HDFC Bank', 'Finance', 'NIFTY50'),
        ('ICICIBANK', 'ICICI Bank', 'Finance', 'NIFTY50'),
    ]
    
    print(f"Adding {len(stocks)} stocks...")
    for symbol, name, sector, universe in stocks:
        existing = db_ops.get_stock(symbol)
        if not existing:
            db_ops.add_stock(symbol, name, sector, universe)
            print(f"  ✓ {symbol}")
    
    # Generate sample OHLCV data
    print("\nGenerating sample OHLCV data...")
    base_date = datetime.now() - timedelta(days=252)
    
    for symbol, _, _, _ in stocks:
        print(f"  Generating data for {symbol}...")
        
        data_records = []
        price = np.random.uniform(100, 500)
        
        for i in range(252):
            date = base_date + timedelta(days=i)
            
            # Generate OHLCV
            open_price = price
            close_price = price * (1 + np.random.normal(0.0005, 0.02))
            high = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.01)))
            low = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.01)))
            volume = np.random.uniform(1e6, 10e6)
            
            data_records.append({
                'date': date,
                'open': open_price,
                'high': high,
                'low': low,
                'close': close_price,
                'volume': volume
            })
            
            price = close_price
        
        # Save to parquet
        df = pd.DataFrame(data_records)
        data_manager.save_to_parquet(df, symbol)
    
    print("\n✓ Database initialized successfully!")
    print(f"Added {len(stocks)} stocks with 252 days of sample data")


if __name__ == '__main__':
    init_sample_data()
