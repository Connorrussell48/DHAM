# home.py - Final Design Polish for Market Hub
from __future__ import annotations
import json
from pathlib import Path
from textwrap import dedent
from datetime import datetime, timedelta
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
BLOOM_TEXT     = "#FFFFF5"    # ADJUSTED: Slightly brighter than pure white
BLOOM_MUTED    = "rgba(255,255,255,0.45)" # Sidebar Text / Sub-text
NEUTRAL_GRAY   = "#4A5B6E"    
INPUT_BG       = "#2E3A46"    
INPUT_BG_LIGHT = "#3A4654"    
ACCENT_BLUE    = "#2BB3F3"    
ACCENT_GREEN   = "#26D07C"    
ACCENT_PURPLE  = "#8A7CF5"    
DARK_PURPLE    = "#3A2A6A"    

# --- Market Data Configuration ---
MAJOR_TICKERS = ["SPY", "QQQ", "IWM", "^VIX", "GLD", "SLV", "TLT"]
# Expanded Sector/Country Tickers
SECTOR_TICKERS = {
    "Technology": "XLK", "Healthcare": "XLV", "Financials": "XLF", 
    "Consumer Disc.": "XLY", "Industrials": "XLI", "Energy": "XLE",
    "Materials": "XLB", "Utilities": "XLU", "Real Estate": "XLRE"
}
COUNTRY_TICKERS = {
    "EAFE": "EFA", "Emerging": "EEM", "Europe": "EZU", "Japan": "EWJ", "China": "MCHI",
    "Canada": "EWC", "Brazil": "EWZ"
}
HEATMAP_TICKERS = list(set(MAJOR_TICKERS + list(SECTOR_TICKERS.values()) + list(COUNTRY_TICKERS.values())))

# List of high-profile stocks for the Movers section (simulating S&P 500)
SPX_MOVER_TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "JPM", "JNJ", 
    "V", "NVDA", "PG", "UNH", "HD", "MA", "DIS", "KO", "PFE", "T", "XOM"
]

# --------------------------------------------------------------------------------------
# --- GLOBAL HELPER FUNCTIONS ---
# --------------------------------------------------------------------------------------

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
    """Determines color and icon based on percentage percentage change."""
    if change_pct > 0.01:
        color_token = "--green-accent"
        icon = '↑'
    elif change_pct < -0.01:
        color_token = "--red-neg"
        icon = '↓'
    else:
        color_token = "--muted-text-new" 
        icon = '•'
    return f"var({color_token})", icon, f"var({color_token})"

@st.cache_data(ttl="1h")
def fetch_ticker_data(tickers):
    """Fetches the last 15 months of adjusted close prices for tickers."""
    # Ensure no duplicates in the list
    tickers = list(set(tickers)) 
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
            # Transpose to get {Ticker: {key: value}} structure
            summary = data.T.to_dict() 
        else:
            summary = {t: data.get(t, {}) for t in tickers}
        return summary
    except Exception:
        return {}


def calculate_returns(data, period):
    """Calculates returns for the given period (1D, 7D, 30D, 1Y, YTD)."""
    if data.empty: return pd.Series(dtype='float64')
    
    last_price = data.iloc[-1]
    
    # Calculate reference price based on period (logic is robust)
    if period == '1D':
        # Safely get previous close
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
            # If YTD start is same as current date, return 0.0
            return pd.Series(0.0, index=data.columns) 

    returns = ((last_price - ref_price) / ref_price) * 100

    return returns.fillna(0.0)

@st.cache_data(ttl="4h")
def generate_heatmap_data(period, tickers_list):
    all_close_data = fetch_ticker_data(tickers_list)
    if all_close_data.empty: return pd.DataFrame(), False
    
    returns = calculate_returns(all_close_data, period)
    
    data = []
    
    major_row = {"Category": "Major Indices"}
    for ticker in MAJOR_TICKERS:
        if ticker in returns: major_row[ticker] = returns[ticker]
    data.append(major_row)
    
    sector_row = {"Category": "Sector ETFs"}
    for ticker in list(SECTOR_TICKERS.values()):
        if ticker in returns: sector_row[ticker] = returns[ticker]
    data.append(sector_row)

    country_row = {"Category": "Country ETFs"}
    for ticker in list(COUNTRY_TICKERS.values()):
        if ticker in returns: country_row[ticker] = returns[ticker]
    data.append(country_row)
    
    df = pd.DataFrame(data).set_index("Category").fillna(np.nan)
    return df, True

