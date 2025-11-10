# home.py - Final Design Polish for Market Hub
from __future__ import annotations
import json
from pathlib import Path
from textwrap import dedent
from datetime import datetime
import os
import pytz 
import yfinance as yf 
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
# Theme / CSS (Final Polish)
# --------------------------------------------------------------------------------------
BLOOM_BG       = "#0B0F14"    
BLOOM_PANEL    = "#121820"    
BLOOM_TEXT     = "#FFFFFF"    
BLOOM_MUTED    = "rgba(255,255,255,0.45)" # Lighter grey for sidebar text
NEUTRAL_GRAY   = "#4A5B6E"    
INPUT_BG       = "#2E3A46"    
INPUT_BG_LIGHT = "#3A4654"    
ACCENT_BLUE    = "#2BB3F3"    
ACCENT_GREEN   = "#26D07C"    
ACCENT_PURPLE  = "#8A7CF5"    # Strategy Card Hover Color
DARK_PURPLE    = "#3A2A6A"    

# --- Market Data Configuration ---
MAJOR_TICKERS = ["SPY", "QQQ", "IWM", "^VIX", "GLD", "SLV", "TLT"]
# Adjusted Sector/Country Tickers for standard use
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
    
    is_weekday = 0 <= now.weekday() <= 4
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

def get_metric_styles(change_pct):
    """Determines color and icon based on percentage change."""
    if change_pct > 0.01:
        color_token = "--green-accent"
        icon = '↑'
    elif change_pct < -0.01:
        color_token = "--red-neg"
        icon = '↓'
    else:
        color_token = "--purple"
        icon = '•'
    return f"var({color_token})", icon, f"var({color_token})"

@st.cache_data(ttl="1h")
def fetch_ticker_data(tickers):
    """Fetches the last 15 months of adjusted close prices for tickers."""
    data = yf.download(tickers, period="15mo", interval="1d", progress=False, auto_adjust=True)
    if data.empty:
        return pd.DataFrame()
    return data['Close']

@st.cache_data(ttl="5m")
def fetch_live_summary(tickers):
    """Fetches key metrics for market summary (Run frequently)."""
    try:
        data = yf.Tickers(tickers).fast_info
        if isinstance(data, pd.DataFrame):
            summary = data.T.to_dict()
        else:
            summary = {t: data.get(t, {}) for t in tickers}
        return summary
    except Exception:
        return {}


def calculate_returns(data, period):
    """Calculates returns for the given period (1D, 7D, 30D, 1Y, YTD)."""
    if data.empty: return pd.Series()
    
    last_price = data.iloc[-1]
    
    # Calculate reference price based on period (logic is robust)
    if period == '1D':
        ref_price = data.iloc[-2] if len(data) >= 2 else data.iloc[-1]
    elif period == '7D':
        idx = max(0, len(data) - 6) 
        ref_price = data.iloc[idx]
    elif period == '30D':
        idx = max(0, len(data) - 22) 
        ref_price = data.iloc[idx]
    elif period == '1Y':
        idx = max(0, len(data) - 260) 
        ref_price = data.iloc[idx]
    elif period == 'YTD':
        current_year = data.index[-1].year
        ytd_start_index = data.index[data.index.year == current_year].min()
        if pd.notna(ytd_start_index) and ytd_start_index in data.index:
             ref_price = data.loc[ytd_start_index]
        else:
            return pd.Series(0.0, index=data.columns) 

    if isinstance(last_price, (pd.Series, np.ndarray)) and isinstance(ref_price, (pd.Series, np.ndarray)):
        returns = ((last_price - ref_price) / ref_price) * 100
    elif isinstance(last_price, (pd.Series, np.ndarray)):
         returns = ((last_price - ref_price) / ref_price) * 100
    else:
        returns = pd.Series(0.0, index=data.columns)

    return returns.fillna(0.0)

