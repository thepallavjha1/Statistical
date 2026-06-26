"""Streamlit page displaying the virtual paper trading portfolio."""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.database.models import (
    VirtualPortfolio, VirtualPosition, VirtualTradeHistory, DatabaseManager
)
from src.pipeline import get_pipeline
from src.data_ingestion.manager import get_data_manager

def show():
    st.markdown("### 💼 Virtual Trading Portfolio (1 Crore INR Pool)")
    
    db = DatabaseManager()
    session = db.get_session()
    
    pipeline = get_pipeline()
    data_manager = get_data_manager()
    
    # Run manual pipeline trigger
    col_trigger_1, col_trigger_2 = st.columns([3, 1])
    with col_trigger_1:
        st.caption("Last Updated: Active real-time paper portfolio tracking daily opportunities.")
    with col_trigger_2:
        if st.button("🔄 Refresh Data & Trade", use_container_width=True):
            with st.spinner("Refreshing stock data and executing virtual trades..."):
                try:
                    from config import UNIVERSE_FILE
                    pipeline.run_full_pipeline(UNIVERSE_FILE)
                    st.success("Pipeline executed successfully!")
                except Exception as e:
                    st.error(f"Execution failed: {str(e)}")
                    
    try:
        # Load portfolio details
        portfolio = session.query(VirtualPortfolio).first()
        if not portfolio:
            # Initialize portfolio if not exists
            portfolio = VirtualPortfolio(
                initial_capital=10000000.0,
                cash=10000000.0,
                equity=10000000.0,
                last_updated=datetime.utcnow()
            )
            session.add(portfolio)
            session.commit()
            session.refresh(portfolio)
            
        # Get all positions
        positions = session.query(VirtualPosition).all()
        
        # Deduplicate positions list for display and calculation (safety against database races)
        seen_pos_keys = set()
        unique_positions = []
        for pos in positions:
            key = tuple(sorted([pos.stock_a, pos.stock_b]))
            if key not in seen_pos_keys:
                seen_pos_keys.add(key)
                unique_positions.append(pos)
        positions = unique_positions
        
        # Calculate current position values and unrealized PnL
        position_list = []
        unrealized_pnl = 0.0
        
        for pos in positions:
            prices_a = data_manager.get_price_series(pos.stock_a)
            prices_b = data_manager.get_price_series(pos.stock_b)
            
            curr_price_a = prices_a.iloc[-1] if prices_a is not None and not prices_a.empty else pos.entry_price_a
            curr_price_b = prices_b.iloc[-1] if prices_b is not None and not prices_b.empty else pos.entry_price_b
            
            # Position current value
            curr_val_a = pos.shares_a * curr_price_a
            curr_val_b = pos.shares_b * curr_price_b
            curr_pos_val = curr_val_a + curr_val_b
            
            # Entry value
            entry_val_a = pos.shares_a * pos.entry_price_a
            entry_val_b = pos.shares_b * pos.entry_price_b
            entry_pos_val = entry_val_a + entry_val_b
            
            # Position P&L
            pos_pnl = curr_pos_val - entry_pos_val
            allocation = abs(entry_val_a)
            pos_pnl_pct = (pos_pnl / allocation) * 100 if allocation > 0 else 0.0
            
            unrealized_pnl += pos_pnl
            
            position_list.append({
                "Pair": f"{pos.stock_a} / {pos.stock_b}",
                "Type": pos.position_type,
                "Entry Date": pos.entry_date.strftime("%Y-%m-%d %H:%M"),
                "Hedge Ratio": f"{pos.hedge_ratio:.3f}",
                "Entry Price A": f"₹{pos.entry_price_a:,.2f}",
                "Current Price A": f"₹{curr_price_a:,.2f}",
                "Entry Price B": f"₹{pos.entry_price_b:,.2f}",
                "Current Price B": f"₹{curr_price_b:,.2f}",
                "Qty A": f"{pos.shares_a:,.1f}",
                "Qty B": f"{pos.shares_b:,.1f}",
                "Position PnL": pos_pnl,
                "Return %": pos_pnl_pct
            })
            
        # Recalculate equity
        total_pos_val = 0.0
        for pos in positions:
            prices_a = data_manager.get_price_series(pos.stock_a)
            prices_b = data_manager.get_price_series(pos.stock_b)
            curr_p_a = prices_a.iloc[-1] if prices_a is not None and not prices_a.empty else pos.entry_price_a
            curr_p_b = prices_b.iloc[-1] if prices_b is not None and not prices_b.empty else pos.entry_price_b
            total_pos_val += pos.shares_a * curr_p_a + pos.shares_b * curr_p_b
            
        portfolio.equity = portfolio.cash + total_pos_val
        session.commit()
        
        # UI Metrics
        total_pnl = portfolio.equity - portfolio.initial_capital
        total_pnl_pct = (total_pnl / portfolio.initial_capital) * 100
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Portfolio Equity",
                value=f"₹{portfolio.equity:,.2f}",
                delta=f"₹{total_pnl:,.2f} ({total_pnl_pct:+.2f}%)"
            )
            
        with col2:
            st.metric(
                label="Cash Balance",
                value=f"₹{portfolio.cash:,.2f}"
            )
            
        with col3:
            st.metric(
                label="Unrealized P&L",
                value=f"₹{unrealized_pnl:,.2f}",
                delta=f"{ (unrealized_pnl / portfolio.initial_capital) * 100:+.2f}% total"
            )
            
        with col4:
            st.metric(
                label="Initial Capital",
                value=f"₹{portfolio.initial_capital:,.2f}"
            )
            
        st.markdown("---")
        
        # Display Open Positions
        st.subheader("📌 Open Positions")
        if position_list:
            df_pos = pd.DataFrame(position_list)
            
            # Format PnL columns with colors
            def color_pnl(val):
                if isinstance(val, str):
                    return ''
                color = 'green' if val >= 0 else 'red'
                return f'color: {color}; font-weight: bold;'
                
            styled_df = df_pos.style.map(color_pnl, subset=['Position PnL', 'Return %'])\
                .format({"Position PnL": "₹{:,.2f}", "Return %": "{:+.2f}%"})
                
            st.write(styled_df)
        else:
            st.info("No active open positions. The system will enter positions when trade signals (LONG/SHORT) are detected on cointegrated pairs.")
            
        st.markdown("---")
        
        # Display Closed Trades History
        st.subheader("📜 Completed Trades History")
        history = session.query(VirtualTradeHistory).order_by(VirtualTradeHistory.exit_date.desc()).all()
        
        if history:
            # Deduplicate completed trades history list
            seen_hist_keys = set()
            unique_history = []
            for h in history:
                key = (h.stock_a, h.stock_b, h.position_type, h.entry_date, h.exit_date)
                if key not in seen_hist_keys:
                    seen_hist_keys.add(key)
                    unique_history.append(h)
            history = unique_history
            
            history_list = []
            for h in history:
                history_list.append({
                    "Pair": f"{h.stock_a} / {h.stock_b}",
                    "Type": h.position_type,
                    "Entry Date": h.entry_date.strftime("%Y-%m-%d %H:%M"),
                    "Exit Date": h.exit_date.strftime("%Y-%m-%d %H:%M"),
                    "Entry Prices": f"A: ₹{h.entry_price_a:,.2f} | B: ₹{h.entry_price_b:,.2f}",
                    "Exit Prices": f"A: ₹{h.exit_price_a:,.2f} | B: ₹{h.exit_price_b:,.2f}",
                    "Qty A/B": f"A: {h.shares_a:,.1f} | B: {h.shares_b:,.1f}",
                    "Realized PnL": h.pnl,
                    "Return %": h.return_pct
                })
                
            df_hist = pd.DataFrame(history_list)
            
            def color_pnl_hist(val):
                if isinstance(val, str):
                    return ''
                color = 'green' if val >= 0 else 'red'
                return f'color: {color}; font-weight: bold;'
                
            styled_hist = df_hist.style.map(color_pnl_hist, subset=['Realized PnL', 'Return %'])\
                .format({"Realized PnL": "₹{:,.2f}", "Return %": "{:+.2f}%"})
                
            st.write(styled_hist)
        else:
            st.info("No completed trades recorded yet.")
            
    except Exception as e:
        st.error(f"Error loading virtual portfolio data: {str(e)}")
    finally:
        session.close()
