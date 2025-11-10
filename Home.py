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

# List of all S&P 500 tickers for the Movers section
def get_spx_tickers():
    return [
        'MMM', 'AOS', 'ABT', 'ABBV', 'ACN', 'ADBE', 'AMD', 'AES', 'AFL', 'A',
        'APD', 'ABNB', 'AKAM', 'ALB', 'ARE', 'ALGN', 'ALLE', 'LNT', 'ALL', 'GOOGL',
        'GOOG', 'MO', 'AMZN', 'AMCR', 'AEE', 'AEP', 'AXP', 'AIG', 'AMT', 'AWK',
        'AMP', 'AME', 'AMGN', 'APH', 'ADI', 'AON', 'APA', 'APO', 'AAPL', 'AMAT',
        'APTV', 'ACGL', 'ADM', 'ANET', 'AJG', 'AIZ', 'T', 'ATO', 'ADSK', 'ADP',
        'AZO', 'AVB', 'AVY', 'AXON', 'BKR', 'BALL', 'BAC', 'BAX', 'BDX',
        'BBY', 'TECH', 'BIIB', 'BLK', 'BX', 'BK', 'BA', 'BKNG', 'BSX', 'BMY',
        'AVGO', 'BR', 'BRO', 'BLDR', 'BG', 'BXP', 'CHRW', 'CDNS', 'CZR',
        'CPT', 'CPB', 'COF', 'CAH', 'KMX', 'CCL', 'CARR', 'CAT', 'CBOE', 'CBRE',
        'CDW', 'COR', 'CNC', 'CNP', 'CF', 'CRL', 'SCHW', 'CHTR', 'CVX', 'CMG',
        'CB', 'CHD', 'CI', 'CINF', 'CTAS', 'CSCO', 'C', 'CFG', 'CLX', 'CME',
        'CMS', 'KO', 'CTSH', 'COIN', 'CL', 'CMCSA', 'CAG', 'COP', 'ED', 'STZ',
        'CEG', 'COO', 'CPRT', 'GLW', 'CPAY', 'CTVA', 'CSGP', 'COST', 'CTRA', 'CRWD',
        'CCI', 'CSX', 'CMI', 'CVS', 'DHR', 'DRI', 'DDOG', 'DVA', 'DAY', 'DECK',
        'DE', 'DELL', 'DAL', 'DVN', 'DXCM', 'FANG', 'DLR', 'DG', 'DLTR', 'D',
        'DPZ', 'DASH', 'DOV', 'DOW', 'DHI', 'DTE', 'DUK', 'DD', 'EMN', 'ETN',
        'EBAY', 'ECL', 'EIX', 'EW', 'EA', 'ELV', 'EMR', 'ENPH', 'ETR', 'EOG',
        'EPAM', 'EQT', 'EFX', 'EQIX', 'EQR', 'ERIE', 'ESS', 'EL', 'EG', 'EVRG',
        'ES', 'EXC', 'EXE', 'EXPE', 'EXPD', 'EXR', 'XOM', 'FFIV', 'FDS', 'FICO',
        'FAST', 'FRT', 'FDX', 'FIS', 'FITB', 'FSLR', 'FE', 'FI', 'F', 'FTNT',
        'FTV', 'FOXA', 'FOX', 'BEN', 'FCX', 'GRMN', 'IT', 'GE', 'GEHC', 'GEV',
        'GEN', 'GNRC', 'GD', 'GIS', 'GM', 'GPC', 'GILD', 'GPN', 'GL', 'GDDY',
        'GS', 'HAL', 'HIG', 'HAS', 'HCA', 'DOC', 'HSIC', 'HSY', 'HPE', 'HLT',
        'HOLX', 'HD', 'HON', 'HRL', 'HST', 'HWM', 'HPQ', 'HUBB', 'HUM', 'HBAN',
        'HII', 'IBM', 'IEX', 'IDXX', 'ITW', 'INCY', 'IR', 'PODD', 'INTC', 'IBKR',
        'ICE', 'IFF', 'IP', 'IPG', 'INTU', 'ISRG', 'IVZ', 'INVH', 'IQV', 'IRM',
        'JBHT', 'JBL', 'JKHY', 'J', 'JNJ', 'JCI', 'JPM', 'K', 'KVUE', 'KDP',
        'KEY', 'KEYS', 'KMB', 'KIM', 'KMI', 'KKR', 'KLAC', 'KHC', 'KR', 'LHX',
        'LH', 'LRCX', 'LW', 'LVS', 'LDOS', 'LEN', 'LII', 'LLY', 'LIN', 'LYV',
        'LKQ', 'LMT', 'L', 'LOW', 'LULU', 'LYB', 'MTB', 'MPC', 'MKTX', 'MAR',
        'MMC', 'MLM', 'MAS', 'MA', 'MTCH', 'MKC', 'MCD', 'MCK', 'MDT', 'MRK',
        'META', 'MET', 'MTD', 'MGM', 'MCHP', 'MU', 'MSFT', 'MAA', 'MRNA', 'MHK',
        'MOH', 'TAP', 'MDLZ', 'MPWR', 'MNST', 'MCO', 'MS', 'MOS', 'MSI', 'MSCI',
        'NDAQ', 'NTAP', 'NFLX', 'NEM', 'NWSA', 'NWS', 'NEE', 'NKE', 'NI', 'NDSN',
        'NSC', 'NTRS', 'NOC', 'NCLH', 'NRG', 'NUE', 'NVDA', 'NVR', 'NXPI', 'ORLY',
        'OXY', 'ODFL', 'OMC', 'ON', 'OKE', 'ORCL', 'OTIS', 'PCAR', 'PKG', 'PLTR',
        'PANW', 'PSKY', 'PH', 'PAYX', 'PAYC', 'PYPL', 'PNR', 'PEP', 'PFE', 'PCG',
        'PM', 'PSX', 'PNW', 'PNC', 'POOL', 'PPG', 'PPL', 'PFG', 'PG', 'PGR',
        'PLD', 'PRU', 'PEG', 'PTC', 'PSA', 'PHM', 'PWR', 'QCOM', 'DGX', 'RL',
        'RJF', 'RTX', 'O', 'REG', 'REGN', 'RF', 'RSG', 'RMD', 'RVTY', 'ROK',
        'ROL', 'ROP', 'ROST', 'RCL', 'SPGI', 'CRM', 'SBAC', 'SLB', 'STX', 'SRE',
        'NOW', 'SHW', 'SPG', 'SWKS', 'SJM', 'SW', 'SNA', 'SOLV', 'SO', 'LUV',
        'SWK', 'SBUX', 'STT', 'STLD', 'STE', 'SYK', 'SMCI', 'SYF', 'SNPS', 'SYY',
        'TMUS', 'TROW', 'TTWO', 'TPR', 'TRGP', 'TGT', 'TEL', 'TDY', 'TER', 'TSLA',
        'TXN', 'TPL', 'TXT', 'TMO', 'TJX', 'TKO', 'TTD', 'TSCO', 'TT', 'TDG',
        'TRV', 'TRMB', 'TFC', 'TYL', 'TSN', 'USB', 'UBER', 'UDR', 'ULTA', 'UNP',
        'UAL', 'UPS', 'URI', 'UNH', 'UHS', 'VLO', 'VTR', 'VLTO', 'VRSN', 'VRSK',
        'VZ', 'VRTX', 'VTRS', 'VICI', 'V', 'VST', 'VMC', 'WRB', 'GWW', 'WAB',
        'WMT', 'DIS', 'WBD', 'WM', 'WAT', 'WEC', 'WFC', 'WELL', 'WST', 'WDC',
        'WY', 'WSM', 'WMB', 'WTW', 'WDAY', 'WYNN', 'XEL', 'XYL', 'YUM', 'ZBRA',
        'ZBH', 'ZTS', 'HIMS'
    ]