def get_metric_html(title, price, change_pct, accent_color_token):
    """Generates the HTML for a Market KPI Card."""
    color, icon, _ = get_metric_styles(change_pct)
    change_text = f"{icon} {abs(change_pct):.2f}%"
    
    return dedent(f"""
        <div class="kpi" style="border-left: 5px solid {color};"
             onmouseover="this.style.borderColor='var(--green-accent)';"
             onmouseout="this.style.borderColor='{color}';">
            <div class="h">{title}</div>
            <div class="v" style="color: {color};">
                {price:.2f}
            </div>
            <div class="text-sm font-semibold" style="color: {color};">{change_text}</div>
        </div>
    """)

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
          --sidebar-bg: {BLOOM_PANEL};
          --card-purple-shadow: rgba(138, 124, 245, 0.4); 
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
        
        /* Sidebar Text: Lighter Grey */
        [data-testid="stSidebar"] .stMarkdown > div {{
            color: var(--muted) !important; 
        }}
        
        /* Sidebar Navigation Arrows & Links Pop */
        [data-testid="stSidebarNav"] a, [data-testid="stSidebarNav"] svg {{
            color: var(--text) !important;
            fill: var(--purple) !important;
            transition: all 0.2s;
        }}
        [data-testid="stSidebarNav"] a:hover {{
            color: var(--green-accent) !important;
        }}
        
        /* --- Strategy Navigation Card: Final Polish --- */
        .strategy-group-container {{
            margin-bottom: 25px; 
            position: relative; 
            min-height: 120px; /* Ensure space for the card and link to sit */
        }}
        .strategy-link-card {{
            background: linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.00));
            border: 1px solid var(--neutral); 
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 5px 15px rgba(0,0,0,.4); 
            transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94); 
            height: 100%;
            pointer-events: none; 
            display: flex; 
            flex-direction: column;
            justify-content: space-between;
        }}
        /* Change border and shadow color on hover */
        .strategy-group-container:hover .strategy-link-card {{
            border-color: var(--purple); 
            transform: translateY(-5px); 
            box-shadow: 0 15px 40px var(--card-purple-shadow); 
        }}
        /* Target the actual st.page_link button and stretch it over the card */
        .strategy-group-container button[kind="page-link"] {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            opacity: 0; /* Make it invisible */
            cursor: pointer;
            z-index: 10;
        }}
        /* Hide the label text from the page link button */
        .strategy-group-container button[kind="page-link"] > div > p {{
            display: none !important;
        }}

        .strategy-link-title {{ 
            font-weight: 800; 
            font-size: 1.5rem; 
            letter-spacing: .5px; 
            display: flex;
            align-items: center;
            gap: 15px; 
            margin-bottom: 10px;
        }}
        .strategy-link-desc {{ color: var(--muted); font-size: 1.0rem; }} 

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
        
        /* --- Heatmap Styling --- */
        
        /* Ensures row index/category is visible */
        [data-testid="stDataFrame"] .row_heading.level0 > div {{
            color: var(--text) !important;
            font-weight: 600;
        }}
        
        /* Cell content styling (ticker + return) */
        .heatmap-cell {{
            font-size: 0.95rem; 
            font-weight: 700;
            text-align: center;
            line-height: 1.2;
            padding: 8px 4px; /* Reduced padding */
        }}
        .heatmap-ticker {{
            font-size: 1.0rem;
            font-weight: 900;
            display: block;
            opacity: 0.9;
        }}
        .heatmap-return {{
            font-size: 0.75rem;
            display: block;
            opacity: 0.7;
            margin-top: 2px;
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
# Sidebar: Cleaned up (Minimal info, lighter text)
# --------------------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### Workspace Info")
    # Using the new BLOOM_MUTED color defined in the CSS
    st.markdown(f"""
        <div style="color: var(--muted); font-size: .85rem; padding: 10px 0;">
            <p>:small_blue_diamond: Session started <b>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</b></p>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown("### Strategy Configuration")
    st.markdown(f"""
        <div style="color: var(--muted); font-size: .85rem;">
            <p>Parameters used by the pages:</p>
            <ul style="list-style: none; padding-left: 0;">
                <li>Tickers: {len(st.session_state['tickers'])}</li>
                <li>MA Window: {st.session_state['ma_window']}</li>
                <li>Lookback: {st.session_state['lookback']}</li>
            </ul>
            <p>Configure these values in the settings section of the strategy pages.</p>
        </div>
    """, unsafe_allow_html=True)


# --------------------------------------------------------------------------------------
# 🌎 Dynamic Market Summary Section
# --------------------------------------------------------------------------------------
st.markdown("### 🌎 Today's Market Summary")
st.caption("Live data summary based on US market hours (EST/EDT).")

now, is_open, status_text, status_color = get_market_status()
current_time_str = now.strftime('%H:%M:%S EST')

st.markdown(f"#### Status: <span style='color: {status_color};'>{status_text}</span>", unsafe_allow_html=True)
st.markdown("---")

def display_market_kpis(is_open, status_text, status_color):
    
    col_spy, col_qqq, col_vix, col_time = st.columns(4)
    
    tickers_to_fetch = ["SPY", "QQQ", "^VIX"]
    if is_open:
        market_data = fetch_live_summary(tickers_to_fetch)
    else:
        market_data = {} 
        
    def get_ticker_metric(ticker):
        if is_open and ticker in market_data:
            data = market_data[ticker]
            price = data.get('lastPrice', 0.0)
            change_pct = data.get('regularMarketChangePercent', 0.0)
        else:
            price = 0.0
            change_pct = 0.0
            
            try:
                close_data = fetch_ticker_data([ticker])
                if not close_data.empty and len(close_data) >= 2:
                    close_data = close_data[ticker]
                    price = close_data.iloc[-1]
                    change_pct = ((close_data.iloc[-1] - close_data.iloc[-2]) / close_data.iloc[-2]) * 100
            except Exception:
                pass 

        return price, change_pct

    # --- SPY ---
    spy_price, spy_change_pct = get_ticker_metric("SPY")
    with col_spy:
        st.markdown(get_metric_html("S&P 500 (SPY)", spy_price, spy_change_pct, "--green-accent"), unsafe_allow_html=True)

    # --- QQQ ---
    qqq_price, qqq_change_pct = get_ticker_metric("QQQ")
    with col_qqq:
        st.markdown(get_metric_html("NASDAQ 100 (QQQ)", qqq_price, qqq_change_pct, "--red-neg"), unsafe_allow_html=True)

    # --- VIX ---
    vix_price, vix_change_pct = get_ticker_metric("^VIX")
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
# Page navigation (Final Polish)
# --------------------------------------------------------------------------------------
st.markdown("### 🧭 Jump to a Strategy")

PAGE_MAPPING = {
    "📈 Slope Convexity": {"file": "1_Slope_Convexity.py", "desc": "Advanced Momentum and Trend Analysis", "icon": "🚀"},
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
            # The HTML div container that holds the visual style
            st.markdown(
                f"""
                <div class="strategy-group-container">
                    <div class="strategy-link-card">
                        <div class="strategy-link-title">
                            <span style="color: var(--green-accent); font-size: 1.5rem;">{icon}</span> 
                            {label}
                        </div>
                        <div class="strategy-link-desc">{desc}</div>
                        <!-- Path/File name removed to make the card cleaner -->
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            # The st.page_link button is placed directly below and stretched over the card via CSS
            # The label is now an empty string to remove the "Open" text that was visible
            st.page_link(rel_path, label="", icon=None) 
else:
    st.info("No pages detected in `pages/` yet. Add files like `1_Slope_Convexity.py` to enable navigation.")

st.markdown("---")

# --------------------------------------------------------------------------------------
# ♨️ Market Heatmap Section
# --------------------------------------------------------------------------------------
st.markdown("### ♨️ Market Return Heatmap")

return_period = st.selectbox(
    "Select Return Period", 
    options=['1D', '7D', '30D', 'YTD', '1Y'], 
    index=0, 
    key='return_period_toggle'
)

# @st.cache_data is reused from above

heatmap_df, data_loaded = generate_heatmap_data(return_period, HEATMAP_TICKERS)

if data_loaded and not heatmap_df.empty:
    
    # Map back from Ticker to Display Name for sectors/countries
    ticker_to_name = {v: k for k, v in SECTOR_TICKERS.items()}
    ticker_to_name.update({v: k for k, v in COUNTRY_TICKERS.items()})

    # --- NEW COLORING FUNCTION ---
    def color_return(val):
        """Generates background color based on return value."""
        if pd.isna(val):
            return 'background-color: transparent; color: var(--muted); border: 1px solid rgba(255,255,255,0.05);'
        
        try:
            val = float(val)
        except ValueError:
            return 'background-color: transparent; color: var(--muted); border: 1px solid rgba(255,255,255,0.05);'

        # Defines range: Green for positive, Red for negative, Yellow/Purple around zero
        # 4.0% is the max saturation point
        max_saturation = 4.0
        
        if val > 0:
            # Scale alpha from 0.1 to 0.9 based on value up to max_saturation
            alpha = min(0.9, 0.1 + (val / max_saturation) * 0.8) 
            bg = f'rgba(38, 208, 124, {alpha})' # Green
            text_color = 'var(--text)'
        elif val < 0:
            alpha = min(0.9, 0.1 + (abs(val) / max_saturation) * 0.8)
            bg = f'rgba(217, 83, 79, {alpha})' # Red
            text_color = 'var(--text)'
        else:
            bg = f'rgba(138, 124, 245, 0.1)' # Light Purple/Yellow for low movement
            text_color = 'var(--muted)'
            
        return f'background-color: {bg}; color: {text_color}; border: 1px solid rgba(255,255,255,0.05);'

    def format_heatmap_cell(x, ticker):
        """Formats the cell content to show Ticker and Return (HTML)."""
        if pd.isna(x):
            return ""
        
        # Get the ticker symbol, defaulting to the column name for indices
        symbol = ticker_to_name.get(ticker, ticker)
        
        return f"""
        <div class="heatmap-cell">
            <span class="heatmap-ticker">{symbol}</span>
            <span class="heatmap-return">{x:.2f}%</span>
        </div>
        """
    
    # --- New Styling Application ---
    
    # 1. Map color styling to the numeric values
    styled_df = heatmap_df.style.map(color_return, subset=pd.IndexSlice[:, heatmap_df.columns.difference(['Category'])])
    
    # 2. Map the custom HTML formatting (Ticker + Return) to the values
    for col in heatmap_df.columns:
        styled_df = styled_df.format({col: lambda x, col=col: format_heatmap_cell(x, col)})

    st.markdown("<div class='dataframe-container'>", unsafe_allow_html=True)
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=False,
    )
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.warning("Could not load market data for the heatmap. Check connectivity or try again later.")
    

st.markdown("---")
st.subheader("Tips")
st.markdown(
    """
- The **Market Summary** uses real-time or end-of-day data from `yfinance`.
- The **Market Heatmap** uses calculated returns for the selected period, with color intensity showing return magnitude.
- Global parameters are initialized here but are only visible and editable on the strategy pages.
"""
)
