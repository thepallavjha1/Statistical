"""
Data ingestion module for downloading and managing OHLCV data.
"""

import os
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataIngestionManager:
    """Manages data download and storage."""
    
    # NSE suffix for Indian stocks on yfinance
    NSE_SUFFIX = '.NS'
    
    def __init__(self, data_dir: str = None):
        """Initialize data manager."""
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
    
    def download_stock_data(self, symbol: str, start_date: datetime = None,
                          end_date: datetime = None) -> pd.DataFrame:
        """Download OHLCV data for a stock using yfinance."""
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=3*365)  # 3 years
        
        try:
            # Add NSE suffix for Indian stocks
            ticker_symbol = f"{symbol}{self.NSE_SUFFIX}"
            
            logger.info(f"Downloading {symbol} from {start_date.date()} to {end_date.date()}")
            data = yf.download(
                ticker_symbol,
                start=start_date,
                end=end_date,
                progress=False
            )
            
            if data.empty:
                logger.warning(f"No data downloaded for {symbol}")
                return pd.DataFrame()
            
            # Rename columns to lowercase
            data.columns = [col.lower() for col in data.columns]
            
            # Reset index to make date a column
            data.reset_index(inplace=True)
            data.rename(columns={'Date': 'date'}, inplace=True)
            
            # Ensure date is datetime
            data['date'] = pd.to_datetime(data['date'])
            
            logger.info(f"Downloaded {len(data)} records for {symbol}")
            return data
        
        except Exception as e:
            logger.error(f"Error downloading {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def download_multiple_stocks(self, symbols: List[str], 
                                start_date: datetime = None,
                                end_date: datetime = None) -> Dict[str, pd.DataFrame]:
        """Download data for multiple stocks."""
        data_dict = {}
        
        for symbol in symbols:
            data = self.download_stock_data(symbol, start_date, end_date)
            if not data.empty:
                data_dict[symbol] = data
        
        return data_dict
    
    def save_to_parquet(self, data: pd.DataFrame, symbol: str):
        """Save data to parquet file."""
        file_path = os.path.join(self.data_dir, f"{symbol}_ohlcv.parquet")
        data.to_parquet(file_path, index=False)
        logger.info(f"Saved {symbol} to {file_path}")
    
    def load_from_parquet(self, symbol: str) -> Optional[pd.DataFrame]:
        """Load data from parquet file."""
        file_path = os.path.join(self.data_dir, f"{symbol}_ohlcv.parquet")
        if os.path.exists(file_path):
            data = pd.read_parquet(file_path)
            logger.info(f"Loaded {symbol} from {file_path}")
            return data
        return None
    
    def update_stock_data(self, symbol: str) -> pd.DataFrame:
        """Update stock data (load existing + download recent)."""
        # Load existing data
        existing_data = self.load_from_parquet(symbol)
        
        if existing_data is not None and not existing_data.empty:
            last_date = pd.to_datetime(existing_data['date']).max()
            start_date = last_date - timedelta(days=7)  # Overlap for accuracy
        else:
            start_date = datetime.now() - timedelta(days=3*365)
        
        # Download new data
        new_data = self.download_stock_data(symbol, start_date=start_date)
        
        if new_data.empty:
            return existing_data
        
        # Combine and deduplicate
        if existing_data is not None and not existing_data.empty:
            combined = pd.concat([existing_data, new_data], ignore_index=True)
            combined['date'] = pd.to_datetime(combined['date'])
            combined = combined.drop_duplicates(subset=['date'], keep='last')
            combined = combined.sort_values('date').reset_index(drop=True)
        else:
            combined = new_data
        
        # Save updated data
        self.save_to_parquet(combined, symbol)
        return combined
    
    def load_universe(self, universe_file: str) -> List[str]:
        """Load stock universe from CSV file."""
        try:
            df = pd.read_csv(universe_file)
            symbols = df['symbol'].tolist()
            logger.info(f"Loaded {len(symbols)} stocks from {universe_file}")
            return symbols
        except Exception as e:
            logger.error(f"Error loading universe from {universe_file}: {str(e)}")
            return []
    
    def update_universe(self, universe_file: str):
        """Update all stocks in a universe."""
        symbols = self.load_universe(universe_file)
        
        for symbol in symbols:
            try:
                self.update_stock_data(symbol)
            except Exception as e:
                logger.error(f"Error updating {symbol}: {str(e)}")
    
    def get_price_series(self, symbol: str) -> Optional[pd.Series]:
        """Get closing price series for a symbol."""
        data = self.load_from_parquet(symbol)
        if data is not None and not data.empty:
            data = data.sort_values('date')
            return data.set_index('date')['close']
        return None
    
    def get_normalized_prices(self, symbol: str, 
                            start_date: datetime = None,
                            end_date: datetime = None) -> Optional[pd.Series]:
        """Get normalized (0-1) price series."""
        prices = self.get_price_series(symbol)
        
        if prices is None or prices.empty:
            return None
        
        if start_date:
            prices = prices[prices.index >= start_date]
        if end_date:
            prices = prices[prices.index <= end_date]
        
        min_price = prices.min()
        max_price = prices.max()
        
        if max_price == min_price:
            return pd.Series(0.5, index=prices.index)
        
        normalized = (prices - min_price) / (max_price - min_price)
        return normalized
    
    def data_quality_check(self, data: pd.DataFrame) -> Dict[str, any]:
        """Check data quality."""
        checks = {
            'total_records': len(data),
            'missing_dates': data['date'].isna().sum(),
            'missing_open': data['open'].isna().sum(),
            'missing_close': data['close'].isna().sum(),
            'missing_volume': data['volume'].isna().sum(),
            'zero_volume': (data['volume'] == 0).sum(),
            'invalid_ohlc': ((data['high'] < data['low']).sum() + 
                           (data['open'] > data['high']).sum() +
                           (data['close'] > data['high']).sum())
        }
        return checks


# Global instance
_data_manager = None


def get_data_manager(data_dir: str = None) -> DataIngestionManager:
    """Get or create data manager instance."""
    global _data_manager
    if _data_manager is None:
        _data_manager = DataIngestionManager(data_dir)
    return _data_manager
