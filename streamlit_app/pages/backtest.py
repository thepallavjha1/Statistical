"""
Backtest page.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.backtesting import get_backtest_engine
from src.database import get_db_ops


def show():
    """Display backtest page."""
    
    st.markdown("Run custom backtests on pair trading strategies")
    
    # Input controls
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        symbol_a = st.text_input("Stock A", "RELIANCE").upper()
    
    with col2:
        symbol_b = st.text_input("Stock B", "TCS").upper()
    
    with col3:
        start_date = st.date_input("Start Date", datetime.now() - timedelta(days=365))
    
    with col4:
        end_date = st.date_input("End Date", datetime.now())
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        entry_threshold = st.slider("Entry Threshold (Z-score)", 1.0, 3.0, 2.0, 0.1)
    
    with col2:
        exit_threshold = st.slider("Exit Threshold (Z-score)", 0.1, 1.0, 0.5, 0.1)
    
    with col3:
        initial_capital = st.number_input("Initial Capital ($)", 10000, 1000000, 100000, 10000)
    
    if st.button("Run Backtest", type="primary"):
        st.markdown("---")
        
        backtest_engine = get_backtest_engine()
        
        with st.spinner("Running backtest..."):
            result = backtest_engine.backtest_pair(
                symbol_a, symbol_b,
                start_date=datetime.combine(start_date, datetime.min.time()),
                end_date=datetime.combine(end_date, datetime.min.time()),
                entry_threshold=entry_threshold,
                exit_threshold=exit_threshold,
                initial_capital=initial_capital
            )
        
        if result['num_trades'] == 0:
            st.warning("No trades generated in this period.")
            return
        
        st.subheader(f"📈 Backtest Results - {symbol_a}/{symbol_b}")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Return", f"{result['total_return']:.2f}%")
        
        with col2:
            st.metric("Annualized Return", f"{result['annualized_return']:.2f}%")
        
        with col3:
            st.metric("Sharpe Ratio", f"{result['sharpe_ratio']:.2f}")
        
        with col4:
            st.metric("Max Drawdown", f"{result['max_drawdown']:.2f}%")
        
        st.markdown("---")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Number of Trades", int(result['num_trades']))
        
        with col2:
            st.metric("Hit Rate", f"{result['hit_rate']:.1f}%")
        
        with col3:
            st.metric("Profit Factor", f"{result['profit_factor']:.2f}")
        
        with col4:
            st.metric("Avg Holding Days", f"{result['avg_holding_days']:.1f}")
        
        st.markdown("---")
        
        # Trade log
        if result['trades']:
            st.subheader("Trade Log")
            
            trades_df = pd.DataFrame(result['trades'])
            
            # Format for display
            display_trades = trades_df[[
                'entry_date', 'exit_date', 'position_type', 'pnl', 'return_pct', 'holding_days'
            ]].copy()
            
            display_trades.columns = ['Entry', 'Exit', 'Type', 'P&L ($)', 'Return (%)', 'Days']
            display_trades['P&L ($)'] = display_trades['P&L ($)'].apply(lambda x: f"{x:.2f}")
            display_trades['Return (%)'] = display_trades['Return (%)'].apply(lambda x: f"{x:.2f}%")
            display_trades['Days'] = display_trades['Days'].astype(int)
            
            st.dataframe(display_trades, use_container_width=True)
            
            st.markdown("---")
            
            # Cumulative PnL
            st.subheader("Cumulative P&L")
            
            cumulative_pnl = [0]
            for trade in result['trades']:
                cumulative_pnl.append(cumulative_pnl[-1] + trade['pnl'])
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                y=cumulative_pnl,
                name='Cumulative P&L',
                line_color='#1f77b4',
                fill='tozeroy'
            ))
            fig.update_layout(
                title="Cumulative P&L Over Time",
                xaxis_title="Trade #",
                yaxis_title="Cumulative P&L ($)",
                height=400,
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    show()
