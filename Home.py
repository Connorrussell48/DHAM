# pages/3_Options_Skew.py
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
from textwrap import dedent
import pytz # Import pytz for timezone awareness (though not strictly necessary for this plot, good practice)

# --- Theme Variables (Must be consistent with Home.py) ---
BLOOM_BG       = "#0B0F14"    
BLOOM_TEXT     = "#FFFFF5"
NEUTRAL_GRAY   = "#4A5B6E"    
INPUT_BG_LIGHT = "#3A4654"    
ACCENT_GREEN   = "#26D07C"    
ACCENT_PURPLE  = "#8A7CF5"    

# --- Helper to Get Skew Data ---
# Note: Since the core options fetching function is heavy, we'll redefine it
# here, slightly adapting the logic for plotting, but keeping it uncached 
# to run in the strategy page scope.

def get_options_chain_for_plot(ticker_symbol='SPY'):
    """
    Fetches the option chain for the expiration date closest to 30 days out.
    """
    ticker = yf.Ticker(ticker_symbol)
    
    # 1. Find the expiration date closest to 30 days out
    today = datetime.now().date()
    target_date = today + timedelta(days=30)
    
    if not ticker.options:
        return None, None, 0, "No active options chain found."
        
    available_dates = [datetime.strptime(d, '%Y-%m-%d').date() for d in ticker.options]
    closest_date = min(available_dates, key=lambda d: abs(d - target_date))
    closest_date_str = closest_date.strftime('%Y-%m-%d')
    dte = (closest_date - today).days

    # 2. Fetch the option chain and current price
    try:
        chain = ticker.option_chain(closest_date_str)
        current_price = ticker.info.get('regularMarketPrice', None)
    except Exception as e:
        return None, None, 0, f"Failed to fetch options chain or price: {e}"

    if current_price is None:
        return None, None, 0, "Failed to fetch current market price."

    # 3. Clean and prepare dataframes
    calls = chain.calls.copy()
    puts = chain.puts.copy()
    
    calls['impliedVolatility'] = pd.to_numeric(calls['impliedVolatility'], errors='coerce') * 100 # Convert to %
    puts['impliedVolatility'] = pd.to_numeric(puts['impliedVolatility'], errors='coerce') * 100   # Convert to %
    
    # Calculate Moneyness (Strike / Current Price)
    calls['moneyness'] = calls['strike'] / current_price
    puts['moneyness'] = puts['strike'] / current_price
    
    # Filter to the desired moneyness range: -10% to +10% (0.90 to 1.10)
    calls_filtered = calls[
        (calls['moneyness'] >= 0.90) & 
        (calls['moneyness'] <= 1.10) & 
        (calls['impliedVolatility'] > 0.1)
    ].sort_values('moneyness')
    
    puts_filtered = puts[
        (puts['moneyness'] >= 0.90) & 
        (puts['moneyness'] <= 1.10) & 
        (puts['impliedVolatility'] > 0.1)
    ].sort_values('moneyness')
    
    return calls_filtered, puts_filtered, dte, None

# --- Plotting Function using Plotly ---
def create_plotly_skew_plot(df, title, line_color, iv_min, iv_max, current_price, moneyness_label):
    fig = go.Figure()
    
    # Main Volatility Line
    fig.add_trace(go.Scatter(
        x=df['moneyness'],
        y=df['impliedVolatility'],
        mode='lines+markers',
        name='Implied Volatility',
        line=dict(color=line_color, width=3),
        marker=dict(size=7, color=line_color)
    ))
    
    # ATM line (1.0 Moneyness)
    fig.add_vrect(
        x0=0.999, x1=1.001,
        fillcolor="White", opacity=0.1, line_width=0,
        annotation_text=f"ATM (${current_price:.2f})",
        annotation_position="top right"
    )

    fig.update_layout(
        title=f'<span style="font-size:1.3rem;">{title}</span>',
        xaxis_title=moneyness_label,
        yaxis_title='Implied Volatility (%)',
        template='plotly_dark',
        height=400,
        margin=dict(l=20, r=20, t=50, b=20),
        plot_bgcolor=INPUT_BG_LIGHT,
        paper_bgcolor='transparent',
        font=dict(color=BLOOM_TEXT),
        yaxis_range=[iv_min, iv_max],
        xaxis=dict(
            tickformat=".1%",
            range=[0.90, 1.10], # Enforce -10% to +10% moneyness
        ),
        showlegend=False
    )
    
    return fig

# ---------------------------------------------------------------------
# Page Setup & Layout
# ---------------------------------------------------------------------

