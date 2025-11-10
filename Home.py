# home.py - Updated for Market Summary Layout
from __future__ import annotations
import json
from pathlib import Path
from textwrap import dedent
from datetime import datetime
import os
import pytz # New: For timezone-aware market logic
import yfinance as yf # New: For fetching live data
import pandas as pd
import numpy as np

import streamlit as st

# --------------------------------------------------------------------------------------
# Page setup
# --------------------------------------------------------------------------------------
st.set_page_config(
    page_title="Desk Hub",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------------------
# Theme / CSS (Enhanced for Professional & Dynamic Look)
# --------------------------------------------------------------------------------------
BLOOM_BG       = "#0B0F14"    # Primary Background: Deep Black/Navy
BLOOM_PANEL    = "#121820"    # Component Background: Dark Panel
BLOOM_TEXT     = "#FFFFFF"    # Primary Text
BLOOM_MUTED    = "rgba(255,255,255,0.70)" # Muted Text
NEUTRAL_GRAY   = "#4A5B6E"    # Borders/Separators
INPUT_BG       = "#2E3A46"    # Dark Gray Input (Sidebar)
INPUT_BG_LIGHT = "#3A4654"    # Lighter Input/Container (Main)
ACCENT_BLUE    = "#2BB3F3"    # Secondary Accent (Flashes)
ACCENT_GREEN   = "#26D07C"    # Bullish (Vibrant Teal)
ACCENT_PURPLE  = "#8A7CF5"    # Tertiary Accent (Vibrant Purple)
DARK_PURPLE    = "#3A2A6A"    # Gradient End Point

# --- Market Data Configuration ---
MAJOR_TICKERS = ["SPY", "QQQ", "IWM", "^VIX", "GLD", "SLV", "TLT"]
SECTOR_TICKERS = {
    "Technology": "XLK", "Healthcare": "XLV", "Financials": "XLF", 
    "Consumer Disc.": "XLY", "Industrials": "XLI", "Energy": "XLE"
}
COUNTRY_TICKERS = {
    "EAFE": "EFA", "Emerging": "EEM", "Europe": "EZU", "Japan": "EWJ", "China": "MCHI"
}
HEATMAP_TICKERS = list(set(MAJOR_TICKERS + list(SECTOR_TICKERS.values()) + list(COUNTRY_TICKERS.values())))

# --- Helper Functions ---

def get_market_status():
    """Checks the status of the US equity market (NYSE/NASDAQ)."""
    tz = pytz.timezone('America/New_York')
    now = datetime.now(tz)
    
    # Check if it's a weekday (Monday=0, Sunday=6)
    is_weekday = 0 <= now.weekday() <= 4
    
    # Define market hours (9:30 AM to 4:00 PM)
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)

    is_open = is_weekday and (market_open <= now < market_close)
    
    if not is_weekday:
        status_text = "Market Closed (Weekend)"
        status_color = ACCENT_PURPLE
    elif now >= market_close:
        status_text = "Market Closed (After Hours)"
        status_color = "#D9534F" # Red
    elif now < market_open:
        status_text = "Market Closed (Pre-Market)"
        status_color = ACCENT_BLUE
    else:
        status_text = "Regular Session Open"
        status_color = ACCENT_GREEN

    return now, is_open, status_text, status_color

@st.cache_data(ttl="1h")
def fetch_ticker_data(tickers):
    """Fetches the last 15 months of adjusted close prices for tickers."""
    # Fetch 15 months to ensure enough data for 1Y/YTD calculations
    data = yf.download(tickers, period="15mo", interval="1d", progress=False, auto_adjust=True)
    if data.empty:
        return pd.DataFrame()
    return data['Close']

@st.cache_data(ttl="5m")
def fetch_live_summary(tickers):
    """Fetches key metrics for market summary (Run frequently)."""
    try:
        data = yf.Tickers(tickers).fast_info
        
        # yfinance returns different structures, normalize to a Series of dicts
        if isinstance(data, pd.DataFrame):
            summary = data.T.to_dict()
        else:
            summary = {t: data.get(t, {}) for t in tickers}
            
        return summary
    except Exception as e:
        # st.error(f"Error fetching live summary: {e}")
        return {}