def get_metric_html(title, price, change_pct, accent_color_token):
    """Generates the HTML for a Market KPI Card with full border/outer bounds."""
    color, icon, _ = get_metric_styles(change_pct)
    change_text = f"{icon} {abs(change_pct):.2f}%"
    
    # Using inline styles to define the outer boundary, background, and accent left border
    return dedent(f"""
        <div class="kpi" style="
             background: var(--inputlight); 
             border: 1px solid var(--neutral); 
             border-left: 5px solid {color};
             padding: 10px 14px; /* Combined padding */
             border-radius: 10px;
             box-shadow: 0 2px 5px rgba(0,0,0,0.3);
             transition: all 0.2s;
        "
             onmouseover="this.style.borderColor='var(--green-accent)';"
             onmouseout="this.style.borderColor='var(--neutral)';">
            <div class="h">{title}</div>
            <div class="v" style="color: {color};">
                {price:.2f}
            </div>
            <div class="text-sm font-semibold" style="color: {color};">{change_text}</div>
        </div>
    """)

# --- New Function for Heatmap Box Styling ---
def get_heatmap_color_style(return_val):
    """Calculates the CSS style string for a single heatmap box based on return value."""
    if pd.isna(return_val):
        # Placeholder style for missing data
        return "background-color: var(--inputlight); color: var(--muted-text-new); border: 1px dashed var(--neutral);"
    
    try:
        val = float(return_val)
    except ValueError:
        return "background-color: var(--inputlight); color: var(--muted-text-new); border: 1px dashed var(--neutral);"

    # Max saturation point (4.0% move means maximum color intensity/opacity)
    max_saturation = 4.0
    
    if val > 0:
        # Green: Scale alpha from 0.1 (low return) to 0.9 (high return)
        alpha = min(0.9, 0.1 + (val / max_saturation) * 0.8) 
        bg = f'rgba(38, 208, 124, {alpha})' 
    elif val < 0:
        # Red: Scale alpha from 0.1 (low return) to 0.9 (high return)
        alpha = min(0.9, 0.1 + (abs(val) / max_saturation) * 0.8)
        bg = f'rgba(217, 83, 79, {alpha})' 
    else:
        # Returns near zero get a light purple hue
        bg = f'rgba(138, 124, 245, 0.1)' 
        
    # Text color is always white (var(--text)) for maximum readability
    return f'background-color: {bg}; color: var(--text); border: 1px solid rgba(255,255,255,0.1);'

@st.cache_data(ttl="1h")
def get_top_movers(ticker_list, period):
    """Fetches data, calculates returns, and returns top 5 gainers/losers."""
    
    all_close_data = fetch_ticker_data(ticker_list)
    if all_close_data.empty: return pd.DataFrame(), pd.DataFrame()
    
    returns = calculate_returns(all_close_data, period).rename("Return (%)")
    
    # Get last closing price for display
    last_prices = all_close_data.iloc[-1].rename("Price ($)")
    
    # Combine returns and prices
    combined_df = pd.concat([returns, last_prices], axis=1)
    
    # Sort and slice
    top_gainers = combined_df.nlargest(5, "Return (%)")
    top_losers = combined_df.nsmallest(5, "Return (%)")
    
    return top_gainers, top_losers


