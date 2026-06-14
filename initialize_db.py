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
    
    print("📊 Initializing Statistical Arbitrage Platform database...")
    
    db_ops = get_db_ops()
    data_manager = get_data_manager()
    
    # Sample stocks from NIFTY 50
    stocks = [
        ('RELIANCE', 'Reliance Industries', 'Energy', 'NIFTY50'),
        ('TCS', 'Tata Consultancy Services', 'IT', 'NIFTY50'),
        ('INFY', 'Infosys', 'IT', 'NIFTY50'),
        ('HDFCBANK', 'HDFC Bank', 'Finance', 'NIFTY50'),
        ('ICICIBANK', 'ICICI Bank', 'Finance', 'NIFTY50'),
        ('WIPRO', 'Wipro', 'IT', 'NIFTY50'),
        ('AXISBANK', 'Axis Bank', 'Finance', 'NIFTY50'),
        ('LT', 'Larsen & Toubro', 'Infrastructure', 'NIFTY50'),
        ('MARUTI', 'Maruti Suzuki', 'Automobile', 'NIFTY50'),
        ('BAJAJFINSV', 'Bajaj Finserv', 'Finance', 'NIFTY50'),
    ]
    
    print(f"\n✓ Adding {len(stocks)} stocks to database...")
    for symbol, name, sector, universe in stocks:
        try:
            existing = db_ops.get_stock(symbol)
            if not existing:
                db_ops.add_stock(symbol, name, sector, universe)
                print(f"  ✓ {symbol:12} - {name}")
            else:
                print(f"  ~ {symbol:12} - Already exists")
        except Exception as e:
            print(f"  ✗ {symbol:12} - Error: {e}")
    
    # Generate sample OHLCV data
    print(f"\n✓ Generating sample OHLCV data (252 days per stock)...")
    base_date = datetime.now() - timedelta(days=252)
    
    for symbol, _, _, _ in stocks:
        try:
            print(f"  ↓ {symbol}...", end=" ", flush=True)
            
            data_records = []
            price = np.random.uniform(100, 500)
            
            for i in range(252):
                date = base_date + timedelta(days=i)
                
                # Generate OHLCV with realistic simulation
                open_price = price
                daily_return = np.random.normal(0.0005, 0.02)
                close_price = price * (1 + daily_return)
                high = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.01)))
                low = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.01)))
                volume = np.random.uniform(1e6, 10e6)
                
                data_records.append({
                    'Date': date,
                    'Open': open_price,
                    'High': high,
                    'Low': low,
                    'Close': close_price,
                    'Volume': volume
                })
                
                price = close_price
            
            # Save to parquet
            df = pd.DataFrame(data_records)
            df.set_index('Date', inplace=True)
            data_manager.save_to_parquet(df, symbol)
            print("✓")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    print("\n" + "="*60)
    print("✓ DATABASE INITIALIZATION COMPLETE!")
    print("="*60)
    print(f"\n  Stocks added: {len(stocks)}")
    print(f"  Database: data/statarb.db")
    print(f"  Data files: data/*.parquet")
    print(f"\n  Next step: streamlit run streamlit_app/app.py")
    print("="*60 + "\n")


if __name__ == '__main__':
    init_sample_data()