def calculate_returns(data, period):
    """Calculates returns for the given period (1D, 7D, 30D, 1Y, YTD)."""
    if data.empty: return pd.Series()
    
    last_price = data.iloc[-1]
    
    if period == '1D':
        # Today's close vs Yesterday's close (last two available trading days)
        ref_price = data.iloc[-2] if len(data) >= 2 else data.iloc[-1]
    elif period == '7D':
        # Last available close vs 5 business days ago
        idx = max(0, len(data) - 6) # 5 trading days + 1 = 6th row back
        ref_price = data.iloc[idx]
    elif period == '30D':
        # Last available close vs 21 business days ago (~1 month)
        idx = max(0, len(data) - 22) # 21 trading days + 1 = 22nd row back
        ref_price = data.iloc[idx]
    elif period == '1Y':
        # Find price closest to 1 year ago (52 weeks * 5 days = ~260 days)
        idx = max(0, len(data) - 260) 
        ref_price = data.iloc[idx]
    elif period == 'YTD':
        # Find the price on the first trading day of the current year
        current_year = data.index[-1].year
        ytd_start_index = data.index[data.index.year == current_year].min()
        if pd.notna(ytd_start_index):
             ref_price = data.loc[ytd_start_index]
        else:
            return pd.Series(0.0, index=data.columns) # Fallback to 0 if year start is missing

    returns = ((last_price - ref_price) / ref_price) * 100
    return returns.fillna(0.0)