# --------------------------------------------------------------------------------------
# CSS injection
# --------------------------------------------------------------------------------------
st.markdown(
    dedent(
        f"""
        <style>
        :root {{
          --bg:{BLOOM_BG}; --panel:{BLOOM_PANEL}; --text:{BLOOM_TEXT}; --muted:{BLOOM_MUTED};
          --muted-text-new: rgba(255, 255, 255, 0.75); /* Lighter grey for neutral elements */
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

        /* --- Global Text Coloring (Lighter Gray) --- */
        
        /* Header Subtitle */
        div[data-testid="stHeader"] > div:last-child > div:last-child {{
            color: var(--muted-text-new) !important;
        }}
        /* Fun Quote */
        div[data-testid="stAppViewContainer"] > div > div > div > div:nth-child(2) > div {{
            color: var(--muted-text-new) !important;
        }}
        /* KPI Subtitles */
        .kpi .h {{ 
            color: var(--muted-text-new) !important; 
        }}
        /* Market Status Text */
        .text-gray-400 {{
            color: var(--muted-text-new) !important;
        }}

        /* --- Global Text Color Application --- */
        /* Forces all primary text (st.markdown/st.header/st.subheader) to use the new BLOOM_TEXT */
        .stMarkdown, .stText, h1, h2, h3, h4, h5, h6 {{
            color: var(--text) !important;
        }}


        /* --- Sidebar Enhancements --- */
        section[data-testid="stSidebar"], aside[data-testid="stSidebar"] {{
          background: var(--sidebar-bg) !important;
          box-shadow: 4px 0 10px rgba(0,0,0,0.4);
        }}
        
        /* Sidebar Text: Lighter Grey */
        [data-testid="stSidebar"] .stMarkdown > div {{
            color: var(--muted) !important; 
        }}
        
        /* Sidebar Navigation Arrows & Links Pop (using muted-text-new for links) */
        [data-testid="stSidebarNav"] a, [data-testid="stSidebarNav"] svg {{
            color: var(--muted-text-new) !important; /* Lighter Grey for links */
            fill: var(--purple) !important;
            transition: all 0.2s;
        }}
        [data-testid="stSidebarNav"] a:hover {{
            color: var(--green-accent) !important;
        }}
        
        /* --- Strategy Navigation Card: Final Polish --- */
        /* This is the div that holds the visual content of the card */
        .strategy-link-card {{
            background: linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.00));
            border: 1px solid var(--neutral); 
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 5px 15px rgba(0,0,0,.4); 
            transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94); 
            height: 100%;
            display: flex; 
            flex-direction: column;
            justify-content: space-between;
        }}
        /* Hover effect on the card itself */
        /* Note: This class is applied via the Streamlit button's CSS hook */
        .strategy-link-card:hover {{
            border-color: var(--purple); 
            transform: translateY(-5px); 
            box-shadow: 0 15px 40px var(--card-purple-shadow); 
        }}

        /* Apply lighter grey to card description */
        .strategy-link-desc {{ color: var(--muted-text-new); font-size: 1.0rem; }} 

        .strategy-link-title {{ 
            font-weight: 800; 
            font-size: 1.5rem; 
            letter-spacing: .5px; 
            display: flex;
            align-items: center;
            gap: 15px; 
            margin-bottom: 10px;
        }}
        
        /* --- Heatmap Grid Layout --- */
        .heatmap-grid-container {{
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            padding: 15px;
            background: var(--inputlight);
            border-radius: 12px;
            box-shadow: inset 0 0 10px rgba(0,0,0,0.2);
        }}
        .heatmap-box {{
            flex-grow: 1; 
            flex-basis: 120px; /* Minimum width before wrapping */
            min-height: 80px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            border-radius: 8px;
            padding: 8px;
            font-weight: 700;
            transition: all 0.3s;
            box-shadow: 0 2px 5px rgba(0,0,0,0.3);
            cursor: default; /* Not clickable */
        }}
        .heatmap-box-ticker {{
            font-size: 1.1rem;
            font-weight: 900;
            line-height: 1.2;
            margin-bottom: 2px;
            color: var(--text); /* Always white */
        }}
        .heatmap-box-return {{
            font-size: 0.85rem;
            line-height: 1.0;
            opacity: 0.8;
            color: var(--text); /* Always white */
        }}
        /* Hover effect for boxes */
        .heatmap-box:hover {{
            transform: scale(1.03);
            opacity: 0.95;
            box-shadow: 0 5px 15px rgba(0,0,0,0.5);
        }}
        
        /* --- Top Movers List Styling --- */
        .movers-list {{
            background: var(--inputlight);
            border: 1px solid var(--neutral);
            border-radius: 12px;
            padding: 15px;
            height: 100%;
        }}
        .movers-item {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px dashed rgba(255, 255, 255, 0.1);
            font-size: 1.05rem;
        }}
        .movers-item:last-child {{
            border-bottom: none;
        }}
        .movers-ticker {{
            font-weight: 800;
            flex: 0 0 25%;
        }}
        .movers-price {{
            font-weight: 500;
            flex: 0 0 35%;
            text-align: right;
            padding-right: 15px;
            color: var(--muted-text-new);
        }}
        .movers-return {{
            font-weight: 700;
            flex: 0 0 40%;
            text-align: right;
        }}

        /* --- Strategy Link Fix CSS --- */
        /* Targets the st.page_link button container */
        [data-testid="stPageLink"] button {{
            width: 100%;
            text-align: left;
            padding: 0;
            border: none;
            background: none;
            line-height: normal; /* Fixes text spacing */
        }}
        /* Ensures the custom HTML inside the link is styled like a card */
        [data-testid="stPageLink"] button:hover .strategy-link-card {{
            border-color: var(--purple); 
            transform: translateY(-5px); 
            box-shadow: 0 15px 40px var(--card-purple-shadow); 
        }}

        </style>
        """
    ),
    unsafe_allow_html=True
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
    unsafe_allow_html=True
)

