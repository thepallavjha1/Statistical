"""
Pair Explorer page.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.database import get_db_ops
from src.data_ingestion import get_data_manager
from src.cointegration import get_cointegration_analyzer


def show():
    """Display pair explorer."""
    
    st.markdown("Search and analyze specific pairs")
    
    # Initialize defaults
    if "pair_a" not in st.session_state:
        st.session_state.pair_a = "RELIANCE"
    if "pair_b" not in st.session_state:
        st.session_state.pair_b = "TCS"
        
    analyze_clicked = False
    
    # Handle redirect from Home or Signal Dashboard
    if 'selected_pair' in st.session_state and st.session_state.selected_pair:
        stock_a, stock_b = st.session_state.selected_pair
        st.session_state.pair_a = stock_a
        st.session_state.pair_b = stock_b
        st.session_state.selected_pair = None  # Consume the redirect selection
        analyze_clicked = True

    db_ops = get_db_ops()
    coint_pairs = db_ops.get_cointegrated_pairs(threshold=0.05)
    
    if coint_pairs:
        # Quick Select Dropdown
        pair_options = ["-- Select a Cointegrated Pair --"] + [
            f"{p.stock_a} / {p.stock_b} (p-val: {p.p_value:.4f})" for p in coint_pairs
        ]
        
        selected_option = st.selectbox(
            "🎯 Quick Select Cointegrated Pair",
            pair_options,
            key="quick_select_pair"
        )
        
        if selected_option != "-- Select a Cointegrated Pair --":
            # Extract symbols
            pair_part = selected_option.split(" (")[0]
            stock_a, stock_b = [s.strip() for s in pair_part.split("/")]
            
            # If selection has changed, update inputs and trigger analyze
            if st.session_state.pair_a != stock_a or st.session_state.pair_b != stock_b:
                st.session_state.pair_a = stock_a
                st.session_state.pair_b = stock_b
                analyze_clicked = True
    
    col1, col2 = st.columns(2)
    
    with col1:
        symbol_a = st.text_input("Stock A", key="pair_a").upper()
    
    with col2:
        symbol_b = st.text_input("Stock B", key="pair_b").upper()
    
    if st.button("Analyze Pair") or analyze_clicked:
        st.markdown("---")
        
        data_mgr = get_data_manager()
        coint_analyzer = get_cointegration_analyzer()
        db_ops = get_db_ops()
        
        # Get price data
        prices_a = data_mgr.get_price_series(symbol_a)
        prices_b = data_mgr.get_price_series(symbol_b)
        
        if prices_a is None or prices_b is None:
            st.error(f"Could not load data for {symbol_a} or {symbol_b}")
            return
        
        # Align dates
        common_dates = prices_a.index.intersection(prices_b.index)
        prices_a = prices_a[common_dates]
        prices_b = prices_b[common_dates]
        
        # Run analysis
        st.subheader(f"📊 {symbol_a}/{symbol_b} Analysis")
        
        # Test cointegration
        coint_result = coint_analyzer.test_cointegration(symbol_a, symbol_b)
        spread_stats = coint_analyzer.analyze_spread(
            symbol_a, symbol_b, coint_result.get('hedge_ratio')
        )
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            p_value = coint_result['p_value']
            color = "🟢" if p_value < 0.05 else "🔴"
            st.metric(f"{color} Cointegrated", f"{p_value:.4f}", 
                     "p < 0.05" if p_value < 0.05 else "p > 0.05")
        
        with col2:
            hedge_ratio = coint_result.get('hedge_ratio', np.nan)
            st.metric("Hedge Ratio (β)", f"{hedge_ratio:.4f}")
        
        with col3:
            half_life = spread_stats.get('half_life', np.nan)
            st.metric("Half-Life", f"{half_life:.1f} days")
        
        with col4:
            z_score = (prices_a.iloc[-1] - spread_stats.get('mean_spread', 0)) / spread_stats.get('std_spread', 1)
            st.metric("Current Z-Score", f"{z_score:.2f}")
        
        st.markdown("---")
        
        # Price charts
        st.subheader("Price Charts")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Price chart A
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=prices_a.index,
                y=prices_a.values,
                name=symbol_a,
                line_color='#1f77b4'
            ))
            fig.update_layout(
                title=f"{symbol_a} Price",
                xaxis_title="Date",
                yaxis_title="Price",
                height=400,
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Price chart B
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=prices_b.index,
                y=prices_b.values,
                name=symbol_b,
                line_color='#ff7f0e'
            ))
            fig.update_layout(
                title=f"{symbol_b} Price",
                xaxis_title="Date",
                yaxis_title="Price",
                height=400,
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Normalized prices
        st.subheader("Normalized Price Chart")
        
        norm_a = (prices_a - prices_a.min()) / (prices_a.max() - prices_a.min())
        norm_b = (prices_b - prices_b.min()) / (prices_b.max() - prices_b.min())
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=norm_a.index,
            y=norm_a.values,
            name=symbol_a,
            line_color='#1f77b4'
        ))
        fig.add_trace(go.Scatter(
            x=norm_b.index,
            y=norm_b.values,
            name=symbol_b,
            line_color='#ff7f0e'
        ))
        fig.update_layout(
            title="Normalized Prices (0-1 scale)",
            xaxis_title="Date",
            yaxis_title="Normalized Price",
            height=400,
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Spread chart
        st.subheader("Spread Chart")
        
        if not spread_stats.empty:
            spread = prices_a.values - hedge_ratio * prices_b.values
            mean_spread = spread_stats['mean_spread']
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=common_dates,
                y=spread,
                name='Spread',
                line_color='#1f77b4',
                fill='tozeroy'
            ))
            fig.add_hline(y=mean_spread, line_dash="dash", line_color="red", 
                         annotation_text="Mean")
            fig.add_hline(y=mean_spread + 2*spread_stats['std_spread'], 
                         line_dash="dash", line_color="orange")
            fig.add_hline(y=mean_spread - 2*spread_stats['std_spread'], 
                         line_dash="dash", line_color="orange")
            fig.update_layout(
                title="Spread (Stock A - β × Stock B)",
                xaxis_title="Date",
                yaxis_title="Spread Value",
                height=400,
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Statistics table
        st.subheader("📊 Statistics")
        
        stats_data = {
            'Metric': [
                'Mean Spread',
                'Std Dev Spread',
                'Median Spread',
                'Min Spread',
                'Max Spread',
                'Observations'
            ],
            'Value': [
                f"{spread_stats.get('mean_spread', np.nan):.4f}",
                f"{spread_stats.get('std_spread', np.nan):.4f}",
                f"{spread_stats.get('median_spread', np.nan):.4f}",
                f"{spread_stats.get('min_spread', np.nan):.4f}",
                f"{spread_stats.get('max_spread', np.nan):.4f}",
                f"{len(common_dates)}"
            ]
        }
        
        st.dataframe(pd.DataFrame(stats_data), use_container_width=True)