# --------------------------------------------------------------------------------------
# CSS injection
# --------------------------------------------------------------------------------------
st.markdown(
    dedent(
        f"""
        <style>
        :root {{
          --bg:{BLOOM_BG}; --panel:{BLOOM_PANEL}; --text:{BLOOM_TEXT}; --muted:{BLOOM_MUTED};
          --neutral:{NEUTRAL_GRAY}; --input:{INPUT_BG}; --inputlight:{INPUT_BG_LIGHT};
          --blue:{ACCENT_BLUE}; --green:{ACCENT_GREEN}; --purple:{ACCENT_PURPLE};
          --green-accent: #26D07C;
          --red-neg: #D9534F; 
          --sidebar-bg: {BLOOM_PANEL}; /* Darker Panel for Sidebar */
        }}
        html, body {{
          height:100%;
          background: radial-gradient(1200px 600px at 15% -10%, rgba(43,179,243,0.15), transparent 60%),
                      radial-gradient(1200px 600px at 85% 110%, rgba(138,124,245,0.15), transparent 60%),
                      linear-gradient(135deg, var(--bg) 0%, {DARK_PURPLE} 100%) fixed !important;
        }}
        .stApp {{ background:transparent!important; color:var(--text); }}
        .block-container {{ max-width: 1500px; padding-top: .6rem; padding-bottom: 2rem; }}
        header[data-testid="stHeader"] {{ background:transparent!important; height:2.5rem!important; }}
        [data-testid="stDecoration"] {{ background:transparent!important; }}

        /* --- Sidebar Enhancements --- */
        section[data-testid="stSidebar"], aside[data-testid="stSidebar"] {{
          background: var(--sidebar-bg) !important;
          box-shadow: 4px 0 10px rgba(0,0,0,0.4);
        }}
        
        /* Make sidebar links/expander arrows 'pop' (Use Streamlit's targetable classes) */
        /* Targets the arrow/icon area of expanders and sidebar selections */
        .stSelectbox>label, .stMultiSelect>label, .stRadio>label, 
        .stFileUploader>label, .stDateInput>label, 
        .stSidebar .stSelectbox [data-baseweb="select"] svg,
        .stSidebar .stMultiSelect [data-baseweb="select"] svg {{
            fill: var(--purple) !important;
        }}
        
        /* --- Strategy Navigation Card: Make whole box clickable visually --- */
        .strategy-group-container {{
            margin-bottom: 25px; /* Spacing between groups */
        }}
        .strategy-link-card {{
            background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.00));
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,.4);
            transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94); 
            height: 100%;
            pointer-events: none; /* Important: prevents the div from intercepting the link click below it */
        }}
        .strategy-link-card:hover {{
            border-color: var(--green-accent);
            transform: translateY(-5px); 
            box-shadow: 0 15px 40px rgba(38, 208, 124, 0.3);
        }}
        /* Target the actual st.page_link button and stretch it over the card */
        .strategy-group-container button[kind="page-link"] {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            opacity: 0;
            cursor: pointer;
            z-index: 10;
        }}

        .strategy-link-title {{ 
            font-weight: 800; 
            font-size: 1.25rem; 
            letter-spacing: .5px; 
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .strategy-link-desc {{ color: var(--muted); font-size: .88rem; margin-top: 4px; }}

        /* KPI / Metric Cards (Market Summary) */
        .kpi {{
          background: linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.00));
          border: 1px solid rgba(255,255,255,0.10);
          border-radius: 14px;
          padding: 12px 14px;
          text-align: left;
          transition: border-color 0.2s;
        }}
        .kpi .h {{ font-size: .85rem; color: var(--muted); margin-bottom: 4px; }}
        .kpi .v {{ font-size: 1.45rem; font-weight: 800; }}
        
        .small-muted {{ color: var(--muted); font-size: .86rem; }}
        
        /* Heatmap Styling (Background color based on return) */
        .heatmap-cell {{
            padding: 8px 6px;
            font-weight: 700;
            font-size: 0.9rem;
            color: var(--text);
            border-radius: 4px;
            text-align: center;
        }}
        </style>
        """
    ),
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------------------
# Header
# --------------------------------------------------------------------------------------
st.markdown(
    """
    <div style="display:flex;align-items:center;gap:12px;padding:12px 20px;margin:0 0 10px 0;border-bottom:1px solid var(--neutral);">
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
        <rect x="2" y="3" width="20" height="18" rx="3" stroke="#2BB3F3" stroke-width="1.5"/>
        <polyline points="5,15 9,11 12,13 17,7 19,9" stroke="#26D07C" stroke-width="2" fill="none" />
        <circle cx="19" cy="9" r="1.8" fill="#26D07C"/>
      </svg>
      <div style="font-weight:900;letter-spacing:.3px;font-size:1.6rem;">Desk Hub</div>
      <div style="margin-left:auto;font-size:.95rem;color:rgba(255,255,255,.70);font-weight:500;">Multi‑Strategy Workspace</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Fun one-liner
st.markdown(
    """
    <div style="text-align:center; font-size:1.05rem; font-style:italic; color:rgba(255,255,255,0.80); margin:-4px 0 18px 0;">
      "You're either a smart-fella or fart smella" – Confucius
    </div>
    """,
    unsafe_allow_html=True,
)

# Initialize Session State (Hidden from user, but required for app state persistence)
if "tickers" not in st.session_state:
    st.session_state["tickers"] = ["SPY", "AAPL", "MSFT"]
if "ma_window" not in st.session_state:
    st.session_state["ma_window"] = 200
if "lookback" not in st.session_state:
    st.session_state["lookback"] = 200

# --------------------------------------------------------------------------------------
# Sidebar: Cleaned up (No user widgets here)
# --------------------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### Global Parameters")
    st.info(
        f"""
        These values are used on the strategy pages:
        * **Tickers:** {len(st.session_state['tickers'])}
        * **MA Window:** {st.session_state['ma_window']}
        * **Lookback:** {st.session_state['lookback']}
        """
    )
    st.markdown("---")
    st.caption("Workspace Info")
    st.write(f":small_blue_diamond: Session started **{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}**")


# --------------------------------------------------------------------------------------
# 🌎 Dynamic Market Summary Section
# --------------------------------------------------------------------------------------
st.markdown("### 🌎 Today's Market Summary")
st.caption("Live data summary based on US market hours (EST/EDT).")

now, is_open, status_text, status_color = get_market_status()
current_time_str = now.strftime('%H:%M:%S EST')

def display_market_kpis(is_open, status_text, status_color):
    
    st.subheader(f"Status: <span style='color: {status_color};'>{status_text}</span>", unsafe_allow_html=True)
    st.markdown("---")

    col_spy, col_qqq, col_vix, col_time = st.columns(4)
    
    # --- Live Data Fetching ---
    tickers_to_fetch = ["SPY", "QQQ", "^VIX"]
    if is_open:
        # Fetch frequently if market is open
        market_data = fetch_live_summary(tickers_to_fetch)
    else:
        # For a closed market, only use cached data or show placeholders
        market_data = {} 
        
    def get_ticker_metric(ticker):
        if is_open and ticker in market_data:
            data = market_data[ticker]
            price = data.get('lastPrice', 0.0)
            change_pct = data.get('regularMarketChangePercent', 0.0)
        else:
            # Fallback/Closed Market Mock
            price = 0.0
            change_pct = 0.0
            
            # For non-live status, we need to fetch 1D return to show context
            try:
                # Use cached function to get context data
                close_data = fetch_ticker_data([ticker])
                if not close_data.empty:
                    close_data = close_data[ticker]
                    price = close_data.iloc[-1]
                    # Calculate true 1-Day return from cached data
                    change_pct = ((close_data.iloc[-1] - close_data.iloc[-2]) / close_data.iloc[-2]) * 100
            except Exception:
                pass # Silent fail if data unavailable

        return price, change_pct

    # --- SPY ---
    spy_price, spy_change_pct = get_ticker_metric("SPY")
    spy_color, spy_icon, _ = get_metric_styles(spy_change_pct)
    with col_spy:
        st.markdown(get_metric_html("S&P 500 (SPY)", spy_price, spy_change_pct, "--green-accent"), unsafe_allow_html=True)

    # --- QQQ ---
    qqq_price, qqq_change_pct = get_ticker_metric("QQQ")
    qqq_color, qqq_icon, _ = get_metric_styles(qqq_change_pct)
    with col_qqq:
        st.markdown(get_metric_html("NASDAQ 100 (QQQ)", qqq_price, qqq_change_pct, "--red-neg"), unsafe_allow_html=True)

    # --- VIX ---
    vix_price, vix_change_pct = get_ticker_metric("^VIX")
    vix_color, vix_icon, _ = get_metric_styles(vix_change_pct)
    with col_vix:
        st.markdown(get_metric_html("VIX Index (^VIX)", vix_price, vix_change_pct, "--purple"), unsafe_allow_html=True)

    # --- Time ---
    with col_time:
        st.markdown(f"""
            <div class="kpi" style="border-left: 5px solid {status_color};">
                <div class="h">Current Time</div>
                <div class="v" style="color: {status_color};">{current_time_str}</div>
                <div class="text-sm font-semibold text-gray-400">Market Status</div>
            </div>
        """, unsafe_allow_html=True)

# Display the summary
display_market_kpis(is_open, status_text, status_color)


# --------------------------------------------------------------------------------------
# Page navigation (Enhanced Card Design - Clickable Wrapper)
# --------------------------------------------------------------------------------------
st.markdown("### 🧭 Jump to a Strategy")

PAGE_MAPPING = {
    "📈 Slope Convexity": {"file": "1_Slope_Convexity.py", "desc": "Advanced Sentiment Scanning", "icon": "🚀"},
    "📉 Mean Reversion (draft)": {"file": "2_Mean_Reversion.py", "desc": "Z-Score-based Statistical Trading", "icon": "🔬"},
}
pages_dir = Path("pages")
available = []

for label, data in PAGE_MAPPING.items():
    rel_path = pages_dir / data["file"]
    if rel_path.exists():
        available.append((label, rel_path.as_posix(), data["desc"], data["icon"]))

if available:
    cols = st.columns(len(available))
    for i, (label, rel_path, desc, icon) in enumerate(available):
        with cols[i]:
            # Use a div wrapper to apply the combined styling
            st.markdown(
                f"""
                <div class="strategy-group-container">
                    <div class="strategy-link-card">
                        <div class="strategy-link-title">
                            <span style="color: var(--green-accent); font-size: 1.5rem;">{icon}</span> 
                            {label}
                        </div>
                        <div class="strategy-link-desc">{desc}</div>
                        <div class="small-muted font-mono" style="margin:.25rem 0 .6rem 0;">Path: <code>{rel_path}</code></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            # st.page_link is placed right after the custom card HTML. 
            # The CSS above stretches the link button visually over the card.
            st.page_link(rel_path, label="Open", icon=None) 
else:
    st.info("No pages detected in `pages/` yet. Add files like `1_Slope_Convexity.py` to enable navigation.")

st.markdown("---")

# --------------------------------------------------------------------------------------
# ♨️ Market Heatmap Section
# --------------------------------------------------------------------------------------
st.markdown("### ♨️ Market Return Heatmap")

# Period Toggle
return_period = st.selectbox(
    "Select Return Period", 
    options=['1D', '7D', '30D', 'YTD', '1Y'], 
    index=0, 
    key='return_period_toggle'
)

# --- Data Processing for Heatmap ---
@st.cache_data(ttl="4h")
def generate_heatmap_data(period, tickers_list):
    # Fetch data for all heatmap tickers
    all_close_data = fetch_ticker_data(tickers_list)
    if all_close_data.empty: return pd.DataFrame(), False
    
    # Calculate returns for the selected period
    returns = calculate_returns(all_close_data, period)
    
    # Structure the heatmap data
    data = []
    
    # 1. Major Indexes
    major_row = {"Category": "Major Indices"}
    for ticker in MAJOR_TICKERS:
        if ticker in returns: major_row[ticker] = returns[ticker]
    data.append(major_row)
    
    # 2. Sector ETFs
    sector_row = {"Category": "Sector ETFs"}
    for name, ticker in SECTOR_TICKERS.items():
        if ticker in returns: sector_row[name] = returns[ticker]
    data.append(sector_row)

    # 3. Country ETFs
    country_row = {"Category": "Country ETFs"}
    for name, ticker in COUNTRY_TICKERS.items():
        if ticker in returns: country_row[name] = returns[ticker]
    data.append(country_row)
    
    # Convert to DataFrame
    df = pd.DataFrame(data).set_index("Category").fillna(np.nan)
    return df, True

heatmap_df, data_loaded = generate_heatmap_data(return_period, HEATMAP_TICKERS)

# --- Heatmap Display Logic ---
if data_loaded and not heatmap_df.empty:
    
    # Define a color map function
    def color_return(val):
        """Generates background color based on return value."""
        if pd.isna(val):
            return 'background-color: transparent; color: var(--muted);'
            
        val = float(val)
        
        # Color gradient logic
        if val > 2.0: # Strong Positive
            bg = f'rgba(38, 208, 124, {min(0.8, 0.4 + (val - 2.0) * 0.1)})'
            color = 'var(--text)'
        elif val > 0.0: # Mild Positive
            bg = f'rgba(38, 208, 124, {min(0.4, 0.1 + val * 0.1)})'
            color = 'var(--text)'
        elif val < -2.0: # Strong Negative
            bg = f'rgba(217, 83, 79, {min(0.8, 0.4 + abs(val) * 0.1)})'
            color = 'var(--text)'
        elif val < 0.0: # Mild Negative
            bg = f'rgba(217, 83, 79, {min(0.4, 0.1 + abs(val) * 0.1)})'
            color = 'var(--text)'
        else:
            # Neutral / Zero
            bg = f'rgba(138, 124, 245, 0.1)' # Subtle Purple for Neutral
            color = 'var(--muted)'
            
        return f'background-color: {bg}; color: {color}; border: 1px solid rgba(255,255,255,0.05);'

    # Format the numbers to 2 decimal places with percentage sign
    formatted_df = heatmap_df.applymap(lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A")
    
    # Apply the styling
    styled_df = formatted_df.style.applymap(color_return)
    
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=False,
    )
else:
    st.warning("Could not load market data for the heatmap. Check connectivity or try again later.")
    

st.markdown("---")
st.subheader("Tips")
st.markdown(
    """
- All global parameters (Tickers, MA Window, Lookback) are still set and maintained in the **Sidebar** for the strategy pages.
- The **Market Summary** now uses real-time data from `yfinance` when the market is open.
- The **Market Heatmap** displays returns for the selected period (`1D`, `7D`, `30D`, `YTD`, `1Y`) for major asset groups.
"""
)