# Fun one-liner
st.markdown(
    """
    <div style="text-align:center; font-size:1.05rem; font-style:italic; color:rgba(255,255,255,0.80); margin:-4px 0 18px 0;">
      "You're either a smart-fella or fart smella" – Confucius
    </div>
    """,
    unsafe_allow_html=True
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
    st.markdown(f"""
        <div style="color: var(--muted); font-size: .85rem; padding: 10px 0;">
            <p>Session started <b>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</b></p>
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
st.markdown("### Today's Market Summary")
st.caption("Live data summary based on US market hours (EST/EDT).")

now, is_open, status_text, status_color = get_market_status()
current_time_str = now.strftime('%H:%M:%S EST')

# --- Status Display ---
st.markdown(f"""
    <div style="margin-bottom: 5px; margin-top: -10px;">
        <h4 style="font-size: 1.15rem; font-weight: 700; margin: 0; padding: 0;">Status: <span style='color: {status_color};'>{status_text}</span></h4>
    </div>
    <div style="border-top: 1px solid var(--neutral); margin-bottom: 20px;"></div>
""", unsafe_allow_html=True)


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
            <div class="kpi" style="
                 background: var(--inputlight); 
                 border: 1px solid var(--neutral); 
                 border-left: 5px solid {status_color};
                 padding: 10px 14px;
                 border-radius: 10px;
                 box-shadow: 0 2px 5px rgba(0,0,0,0.3);
                 transition: all 0.2s;
            "
             onmouseover="this.style.borderColor='var(--green-accent)';"
             onmouseout="this.style.borderColor='var(--neutral)';">
                <div class="h">Current Time</div>
                <div class="v" style="color: {status_color};">{current_time_str}</div>
                <div class="text-sm font-semibold" style="color: var(--muted-text-new);">Market Status</div>
            </div>
        """, unsafe_allow_html=True)

# Display the summary
display_market_kpis(is_open, status_text, status_color)


# --------------------------------------------------------------------------------------
# Page navigation (Final Polish)
# --------------------------------------------------------------------------------------
st.markdown("### Jump to a Strategy")

PAGE_MAPPING = {
    "Slope Convexity": {"file": "1_Slope_Convexity.py", "desc": "Advanced Momentum and Trend Analysis"},
    "Mean Reversion (draft)": {"file": "2_Mean_Reversion.py", "desc": "Z-Score-based Statistical Trading"},
}
pages_dir = Path("pages")
available = []

# --- Custom HTML rendering function for the card content ---
def get_card_html(label, desc):
    """Generates the clean card HTML structure for display inside the link."""
    return dedent(f"""
        <div class="strategy-link-card">
            <div class="strategy-link-title">{label}</div>
            <div class="strategy-link-desc">{desc}</div>
        </div>
    """)

for label, data in PAGE_MAPPING.items():
    rel_path = pages_dir / data["file"]
    if rel_path.exists():
        available.append((label, rel_path.as_posix(), data["desc"]))

if available:
    cols = st.columns(len(available))
    for i, (label, rel_path, desc) in enumerate(available):
        with cols[i]:
            # Use st.page_link with the custom HTML content as the label.
            # Streamlit handles the button placement and makes the link work.
            st.page_link(
                rel_path, 
                label=get_card_html(label, desc), # THIS IS THE VISUAL CARD CONTENT
                icon=None,
                use_container_width=True
            )
            # We don't need any complex inline CSS here because the global CSS targets 
            # the link buttons and the .strategy-link-card class directly.
            
else:
    st.info("No pages detected in `pages/` yet. Add files like `1_Slope_Convexity.py` to enable navigation.")

st.markdown("---")

# --------------------------------------------------------------------------------------
# ♨️ Market Heatmap Section
# --------------------------------------------------------------------------------------
st.markdown("### Market Return Heatmap")

return_period = st.selectbox(
    "Select Return Period", 
    options=['1D', '7D', '30D', 'YTD', '1Y'], 
    index=0, 
    key='return_period_toggle'
)

heatmap_df, data_loaded = generate_heatmap_data(return_period, HEATMAP_TICKERS)

if data_loaded and not heatmap_df.empty:
    
    # --- FLATTEN DATA STRUCTURE ---
    all_tickers_data = []
    
    major_data = heatmap_df.loc["Major Indices"].dropna()
    for ticker, ret in major_data.items():
        all_tickers_data.append({"ticker": ticker, "return": ret, "category": "Major Indices"})
    
    sector_data = heatmap_df.loc["Sector ETFs"].dropna()
    for ticker, ret in sector_data.items():
        all_tickers_data.append({"ticker": ticker, "return": ret, "category": "Sector ETFs"})

    country_data = heatmap_df.loc["Country ETFs"].dropna()
    for ticker, ret in country_data.items():
        all_tickers_data.append({"ticker": ticker, "return": ret, "category": "Country ETFs"})
    
    # --- GENERATE HTML GRID ---
    
    html_content = '<div class="heatmap-grid-container">'
    
    for item in all_tickers_data:
        ticker = item['ticker']
        ret = item['return']
        
        box_style = get_heatmap_color_style(ret)
        return_str = f"{'+' if ret > 0 else ''}{ret:.2f}%"
        
        html_content += dedent(f"""
        <div class="heatmap-box" style="{box_style}">
            <span class="heatmap-box-ticker">{ticker}</span>
            <span class="heatmap-box-return">{return_str}</span>
        </div>
        """)

    html_content += '</div>'
    
    st.markdown(html_content, unsafe_allow_html=True)
    
else:
    st.warning("Could not load market data for the heatmap. Check connectivity or try again later.")
    

st.markdown("---")

# --------------------------------------------------------------------------------------
# 📈 Top Movers Section
# --------------------------------------------------------------------------------------
st.markdown(f"### Top Movers ({return_period})")

gainer_df, loser_df = get_top_movers(SPX_MOVER_TICKERS, return_period)

col_gainers, col_losers = st.columns(2)

# --- Top Gainers ---
with col_gainers:
    st.markdown("#### Top 5 Gainers", unsafe_allow_html=True)
    if not gainer_df.empty:
        gainer_list_html = '<div class="movers-list">'
        for ticker, row in gainer_df.iterrows():
            return_str = f"+{row['Return (%)']:.2f}%"
            price_str = f"{row['Price ($)']:.2f}"
            
            gainer_list_html += dedent(f"""
                <div class="movers-item">
                    <span class="movers-ticker" style="color: var(--green-accent);">{ticker}</span>
                    <span class="movers-price">${price_str}</span>
                    <span class="movers-return" style="color: var(--green-accent);">{return_str}</span>
                </div>
            """)
        gainer_list_html += '</div>'
        st.markdown(gainer_list_html, unsafe_allow_html=True)
    else:
        st.info("No gainer data available.")

# --- Top Losers ---
with col_losers:
    st.markdown("#### Top 5 Losers", unsafe_allow_html=True)
    if not loser_df.empty:
        loser_list_html = '<div class="movers-list">'
        for ticker, row in loser_df.iterrows():
            return_str = f"{row['Return (%)']:.2f}%"
            price_str = f"{row['Price ($)']:.2f}"
            
            loser_list_html += dedent(f"""
                <div class="movers-item">
                    <span class="movers-ticker" style="color: var(--red-neg);">{ticker}</span>
                    <span class="movers-price">${price_str}</span>
                    <span class="movers-return" style="color: var(--red-neg);">{return_str}</span>
                </div>
            """)
        loser_list_html += '</div>'
        st.markdown(loser_list_html, unsafe_allow_html=True)
    else:
        st.info("No loser data available.")


st.markdown("---")
st.subheader("Tips")
st.markdown(
    """
- The **Market Summary** uses real-time or end-of-day data from `yfinance`.
- The **Market Heatmap** uses calculated returns for the selected period, with color intensity showing return magnitude.
- The **Strategy** pages (Slope Convexity, Mean Reversion) are accessible via the cards above.
"""
)
