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
# Data Fetching Functions (with caching)
# --------------------------------------------------------------------------------------

@st.cache_data(ttl=86400, show_spinner=False)  # Cache for 24 hours (1 day)
def fetch_sp500_historical_data():
    """
    Fetches comprehensive S&P 500 historical data.
    Cached for 24 hours to avoid repeated API calls.
    """
    try:
        # Fetch maximum available history for S&P 500
        sp500 = yf.Ticker("^GSPC")
        df = sp500.history(period="max", auto_adjust=True)
        
        if df.empty:
            st.error("Failed to fetch S&P 500 data")
            return pd.DataFrame()
        
        # Calculate daily returns
        df['Returns'] = df['Close'].pct_change() * 100
        
        # Add time-based columns
        df['Year'] = df.index.year
        df['Month'] = df.index.month
        df['MonthName'] = df.index.strftime('%B')
        df['Week'] = df.index.isocalendar().week
        df['DayOfWeek'] = df.index.dayofweek  # Monday=0, Sunday=6
        df['DayName'] = df.index.strftime('%A')
        df['Quarter'] = df.index.quarter
        
        return df
    
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=86400, show_spinner=False)
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

@st.cache_data(ttl=86400, show_spinner=False)
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

@st.cache_data(ttl=86400, show_spinner=False)
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

@st.cache_data(ttl=86400, show_spinner=False)
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

# Fetch data with loading indicator
with st.spinner("Loading S&P 500 historical data..."):
    sp500_data = fetch_sp500_historical_data()

if not sp500_data.empty:
    # Data info
    st.markdown(f"""
        <div style="background: var(--inputlight); padding: 15px; border-radius: 10px; border: 1px solid var(--neutral); margin-bottom: 20px;">
            <p style="margin: 0; color: var(--muted-text-new);">
                📊 <strong>Data Range:</strong> {sp500_data.index[0].strftime('%B %d, %Y')} to {sp500_data.index[-1].strftime('%B %d, %Y')} 
                ({len(sp500_data):,} trading days)
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
    
    with st.expander("📊 View Detailed Monthly Statistics"):
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
    
    with st.expander("📊 View Detailed Weekly Statistics"):
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
    
    with st.expander("📊 View Detailed Election Cycle Statistics"):
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
