import streamlit as st
from textwrap import dedent

# Set up the page configuration
st.set_page_config(
    page_title="Mean Reversion (draft)",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------------------
# Theme / CSS (Keep this in sync with the main Home.py theme)
# ---------------------------------------------------------------------
# Use the same color variables as Home.py for consistent theming
DARK_PURPLE = "#3A2A6A"
NEUTRAL_GRAY = "#4A5B6E"
INPUT_BG_LIGHT = "#3A4654"
BLOOM_TEXT = "#FFFFFF"

# Apply basic background and global container styles
st.markdown(dedent(f"""
<style>
/* Inherit the main gradient background */
html, body {{
  background: linear-gradient(135deg, #0B0F14 0%, {DARK_PURPLE} 100%) fixed !important;
}}
.stApp {{ background:transparent!important; color:{BLOOM_TEXT}; }}
.block-container {{ max-width:1500px; padding-top:.6rem; padding-bottom:2rem; }}

/* Ensure elements like containers and input backgrounds are consistent */
div[data-testid="stAppViewContainer"] input,
div[data-testid="stAppViewContainer"] textarea,
div[data-testid="stAppViewContainer"] [data-baseweb="select"] > div {{
  background: {INPUT_BG_LIGHT} !important;
  color: {BLOOM_TEXT} !important;
  border: 1px solid {NEUTRAL_GRAY} !important;
}}

/* Header styling */
.page-header {{
    font-weight: 900;
    letter-spacing: .3px;
    font-size: 1.6rem;
    padding: 12px 20px;
    margin: 0 0 8px 0;
    border-bottom: 1px solid {NEUTRAL_GRAY};
    display: flex;
    align-items: center;
    gap: 12px;
}}
</style>
"""), unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Header (Replicate the style from Home.py and 1_Slope_Convexity.py)
# ---------------------------------------------------------------------
st.markdown(
    """
    <div class="page-header">
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
        <rect x="2" y="3" width="20" height="18" rx="3" stroke="#2BB3F3" stroke-width="1.5"/>
        <polyline points="5,15 9,11 12,13 17,7 19,9" stroke="#26D07C" stroke-width="2" fill="none" />
        <circle cx="19" cy="9" r="1.8" fill="#26D07C"/>
      </svg>
      <div>Mean Reversion Strategy</div>
      <div style="margin-left:auto;font-size:.95rem;color:rgba(255,255,255,.70);font-weight:500;">Draft Strategy Page</div>
    </div>
    """,
    unsafe_allow_html=True
)

# ---------------------------------------------------------------------
# Main Content Area
# ---------------------------------------------------------------------
st.subheader("Strategy Parameters")

# Retrieve global settings from session state (set in Home.py)
tickers = st.session_state.get("tickers", ["SPY", "AAPL", "MSFT"])
ma_window = st.session_state.get("ma_window", 200)
lookback = st.session_state.get("lookback", 200)

st.info(f"""
This page will use the global settings:
* **Tickers:** {', '.join(tickers)}
* **MA Window:** {ma_window}
* **Convexity Lookback:** {lookback}
""")

# Example UI elements for a mean reversion strategy
c1, c2 = st.columns(2)

with c1:
    st.markdown("#### Mean Reversion Setup")
    mr_period = st.slider("Mean Reversion Lookback (Days)", 10, 100, 20, step=5)
    z_score_threshold = st.number_input("Z-Score Entry Threshold", 1.0, 3.0, 2.0, step=0.1)
    
with c2:
    st.markdown("#### Position Management")
    exit_threshold = st.number_input("Z-Score Exit Threshold", 0.0, 1.0, 0.5, step=0.1)
    max_drawdown = st.number_input("Max Position Drawdown (%)", 1.0, 10.0, 3.0, step=0.5)
    
st.markdown("---")

st.markdown("### Visualization & Results")
st.warning("Data loading and strategy backtesting logic goes here.")

if st.button("Run Mean Reversion Backtest"):
    st.success(f"Running backtest on {len(tickers)} tickers with a {mr_period}-day period and Z-Score > {z_score_threshold}.")

# ---------------------------------------------------------------------
# Developer Tips
# ---------------------------------------------------------------------
st.markdown("---")
st.caption("Developer Notes")
st.code("""
# To access the global settings from Home.py, use:
# tickers = st.session_state.get("tickers", [])
# ma_window = st.session_state.get("ma_window", 200)

# Import necessary libraries here (pandas, numpy, etc.)
# import pandas as pd
# import numpy as np
""")
