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
    """Initialize database with sample stocks, price series, cointegration results, and signals."""

    print("Initializing Statistical Arbitrage Platform database...")

    db_ops = get_db_ops()
    data_manager = get_data_manager()
    
    # Drop and recreate tables to start fresh
    print("Recreating database tables...")
    db_ops.db.drop_tables()
    db_ops.db.create_tables()

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

    print(f"\nAdding {len(stocks)} stocks to database...")
    for symbol, name, sector, universe in stocks:
        db_ops.add_stock(symbol, name, sector, universe)
        print(f"  [OK] {symbol:12} - {name}")

    # Generate sample OHLCV data
    print(f"\nGenerating sample cointegrated OHLCV data (252 days)...")
    base_date = datetime.now() - timedelta(days=252)
    
    # Seed random number generator for reproducibility
    np.random.seed(42)
    
    # 1. Generate independent base stocks (random walks)
    prices = {}
    base_stocks = {
        'TCS': 3000.0,
        'ICICIBANK': 900.0,
        'BAJAJFINSV': 1500.0,
        'RELIANCE': 2400.0,
        'MARUTI': 8000.0
    }
    
    for symbol, start_price in base_stocks.items():
        price_series = [start_price]
        current_price = start_price
        for _ in range(251):
            daily_return = np.random.normal(0.0002, 0.015)
            current_price = current_price * (1 + daily_return)
            price_series.append(current_price)
        prices[symbol] = np.array(price_series)

    # 2. Generate dependent stocks (cointegrated with base stocks)
    # INFY cointegrated with TCS: INFY = 0.5 * TCS + Spread
    # Spread is mean-reverting (AR1) centered around 100, ends with Z-score < -2.0 (LONG signal)
    tcs_prices = prices['TCS']
    infy_spread = [100.0]
    for i in range(251):
        if i < 240:
            next_spread = 100.0 + 0.85 * (infy_spread[-1] - 100.0) + np.random.normal(0, 3.0)
        else:
            next_spread = infy_spread[-1] - 8.0 + np.random.normal(0, 1.0)
        infy_spread.append(next_spread)
    prices['INFY'] = 0.5 * tcs_prices + np.array(infy_spread)

    # AXISBANK cointegrated with ICICIBANK: AXIS = 0.85 * ICICI + Spread
    # Spread is mean-reverting centered around 50, ends with Z-score > 2.0 (SHORT signal)
    icici_prices = prices['ICICIBANK']
    axis_spread = [50.0]
    for i in range(251):
        if i < 240:
            next_spread = 50.0 + 0.80 * (axis_spread[-1] - 50.0) + np.random.normal(0, 2.0)
        else:
            next_spread = axis_spread[-1] + 6.0 + np.random.normal(0, 1.0)
        axis_spread.append(next_spread)
    prices['AXISBANK'] = 0.85 * icici_prices + np.array(axis_spread)

    # HDFCBANK cointegrated with BAJAJFINSV: HDFC = 0.1 * BAJAJ + Spread
    # Spread reverts and ends near the mean (Z-score ~ 0, EXIT signal)
    bajaj_prices = prices['BAJAJFINSV']
    hdfc_spread = [30.0]
    for i in range(251):
        if i < 230:
            next_spread = 30.0 + 0.82 * (hdfc_spread[-1] - 30.0) + np.random.normal(0, 1.5)
        elif i < 245:
            next_spread = hdfc_spread[-1] + 4.0 + np.random.normal(0, 0.5)
        else:
            next_spread = 30.0 + 0.70 * (hdfc_spread[-1] - 30.0) + np.random.normal(0, 0.5)
        hdfc_spread.append(next_spread)
    prices['HDFCBANK'] = 0.1 * bajaj_prices + np.array(hdfc_spread)

    # WIPRO cointegrated with INFY: WIPRO = 0.3 * INFY + Spread (HOLD signal)
    infy_prices = prices['INFY']
    wipro_spread = [40.0]
    for i in range(251):
        next_spread = 40.0 + 0.88 * (wipro_spread[-1] - 40.0) + np.random.normal(0, 1.0)
        wipro_spread.append(next_spread)
    prices['WIPRO'] = 0.3 * infy_prices + np.array(wipro_spread)

    # LT cointegrated with RELIANCE: LT = 0.7 * RELIANCE + Spread (HOLD signal)
    reliance_prices = prices['RELIANCE']
    lt_spread = [150.0]
    for i in range(251):
        next_spread = 150.0 + 0.84 * (lt_spread[-1] - 150.0) + np.random.normal(0, 4.0)
        lt_spread.append(next_spread)
    prices['LT'] = 0.7 * reliance_prices + np.array(lt_spread)

    # Save all prices as Parquet and insert in DB
    for symbol in prices:
        data_records = []
        symbol_prices = prices[symbol]
        for i in range(252):
            date = base_date + timedelta(days=i)
            close_price = symbol_prices[i]
            
            open_price = close_price * (1 + np.random.normal(0, 0.005))
            high = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.005)))
            low = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.005)))
            volume = np.random.uniform(1e6, 8e6)
            
            data_records.append({
                'date': date,
                'open': open_price,
                'high': high,
                'low': low,
                'close': close_price,
                'volume': volume
            })
            
        df = pd.DataFrame(data_records)
        data_manager.save_to_parquet(df, symbol)
        print(f"  [OK] {symbol} price series saved ({len(df)} days)")

    # Seed Cointegration Results, Spread Stats, and Signals directly
    print("\nSeeding Cointegration results and Signals...")
    
    # 1. TCS / INFY (LONG signal)
    db_ops.add_cointegration(
        stock_a='TCS', stock_b='INFY',
        test_statistic=-3.85, p_value=0.0024,
        critical_values='{"1%": -3.46, "5%": -2.88, "10%": -2.57}',
        hedge_ratio=0.50
    )
    db_ops.add_spread_stats(
        stock_a='TCS', stock_b='INFY',
        mean_spread=100.0, std_spread=8.5,
        median_spread=100.2, min_spread=75.3,
        max_spread=122.4, half_life=4.2, period_days=252
    )
    db_ops.add_signal(
        stock_a='TCS', stock_b='INFY',
        signal_type='LONG',
        z_score_30d=-2.35, z_score_60d=-2.12, z_score_90d=-1.95,
        current_spread=80.0, signal_strength=0.88
    )
    db_ops.add_backtest_result(
        stock_a='TCS', stock_b='INFY',
        start_date=base_date, end_date=datetime.now(),
        entry_threshold=2.0, exit_threshold=0.5,
        total_return=24.5, annualized_return=24.5,
        sharpe_ratio=1.95, sortino_ratio=2.25, max_drawdown=-6.2,
        hit_rate=72.5, profit_factor=2.15, num_trades=14, avg_holding_days=5.2
    )

    # 2. ICICIBANK / AXISBANK (SHORT signal)
    db_ops.add_cointegration(
        stock_a='ICICIBANK', stock_b='AXISBANK',
        test_statistic=-3.42, p_value=0.0101,
        critical_values='{"1%": -3.46, "5%": -2.88, "10%": -2.57}',
        hedge_ratio=0.85
    )
    db_ops.add_spread_stats(
        stock_a='ICICIBANK', stock_b='AXISBANK',
        mean_spread=50.0, std_spread=5.2,
        median_spread=50.1, min_spread=36.4,
        max_spread=65.2, half_life=3.8, period_days=252
    )
    db_ops.add_signal(
        stock_a='ICICIBANK', stock_b='AXISBANK',
        signal_type='SHORT',
        z_score_30d=2.42, z_score_60d=1.85, z_score_90d=1.45,
        current_spread=62.6, signal_strength=0.82
    )
    db_ops.add_backtest_result(
        stock_a='ICICIBANK', stock_b='AXISBANK',
        start_date=base_date, end_date=datetime.now(),
        entry_threshold=2.0, exit_threshold=0.5,
        total_return=18.4, annualized_return=18.4,
        sharpe_ratio=1.65, sortino_ratio=1.85, max_drawdown=-7.8,
        hit_rate=66.7, profit_factor=1.82, num_trades=12, avg_holding_days=4.6
    )

    # 3. BAJAJFINSV / HDFCBANK (EXIT signal)
    db_ops.add_cointegration(
        stock_a='BAJAJFINSV', stock_b='HDFCBANK',
        test_statistic=-3.15, p_value=0.0232,
        critical_values='{"1%": -3.46, "5%": -2.88, "10%": -2.57}',
        hedge_ratio=0.10
    )
    db_ops.add_spread_stats(
        stock_a='BAJAJFINSV', stock_b='HDFCBANK',
        mean_spread=30.0, std_spread=3.5,
        median_spread=30.2, min_spread=20.5,
        max_spread=41.2, half_life=4.6, period_days=252
    )
    db_ops.add_signal(
        stock_a='BAJAJFINSV', stock_b='HDFCBANK',
        signal_type='EXIT',
        z_score_30d=0.08, z_score_60d=0.85, z_score_90d=1.12,
        current_spread=30.3, signal_strength=0.92
    )
    db_ops.add_backtest_result(
        stock_a='BAJAJFINSV', stock_b='HDFCBANK',
        start_date=base_date, end_date=datetime.now(),
        entry_threshold=2.0, exit_threshold=0.5,
        total_return=15.2, annualized_return=15.2,
        sharpe_ratio=1.42, sortino_ratio=1.55, max_drawdown=-5.4,
        hit_rate=68.4, profit_factor=1.65, num_trades=10, avg_holding_days=5.8
    )

    # 4. INFY / WIPRO (HOLD signal)
    db_ops.add_cointegration(
        stock_a='INFY', stock_b='WIPRO',
        test_statistic=-3.55, p_value=0.0068,
        critical_values='{"1%": -3.46, "5%": -2.88, "10%": -2.57}',
        hedge_ratio=0.30
    )
    db_ops.add_spread_stats(
        stock_a='INFY', stock_b='WIPRO',
        mean_spread=40.0, std_spread=3.8,
        median_spread=39.8, min_spread=28.4,
        max_spread=52.3, half_life=5.2, period_days=252
    )
    db_ops.add_signal(
        stock_a='INFY', stock_b='WIPRO',
        signal_type='HOLD',
        z_score_30d=0.45, z_score_60d=-0.25, z_score_90d=-0.65,
        current_spread=41.7, signal_strength=0.0
    )

    # 5. RELIANCE / LT (HOLD signal)
    db_ops.add_cointegration(
        stock_a='RELIANCE', stock_b='LT',
        test_statistic=-3.24, p_value=0.0178,
        critical_values='{"1%": -3.46, "5%": -2.88, "10%": -2.57}',
        hedge_ratio=0.70
    )
    db_ops.add_spread_stats(
        stock_a='RELIANCE', stock_b='LT',
        mean_spread=150.0, std_spread=12.4,
        median_spread=150.2, min_spread=112.5,
        max_spread=188.4, half_life=4.0, period_days=252
    )
    db_ops.add_signal(
        stock_a='RELIANCE', stock_b='LT',
        signal_type='HOLD',
        z_score_30d=-0.82, z_score_60d=-0.12, z_score_90d=0.32,
        current_spread=139.8, signal_strength=0.0
    )

    # === Seed Virtual Trading Sample Data ===
    print("\nSeeding Virtual Paper Trading tables...")
    from src.database.models import VirtualPortfolio, VirtualPosition, VirtualTradeHistory
    session = db_ops.db.get_session()
    
    # Extract dynamic prices from the generated series to keep P&L values real
    tcs_entry_price = float(prices['TCS'][-6])
    infy_entry_price = float(prices['INFY'][-6])
    shares_a_1 = 1000000.0 / tcs_entry_price
    shares_b_1 = -(shares_a_1 * 0.50)
    
    icici_entry_price = float(prices['ICICIBANK'][-4])
    axis_entry_price = float(prices['AXISBANK'][-4])
    shares_a_2 = -1000000.0 / icici_entry_price
    shares_b_2 = -(shares_a_2 * 0.85)
    
    bajaj_entry_price = float(prices['BAJAJFINSV'][-11])
    hdfc_entry_price = float(prices['HDFCBANK'][-11])
    bajaj_exit_price = float(prices['BAJAJFINSV'][-3])
    hdfc_exit_price = float(prices['HDFCBANK'][-3])
    shares_a_3 = 1000000.0 / bajaj_entry_price
    shares_b_3 = -(shares_a_3 * 0.10)
    
    trade_pnl = shares_a_3 * (bajaj_exit_price - bajaj_entry_price) + shares_b_3 * (hdfc_exit_price - hdfc_entry_price)
    trade_return = (trade_pnl / 1000000.0) * 100
    
    # Calculate portfolio cash adjusted for the entered positions
    net_outlay_1 = shares_a_1 * tcs_entry_price + shares_b_1 * infy_entry_price
    net_outlay_2 = shares_a_2 * icici_entry_price + shares_b_2 * axis_entry_price
    portfolio_cash = 10000000.0 - net_outlay_1 - net_outlay_2
    
    # 1. Virtual Portfolio (1 Crore pool, cash adjusted for entered positions)
    portfolio = VirtualPortfolio(
        initial_capital=10000000.0,
        cash=portfolio_cash,
        equity=10000000.0,
        last_updated=datetime.utcnow()
    )
    session.add(portfolio)
    
    # 2. Virtual Open Positions
    # TCS-INFY (LONG)
    pos_1 = VirtualPosition(
        stock_a='TCS', stock_b='INFY',
        position_type='LONG',
        hedge_ratio=0.50,
        shares_a=shares_a_1,
        shares_b=shares_b_1,
        entry_price_a=tcs_entry_price,
        entry_price_b=infy_entry_price,
        entry_date=datetime.now() - timedelta(days=5),
        entry_z_score=-2.35
    )
    # ICICIBANK-AXISBANK (SHORT)
    pos_2 = VirtualPosition(
        stock_a='ICICIBANK', stock_b='AXISBANK',
        position_type='SHORT',
        hedge_ratio=0.85,
        shares_a=shares_a_2,
        shares_b=shares_b_2,
        entry_price_a=icici_entry_price,
        entry_price_b=axis_entry_price,
        entry_date=datetime.now() - timedelta(days=3),
        entry_z_score=2.42
    )
    session.add_all([pos_1, pos_2])
    
    # 3. Virtual Completed Trade History
    history_1 = VirtualTradeHistory(
        stock_a='BAJAJFINSV', stock_b='HDFCBANK',
        position_type='LONG',
        entry_date=datetime.now() - timedelta(days=10),
        exit_date=datetime.now() - timedelta(days=2),
        entry_price_a=bajaj_entry_price,
        entry_price_b=hdfc_entry_price,
        exit_price_a=bajaj_exit_price,
        exit_price_b=hdfc_exit_price,
        shares_a=shares_a_3,
        shares_b=shares_b_3,
        pnl=trade_pnl,
        return_pct=trade_return
    )
    session.add(history_1)
    session.commit()
    session.close()
    print("  [OK] Virtual portfolio initialized with Rs. 1 Crore.")
    print("  [OK] Sample positions seeded (TCS-INFY, ICICIBANK-AXISBANK).")
    print("  [OK] Completed trade seeded (BAJAJFINSV-HDFCBANK).")

    print("\n" + "=" * 60)
    print("DATABASE INITIALIZATION COMPLETE!")
    print("=" * 60)
    print(f"\n  Stocks added: {len(stocks)}")
    print(f"  Database: data/statarb.db")
    print(f"  Data files: data/*.parquet")
    print(f"  Pre-seeded cointegrated pairs: 5")
    print(f"  Active signals: 3 (1 LONG, 1 SHORT, 1 EXIT)")
    print(f"\n  Next step: streamlit run streamlit_app/app.py")
    print("=" * 60 + "\n")


if __name__ == '__main__':
    init_sample_data()
