# 5_Seasonality.py - Seasonality Analysis Dashboard
from __future__ import annotations
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from textwrap import dedent
import yfinance as yf
import plotly.graph_objects as go

# --------------------------------------------------------------------------------------
# Page setup
# --------------------------------------------------------------------------------------
st.set_page_config(
    page_title="Seasonality - D-HAM",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------------------
# Theme / CSS
# --------------------------------------------------------------------------------------
BLOOM_BG       = "#0B0F14"    
BLOOM_PANEL    = "#121820"    
BLOOM_TEXT     = "#FFFFFF"
BLOOM_MUTED    = "rgba(255,255,255,0.45)"
NEUTRAL_GRAY   = "#4A5B6E"    
INPUT_BG       = "#2E3A46"    
INPUT_BG_LIGHT = "#3A4654"    
ACCENT_BLUE    = "#2BB3F3"    
ACCENT_GREEN   = "#26D07C"    
ACCENT_PURPLE  = "#8A7CF5"    
DARK_PURPLE    = "#3A2A6A"

st.markdown(
    f"""
    <style>
    :root {{
      --bg:{BLOOM_BG}; --panel:{BLOOM_PANEL}; --text:{BLOOM_TEXT}; --muted:{BLOOM_MUTED};
      --muted-text-new: rgba(255, 255, 255, 0.75);
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

    div[data-testid="stHeader"] > div:last-child > div:last-child {{
        color: var(--muted-text-new) !important;
    }}
    div[data-testid="stAppViewContainer"] > div > div > div > div:nth-child(2) > div {{
        color: var(--muted-text-new) !important;
    }}
    .kpi .h {{ 
        color: var(--muted-text-new) !important; 
    }}
    .text-gray-400 {{
        color: var(--muted-text-new) !important;
    }}
    
    div[data-testid="stAppViewContainer"] label {{
        color: var(--text) !important;
        font-weight: 600;
    }}

    .stMarkdown, .stText, h1, h2, h3, h4, h5, h6 {{
        color: var(--text) !important;
    }}

    section[data-testid="stSidebar"], aside[data-testid="stSidebar"] {{
      background: var(--sidebar-bg) !important;
      box-shadow: 4px 0 10px rgba(0,0,0,0.4);
    }}
    
    [data-testid="stSidebar"] .stMarkdown > div {{
        color: var(--muted) !important; 
    }}
    
    [data-testid="stSidebarNav"] a, [data-testid="stSidebarNav"] svg {{
        color: var(--text) !important;
        fill: var(--text) !important;
        transition: all 0.2s;
    }}
    [data-testid="stSidebarNav"] a:hover {{
        color: var(--green-accent) !important;
    }}
    
    /* Make sidebar navigation links text white */
    [data-testid="stSidebarNav"] li a span {{
        color: var(--text) !important;
    }}
    [data-testid="stSidebarNav"] li a:hover span {{
        color: var(--green-accent) !important;
    }}
    [data-testid="stSidebarNav"] ul li {{
        color: var(--text) !important;
    }}
    
    /* Buttons */
    .stButton > button {{
        background: var(--input) !important;
        color: var(--text) !important;
        border: 1px solid var(--neutral) !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 10px 16px !important;
        transition: all 0.2s !important;
        width: 100% !important;
    }}
    .stButton > button:hover {{
        background: var(--inputlight) !important;
        border-color: var(--purple) !important;
        color: var(--purple) !important;
    }}
    .stButton > button p {{
        color: var(--text) !important;
        margin: 0 !important;
    }}
    .stButton > button:hover p {{
        color: var(--purple) !important;
    }}
    
    /* Expander styling */
    div[data-testid="stExpander"] {{
        background: var(--inputlight) !important;
        border: 1px solid var(--neutral) !important;
        border-radius: 8px !important;
    }}
    div[data-testid="stExpander"] details {{
        background: var(--inputlight) !important;
    }}
    div[data-testid="stExpander"] summary {{
        background: var(--inputlight) !important;
        color: var(--text) !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --------------------------------------------------------------------------------------
# Page Header
# --------------------------------------------------------------------------------------
st.markdown(f"""
    <h1 style="color: var(--purple); margin-bottom: 5px;">Seasonality Analysis</h1>
    <p style="color: var(--muted-text-new); font-size: 0.95rem; margin-top: 0;">
        Historical seasonal patterns in S&P 500 returns
    </p>
""", unsafe_allow_html=True)

st.markdown("---")

# --------------------------------------------------------------------------------------
# Data Fetching Functions (CSV-based with auto-update)
# --------------------------------------------------------------------------------------

@st.cache_data(ttl=3600, show_spinner=False)  # Cache for 1 hour
def load_and_update_sp500_data():
    """
    Loads S&P 500 data from CSV and updates with latest data if needed.
    This function:
    1. Loads historical data from CSV (fast)
    2. Checks if today's data is missing
    3. Fetches only recent data if needed (efficient)
    4. Appends new data in memory (works with read-only GitHub files)
    5. Returns complete dataset
    
    Note: When deployed, CSV in GitHub is read-only. Updates are kept in memory
    and cached. To permanently update the CSV, run update_sp500_data.py locally
    or use GitHub Actions.
    """
    import os
    import pytz
    
    # Path to CSV file in GitHub repo
    csv_path = "data/sp500_daily_full_history.csv"
    
    # Try to load existing CSV
    try:
        if os.path.exists(csv_path):
            # Load CSV with custom date parsing for 2-digit years
            # Format: mm/dd/yy where yy < 70 = 20xx, yy >= 70 = 19xx
            df = pd.read_csv(csv_path)
            
            # Parse dates manually to handle 2-digit years correctly
            def parse_date(date_str):
                try:
                    # Try parsing as-is first
                    parsed = pd.to_datetime(date_str)
                    # If year is > 2030, it's probably 19xx not 20xx
                    if parsed.year > 2030:
                        # Subtract 100 years
                        parsed = parsed - pd.DateOffset(years=100)
                    return parsed
                except:
                    return pd.NaT
            
            df['Date'] = df['Date'].apply(parse_date)
            df = df.set_index('Date')
            df = df.dropna()  # Remove any rows with bad dates
            df = df.sort_index()  # Ensure chronological order
            
            # Ensure timezone-naive for comparison
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)
            last_date_in_csv = df.index[-1].strftime('%Y-%m-%d')
            st.success(f"Loaded {len(df):,} days from CSV (through {last_date_in_csv})")
        else:
            st.warning(f"CSV not found at {csv_path}. Fetching full history from Yahoo Finance...")
            df = pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading CSV: {str(e)}")
        df = pd.DataFrame()
    
    # Check if we need to update with recent data
    needs_update = False
    if not df.empty:
        last_date = df.index[-1]
        # Make sure last_date is timezone-naive
        if hasattr(last_date, 'tz') and last_date.tz is not None:
            last_date = last_date.tz_localize(None)
        
        # Get current time in ET (market timezone)
        et_tz = pytz.timezone('America/New_York')
        now_et = datetime.now(et_tz)
        today = now_et.date()
        
        # Markets are open Mon-Fri, close at 4 PM ET
        is_weekday = now_et.weekday() < 5  # 0=Mon, 4=Fri
        market_close_time = now_et.replace(hour=16, minute=0, second=0, microsecond=0)
        is_after_close = now_et >= market_close_time
        
        # Determine what date we should have data through
        if is_weekday and is_after_close:
            # It's a weekday after close - should have today's data
            expected_last_date = today
        elif is_weekday and not is_after_close:
            # It's a weekday before close - should have yesterday's data
            expected_last_date = (now_et - timedelta(days=1)).date()
        else:
            # It's a weekend - should have Friday's data
            days_back = now_et.weekday() - 4  # Days since Friday
            expected_last_date = (now_et - timedelta(days=days_back)).date()
        
        # Check if we're missing data
        if last_date.date() < expected_last_date:
            days_behind = (expected_last_date - last_date.date()).days
            needs_update = True
            st.info(f"Data is {days_behind} day(s) behind. Fetching updates from Yahoo Finance...")
    else:
        needs_update = True
        st.info("No local CSV found. Fetching complete S&P 500 history...")
    
    # Fetch recent data if needed
    if needs_update:
        try:
            sp500 = yf.Ticker("^GSPC")
            
            if df.empty:
                # Fetch full history if CSV doesn't exist
                new_data = sp500.history(period="max", auto_adjust=False)
            else:
                # Fetch only recent data (more efficient)
                start_date = (last_date + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
                new_data = sp500.history(start=start_date, auto_adjust=False)
            
            # Make sure new_data index is timezone-naive
            if not new_data.empty and new_data.index.tz is not None:
                new_data.index = new_data.index.tz_localize(None)
            
            if not new_data.empty:
                # Combine with existing data
                if df.empty:
                    df = new_data
                    st.success(f"Downloaded {len(df):,} days of S&P 500 history")
                else:
                    df = pd.concat([df, new_data])
                    df = df[~df.index.duplicated(keep='last')]  # Remove any duplicates
                    df = df.sort_index()  # Ensure chronological order
                    st.success(f"Added {len(new_data)} new day(s) to dataset (in memory)")
                
                # Try to save updated data back to CSV (works locally, not on deployed apps)
                try:
                    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
                    df.to_csv(csv_path)
                    st.success(f"Updated CSV file: {csv_path}")
                except (PermissionError, OSError) as e:
                    # Expected on deployed apps - CSV is read-only
                    st.info(f"Updates cached in memory (CSV is read-only in deployment)")
                    st.caption("To permanently update CSV: Run update_sp500_data.py locally or use GitHub Actions")
            else:
                st.info("No new data available (markets closed or data is current)")
                
        except Exception as e:
            st.error(f"Error fetching updates from Yahoo Finance: {str(e)}")
            if df.empty:
                return pd.DataFrame()
    
    # Process the data
    if not df.empty:
        # Ensure index is timezone-naive DatetimeIndex
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        
        # Use Adj Close if available, otherwise Close
        if 'Adj Close' in df.columns:
            df['Price'] = df['Adj Close']
        elif 'Close' in df.columns:
            df['Price'] = df['Close']
        else:
            st.error("CSV must contain 'Close' or 'Adj Close' column")
            return pd.DataFrame()
        
        # Calculate daily returns
        df['Returns'] = df['Price'].pct_change() * 100
        
        # Add time-based columns
        df['Year'] = df.index.year
        df['Month'] = df.index.month
        df['MonthName'] = df.index.strftime('%B')
        df['Week'] = df.index.isocalendar().week
        df['DayOfWeek'] = df.index.dayofweek  # Monday=0, Sunday=6
        df['DayName'] = df.index.strftime('%A')
        df['Quarter'] = df.index.quarter
        
        return df
    
    return pd.DataFrame()

@st.cache_data(ttl=3600, show_spinner=False)
def calculate_monthly_seasonality(df):
    """Calculate average returns by month using actual monthly returns."""
    if df.empty:
        return pd.DataFrame()
    
    # Create a copy to avoid modifying original
    df_copy = df.copy()
    
    # Group by Year and Month to get first and last price of each month
    df_copy['Year'] = df_copy.index.year
    df_copy['Month'] = df_copy.index.month
    
    # Calculate monthly returns: (last price of month - first price of month) / first price of month
    monthly_returns = []
    
    for (year, month), group in df_copy.groupby(['Year', 'Month']):
        if len(group) > 0:
            first_price = group['Price'].iloc[0]
            last_price = group['Price'].iloc[-1]
            monthly_return = ((last_price - first_price) / first_price) * 100
            monthly_returns.append({
                'Year': year,
                'Month': month,
                'Return': monthly_return
            })
    
    monthly_df = pd.DataFrame(monthly_returns)
    
    # Now calculate statistics by month (aggregating across all years)
    monthly_stats = monthly_df.groupby('Month')['Return'].agg([
        ('Mean Return', 'mean'),
        ('Median Return', 'median'),
        ('Std Dev', 'std'),
        ('Win Rate', lambda x: (x > 0).sum() / len(x) * 100),
        ('Count', 'count')
    ]).reset_index()
    
    # Add month names
    month_names = {1: 'January', 2: 'February', 3: 'March', 4: 'April', 
                   5: 'May', 6: 'June', 7: 'July', 8: 'August',
                   9: 'September', 10: 'October', 11: 'November', 12: 'December'}
    monthly_stats['Month Name'] = monthly_stats['Month'].map(month_names)
    
    return monthly_stats

@st.cache_data(ttl=3600, show_spinner=False)
def calculate_weekly_seasonality(df):
    """Calculate average returns by day of week."""
    if df.empty:
        return pd.DataFrame()
    
    weekly_stats = df.groupby('DayOfWeek')['Returns'].agg([
        ('Mean Return', 'mean'),
        ('Median Return', 'median'),
        ('Std Dev', 'std'),
        ('Win Rate', lambda x: (x > 0).sum() / len(x) * 100),
        ('Count', 'count')
    ]).reset_index()
    
    # Add day names
    day_names = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 
                 3: 'Thursday', 4: 'Friday'}
    weekly_stats['Day Name'] = weekly_stats['DayOfWeek'].map(day_names)
    
    return weekly_stats

@st.cache_data(ttl=3600, show_spinner=False)
def calculate_election_cycle_seasonality(df):
    """Calculate returns based on presidential election cycle (4-year cycle)."""
    if df.empty:
        return pd.DataFrame()
    
    # Election years: 2024, 2020, 2016, 2012, etc.
    df['Years Since Election'] = (df['Year'] - 2024) % 4
    
    election_stats = df.groupby('Years Since Election')['Returns'].agg([
        ('Mean Return', 'mean'),
        ('Median Return', 'median'),
        ('Std Dev', 'std'),
        ('Win Rate', lambda x: (x > 0).sum() / len(x) * 100),
        ('Count', 'count')
    ]).reset_index()
    
    # Add cycle labels
    cycle_labels = {0: 'Election Year', 1: 'Post-Election Year', 
                    2: 'Mid-Term Year', 3: 'Pre-Election Year'}
    election_stats['Cycle Phase'] = election_stats['Years Since Election'].map(cycle_labels)
    
    return election_stats

@st.cache_data(ttl=3600, show_spinner=False)
def create_monthly_chart(monthly_stats):
    """Create bar chart for monthly seasonality."""
    import plotly.graph_objects as go
    
    fig = go.Figure()
    
    colors = ['#26D07C' if x > 0 else '#D9534F' for x in monthly_stats['Mean Return']]
    
    fig.add_trace(go.Bar(
        x=monthly_stats['Month Name'],
        y=monthly_stats['Mean Return'],
        marker_color=colors,
        text=monthly_stats['Mean Return'].apply(lambda x: f"{x:.2f}%"),
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Mean Return: %{y:.2f}%<br>Win Rate: %{customdata[0]:.1f}%<extra></extra>',
        customdata=monthly_stats[['Win Rate']].values
    ))
    
    fig.update_layout(
        title="Average S&P 500 Returns by Month",
        xaxis_title="Month",
        yaxis_title="Average Return (%)",
        template="plotly_dark",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color=BLOOM_TEXT),
        height=450
    )
    
    return fig

@st.cache_data(ttl=86400, show_spinner=False)
def create_weekly_chart(weekly_stats):
    """Create bar chart for day-of-week seasonality."""
    import plotly.graph_objects as go
    
    fig = go.Figure()
    
    colors = ['#26D07C' if x > 0 else '#D9534F' for x in weekly_stats['Mean Return']]
    
    fig.add_trace(go.Bar(
        x=weekly_stats['Day Name'],
        y=weekly_stats['Mean Return'],
        marker_color=colors,
        text=weekly_stats['Mean Return'].apply(lambda x: f"{x:.3f}%"),
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Mean Return: %{y:.3f}%<br>Win Rate: %{customdata[0]:.1f}%<extra></extra>',
        customdata=weekly_stats[['Win Rate']].values
    ))
    
    fig.update_layout(
        title="Average S&P 500 Returns by Day of Week",
        xaxis_title="Day",
        yaxis_title="Average Return (%)",
        template="plotly_dark",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color=BLOOM_TEXT),
        height=450
    )
    
    return fig

@st.cache_data(ttl=86400, show_spinner=False)
def create_election_cycle_chart(election_stats):
    """Create bar chart for election cycle seasonality."""
    import plotly.graph_objects as go
    
    fig = go.Figure()
    
    colors = ['#26D07C' if x > 0 else '#D9534F' for x in election_stats['Mean Return']]
    
    fig.add_trace(go.Bar(
        x=election_stats['Cycle Phase'],
        y=election_stats['Mean Return'],
        marker_color=colors,
        text=election_stats['Mean Return'].apply(lambda x: f"{x:.3f}%"),
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Mean Return: %{y:.3f}%<br>Win Rate: %{customdata[0]:.1f}%<extra></extra>',
        customdata=election_stats[['Win Rate']].values
    ))
    
    fig.update_layout(
        title="Average S&P 500 Returns by Presidential Election Cycle",
        xaxis_title="Election Cycle Phase",
        yaxis_title="Average Return (%)",
        template="plotly_dark",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color=BLOOM_TEXT),
        height=450,
        xaxis={'categoryorder': 'array', 'categoryarray': ['Post-Election Year', 'Mid-Term Year', 'Pre-Election Year', 'Election Year']}
    )
    
    return fig

# --------------------------------------------------------------------------------------
# Main Content
# --------------------------------------------------------------------------------------

# Add specific styling for refresh button
st.markdown("""
    <style>
    /* Force refresh button to match theme */
    button[key="refresh_btn"], 
    div[data-testid="column"] button,
    .stButton button {
        background: var(--input) !important;
        color: var(--text) !important;
        border: 1px solid var(--neutral) !important;
    }
    button[key="refresh_btn"]:hover,
    div[data-testid="column"] button:hover,
    .stButton button:hover {
        background: var(--inputlight) !important;
        border-color: var(--purple) !important;
        color: var(--purple) !important;
    }
    </style>
""", unsafe_allow_html=True)

# Add refresh button with consistent styling
col1, col2 = st.columns([4, 1])
with col2:
    if st.button("Refresh Data", use_container_width=True, help="Check for latest S&P 500 data", key="refresh_btn"):
        st.cache_data.clear()
        st.rerun()

# Fetch data with loading indicator
with st.spinner("Loading S&P 500 data..."):
    sp500_data = load_and_update_sp500_data()

if not sp500_data.empty:
    # Validate data dates
    first_date = sp500_data.index[0]
    last_date = sp500_data.index[-1]
    current_year = pd.Timestamp.now().year
    
    # Check for obviously bad dates (future dates or way too old)
    if last_date.year > current_year + 1:
        st.error(f"Error: CSV contains future dates (last date: {last_date.strftime('%Y-%m-%d')}). Please check your CSV file.")
        st.stop()
    
    if first_date.year < 1900 or first_date.year > current_year:
        st.error(f"Error: CSV contains invalid dates (first date: {first_date.strftime('%Y-%m-%d')}). Please check your CSV file.")
        st.stop()
    
    # Data info with last update date
    days_old = (pd.Timestamp.now().normalize() - last_date).days
    
    # Determine data freshness status
    if days_old == 0:
        status_color = "var(--green)"
        status_text = "Current (today's data)"
    elif days_old == 1:
        status_color = "var(--blue)"
        status_text = "1 day old"
    elif days_old <= 3:
        status_color = "#FFA500"
        status_text = f"{days_old} days old"
    else:
        status_color = "#D9534F"
        status_text = f"{days_old} days old"
    
    st.markdown(f"""
        <div style="background: var(--inputlight); padding: 15px; border-radius: 10px; border: 1px solid var(--neutral); margin-bottom: 20px;">
            <p style="margin: 0 0 8px 0; color: var(--muted-text-new);">
                <strong>Data Range:</strong> {sp500_data.index[0].strftime('%B %d, %Y')} to {sp500_data.index[-1].strftime('%B %d, %Y')} 
                ({len(sp500_data):,} trading days)
            </p>
            <p style="margin: 0; color: {status_color}; font-weight: 600;">
                {status_text}
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # --------------------------------------------------------------------------------------
    # Lookback Period Selector
    # --------------------------------------------------------------------------------------
    st.markdown("### Analysis Period")
    
    lookback_options = {
        "1 Year": 1,
        "5 Years": 5,
        "10 Years": 10,
        "20 Years": 20,
        "Max (All Data)": None
    }
    
    selected_lookback = st.selectbox(
        "Select time period for seasonality analysis:",
        options=list(lookback_options.keys()),
        index=4,  # Default to "Max (All Data)"
        key="lookback_selector"
    )
    
    # Filter data based on lookback period
    years_back = lookback_options[selected_lookback]
    if years_back is not None:
        # Calculate cutoff date
        cutoff_date = sp500_data.index[-1] - pd.DateOffset(years=years_back)
        filtered_data = sp500_data[sp500_data.index >= cutoff_date]
        
        # Display filtered range
        st.markdown(f"""
            <div style="background: var(--panel); padding: 12px; border-radius: 8px; border: 1px solid var(--neutral); margin-top: 10px; margin-bottom: 20px;">
                <p style="margin: 0; color: var(--muted-text-new); font-size: 0.9rem;">
                    <strong>Analyzing:</strong> {filtered_data.index[0].strftime('%B %d, %Y')} to {filtered_data.index[-1].strftime('%B %d, %Y')} 
                    ({len(filtered_data):,} trading days)
                </p>
            </div>
        """, unsafe_allow_html=True)
    else:
        # Use all data
        filtered_data = sp500_data
        st.markdown(f"""
            <div style="background: var(--panel); padding: 12px; border-radius: 8px; border: 1px solid var(--neutral); margin-top: 10px; margin-bottom: 20px;">
                <p style="margin: 0; color: var(--muted-text-new); font-size: 0.9rem;">
                    <strong>Analyzing:</strong> Complete historical dataset ({len(filtered_data):,} trading days)
                </p>
            </div>
        """, unsafe_allow_html=True)
    
    # --------------------------------------------------------------------------------------
    # Monthly Seasonality
    # --------------------------------------------------------------------------------------
    st.markdown("## Monthly Seasonality")
    
    monthly_stats = calculate_monthly_seasonality(filtered_data)
    
    # Calculate color for each month based on return
    min_return = monthly_stats['Mean Return'].min()
    max_return = monthly_stats['Mean Return'].max()
    
    def get_month_color(return_val):
        """Generate color based on return value - matches Home page heatmap"""
        max_saturation = 4.0
        
        if return_val > 0:
            # Green for positive - same as Home page
            alpha = min(0.9, 0.1 + (return_val / max_saturation) * 0.8)
            return f'rgba(38, 208, 124, {alpha})'
        elif return_val < 0:
            # Red for negative - same as Home page
            alpha = min(0.9, 0.1 + (abs(return_val) / max_saturation) * 0.8)
            return f'rgba(217, 83, 79, {alpha})'
        else:
            # Neutral for zero
            return f'rgba(138, 124, 245, 0.1)'
    
    # Build HTML for month grid
    html_content = '''
    <style>
    .month-heatmap-container {
        display: grid;
        grid-template-columns: repeat(12, 1fr);
        gap: 10px;
        margin: 20px 0;
    }
    .month-box {
        border-radius: 8px;
        padding: 15px 10px;
        text-align: center;
        transition: all 0.3s;
        border: 1px solid rgba(255,255,255,0.1);
        min-height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .month-box:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 15px rgba(0,0,0,0.5);
    }
    .month-name {
        font-size: 0.9rem;
        font-weight: 700;
        margin-bottom: 8px;
        color: #FFFFFF;
    }
    .month-return {
        font-size: 1.1rem;
        font-weight: 800;
        margin-bottom: 5px;
        color: #FFFFFF;
    }
    .month-std {
        font-size: 0.75rem;
        color: rgba(255,255,255,0.75);
        margin-bottom: 3px;
    }
    .month-win {
        font-size: 0.75rem;
        color: rgba(255,255,255,0.75);
    }
    </style>
    <div class="month-heatmap-container">
    '''
    
    for _, row in monthly_stats.iterrows():
        month_name = row['Month Name'][:3]  # Abbreviated month name
        mean_return = row['Mean Return']
        std_dev = row['Std Dev']
        win_rate = row['Win Rate']
        
        bg_color = get_month_color(mean_return)
        
        html_content += f'''
        <div class="month-box" style="background: {bg_color};">
            <div class="month-name">{month_name}</div>
            <div class="month-return">{mean_return:+.2f}%</div>
            <div class="month-std">σ: {std_dev:.2f}%</div>
            <div class="month-win">{win_rate:.0f}% ↑</div>
        </div>
        '''
    
    html_content += '</div>'
    
    import streamlit.components.v1 as components
    components.html(html_content, height=180)
    
    # Current year monthly performance
    st.markdown("### This Year's Monthly Performance")
    
    current_year = pd.Timestamp.now().year
    current_year_data = filtered_data[filtered_data.index.year == current_year].copy()
    
    if not current_year_data.empty:
        # Calculate monthly returns for current year
        current_year_data['Year'] = current_year_data.index.year
        current_year_data['Month'] = current_year_data.index.month
        
        current_year_returns = []
        for month in range(1, 13):
            month_data = current_year_data[current_year_data['Month'] == month]
            if len(month_data) > 0:
                first_price = month_data['Price'].iloc[0]
                last_price = month_data['Price'].iloc[-1]
                monthly_return = ((last_price - first_price) / first_price) * 100
                
                # Calculate stats for the month
                daily_returns = month_data['Returns'].dropna()
                win_rate = (daily_returns > 0).sum() / len(daily_returns) * 100 if len(daily_returns) > 0 else 0
                std_dev = daily_returns.std() if len(daily_returns) > 1 else 0
                
                current_year_returns.append({
                    'Month': month,
                    'Return': monthly_return,
                    'Std Dev': std_dev,
                    'Win Rate': win_rate
                })
            else:
                current_year_returns.append({
                    'Month': month,
                    'Return': None,
                    'Std Dev': None,
                    'Win Rate': None
                })
        
        # Build HTML for current year grid
        html_content_year = '''
        <style>
        .month-heatmap-container-year {
            display: grid;
            grid-template-columns: repeat(12, 1fr);
            gap: 10px;
            margin: 20px 0;
        }
        .month-box-year {
            border-radius: 8px;
            padding: 15px 10px;
            text-align: center;
            transition: all 0.3s;
            border: 1px solid rgba(255,255,255,0.1);
            min-height: 120px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        .month-box-year:hover {
            transform: scale(1.05);
            box-shadow: 0 5px 15px rgba(0,0,0,0.5);
        }
        .month-name-year {
            font-size: 0.9rem;
            font-weight: 700;
            margin-bottom: 8px;
            color: #FFFFFF;
        }
        .month-return-year {
            font-size: 1.1rem;
            font-weight: 800;
            margin-bottom: 5px;
            color: #FFFFFF;
        }
        .month-std-year {
            font-size: 0.75rem;
            color: rgba(255,255,255,0.75);
            margin-bottom: 3px;
        }
        .month-win-year {
            font-size: 0.75rem;
            color: rgba(255,255,255,0.75);
        }
        .month-empty {
            opacity: 0.3;
        }
        </style>
        <div class="month-heatmap-container-year">
        '''
        
        month_abbrev = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        for i, month_data in enumerate(current_year_returns):
            month_name = month_abbrev[i]
            
            if month_data['Return'] is not None:
                return_val = month_data['Return']
                std_val = month_data['Std Dev']
                win_val = month_data['Win Rate']
                
                bg_color = get_month_color(return_val)
                
                html_content_year += f'''
                <div class="month-box-year" style="background: {bg_color};">
                    <div class="month-name-year">{month_name}</div>
                    <div class="month-return-year">{return_val:+.2f}%</div>
                    <div class="month-std-year">σ: {std_val:.2f}%</div>
                    <div class="month-win-year">{win_val:.0f}% ↑</div>
                </div>
                '''
            else:
                # Month hasn't happened yet
                html_content_year += f'''
                <div class="month-box-year month-empty" style="background: rgba(138, 124, 245, 0.1);">
                    <div class="month-name-year">{month_name}</div>
                    <div class="month-return-year">-</div>
                    <div class="month-std-year">Not yet</div>
                    <div class="month-win-year">-</div>
                </div>
                '''
        
        html_content_year += '</div>'
        
        components.html(html_content_year, height=180)
        
        # Best/worst months for current year (above YTD)
        completed_month_data = [m for m in current_year_returns if m['Return'] is not None]
        if len(completed_month_data) > 0:
            month_names = ['January', 'February', 'March', 'April', 'May', 'June', 
                          'July', 'August', 'September', 'October', 'November', 'December']
            
            best_month_idx = max(range(len(completed_month_data)), 
                               key=lambda i: completed_month_data[i]['Return'])
            worst_month_idx = min(range(len(completed_month_data)), 
                                key=lambda i: completed_month_data[i]['Return'])
            
            best = completed_month_data[best_month_idx]
            worst = completed_month_data[worst_month_idx]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                **Best Month:** {month_names[best['Month']-1]} ({best['Return']:+.2f}%, {best['Win Rate']:.0f}% win rate)
                """)
            
            with col2:
                st.markdown(f"""
                **Worst Month:** {month_names[worst['Month']-1]} ({worst['Return']:+.2f}%, {worst['Win Rate']:.0f}% win rate)
                """)
        
        # Calculate YTD return
        if len(current_year_data) > 0:
            ytd_return = ((current_year_data['Price'].iloc[-1] - current_year_data['Price'].iloc[0]) / 
                         current_year_data['Price'].iloc[0]) * 100
            completed_months = sum(1 for m in current_year_returns if m['Return'] is not None)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**YTD Return ({current_year}):** {ytd_return:+.2f}%")
            with col2:
                st.markdown(f"**Completed Months:** {completed_months}/12")
    else:
        st.info(f"No data available for {current_year} in the selected lookback period.")
    
    # Key insights for historical averages (below everything)
    st.markdown("### Historical Averages")
    col1, col2 = st.columns(2)
    
    with col1:
        best_month = monthly_stats.loc[monthly_stats['Mean Return'].idxmax()]
        st.markdown(f"""
        **Best Month:** {best_month['Month Name']} ({best_month['Mean Return']:+.2f}% avg, {best_month['Win Rate']:.0f}% win rate)
        """)
    
    with col2:
        worst_month = monthly_stats.loc[monthly_stats['Mean Return'].idxmin()]
        st.markdown(f"""
        **Worst Month:** {worst_month['Month Name']} ({worst_month['Mean Return']:+.2f}% avg, {worst_month['Win Rate']:.0f}% win rate)
        """)
    
    with st.expander("View Detailed Monthly Statistics"):
        display_monthly = monthly_stats[['Month Name', 'Mean Return', 'Median Return', 'Std Dev', 'Win Rate', 'Count']].copy()
        display_monthly['Mean Return'] = display_monthly['Mean Return'].apply(lambda x: f"{x:.3f}%")
        display_monthly['Median Return'] = display_monthly['Median Return'].apply(lambda x: f"{x:.3f}%")
        display_monthly['Std Dev'] = display_monthly['Std Dev'].apply(lambda x: f"{x:.3f}%")
        display_monthly['Win Rate'] = display_monthly['Win Rate'].apply(lambda x: f"{x:.1f}%")
        st.dataframe(display_monthly, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # --------------------------------------------------------------------------------------
    # Weekly Seasonality (Day of Week)
    # --------------------------------------------------------------------------------------
    st.markdown("## Day of Week Seasonality")
    
    weekly_stats = calculate_weekly_seasonality(filtered_data)
    
    # Build HTML for day of week cards
    html_content_week = '''
    <style>
    .week-container {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 15px;
        margin: 20px 0;
    }
    .day-card {
        border-radius: 10px;
        padding: 20px 15px;
        text-align: center;
        transition: all 0.3s;
        border: 1px solid rgba(255,255,255,0.1);
        min-height: 160px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    .day-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.6);
    }
    .day-name-big {
        font-size: 1.1rem;
        font-weight: 700;
        margin-bottom: 12px;
        color: #FFFFFF;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .day-return-big {
        font-size: 1.4rem;
        font-weight: 800;
        margin-bottom: 10px;
        color: #FFFFFF;
    }
    .day-stat {
        font-size: 0.85rem;
        color: rgba(255,255,255,0.75);
        margin: 3px 0;
    }
    .day-label {
        font-size: 0.7rem;
        color: rgba(255,255,255,0.5);
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 2px;
    }
    </style>
    <div class="week-container">
    '''
    
    day_names_full = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    day_names_abbrev = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
    
    for idx, row in weekly_stats.iterrows():
        day_name = day_names_abbrev[idx]
        day_full = day_names_full[idx]
        mean_return = row['Mean Return']
        std_dev = row['Std Dev']
        win_rate = row['Win Rate']
        count = row['Count']
        
        bg_color = get_month_color(mean_return)
        
        html_content_week += f'''
        <div class="day-card" style="background: {bg_color};">
            <div class="day-name-big">{day_name}</div>
            <div class="day-return-big">{mean_return:+.3f}%</div>
            <div class="day-label">Win Rate</div>
            <div class="day-stat">{win_rate:.1f}%</div>
            <div class="day-label">Volatility</div>
            <div class="day-stat">σ: {std_dev:.2f}%</div>
        </div>
        '''
    
    html_content_week += '</div>'
    
    import streamlit.components.v1 as components
    components.html(html_content_week, height=220)
    
    # Key insights below cards
    best_day = weekly_stats.loc[weekly_stats['Mean Return'].idxmax()]
    worst_day = weekly_stats.loc[weekly_stats['Mean Return'].idxmin()]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        **Best Day:** {best_day['Day Name']} ({best_day['Mean Return']:+.3f}% avg, {best_day['Win Rate']:.1f}% win rate)
        """)
    
    with col2:
        st.markdown(f"""
        **Worst Day:** {worst_day['Day Name']} ({worst_day['Mean Return']:+.3f}% avg, {worst_day['Win Rate']:.1f}% win rate)
        """)
    
    with st.expander("View Detailed Weekly Statistics"):
        display_weekly = weekly_stats[['Day Name', 'Mean Return', 'Median Return', 'Std Dev', 'Win Rate', 'Count']].copy()
        display_weekly['Mean Return'] = display_weekly['Mean Return'].apply(lambda x: f"{x:.4f}%")
        display_weekly['Median Return'] = display_weekly['Median Return'].apply(lambda x: f"{x:.4f}%")
        display_weekly['Std Dev'] = display_weekly['Std Dev'].apply(lambda x: f"{x:.3f}%")
        display_weekly['Win Rate'] = display_weekly['Win Rate'].apply(lambda x: f"{x:.1f}%")
        st.dataframe(display_weekly, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # --------------------------------------------------------------------------------------
    # YTD Weekly Performance vs Historical Average
    # --------------------------------------------------------------------------------------
    st.markdown("## YTD Weekly Performance Comparison")
    st.markdown("Current year weekly returns vs. historical average with ±1 standard deviation bands")
    
    current_year = pd.Timestamp.now().year
    
    # Get current year data
    current_year_data = filtered_data[filtered_data.index.year == current_year].copy()
    
    # Get historical data (all years except current)
    historical_data = filtered_data[filtered_data.index.year < current_year].copy()
    
    if not current_year_data.empty and not historical_data.empty:
        # Calculate week number within the year (1-52)
        current_year_data['WeekNum'] = current_year_data.index.isocalendar().week
        
        # Calculate base 100 index for current year
        base_price = current_year_data['Price'].iloc[0]
        current_year_data['Index'] = (current_year_data['Price'] / base_price) * 100
        
        # Group by week and take last value of each week
        current_weekly = current_year_data.groupby('WeekNum').agg({
            'Index': 'last',
            'Price': 'last'
        }).reset_index()
        
        # Add week labels
        current_weekly['Week_Label'] = current_weekly['WeekNum'].astype(int)
        
        # Calculate historical base 100 indices
        historical_data['WeekNum'] = historical_data.index.isocalendar().week
        historical_data['Year'] = historical_data.index.year
        
        # For each historical year, calculate base 100 index
        historical_indices = []
        
        for year in historical_data['Year'].unique():
            year_data = historical_data[historical_data['Year'] == year]
            if len(year_data) > 10:  # Only include years with reasonable data
                base_price_year = year_data['Price'].iloc[0]
                year_data = year_data.copy()
                year_data['Index'] = (year_data['Price'] / base_price_year) * 100
                
                # Group by week
                year_weekly = year_data.groupby('WeekNum')['Index'].last().reset_index()
                year_weekly['Year'] = year
                historical_indices.append(year_weekly)
        
        historical_df = pd.concat(historical_indices, ignore_index=True)
        
        # Calculate mean and std by week number
        weekly_stats_hist = historical_df.groupby('WeekNum')['Index'].agg(['mean', 'std']).reset_index()
        weekly_stats_hist['upper_band'] = weekly_stats_hist['mean'] + weekly_stats_hist['std']
        weekly_stats_hist['lower_band'] = weekly_stats_hist['mean'] - weekly_stats_hist['std']
        weekly_stats_hist['Week_Label'] = weekly_stats_hist['WeekNum'].astype(int)
        
        # Keep full year of historical data (don't limit to current week)
        # This shows where the year typically goes even if we're not there yet
        
        # Create Plotly chart
        import plotly.graph_objects as go
        
        fig = go.Figure()
        
        # Add upper band
        fig.add_trace(go.Scatter(
            x=weekly_stats_hist['Week_Label'],
            y=weekly_stats_hist['upper_band'],
            mode='lines',
            name='Avg +1σ',
            line=dict(color='rgba(138, 124, 245, 0.3)', width=1, dash='dash'),
            fill=None,
            showlegend=True,
            hovertemplate='Week %{x}<br>Upper Band: %{y:.2f}<extra></extra>'
        ))
        
        # Add lower band with fill
        fig.add_trace(go.Scatter(
            x=weekly_stats_hist['Week_Label'],
            y=weekly_stats_hist['lower_band'],
            mode='lines',
            name='Avg -1σ',
            line=dict(color='rgba(138, 124, 245, 0.3)', width=1, dash='dash'),
            fill='tonexty',
            fillcolor='rgba(138, 124, 245, 0.15)',
            showlegend=True,
            hovertemplate='Week %{x}<br>Lower Band: %{y:.2f}<extra></extra>'
        ))
        
        # Add historical average
        fig.add_trace(go.Scatter(
            x=weekly_stats_hist['Week_Label'],
            y=weekly_stats_hist['mean'],
            mode='lines',
            name='Historical Avg',
            line=dict(color='rgba(138, 124, 245, 0.8)', width=2),
            showlegend=True,
            hovertemplate='Week %{x}<br>Historical Avg: %{y:.2f}<extra></extra>'
        ))
        
        # Add current year
        fig.add_trace(go.Scatter(
            x=current_weekly['Week_Label'],
            y=current_weekly['Index'],
            mode='lines+markers',
            name=f'{current_year} YTD',
            line=dict(color='#26D07C', width=3),
            marker=dict(size=4, color='#26D07C'),
            showlegend=True,
            hovertemplate='Week %{x}<br>' + f'{current_year}: ' + '%{y:.2f}<extra></extra>'
        ))
        
        # Add horizontal line at 100
        fig.add_hline(y=100, line_dash="dot", line_color="rgba(255,255,255,0.3)", 
                      annotation_text="Start", annotation_position="right")
        
        fig.update_layout(
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#FFFFFF', size=12),
            xaxis=dict(
                title=dict(text='Week of Year', font=dict(color='#FFFFFF')),
                gridcolor='rgba(255,255,255,0.1)',
                showgrid=True,
                dtick=4,  # Show every 4th week
                range=[0, 53],
                tickfont=dict(color='#FFFFFF')
            ),
            yaxis=dict(
                title=dict(text='Index (Base 100 = Year Start)', font=dict(color='#FFFFFF')),
                gridcolor='rgba(255,255,255,0.1)',
                showgrid=True,
                tickfont=dict(color='#FFFFFF')
            ),
            hovermode='x unified',
            height=500,
            margin=dict(l=50, r=50, t=30, b=50),
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor='rgba(0,0,0,0.5)',
                bordercolor='rgba(255,255,255,0.2)',
                borderwidth=1,
                font=dict(color='#FFFFFF')
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Get current week number
        current_week_num = current_weekly['WeekNum'].max()
        next_week_num = current_week_num + 1
        
        # Calculate current week's actual return (cumulative compounded from week start to now)
        current_week_data = current_year_data[current_year_data['WeekNum'] == current_week_num]
        if len(current_week_data) > 0:
            # Get week start price (first price of the week)
            week_start_price = current_week_data['Price'].iloc[0]
            
            # Get current price (last available price, which could be intraday)
            try:
                # Try to get latest intraday price from Yahoo Finance
                import yfinance as yf
                ticker = yf.Ticker("^GSPC")
                latest_data = ticker.history(period="1d", interval="1m")
                if not latest_data.empty:
                    current_price = latest_data['Close'].iloc[-1]
                else:
                    # Fallback to last close
                    current_price = current_week_data['Price'].iloc[-1]
            except:
                # Fallback to last close if real-time fetch fails
                current_price = current_week_data['Price'].iloc[-1]
            
            # Calculate cumulative return from week start to now
            current_week_return = ((current_price - week_start_price) / week_start_price) * 100
        else:
            current_week_return = 0
        
        # Get historical stats for current week
        current_week_hist = historical_df[historical_df['WeekNum'] == current_week_num]
        if len(current_week_hist) > 0:
            # Calculate weekly returns for historical data
            hist_weekly_returns = []
            for year in current_week_hist['Year'].unique():
                year_all_data = historical_data[historical_data['Year'] == year]
                week_data = year_all_data[year_all_data['WeekNum'] == current_week_num]
                
                if len(week_data) > 1:
                    week_start = week_data['Price'].iloc[0]
                    week_end = week_data['Price'].iloc[-1]
                    weekly_return = ((week_end - week_start) / week_start) * 100
                    hist_weekly_returns.append(weekly_return)
                    
                    # Daily volatility
                    daily_returns = week_data['Returns'].dropna()
            
            if len(hist_weekly_returns) > 0:
                avg_week_return = np.mean(hist_weekly_returns)
                win_rate_week = (np.array(hist_weekly_returns) > 0).sum() / len(hist_weekly_returns) * 100
            else:
                avg_week_return = 0
                win_rate_week = 0
            
            # Get average daily volatility for this week
            daily_vols = []
            for year in current_week_hist['Year'].unique():
                year_all_data = historical_data[historical_data['Year'] == year]
                week_data = year_all_data[year_all_data['WeekNum'] == current_week_num]
                if len(week_data) > 1:
                    daily_vol = week_data['Returns'].std()
                    if not np.isnan(daily_vol):
                        daily_vols.append(daily_vol)
            
            avg_daily_vol = np.mean(daily_vols) if len(daily_vols) > 0 else 0
        else:
            avg_week_return = 0
            win_rate_week = 0
            avg_daily_vol = 0
        
        # Get historical stats for next week
        next_week_hist = historical_df[historical_df['WeekNum'] == next_week_num]
        if len(next_week_hist) > 0:
            # Calculate weekly returns for next week
            hist_next_weekly_returns = []
            for year in next_week_hist['Year'].unique():
                year_all_data = historical_data[historical_data['Year'] == year]
                week_data = year_all_data[year_all_data['WeekNum'] == next_week_num]
                
                if len(week_data) > 1:
                    week_start = week_data['Price'].iloc[0]
                    week_end = week_data['Price'].iloc[-1]
                    weekly_return = ((week_end - week_start) / week_start) * 100
                    hist_next_weekly_returns.append(weekly_return)
            
            if len(hist_next_weekly_returns) > 0:
                avg_next_week_return = np.mean(hist_next_weekly_returns)
                win_rate_next_week = (np.array(hist_next_weekly_returns) > 0).sum() / len(hist_next_weekly_returns) * 100
            else:
                avg_next_week_return = 0
                win_rate_next_week = 0
            
            # Get average daily volatility for next week
            daily_vols_next = []
            for year in next_week_hist['Year'].unique():
                year_all_data = historical_data[historical_data['Year'] == year]
                week_data = year_all_data[year_all_data['WeekNum'] == next_week_num]
                if len(week_data) > 1:
                    daily_vol = week_data['Returns'].std()
                    if not np.isnan(daily_vol):
                        daily_vols_next.append(daily_vol)
            
            avg_daily_vol_next = np.mean(daily_vols_next) if len(daily_vols_next) > 0 else 0
        else:
            avg_next_week_return = 0
            win_rate_next_week = 0
            avg_daily_vol_next = 0
        
        # Display info boxes
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
                <div style="background: var(--inputlight); padding: 20px; border-radius: 10px; border: 1px solid var(--neutral); margin-bottom: 15px;">
                    <h4 style="color: var(--purple); margin-top: 0;">Current Week {current_week_num}</h4>
                    <div style="margin: 10px 0;">
                        <span style="color: var(--muted-text-new); font-size: 0.9rem;">This Week's Return:</span><br>
                        <span style="color: var(--text); font-size: 1.3rem; font-weight: 700;">{current_week_return:+.2f}%</span>
                    </div>
                    <div style="margin: 10px 0;">
                        <span style="color: var(--muted-text-new); font-size: 0.9rem;">Historical Avg (Week {current_week_num}):</span><br>
                        <span style="color: var(--text); font-size: 1.3rem; font-weight: 700;">{avg_week_return:+.2f}%</span>
                    </div>
                    <div style="margin: 10px 0;">
                        <span style="color: var(--muted-text-new); font-size: 0.9rem;">Avg Daily Volatility:</span><br>
                        <span style="color: var(--text); font-size: 1.1rem; font-weight: 600;">{avg_daily_vol:.2f}%</span>
                    </div>
                    <div style="margin: 10px 0;">
                        <span style="color: var(--muted-text-new); font-size: 0.9rem;">Historical Win Rate:</span><br>
                        <span style="color: var(--text); font-size: 1.1rem; font-weight: 600;">{win_rate_week:.1f}%</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
                <div style="background: var(--inputlight); padding: 20px; border-radius: 10px; border: 1px solid var(--neutral); margin-bottom: 15px;">
                    <h4 style="color: var(--purple); margin-top: 0;">Next Week {next_week_num}</h4>
                    <div style="margin: 10px 0;">
                        <span style="color: var(--muted-text-new); font-size: 0.9rem;">Expected Return:</span><br>
                        <span style="color: var(--text); font-size: 1.3rem; font-weight: 700;">{avg_next_week_return:+.2f}%</span>
                    </div>
                    <div style="margin: 10px 0;">
                        <span style="color: var(--muted-text-new); font-size: 0.9rem;">Expected Daily Volatility:</span><br>
                        <span style="color: var(--text); font-size: 1.1rem; font-weight: 600;">{avg_daily_vol_next:.2f}%</span>
                    </div>
                    <div style="margin: 10px 0;">
                        <span style="color: var(--muted-text-new); font-size: 0.9rem;">Historical Win Rate:</span><br>
                        <span style="color: var(--text); font-size: 1.1rem; font-weight: 600;">{win_rate_next_week:.1f}%</span>
                    </div>
                    <div style="margin: 10px 0;">
                        <span style="color: var(--muted-text-new); font-size: 0.85rem; font-style: italic;">
                            Based on {len(hist_next_weekly_returns) if len(next_week_hist) > 0 else 0} historical observations
                        </span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        # Key statistics
        st.markdown("### Year-to-Date Performance")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            current_index = current_weekly['Index'].iloc[-1]
            current_return = current_index - 100
            st.markdown(f"**{current_year} Performance:** {current_return:+.2f}% (Index: {current_index:.2f})")
        
        with col2:
            hist_index = weekly_stats_hist[weekly_stats_hist['WeekNum'] == current_weekly['WeekNum'].max()]['mean'].iloc[0]
            hist_return = hist_index - 100
            st.markdown(f"**Historical Avg (Week {int(current_weekly['WeekNum'].max())}):** {hist_return:+.2f}% (Index: {hist_index:.2f})")
        
        with col3:
            difference = current_return - hist_return
            st.markdown(f"**Outperformance:** {difference:+.2f}%")
    else:
        st.info("Insufficient data to create weekly comparison chart.")
    
    st.markdown("---")
    
    # --------------------------------------------------------------------------------------
    # Election Cycle Seasonality
    # --------------------------------------------------------------------------------------
    st.markdown("## Presidential Election Cycle")
    
    election_stats = calculate_election_cycle_seasonality(filtered_data)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        election_chart = create_election_cycle_chart(election_stats)
        st.plotly_chart(election_chart, use_container_width=True)
    
    with col2:
        st.markdown("### Key Insights")
        
        best_phase = election_stats.loc[election_stats['Mean Return'].idxmax()]
        worst_phase = election_stats.loc[election_stats['Mean Return'].idxmin()]
        
        st.markdown(f"""
        **Best Phase:**
        - {best_phase['Cycle Phase']}: **{best_phase['Mean Return']:.3f}%**
        - Win Rate: {best_phase['Win Rate']:.1f}%
        
        **Worst Phase:**
        - {worst_phase['Cycle Phase']}: **{worst_phase['Mean Return']:.3f}%**
        - Win Rate: {worst_phase['Win Rate']:.1f}%
        
        **Current Year:** 2025 (Post-Election)
        """)
    
    with st.expander("View Detailed Election Cycle Statistics"):
        display_election = election_stats[['Cycle Phase', 'Mean Return', 'Median Return', 'Std Dev', 'Win Rate', 'Count']].copy()
        display_election['Mean Return'] = display_election['Mean Return'].apply(lambda x: f"{x:.4f}%")
        display_election['Median Return'] = display_election['Median Return'].apply(lambda x: f"{x:.4f}%")
        display_election['Std Dev'] = display_election['Std Dev'].apply(lambda x: f"{x:.3f}%")
        display_election['Win Rate'] = display_election['Win Rate'].apply(lambda x: f"{x:.1f}%")
        st.dataframe(display_election, use_container_width=True, hide_index=True)

else:
    st.error("Unable to load S&P 500 data. Please check your internet connection and try again.")

st.markdown("---")

# --------------------------------------------------------------------------------------
# Back Button
# --------------------------------------------------------------------------------------
if st.button("← Back to Home", use_container_width=True):
    st.switch_page("Home.py")
