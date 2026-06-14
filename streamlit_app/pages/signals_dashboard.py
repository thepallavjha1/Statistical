"""
Signal Dashboard page.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.database import get_db_ops
from src.utils import OpportunityRanker


def show():
    """Display signal dashboard."""
    
    st.markdown("View all current trading signals and opportunities")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        time_filter = st.selectbox("Time Period", ["Last 24h", "Last 7d", "Last 30d"])
        hours = {"Last 24h": 24, "Last 7d": 168, "Last 30d": 720}[time_filter]
    
    with col2:
        signal_filter = st.selectbox("Signal Type", ["All", "LONG", "SHORT", "EXIT"])
    
    with col3:
        min_strength = st.slider("Min Strength", 0.0, 1.0, 0.0)
    
    st.markdown("---")
    
    # Load data
    db_ops = get_db_ops()
    signals = db_ops.get_latest_signals(hours=hours)
    
    # Filter and convert
    signals_data = []
    for signal in signals:
        if signal_filter != "All" and signal.signal_type != signal_filter:
            continue
        if signal.signal_strength and signal.signal_strength < min_strength:
            continue
        
        signals_data.append({
            'Pair': f"{signal.stock_a}/{signal.stock_b}",
            'Stock A': signal.stock_a,
            'Stock B': signal.stock_b,
            'Signal': signal.signal_type,
            'Z-Score 30d': signal.z_score_30,
            'Z-Score 60d': signal.z_score_60,
            'Z-Score 90d': signal.z_score_90,
            'Spread': signal.current_spread,
            'Strength': signal.signal_strength,
            'Date': signal.created_date
        })
    
    if signals_data:
        df = pd.DataFrame(signals_data)
        
        # Display metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Signals", len(df))
        with col2:
            long_count = len(df[df['Signal'] == 'LONG'])
            st.metric("LONG Signals", long_count)
        with col3:
            short_count = len(df[df['Signal'] == 'SHORT'])
            st.metric("SHORT Signals", short_count)
        
        st.markdown("---")
        
        # Signal table
        st.subheader("📋 Active Signals")
        
        # Format for display
        display_df = df[['Pair', 'Signal', 'Z-Score 30d', 'Spread', 'Strength']].copy()
        display_df['Z-Score 30d'] = display_df['Z-Score 30d'].apply(lambda x: f"{x:.2f}" if x else "N/A")
        display_df['Spread'] = display_df['Spread'].apply(lambda x: f"{x:.2f}" if x else "N/A")
        display_df['Strength'] = display_df['Strength'].apply(lambda x: f"{x:.2%}" if x else "N/A")
        
        st.dataframe(display_df, use_container_width=True)
        
        st.markdown("---")
        
        # Distribution charts
        st.subheader("📊 Signal Distribution")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Z-score distribution
            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=df['Z-Score 30d'].dropna(),
                nbinsx=30,
                name='Z-Score Distribution',
                marker_color='#1f77b4'
            ))
            fig.update_layout(
                title="Z-Score Distribution",
                xaxis_title="Z-Score",
                yaxis_title="Frequency",
                hovermode='x unified',
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Signal type distribution
            signal_counts = df['Signal'].value_counts()
            colors = {'LONG': '#00ff00', 'SHORT': '#ff0000', 'EXIT': '#ffff00'}
            
            fig = go.Figure(data=[
                go.Bar(
                    y=signal_counts.index,
                    x=signal_counts.values,
                    orientation='h',
                    marker_color=[colors.get(s, '#1f77b4') for s in signal_counts.index]
                )
            ])
            fig.update_layout(
                title="Signal Type Distribution",
                xaxis_title="Count",
                height=400,
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.warning("No signals found for the selected filters.")
        st.info("Run the pipeline to generate signals.")