SPX_MOVER_TICKERS = get_spx_tickers()

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
    
    # TTL is fixed for the Market Summary KPIs
    cache_ttl = timedelta(hours=4) 

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

    return now, is_open, status_text, status_color, cache_ttl

# --- IMPORTANT: Caching functions now run with no TTL to be manually invalidated ---

@st.cache_data(show_spinner=False)
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

@st.cache_data(show_spinner=False)
def fetch_ticker_data(tickers):
    """Fetches the last 15 months of adjusted close prices for tickers."""
    tickers = list(set(tickers)) 
    if not tickers:
        return pd.DataFrame()
    data = yf.download(tickers, period="15mo", interval="1d", progress=False, auto_adjust=True)
    if data.empty:
        return pd.DataFrame()
    return data['Close']

@st.cache_data(show_spinner=False)
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
    if data.empty: return pd.Series(dtype='float64')
    
    last_price = data.iloc[-1]
    
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

    returns = ((last_price - ref_price) / ref_price) * 100

    return returns.fillna(0.0)

@st.cache_data(show_spinner=False)
def generate_heatmap_data(period, tickers_list):
    """Generates data for the market heatmap."""
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
    """Generates the HTML for a Market KPI Card."""
    color, icon, _ = get_metric_styles(change_pct)
    change_text = f"{icon} {abs(change_pct):.2f}%"
    
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
        return "background-color: var(--inputlight); color: var(--muted-text-new); border: 1px dashed var(--neutral);"
    
    try:
        val = float(return_val)
    except ValueError:
        return "background-color: var(--inputlight); color: var(--muted-text-new); border: 1px dashed var(--neutral);"

    # Max saturation point (4.0% move means maximum color intensity/opacity)
    max_saturation = 4.0
    
    if val > 0:
        alpha = min(0.9, 0.1 + (val / max_saturation) * 0.8) 
        bg = f'rgba(38, 208, 124, {alpha})' 
    elif val < 0:
        alpha = min(0.9, 0.1 + (abs(val) / max_saturation) * 0.8)
        bg = f'rgba(217, 83, 79, {alpha})' 
    else:
        bg = f'rgba(138, 124, 245, 0.1)' 
        
    return f'background-color: {bg}; color: var(--text); border: 1px solid rgba(255,255,255,0.1);'

