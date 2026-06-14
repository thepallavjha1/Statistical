"""
Analytics page.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.database import get_db_ops
from src.data_ingestion import get_data_manager


def show():
    """Display analytics page."""
    
    st.markdown("Analyze market statistics and opportunity distributions")
    
    db_ops = get_db_ops()
    data_mgr = get_data_manager()
    
    # Load data
    cointegrated_pairs = db_ops.get_cointegrated_pairs()
    latest_signals = db_ops.get_latest_signals(hours=24)
    
    st.subheader("📊 Analytics Dashboard")
    
    # Summary stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Cointegrated", len(cointegrated_pairs))
    
    with col2:
        avg_p_value = np.mean([p.p_value for p in cointegrated_pairs]) if cointegrated_pairs else 0
        st.metric("Avg P-Value", f"{avg_p_value:.4f}")
    
    with col3:
        recent_signals = len(latest_signals)
        st.metric("Recent Signals (24h)", recent_signals)
    
    with col4:
        active_signals = len([s for s in latest_signals if s.signal_type != 'HOLD'])
        st.metric("Active Signals", active_signals)
    
    st.markdown("---")
    
    # P-Value distribution
    st.subheader("P-Value Distribution")
    
    if cointegrated_pairs:
        p_values = [p.p_value for p in cointegrated_pairs]
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=p_values,
                nbinsx=30,
                name='P-Value Distribution',
                marker_color='#1f77b4'
            ))
            fig.add_vline(x=0.05, line_dash="dash", line_color="red",
                         annotation_text="Threshold (0.05)")
            fig.update_layout(
                title="Cointegration P-Value Distribution",
                xaxis_title="P-Value",
                yaxis_title="Count",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = go.Figure()
            fig.add_trace(go.Box(
                y=p_values,
                name='P-Values',
                marker_color='#ff7f0e'
            ))
            fig.update_layout(
                title="P-Value Box Plot",
                yaxis_title="P-Value",
                height=400,
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Hedge ratio distribution
    st.subheader("Hedge Ratio Distribution")
    
    if cointegrated_pairs:
        hedge_ratios = [p.hedge_ratio for p in cointegrated_pairs if p.hedge_ratio is not None]
        
        if hedge_ratios:
            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=hedge_ratios,
                nbinsx=20,
                name='Hedge Ratio Distribution',
                marker_color='#2ca02c'
            ))
            fig.update_layout(
                title="Hedge Ratio Distribution",
                xaxis_title="Hedge Ratio (β)",
                yaxis_title="Count",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Z-score distribution
    st.subheader("Z-Score Distribution (Latest Signals)")
    
    if latest_signals:
        z_scores = [s.z_score_30 for s in latest_signals if s.z_score_30 is not None]
        
        if z_scores:
            fig = go.Figure()
            fig.add_trace(go.Histogram(
                x=z_scores,
                nbinsx=30,
                name='Z-Score Distribution',
                marker_color='#9467bd'
            ))
            fig.add_vline(x=2.0, line_dash="dash", line_color="red",
                         annotation_text="Short Entry (2.0)")
            fig.add_vline(x=-2.0, line_dash="dash", line_color="green",
                         annotation_text="Long Entry (-2.0)")
            fig.update_layout(
                title="Z-Score Distribution",
                xaxis_title="Z-Score",
                yaxis_title="Count",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Pair details
    st.subheader("Cointegrated Pairs Details")
    
    if cointegrated_pairs:
        pairs_data = []
        for pair in cointegrated_pairs[:50]:
            pairs_data.append({
                'Pair': f"{pair.stock_a}/{pair.stock_b}",
                'P-Value': f"{pair.p_value:.4f}",
                'T-Stat': f"{pair.test_statistic:.2f}",
                'Hedge Ratio': f"{pair.hedge_ratio:.4f}" if pair.hedge_ratio else "N/A",
                'Date': pair.test_date.strftime("%Y-%m-%d %H:%M")
            })
        
        pairs_df = pd.DataFrame(pairs_data)
        st.dataframe(pairs_df, use_container_width=True)
        
        # Download button
        csv = pairs_df.to_csv(index=False)
        st.download_button(
            label="Download as CSV",
            data=csv,
            file_name="cointegrated_pairs.csv",
            mime="text/csv"
        )
