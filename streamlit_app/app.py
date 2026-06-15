"""
Streamlit App Configuration and Main Entry Point
"""

import streamlit as st
import sys
import os

# Add project root and streamlit_app to path
STREAMLIT_APP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(STREAMLIT_APP_DIR)
for path in (PROJECT_ROOT, STREAMLIT_APP_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)


def _ensure_data_ready():
    """Initialize sample data on first run (local dev + Streamlit Cloud)."""
    from src.database import get_db_ops
    from initialize_db import init_sample_data

    db_ops = get_db_ops()
    if not db_ops.get_all_stocks():
        init_sample_data()


_ensure_data_ready()

# Configure page
st.set_page_config(
    page_title="Statistical Arbitrage Platform - Indian Equities",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark mode support
st.markdown("""
<style>
    :root {
        --primary-color: #1f77b4;
        --background-color: #0e1117;
        --secondary-background-color: #161b22;
        --text-color: #c9d1d9;
    }
    
    .metric-card {
        background-color: var(--secondary-background-color);
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 4px solid var(--primary-color);
    }
    
    .signal-buy {
        color: #00ff00;
        font-weight: bold;
    }
    
    .signal-sell {
        color: #ff0000;
        font-weight: bold;
    }
    
    .signal-exit {
        color: #ffff00;
        font-weight: bold;
    }
    
    .stMetric {
        background-color: var(--secondary-background-color);
        padding: 10px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Session state initialization
if 'selected_pair' not in st.session_state:
    st.session_state.selected_pair = None

if 'page' not in st.session_state:
    st.session_state.page = 'Home'

# Handle redirection requests
if 'redirect_to' in st.session_state:
    st.session_state.nav_radio = st.session_state.redirect_to
    del st.session_state.redirect_to

# Sidebar navigation
st.sidebar.title("📊 Statistical Arbitrage Platform")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    ["Home", "Signal Dashboard", "Pair Explorer", "Backtest", "Analytics"],
    key="nav_radio"
)

st.session_state.page = page

# Display version info in sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("""
**Version:** 1.0.0  
**Data Source:** yfinance (NSE)  
**Market:** Indian Equities  
**Status:** 🟢 Active
""")

# Display page title
st.title(f"📈 {page}")

# Load and display selected page
if page == "Home":
    from pages import home
    home.show()

elif page == "Signal Dashboard":
    from pages import signals_dashboard
    signals_dashboard.show()

elif page == "Pair Explorer":
    from pages import pair_explorer
    pair_explorer.show()

elif page == "Backtest":
    from pages import backtest
    backtest.show()

elif page == "Analytics":
    from pages import analytics
    analytics.show()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #888; padding: 20px;">
    <p>Statistical Arbitrage Signal Platform for Indian Equities</p>
    <p>Designed for institutional traders and quantitative researchers</p>
    <p>Not investment advice. For research and analysis purposes only.</p>
</div>
""", unsafe_allow_html=True)