@st.cache_data(show_spinner=False)
def get_top_movers_uncached(ticker_list, period, scan_time):
    """
    Fetches data, calculates returns, and returns top 5 gainers/losers.
    The 'scan_time' argument is used solely to force a cache clear when the button is clicked.
    """
    
    # Use the unified caching function to fetch data for the full list
    all_close_data = fetch_ticker_data(ticker_list)
    
    if all_close_data.empty: return pd.DataFrame(), pd.DataFrame()
    
    returns = calculate_returns(all_close_data, period).rename("Return (%)")
    last_prices = all_close_data.iloc[-1].rename("Price ($)")
    
    combined_df = pd.concat([returns, last_prices], axis=1).dropna(subset=['Price ($)'])
    
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
        
        /* --- Strategy Navigation Card: Final Polish (The container the link hides behind) --- */
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
        /* This is the key to fixing the hover/click area: it targets the immediate parent div */
        div.stLinkButton {{
            position: relative !important;
            padding: 0 !important;
            margin: 0 !important;
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
        /* 1. Targets the custom card container generated by st.markdown() */
        .strategy-card-wrapper {{
            position: relative;
            padding: 0;
            margin: 0;
        }}

        /* 2. Targets the st.page_link button (the element we want to be invisible but clickable) */
        [data-testid="stPageLink"] button {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 5; /* Ensure it's above the background card */
            
            /* Make it completely invisible */
            background: transparent !important;
            border: none !important;
            color: transparent !important;
            padding: 0 !important;
            margin: 0 !important;
            cursor: pointer;
        }}
        /* 3. Re-enable the hover effect on the visible card when the invisible link is hovered */
        [data-testid="stPageLink"] button:hover + .strategy-link-card {{
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
            <p>Cache TTL: <b>{get_market_status()[4].total_seconds() / 3600:.1f} hours</b></p>
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

now, is_open, status_text, status_color, _ = get_market_status()
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
        # Use the non-cached version for live pricing for the main KPIs
        market_data = fetch_live_summary(tickers_to_fetch)
    else:
        # If market is closed, rely on the cached data to get EOD/Previous close
        market_data = fetch_live_summary(tickers_to_fetch) 
        
    def get_ticker_metric(ticker):
            # Try to get live data if available (even when closed, yfinance might have delayed data)
            if ticker in market_data:
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
            # This combination puts the link (button) and the visual card in the same relative container.
            st.markdown('<div class="strategy-card-wrapper">', unsafe_allow_html=True)
            
            # 1. The Invisible, Clickable Link (Button)
            st.page_link(
                rel_path, 
                label="", 
                icon=None,
                use_container_width=True
            )
            
            # 2. The Visible, Styled Card (Visual)
            st.markdown(get_card_html(label, desc), unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)
            
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

# NOTE: Heatmap generation is still cached, but it relies on data fetched via a function 
# that is now manually invalidated by the Movers button.

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
# 📈 Top Movers Section (Manually Triggered)
# --------------------------------------------------------------------------------------
st.markdown(f"### Top Movers (S&P 500 Scan)")

# Initialize movers_run timestamp if it doesn't exist
if 'movers_run' not in st.session_state:
    st.session_state['movers_run'] = datetime.min
    # Initialize movers data to empty frames to avoid initial errors
    st.session_state['gainer_df'] = pd.DataFrame()
    st.session_state['loser_df'] = pd.DataFrame()


# Place button and status in the same row
col_btn, col_status = st.columns([1, 1.5])

with col_btn:
    # Check if the button was clicked
    run_clicked = st.button("Run S&P 500 Scan", type="primary", use_container_width=True, 
                            help="Fetch and analyze the latest data for all 496 S&P 500 tickers.")

with col_status:
    st.markdown(f"""
        <div style="font-size: .85rem; color: var(--muted-text-new); margin-top: 10px; text-align: right;">
            Last Scan Time: {st.session_state['movers_run'].strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    """, unsafe_allow_html=True)


# --- Run Logic ---
if run_clicked:
    # 1. Force clear cache and update timestamp
    fetch_ticker_data.clear()
    get_top_movers_uncached.clear() 
    st.session_state['movers_run'] = datetime.now()
    
    # 2. Display loading spinner and perform heavy calculation
    with st.spinner(f"Scanning {len(SPX_MOVER_TICKERS)} tickers for {return_period} returns..."):
        gainer_df, loser_df = get_top_movers_uncached(SPX_MOVER_TICKERS, return_period, st.session_state['movers_run'])
        
        # 3. Store results in session state
        st.session_state['gainer_df'] = gainer_df
        st.session_state['loser_df'] = loser_df

    st.toast("S&P 500 scan complete!", icon="✅")
    
# Retrieve results from state for display
gainer_df = st.session_state['gainer_df']
loser_df = st.session_state['loser_df']

# --- Display Results ---
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
        st.info("Click 'Run S&P 500 Scan' to fetch data.")

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
        st.info("Click 'Run S&P 500 Scan' to fetch data.")

st.markdown("---")
st.subheader("Tips")
st.markdown(
    """
- The **Run S&P 500 Scan** button manually fetches the latest data for all 496 stocks and updates the movers list.
- The **Market Summary** and **Heatmap** are still semi-cached but will use the fresh underlying data once the scan is run.
"""
)
