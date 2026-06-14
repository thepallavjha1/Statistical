"""
Configuration settings for the Statistical Arbitrage Platform
All settings are hardcoded here for simplicity
"""

import os
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent

# === Database Configuration ===
DB_PATH = str(PROJECT_ROOT / "data" / "statarb.db")
DATA_DIR = str(PROJECT_ROOT / "data")

# Create directories if they don't exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(str(PROJECT_ROOT / "logs"), exist_ok=True)

# === Signal Thresholds ===
LONG_THRESHOLD = -2.0        # Z-score threshold for long signal
SHORT_THRESHOLD = 2.0        # Z-score threshold for short signal
EXIT_THRESHOLD = 0.5         # Z-score threshold for exit signal

# === Data Configuration ===
MIN_LIQUIDITY = 1000000      # Minimum daily volume
CORRELATION_THRESHOLD = 0.7  # Minimum correlation for pair selection
COINTEGRATION_PVALUE = 0.05  # P-value threshold for cointegration test

# === Stock Universe ===
STOCK_UNIVERSE = "NIFTY50"  # Can be: NIFTY50, NIFTY100, NIFTY200

# === Data Download Configuration ===
YFINANCE_RATE_LIMIT = 0.1   # Rate limit in seconds
LOOKBACK_PERIOD = 3         # Years of historical data to download

# === Analysis Periods ===
CORRELATION_PERIODS = [252, 504, 756]  # 1Y, 2Y, 3Y in trading days

# === Backtesting Configuration ===
BACKTEST_INITIAL_CAPITAL = 100000      # Initial capital for backtest
BACKTEST_POSITION_SIZE = 0.5           # Fraction of capital per trade
BACKTEST_TRADING_DAYS = 252            # Trading days in a year

# === Logging ===
LOG_LEVEL = "INFO"
LOG_FILE = str(PROJECT_ROOT / "logs" / "statarb.log")

# === Streamlit Configuration ===
STREAMLIT_PAGE_CONFIG = {
    "page_title": "Statistical Arbitrage Platform",
    "page_icon": "📈",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# === Display Configuration ===
DEFAULT_CHART_HEIGHT = 500
DEFAULT_CHART_WIDTH = 900
DATE_FORMAT = "%Y-%m-%d"

print(f"✓ Configuration loaded from {__file__}")
print(f"  Database: {DB_PATH}")
print(f"  Data Directory: {DATA_DIR}")
print(f"  Stock Universe: {STOCK_UNIVERSE}")
