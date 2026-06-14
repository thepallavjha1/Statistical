"""
Home page of the Streamlit application.
"""

import streamlit as st
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.pipeline import get_pipeline
from src.database import get_db_ops
from config import STOCK_UNIVERSE, UNIVERSE_FILE
import pandas as pd


def show():
    """Display home page."""
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("""
        # Welcome to the Statistical Arbitrage Platform
        
        **Identify pair trading opportunities, mean reversion opportunities, and statistical 
        arbitrage signals across Indian equities.**
        
        This platform analyzes correlations, cointegration, and spread dynamics to identify 
        profitable trading opportunities in the Indian stock market.
        """)
    
    with col2:
        st.metric("Status", "🟢 Active", "Last update 2 hours ago")
    
    st.markdown("---")
    
    # Key Metrics
    st.subheader("📊 Platform Overview")
    
    db_ops = get_db_ops()
    
    # Calculate metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        try:
            universe_size = len(pd.read_csv(UNIVERSE_FILE))
        except Exception:
            universe_size = len(db_ops.get_all_stocks())
        st.metric("Stocks Monitored", universe_size, STOCK_UNIVERSE)
    
    with col2:
        cointegrated = db_ops.get_cointegrated_pairs()
        st.metric("Cointegrated Pairs", len(cointegrated), "p < 0.05")
    
    with col3:
        latest_signals = db_ops.get_latest_signals(hours=24)
        active_signals = [s for s in latest_signals if s.signal_type != 'HOLD']
        st.metric("Active Signals (24h)", len(active_signals), "BUY/SELL/EXIT")
    
    with col4:
        st.metric("Last Update", datetime.utcnow().strftime("%H:%M UTC"), "Today")
    
    st.markdown("---")
    
    # Top Opportunities
    st.subheader("🎯 Top Opportunities (Last 24 Hours)")
    
    latest_signals = db_ops.get_latest_signals(hours=24)
    active_signals = [s for s in latest_signals if s.signal_type != 'HOLD']
    
    if active_signals:
        # Create dataframe for display
        signals_data = []
        for signal in active_signals[:10]:
            signals_data.append({
                'Stock A': signal.stock_a,
                'Stock B': signal.stock_b,
                'Pair': f"{signal.stock_a} - {signal.stock_b}",
                'Signal': signal.signal_type,
                'Z-Score': f"{signal.z_score_30:.2f}" if signal.z_score_30 else "N/A",
                'Spread': f"{signal.current_spread:.2f}" if signal.current_spread else "N/A",
                'Strength': f"{signal.signal_strength:.2%}" if signal.signal_strength else "N/A"
            })
        
        df = pd.DataFrame(signals_data)
        st.info("💡 Click on any row in the table below to explore that pair in detail in the Pair Explorer.")
        
        event = st.dataframe(
            df[['Pair', 'Signal', 'Z-Score', 'Spread', 'Strength']],
            use_container_width=True,
            on_select="rerun",
            selection_mode="single_row",
            key="home_signals_df"
        )
        
        if event and event.selection and event.selection.get("rows"):
            selected_row_idx = event.selection["rows"][0]
            selected_row = df.iloc[selected_row_idx]
            st.session_state.selected_pair = (selected_row['Stock A'], selected_row['Stock B'])
            st.session_state.nav_radio = "Pair Explorer"
            st.rerun()
    else:
        st.info("No active signals in the last 24 hours. Run the pipeline to generate signals.")
    
    st.markdown("---")
    
    # Quick Actions
    st.subheader("⚡ Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Run Pipeline Now", use_container_width=True):
            with st.spinner("Running pipeline — this may take 30-60 minutes for NIFTY 500..."):
                pipeline = get_pipeline()
                result = pipeline.run_full_pipeline(UNIVERSE_FILE)
                if result.get('status') == 'SUCCESS':
                    st.success(
                        f"Pipeline completed: {result['active_signals']} signals generated"
                    )
                    st.rerun()
                else:
                    st.error(f"Pipeline failed: {result.get('error', 'Unknown error')}")
    
    with col2:
        if st.button("📊 View Signal Dashboard", use_container_width=True):
            st.session_state.page = "Signal Dashboard"
            st.rerun()
    
    with col3:
        if st.button("🔎 Explore Pairs", use_container_width=True):
            st.session_state.page = "Pair Explorer"
            st.rerun()
    
    st.markdown("---")
    
    # How It Works
    st.subheader("📚 How It Works")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### Data Processing
        1. **Data Download**: Downloads historical OHLCV data for Indian stocks
        2. **Liquidity Filter**: Filters stocks by minimum average daily volume
        3. **Correlation**: Calculates Pearson correlation across multiple time periods
        4. **Cointegration**: Tests for statistical relationships using ADF test
        
        ### Signal Generation
        5. **Hedge Ratio**: Calculates optimal hedge ratio using OLS regression
        6. **Spread Construction**: Computes spread = Stock A - Beta × Stock B
        7. **Z-Score**: Calculates rolling Z-scores with multiple windows
        8. **Signal Rules**: Generates BUY/SELL/EXIT signals based on Z-score thresholds
        """)
    
    with col2:
        st.markdown("""
        ### Analysis & Ranking
        9. **Backtest**: Simulates trading strategy to calculate performance metrics
        10. **Ranking**: Scores opportunities based on multiple criteria:
            - Signal strength (40%)
            - Z-score extremeness (30%)
            - Backtest Sharpe ratio (20%)
            - Cointegration strength (10%)
        
        ### Features
        - **Multiple Timeframes**: 30-day, 60-day, 90-day Z-scores
        - **Half-life Estimation**: Predicts mean reversion timeframes
        - **Risk Controls**: Liquidity filters, volatility checks, data quality validation
        - **Database Storage**: Tracks all signals and historical data
        """)
    
    st.markdown("---")
    
    # Configuration Info
    st.subheader("⚙️ Current Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Signal Thresholds:**
        - Long Entry: Z < -2.0
        - Short Entry: Z > +2.0
        - Exit: |Z| < 0.5
        
        **Filters:**
        - Min Liquidity: 1M shares/day
        - Correlation: > 0.7
        - Cointegration p-value: < 0.05
        """)
    
    with col2:
        st.markdown("""
        **Data Settings:**
        - Data Source: yfinance (NSE)
        - Historical Period: 3 years
        - Update Frequency: Daily at 6 PM IST
        - Database: SQLite
        
        **Backtesting:**
        - Initial Capital: $100,000
        - Entry/Exit: Z-score based
        - Slippage: None (research mode)
        """)
    
    st.markdown("---")
    
    st.info("""
    **📖 Documentation & Support**
    
    - View the [GitHub Repository](https://github.com/yourusername/statarb-platform) for code and documentation
    - For questions and issues, open a GitHub issue
    - This platform is for research and analysis purposes only
    - Not investment advice - always conduct your own due diligence
    """)
