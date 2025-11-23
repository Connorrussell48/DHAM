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
BLOOM_TEXT     = "#FFFFF5"
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
            df = pd.read_csv(csv_path, parse_dates=['Date'], index_col='Date')
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
    """Calculate average returns by month."""
    if df.empty:
        return pd.DataFrame()
    
    monthly_stats = df.groupby('Month')['Returns'].agg([
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
    # Data info with last update date
    last_date = sp500_data.index[-1]
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
    # Monthly Seasonality
    # --------------------------------------------------------------------------------------
    st.markdown("## Monthly Seasonality")
    
    monthly_stats = calculate_monthly_seasonality(sp500_data)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        monthly_chart = create_monthly_chart(monthly_stats)
        st.plotly_chart(monthly_chart, use_container_width=True)
    
    with col2:
        st.markdown("### Key Insights")
        
        best_month = monthly_stats.loc[monthly_stats['Mean Return'].idxmax()]
        worst_month = monthly_stats.loc[monthly_stats['Mean Return'].idxmin()]
        
        st.markdown(f"""
        **Best Month:**
        - {best_month['Month Name']}: **{best_month['Mean Return']:.2f}%**
        - Win Rate: {best_month['Win Rate']:.1f}%
        
        **Worst Month:**
        - {worst_month['Month Name']}: **{worst_month['Mean Return']:.2f}%**
        - Win Rate: {worst_month['Win Rate']:.1f}%
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
    
    weekly_stats = calculate_weekly_seasonality(sp500_data)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        weekly_chart = create_weekly_chart(weekly_stats)
        st.plotly_chart(weekly_chart, use_container_width=True)
    
    with col2:
        st.markdown("### Key Insights")
        
        best_day = weekly_stats.loc[weekly_stats['Mean Return'].idxmax()]
        worst_day = weekly_stats.loc[weekly_stats['Mean Return'].idxmin()]
        
        st.markdown(f"""
        **Best Day:**
        - {best_day['Day Name']}: **{best_day['Mean Return']:.3f}%**
        - Win Rate: {best_day['Win Rate']:.1f}%
        
        **Worst Day:**
        - {worst_day['Day Name']}: **{worst_day['Mean Return']:.3f}%**
        - Win Rate: {worst_day['Win Rate']:.1f}%
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
    # Election Cycle Seasonality
    # --------------------------------------------------------------------------------------
    st.markdown("## Presidential Election Cycle")
    
    election_stats = calculate_election_cycle_seasonality(sp500_data)
    
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