st.set_page_config(
    page_title="Options Skew Analysis",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply basic styling for consistency
st.markdown(dedent(f"""
<style>
/* Inherit the main gradient background */
html, body {{
  background: linear-gradient(135deg, {BLOOM_BG} 0%, #3A2A6A 100%) fixed !important;
}}
.stApp {{ background:transparent!important; color:{BLOOM_TEXT}; }}
.block-container {{ max-width:1500px; padding-top:.6rem; padding-bottom:2rem; }}

/* General input/select styling */
div[data-testid="stAppViewContainer"] input,
div[data-testid="stAppViewContainer"] textarea,
div[data-testid="stAppViewContainer"] [data-baseweb="select"] > div {{
  background: {INPUT_BG_LIGHT} !important;
  color: {BLOOM_TEXT} !important;
  border: 1px solid {NEUTRAL_GRAY} !important;
}}
/* Sidebar metric text consistency */
div[data-testid="stMetric"] * {{ color: {BLOOM_TEXT} !important; }}
</style>
"""), unsafe_allow_html=True)

# ---------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------
st.markdown(
    f"""
    <div style="display:flex;align-items:center;gap:12px;padding:12px 20px;margin:0 0 8px 0;border-bottom:1px solid {NEUTRAL_GRAY};">
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
        <rect x="2" y="3" width="20" height="18" rx="3" stroke="{ACCENT_PURPLE}" stroke-width="1.5"/>
        <polyline points="5,15 9,11 12,13 17,7 19,9" stroke="{ACCENT_PURPLE}" stroke-width="2" fill="none" />
        <circle cx="19" cy="9" r="1.8" fill="{ACCENT_PURPLE}"/>
      </svg>
      <div style="font-weight:900;letter-spacing:.3px;font-size:1.6rem;">Options Skew Analysis</div>
      <div style="margin-left:auto;font-size:.95rem;color:rgba(255,255,255,.70);font-weight:500;">Implied Volatility Difference</div>
    </div>
    """,
    unsafe_allow_html=True
)

st.info("This tool visualizes the current Volatility Skew (Smile) for a near-term expiration date.")

# ---------------------------------------------------------------------
# Input Controls
# ---------------------------------------------------------------------
col_input, col_spacer = st.columns([1, 2])

with col_input:
    ticker_symbol = st.selectbox("Select Ticker", 
        options=["SPY", "QQQ", "IWM"], 
        index=0, 
        help="Options data is only reliably available for major indices/ETFs."
    )

st.markdown("---")

# ---------------------------------------------------------------------
# Data Fetch and Plotting
# ---------------------------------------------------------------------
calls_df, puts_df, dte, error = get_options_chain_for_plot(ticker_symbol)

if error:
    st.error(f"Data Error: {error}")
    st.warning("Please try again later. Options data may be unavailable or limited for this ticker.")
else:
    # Calculate global IV range for consistent Y-axis scaling
    all_ivs = pd.concat([calls_df['impliedVolatility'], puts_df['impliedVolatility']])
    iv_min = all_ivs.min() * 0.95
    iv_max = all_ivs.max() * 1.05
    if iv_min < 0: iv_min = 0
    
    current_price = calls_df['strike'].iloc[calls_df['strike'].abs().argsort()[:1]].mean()

    st.markdown(f"#### Volatility Skew Snapshot: {ticker_symbol}")
    st.caption(f"Expiration: **{calls_df['expiration'].iloc[0]}** ({dte} Days To Expiry)")

    # Create two columns for side-by-side plots
    col_call_plot, col_put_plot = st.columns(2)

    # Plot 1: Call Skew
    with col_call_plot:
        call_fig = create_plotly_skew_plot(
            calls_df,
            f"Call Options IV",
            ACCENT_PURPLE,
            iv_min, iv_max, current_price,
            'Moneyness (Strike / Price) - OTM Calls'
        )
        st.plotly_chart(call_fig, use_container_width=True)

    # Plot 2: Put Skew
    with col_put_plot:
        put_fig = create_plotly_skew_plot(
            puts_df,
            f"Put Options IV",
            ACCENT_GREEN,
            iv_min, iv_max, current_price,
            'Moneyness (Strike / Price) - OTM Puts'
        )
        st.plotly_chart(put_fig, use_container_width=True)


st.markdown("---")
st.markdown("#### About This Visualization")
st.markdown("""
This chart plots the **Implied Volatility (IV)** of options contracts against their **Moneyness** (Strike Price divided by Current Price). 

* **X-Axis (Moneyness):** Represents how far In-The-Money (ITM) or Out-Of-The-Money (OTM) a strike is. 
    * **1.00:** At-The-Money (ATM).
    * **< 1.00:** In-The-Money for Puts (Put Skew).
    * **> 1.00:** In-The-Money for Calls (Call Skew).
* **Skew (or Smile):** A downward-sloping IV curve (higher IV for lower strikes) is the classic "skew," indicating higher demand for OTM puts (bearish tail-risk hedging).
""")
