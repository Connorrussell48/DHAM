import numpy as np
import pandas as pd
import yfinance as yf
import streamlit as st
import plotly.graph_objects as go
from datetime import date, datetime
import json
import os

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="Slope & Convexity Strategy",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================================
# THEME & STYLING
# ============================================================================
st.markdown("""
<style>
/* Dark theme with purple gradient background */
:root {
    --bg-dark: #0B0F14;
    --bg-panel: #121820;
    --text: #FFFFFF;
    --text-muted: rgba(255,255,255,0.70);
    --accent-green: #26D07C;
    --accent-red: #D9534F;
    --neutral: #4A5B6E;
    --input-bg: #2E3A46;
    --shadow: 0 4px 6px rgba(0,0,0,0.1);
}

html, body {
    height: 100%;
    background: linear-gradient(135deg, var(--bg-dark) 0%, #3A2A6A 100%) fixed !important;
}

.stApp {
    background: transparent !important;
    color: var(--text);
}

.block-container {
    max-width: 1600px;
    padding-top: 2rem;
    padding-bottom: 2rem;
}

/* Headers */
h1, h2, h3 {
    color: var(--text) !important;
    font-weight: 700;
}

h1 {
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
}

h2 {
    font-size: 1.8rem;
    margin-top: 2rem;
    margin-bottom: 1rem;
}

h3 {
    font-size: 1.3rem;
    margin-top: 1.5rem;
    margin-bottom: 0.8rem;
}

/* Input fields */
input, textarea, select {
    background: var(--input-bg) !important;
    color: var(--text) !important;
    border: 1px solid var(--neutral) !important;
    border-radius: 8px !important;
}

/* Select boxes */
[data-baseweb="select"] > div {
    background: var(--input-bg) !important;
    border-color: var(--neutral) !important;
    color: var(--text) !important;
}

[data-baseweb="select"] svg {
    fill: var(--text) !important;
}

/* Buttons */
.stButton > button {
    background: var(--input-bg) !important;
    color: var(--text) !important;
    border: 1px solid var(--neutral) !important;
    border-radius: 10px !important;
    box-shadow: var(--shadow) !important;
    font-weight: 600;
    padding: 0.5rem 1.5rem;
}

.stButton > button:hover {
    border-color: var(--accent-green) !important;
    transform: translateY(-1px);
}

.stDownloadButton > button {
    background: var(--accent-green) !important;
    color: #000 !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700;
    padding: 0.6rem 1.8rem;
}

/* Dataframes */
[data-testid="stDataFrame"] {
    background: var(--input-bg) !important;
    border-radius: 12px;
    overflow: hidden;
}

/* Expanders */
[data-testid="stExpander"] {
    background: rgba(18, 24, 32, 0.6) !important;
    border: 1px solid var(--neutral) !important;
    border-radius: 12px;
    margin-bottom: 1rem;
}

[data-testid="stExpander"] summary {
    color: var(--text) !important;
    font-weight: 700;
    font-size: 1.1rem;
}

/* Metric cards */
[data-testid="stMetric"] {
    background: rgba(255, 255, 255, 0.95) !important;
    color: #0B0F14 !important;
    border: 1px solid var(--neutral) !important;
    border-radius: 12px !important;
    padding: 16px !important;
    box-shadow: var(--shadow) !important;
}

[data-testid="stMetric"] * {
    color: #0B0F14 !important;
}

[data-testid="stMetric"] label {
    font-size: 0.9rem;
    font-weight: 600;
}

[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-size: 1.8rem;
    font-weight: 800;
}

/* Form containers */
.stForm {
    background: rgba(18, 24, 32, 0.4);
    border: 1px solid var(--neutral);
    border-radius: 12px;
    padding: 1.5rem;
}

/* Hide fullscreen buttons */
button[title="View fullscreen"] {
    display: none !important;
}

/* Transparent matplotlib backgrounds */
.element-container:has(canvas) {
    background: transparent !important;
}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# CONSTANTS & CONFIGURATION
# ============================================================================
WATCHLIST_PATH = "watchlist.json"
SECTOR_MAP_PATH = "sector_map.json"

# Default S&P 500 constituents with sectors
DEFAULT_TICKERS = {
    "AAPL": "Technology", "MSFT": "Technology", "GOOGL": "Communication Services",
    "AMZN": "Consumer Discretionary", "NVDA": "Technology", "META": "Communication Services",
    "TSLA": "Consumer Discretionary", "BRK.B": "Financials", "V": "Financials",
    "JNJ": "Health Care", "WMT": "Consumer Staples", "JPM": "Financials",
    "MA": "Financials", "PG": "Consumer Staples", "UNH": "Health Care",
    "HD": "Consumer Discretionary", "DIS": "Communication Services", "BAC": "Financials",
    "ADBE": "Technology", "CRM": "Technology", "NFLX": "Communication Services",
    "CMCSA": "Communication Services", "XOM": "Energy", "PFE": "Health Care",
    "CVX": "Energy", "COST": "Consumer Staples", "ABBV": "Health Care",
    "TMO": "Health Care", "ACN": "Information Technology", "MRK": "Health Care",
    "NKE": "Consumer Discretionary", "CSCO": "Technology", "PEP": "Consumer Staples",
    "LLY": "Health Care", "AVGO": "Technology", "TXN": "Technology",
    "QCOM": "Technology", "DHR": "Health Care", "HON": "Industrials",
    "UNP": "Industrials", "NEE": "Utilities", "BMY": "Health Care",
    "ORCL": "Technology", "LOW": "Consumer Discretionary", "UPS": "Industrials",
    "MS": "Financials", "IBM": "Technology", "BA": "Industrials",
    "INTC": "Technology", "AMD": "Technology", "CAT": "Industrials",
    "GE": "Industrials", "DE": "Industrials", "MMM": "Industrials"
}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================
@st.cache_data(ttl=3600, show_spinner=False)
def load_sector_map():
    """Load or create sector mapping"""
    if os.path.exists(SECTOR_MAP_PATH):
        with open(SECTOR_MAP_PATH, "r") as f:
            return json.load(f)
    return DEFAULT_TICKERS.copy()

def save_sector_map(sector_map):
    """Save sector mapping to disk"""
    with open(SECTOR_MAP_PATH, "w") as f:
        json.dump(sector_map, f, indent=2)

def load_watchlist():
    """Load watchlist from disk"""
    if os.path.exists(WATCHLIST_PATH):
        with open(WATCHLIST_PATH, "r") as f:
            return json.load(f)
    return []

def save_watchlist(watchlist):
    """Save watchlist to disk"""
    with open(WATCHLIST_PATH, "w") as f:
        json.dump(watchlist, f, indent=2)

def sync_watchlist_sectors(watchlist, sector_map):
    """Update sector map with any new tickers from watchlist"""
    for item in watchlist:
        ticker = item.get("Ticker", "").upper()
        if ticker and ticker not in sector_map:
            sector_map[ticker] = "Unknown"
    save_sector_map(sector_map)
    return sector_map

@st.cache_data(ttl=300, show_spinner=False)
def fetch_price_data(ticker, lookback_days=60):
    """Fetch historical price data for a ticker"""
    try:
        end_date = date.today()
        stock = yf.Ticker(ticker)
        
        # Try different intervals
        for interval, period in [("1d", f"{lookback_days}d"), ("1h", "60d"), 
                                  ("30m", "60d"), ("15m", "60d"), ("5m", "60d")]:
            try:
                df = stock.history(period=period, interval=interval)
                if not df.empty:
                    return df
            except:
                continue
        return pd.DataFrame()
    except:
        return pd.DataFrame()

def calculate_ma_slope_convexity(prices, window=200):
    """
    Calculate moving average, slope (1st derivative), and convexity (2nd derivative)
    
    Returns: (ma, slope, convexity) all as pandas Series
    """
    if len(prices) < window:
        return None, None, None
    
    # Calculate 200-period moving average
    ma = prices.rolling(window=window, min_periods=window).mean()
    
    # First derivative (slope): difference between consecutive MA values
    slope = ma.diff()
    
    # Second derivative (convexity): difference between consecutive slopes
    convexity = slope.diff()
    
    return ma, slope, convexity

def detect_signals(df, ma_window=200):
    """
    Detect bullish/bearish signals based on slope and convexity
    
    Signal occurs when:
    - Bullish: Both slope > 0 AND convexity > 0 (accelerating uptrend)
    - Bearish: Both slope < 0 AND convexity < 0 (accelerating downtrend)
    """
    if df is None or df.empty or len(df) < ma_window:
        return pd.DataFrame()
    
    prices = df['Close']
    ma, slope, convexity = calculate_ma_slope_convexity(prices, window=ma_window)
    
    if ma is None:
        return pd.DataFrame()
    
    # Detect when both turn positive (bullish) or both turn negative (bearish)
    bullish_signal = (slope > 0) & (convexity > 0) & (slope.shift(1) <= 0) | (convexity.shift(1) <= 0)
    bearish_signal = (slope < 0) & (convexity < 0) & (slope.shift(1) >= 0) | (convexity.shift(1) >= 0)
    
    signals = pd.DataFrame(index=df.index)
    signals['Sentiment'] = 'Neutral'
    signals.loc[bullish_signal, 'Sentiment'] = 'Bullish'
    signals.loc[bearish_signal, 'Sentiment'] = 'Bearish'
    
    # Only return rows with actual signals
    signals = signals[signals['Sentiment'] != 'Neutral']
    
    return signals

def run_scan(tickers, sector_map, lookback_days, ma_window, timeframes, selected_sectors):
    """
    Run the slope/convexity scan across all tickers and timeframes
    """
    all_results = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_scans = len(tickers) * len(timeframes)
    completed = 0
    
    for ticker in tickers:
        sector = sector_map.get(ticker, "Unknown")
        
        # Skip if sector not selected
        if selected_sectors and sector not in selected_sectors:
            completed += len(timeframes)
            continue
        
        for timeframe in timeframes:
            status_text.text(f"Scanning {ticker} ({timeframe})...")
            
            # Fetch data
            df = fetch_price_data(ticker, lookback_days)
            
            if not df.empty:
                # Detect signals
                signals = detect_signals(df, ma_window=ma_window)
                
                # Add to results
                for idx, row in signals.iterrows():
                    all_results.append({
                        'Ticker': ticker,
                        'Sector': sector,
                        'Timeframe': timeframe,
                        'Date': idx.strftime('%Y-%m-%d'),
                        'Time (EST)': idx.strftime('%H:%M:%S'),
                        'Sentiment': row['Sentiment'],
                        'Timestamp': idx
                    })
            
            completed += 1
            progress_bar.progress(completed / total_scans)
    
    progress_bar.empty()
    status_text.empty()
    
    if all_results:
        return pd.DataFrame(all_results).sort_values('Timestamp', ascending=False)
    return pd.DataFrame()

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================
if 'watchlist' not in st.session_state:
    st.session_state['watchlist'] = load_watchlist()

if 'sector_map' not in st.session_state:
    st.session_state['sector_map'] = load_sector_map()

if 'scan_results' not in st.session_state:
    st.session_state['scan_results'] = None

# Sync watchlist with sector map
st.session_state['sector_map'] = sync_watchlist_sectors(
    st.session_state['watchlist'],
    st.session_state['sector_map']
)

# ============================================================================
# PAGE HEADER
# ============================================================================
st.title("📊 Slope & Convexity Strategy")
st.markdown("""
Scan for momentum signals based on 200-period moving average **slope** (direction) 
and **convexity** (acceleration). Signals occur when both indicators turn bullish or bearish simultaneously.
""")

st.markdown("---")

# ============================================================================
# CONFIGURATION SECTION
# ============================================================================
st.markdown("## ⚙️ Scan Configuration")

config_col1, config_col2, config_col3 = st.columns(3)

with config_col1:
    lookback_days = st.slider(
        "Lookback Period (days)",
        min_value=30,
        max_value=200,
        value=60,
        step=10,
        help="Number of days of historical data to analyze"
    )

with config_col2:
    ma_window = st.number_input(
        "MA Window",
        min_value=50,
        max_value=300,
        value=200,
        step=10,
        help="Moving average period for slope/convexity calculation"
    )

with config_col3:
    all_timeframes = ["5m", "15m", "30m", "1h", "1d"]
    selected_timeframes = st.multiselect(
        "Timeframes",
        options=all_timeframes,
        default=["1d"],
        help="Select which timeframes to scan"
    )

# Sector filter
all_sectors = sorted(set(st.session_state['sector_map'].values()))
selected_sectors = st.multiselect(
    "Filter by Sector (leave empty for all)",
    options=all_sectors,
    default=[],
    help="Select specific sectors to scan, or leave empty to scan all"
)

# Get tickers to scan
scan_tickers = list(st.session_state['sector_map'].keys())
watchlist_tickers = [item['Ticker'] for item in st.session_state['watchlist'] if item.get('Ticker')]

# Run scan button
col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 4])
with col_btn1:
    run_scan_btn = st.button("🚀 Run Scan", type="primary", use_container_width=True)
with col_btn2:
    if st.session_state['scan_results'] is not None:
        if st.button("🔄 Clear Results", use_container_width=True):
            st.session_state['scan_results'] = None
            st.rerun()

if run_scan_btn:
    if not selected_timeframes:
        st.error("Please select at least one timeframe")
    else:
        with st.spinner("Running scan..."):
            results = run_scan(
                tickers=scan_tickers,
                sector_map=st.session_state['sector_map'],
                lookback_days=lookback_days,
                ma_window=ma_window,
                timeframes=selected_timeframes,
                selected_sectors=selected_sectors
            )
            st.session_state['scan_results'] = results
            st.success(f"✅ Scan complete! Found {len(results)} signals")
            st.rerun()

st.markdown("---")

# ============================================================================
# RESULTS SECTION
# ============================================================================
if st.session_state['scan_results'] is not None and not st.session_state['scan_results'].empty:
    results = st.session_state['scan_results']
    
    # Summary metrics
    st.markdown("## 📈 Summary")
    
    total_signals = len(results)
    bullish_count = len(results[results['Sentiment'] == 'Bullish'])
    bearish_count = len(results[results['Sentiment'] == 'Bearish'])
    
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    
    with metric_col1:
        st.metric("Total Signals", total_signals)
    
    with metric_col2:
        st.metric("Bullish", bullish_count, 
                  delta=f"{100*bullish_count/total_signals:.0f}%" if total_signals > 0 else "0%")
    
    with metric_col3:
        st.metric("Bearish", bearish_count,
                  delta=f"{100*bearish_count/total_signals:.0f}%" if total_signals > 0 else "0%",
                  delta_color="inverse")
    
    with metric_col4:
        unique_tickers = results['Ticker'].nunique()
        st.metric("Unique Tickers", unique_tickers)
    
    # Pie chart visualization
    st.markdown("### Overall Distribution")
    
    # Create Plotly pie chart
    colors = ['#26D07C', '#D9534F']  # Green for bullish, red for bearish
    
    fig = go.Figure(data=[go.Pie(
        labels=['Bullish', 'Bearish'],
        values=[bullish_count, bearish_count],
        marker=dict(colors=colors),
        textinfo='label+percent',
        textfont=dict(size=16, color='white'),
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>',
        hole=0.0
    )])
    
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#FFFFFF', size=14),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.1,
            xanchor="center",
            x=0.5,
            font=dict(size=14, color='#FFFFFF')
        ),
        height=400,
        margin=dict(l=20, r=20, t=20, b=60)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Sector breakdown
    st.markdown("### Breakdown by Sector")
    
    sector_sentiment = results.groupby(['Sector', 'Sentiment']).size().unstack(fill_value=0)
    sector_sentiment = sector_sentiment.reindex(columns=['Bullish', 'Bearish'], fill_value=0)
    
    for sector in sector_sentiment.index:
        with st.expander(f"**{sector}**", expanded=False):
            bull = int(sector_sentiment.loc[sector, 'Bullish'])
            bear = int(sector_sentiment.loc[sector, 'Bearish'])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Bullish", bull)
            with col2:
                st.metric("Bearish", bear)
            with col3:
                st.metric("Total", bull + bear)
            
            # Sector-specific data
            sector_data = results[results['Sector'] == sector]
            st.dataframe(
                sector_data[['Ticker', 'Timeframe', 'Date', 'Time (EST)', 'Sentiment']],
                use_container_width=True,
                hide_index=True,
                height=300
            )
    
    # Full results table
    st.markdown("### All Signals")
    
    display_results = results[['Ticker', 'Sector', 'Timeframe', 'Date', 'Time (EST)', 'Sentiment']].copy()
    
    st.dataframe(
        display_results,
        use_container_width=True,
        hide_index=True,
        height=600,
        column_config={
            "Ticker": st.column_config.TextColumn(width="small"),
            "Sector": st.column_config.TextColumn(width="medium"),
            "Timeframe": st.column_config.TextColumn(width="small"),
            "Date": st.column_config.TextColumn(width="medium"),
            "Time (EST)": st.column_config.TextColumn(width="small"),
            "Sentiment": st.column_config.TextColumn(width="medium"),
        }
    )
    
    # Download button
    csv_data = display_results.to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 Download Results CSV",
        csv_data,
        file_name=f"slope_convexity_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

else:
    st.info("👆 Configure your scan settings above and click **Run Scan** to begin")

st.markdown("---")

# ============================================================================
# WATCHLIST SECTION
# ============================================================================
st.markdown("## 📓 Watchlist Manager")

# Add to watchlist form
with st.form("add_watchlist", clear_on_submit=True):
    st.markdown("### Add Ticker")
    
    form_col1, form_col2, form_col3, form_col4 = st.columns([2, 2, 2, 1])
    
    with form_col1:
        new_ticker = st.text_input("Ticker", placeholder="e.g., NVDA").upper().strip()
    
    with form_col2:
        new_rating = st.selectbox("Rating", ["Bullish", "Neutral", "Bearish"])
    
    with form_col3:
        new_timeframe = st.selectbox("Timeframe", ["5m", "15m", "30m", "1h", "1d"])
    
    with form_col4:
        st.markdown("<br>", unsafe_allow_html=True)
        add_btn = st.form_submit_button("➕ Add", use_container_width=True)

if add_btn and new_ticker:
    st.session_state['watchlist'].append({
        "Ticker": new_ticker,
        "Rating": new_rating,
        "Timeframe": new_timeframe
    })
    save_watchlist(st.session_state['watchlist'])
    
    # Update sector map if new ticker
    if new_ticker not in st.session_state['sector_map']:
        st.session_state['sector_map'][new_ticker] = "Unknown"
        save_sector_map(st.session_state['sector_map'])
    
    st.success(f"✅ Added {new_ticker} to watchlist")
    st.rerun()

# Display watchlist
if st.session_state['watchlist']:
    st.markdown("### Current Watchlist")
    
    watchlist_df = pd.DataFrame(st.session_state['watchlist'])
    
    edited_watchlist = st.data_editor(
        watchlist_df,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        column_config={
            "Ticker": st.column_config.TextColumn(width="medium"),
            "Rating": st.column_config.SelectboxColumn(
                options=["Bullish", "Neutral", "Bearish"],
                width="medium"
            ),
            "Timeframe": st.column_config.SelectboxColumn(
                options=["5m", "15m", "30m", "1h", "1d"],
                width="medium"
            ),
        },
        height=400
    )
    
    # Save edits
    if not edited_watchlist.equals(watchlist_df):
        st.session_state['watchlist'] = edited_watchlist.to_dict(orient="records")
        save_watchlist(st.session_state['watchlist'])
        st.rerun()
    
    # Delete functionality
    st.markdown("### Remove Tickers")
    
    delete_col1, delete_col2, delete_col3 = st.columns([3, 2, 2])
    
    with delete_col1:
        existing_tickers = sorted({item['Ticker'] for item in st.session_state['watchlist']})
        ticker_to_delete = st.selectbox(
            "Select ticker to delete",
            options=existing_tickers if existing_tickers else ["(none)"]
        )
    
    with delete_col2:
        if st.button("🗑️ Delete Selected", use_container_width=True):
            if ticker_to_delete and ticker_to_delete != "(none)":
                st.session_state['watchlist'] = [
                    item for item in st.session_state['watchlist'] 
                    if item['Ticker'] != ticker_to_delete
                ]
                save_watchlist(st.session_state['watchlist'])
                st.success(f"Deleted {ticker_to_delete}")
                st.rerun()
    
    with delete_col3:
        if st.button("🗑️ Clear All", use_container_width=True):
            st.session_state['watchlist'] = []
            save_watchlist(st.session_state['watchlist'])
            st.success("Watchlist cleared")
            st.rerun()

else:
    st.info("No items in watchlist. Add a ticker above to get started.")
