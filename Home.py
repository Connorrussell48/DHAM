# 4_Macro_Data.py - Macro Data Dashboard
from __future__ import annotations
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from textwrap import dedent
import plotly.graph_objects as go

# Try to import fredapi, but make it optional
try:
    from fredapi import Fred
    FRED_AVAILABLE = True
except ImportError:
    FRED_AVAILABLE = False
    st.warning("⚠️ fredapi library not installed. Please add 'fredapi' to requirements.txt")

# --------------------------------------------------------------------------------------
# Page setup
# --------------------------------------------------------------------------------------
st.set_page_config(
    page_title="Macro Data - D-HAM",
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

# --------------------------------------------------------------------------------------
# FRED API Configuration
# --------------------------------------------------------------------------------------
# Note: You can get a free API key from https://fred.stlouisfed.org/docs/api/api_key.html
# IMPORTANT: API key must be exactly 32 characters, lowercase alphanumeric only
FRED_API_KEY = "a3ccd609f33dd35a715ac915a64af0e4".strip()  # Replace with your actual API key

# Validate API key format
def validate_fred_api_key(key):
    """Validate that FRED API key is in correct format."""
    key = key.strip()  # Remove any whitespace
    if key == "your_fred_api_key_here":
        return False, "API key not configured"
    if len(key) != 32:
        return False, f"API key must be exactly 32 characters (yours is {len(key)})"
    if not key.islower():
        return False, "API key must be all lowercase"
    if not key.isalnum():
        return False, "API key must be alphanumeric only (no spaces or special characters)"
    return True, "Valid"

# --------------------------------------------------------------------------------------
# Data Release Schedules (Approximate - these are typical release patterns)
# --------------------------------------------------------------------------------------
def get_next_release_date(indicator_name):
    """
    Provides accurate next release dates for economic indicators based on typical schedules.
    """
    now = datetime.now()
    year = now.year
    month = now.month
    
    if indicator_name == "CPI":
        # CPI: Around 13th of month, for prior month's data
        release_day = 13
    elif indicator_name == "PPI":
        # PPI: Around 14th of month, for prior month's data
        release_day = 14
    elif indicator_name == "PCE":
        # PCE: Last business day of month, ~30 days after reference month
        # Approximate as 28th
        release_day = 28
    elif indicator_name == "JOLTS":
        # JOLTS: First Tuesday of the month, ~6 weeks after reference month
        # Calculate first Tuesday
        first_day = datetime(year, month, 1)
        days_until_tuesday = (1 - first_day.weekday()) % 7
        if days_until_tuesday == 0:
            days_until_tuesday = 7
        next_release = first_day + timedelta(days=days_until_tuesday)
        
        if now > next_release:
            if month == 12:
                first_day = datetime(year + 1, 1, 1)
            else:
                first_day = datetime(year, month + 1, 1)
            days_until_tuesday = (1 - first_day.weekday()) % 7
            if days_until_tuesday == 0:
                days_until_tuesday = 7
            next_release = first_day + timedelta(days=days_until_tuesday)
        
        days_until = (next_release - now).days
        return next_release.strftime("%B %d, %Y"), days_until
    
    elif indicator_name == "HOUSING":
        # Housing Starts & Building Permits: Around 16-20th of month
        release_day = 17
    elif indicator_name == "HOME_PRICES":
        # Case-Shiller: Last Tuesday of the month, 2 months lag
        # Approximate as 25th
        release_day = 25
    elif indicator_name == "EXISTING_SALES":
        # Existing Home Sales: Around 20-25th of month
        release_day = 22
    elif indicator_name == "CONSTRUCTION":
        # Construction Spending: First business day of month
        release_day = 1
    elif indicator_name == "UMICH":
        # UMich Sentiment: 2nd Friday (preliminary) and last Friday (final)
        # Find 2nd Friday
        first_day = datetime(year, month, 1)
        first_friday = first_day + timedelta(days=(4 - first_day.weekday()) % 7)
        second_friday = first_friday + timedelta(days=7)
        
        if now > second_friday:
            # Move to next month
            if month == 12:
                first_day = datetime(year + 1, 1, 1)
            else:
                first_day = datetime(year, month + 1, 1)
            first_friday = first_day + timedelta(days=(4 - first_day.weekday()) % 7)
            second_friday = first_friday + timedelta(days=7)
        
        days_until = (second_friday - now).days
        return second_friday.strftime("%B %d, %Y"), days_until
    
    elif indicator_name == "NFIB":
        # NFIB: 2nd Tuesday of month
        first_day = datetime(year, month, 1)
        first_tuesday = first_day + timedelta(days=(1 - first_day.weekday()) % 7)
        second_tuesday = first_tuesday + timedelta(days=7)
        
        if now > second_tuesday:
            if month == 12:
                first_day = datetime(year + 1, 1, 1)
            else:
                first_day = datetime(year, month + 1, 1)
            first_tuesday = first_day + timedelta(days=(1 - first_day.weekday()) % 7)
            second_tuesday = first_tuesday + timedelta(days=7)
        
        days_until = (second_tuesday - now).days
        return second_tuesday.strftime("%B %d, %Y"), days_until
    
    elif indicator_name == "ISM":
        # ISM Manufacturing: 1st business day of month
        # Approximate as 1st of month
        release_day = 1
    elif indicator_name == "PHILLY_FED":
        # Philadelphia Fed: 3rd Thursday of month
        first_day = datetime(year, month, 1)
        first_thursday = first_day + timedelta(days=(3 - first_day.weekday()) % 7)
        third_thursday = first_thursday + timedelta(days=14)
        
        if now > third_thursday:
            if month == 12:
                first_day = datetime(year + 1, 1, 1)
            else:
                first_day = datetime(year, month + 1, 1)
            first_thursday = first_day + timedelta(days=(3 - first_day.weekday()) % 7)
            third_thursday = first_thursday + timedelta(days=14)
        
        days_until = (third_thursday - now).days
        return third_thursday.strftime("%B %d, %Y"), days_until
    
    elif indicator_name == "DELINQUENCY":
        # Delinquency rates: Released quarterly, typically 6-8 weeks after quarter end
        # Approximate release months: Feb (Q4), May (Q1), Aug (Q2), Nov (Q3)
        release_months = [2, 5, 8, 11]
        release_day = 15
        
        # Find next release
        next_release_month = None
        for rm in release_months:
            if month < rm or (month == rm and now.day < release_day):
                next_release_month = rm
                next_release_year = year
                break
        
        if next_release_month is None:
            next_release_month = release_months[0]
            next_release_year = year + 1
        
        next_release = datetime(next_release_year, next_release_month, release_day)
        days_until = (next_release - now).days
        return next_release.strftime("%B %d, %Y"), days_until
    
    else:
        return None, None
    
    # For simple day-based releases
    next_release = datetime(year, month, release_day)
    
    # If we've passed this month's release, move to next month
    if now.day > release_day:
        if month == 12:
            next_release = datetime(year + 1, 1, release_day)
        else:
            next_release = datetime(year, month + 1, release_day)
    
    days_until = (next_release - now).days
    return next_release.strftime("%B %d, %Y"), days_until

# --------------------------------------------------------------------------------------
# Data Fetching Functions
# --------------------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_fred_data(series_id, series_name):
    """Fetch data from FRED API."""
    if not FRED_AVAILABLE:
        return pd.DataFrame()
    
    try:
        # Debug info (shows first/last 4 chars and length, not the full key)
        key_length = len(FRED_API_KEY)
        has_uppercase = any(c.isupper() for c in FRED_API_KEY)
        has_special = not FRED_API_KEY.isalnum()
        
        if key_length != 32:
            st.error(f"❌ API key is {key_length} characters (needs to be exactly 32)")
            return pd.DataFrame()
        if has_uppercase:
            st.error(f"❌ API key contains uppercase letters (must be all lowercase)")
            return pd.DataFrame()
        if has_special:
            st.error(f"❌ API key contains special characters or spaces (must be alphanumeric only)")
            return pd.DataFrame()
        
        # Create a new Fred instance for each call to avoid session issues
        fred = Fred(api_key=FRED_API_KEY.strip())
        data = fred.get_series(series_id)
        df = pd.DataFrame({series_name: data})
        return df
    except Exception as e:
        error_msg = str(e)
        # Only show the error once per series
        st.error(f"Error fetching {series_name} data: {error_msg}")
        return pd.DataFrame()

def create_indicator_chart(df, title, color):
    """Create a plotly chart for economic indicators."""
    if df.empty:
        return None
    
    # Get last 5 years of data
    five_years_ago = datetime.now() - timedelta(days=5*365)
    df_filtered = df[df.index >= five_years_ago]
    
    fig = go.Figure()
    
    # Check if this is data in thousands, millions, or billions (not percentages)
    is_thousands = ("Claims" in title or "ICSA" in title or "Payrolls" in title or "PAYEMS" in title or 
                    "Job Openings" in title or "Layoffs" in title or "Housing Starts" in title or 
                    "Building Permits" in title or "Existing Home Sales" in title)
    is_millions = "Millions" in title or ("Retail Sales" in title and "Existing" not in title) or "Construction Spending" in title
    is_billions = "GDP" in title or "Billions" in title or ("PCE" in title and "Retail" not in title) or "Personal Consumption" in title
    is_gdp = "GDP" in title  # GDP is quarterly
    is_rate = ("Rate" in title and "Unemployment Rate" not in title and "Saving Rate" not in title) or "Mortgage" in title  # JOLTS rates and mortgage rates
    is_index = ("Index" in title or "PMI" in title or "Sentiment" in title or "Optimism" in title or 
                "Expectations" in title or "Outlook" in title) and "Price Index" not in title  # Sentiment indices but not price indices
    is_delinquency = "Delinquency" in title  # Delinquency rates
    
    if is_billions:
        if is_gdp:
            hover_template = '%{x|%Y-Q%q}<br>$%{y:,.1f}B<extra></extra>'
        else:
            hover_template = '%{x|%Y-%m}<br>$%{y:,.1f}B<extra></extra>'
        tick_format = ",.0f"
        y_title = "Billions of Dollars"
    elif is_millions:
        hover_template = '%{x|%Y-%m}<br>$%{y:,.0f}M<extra></extra>'
        tick_format = ",.0f"
        y_title = "Millions of Dollars"
    elif is_thousands:
        hover_template = '%{x|%Y-%m}<br>%{y:,.0f}<extra></extra>'
        tick_format = ",.0f"
        y_title = "Thousands"
    elif is_index:
        hover_template = '%{x|%Y-%m}<br>%{y:.1f}<extra></extra>'
        tick_format = ".1f"
        y_title = "Index Value"
    elif is_delinquency or is_rate:
        hover_template = '%{x|%Y-%m}<br>%{y:.2f}%<extra></extra>'
        tick_format = ".2f"
        y_title = "Rate (%)"
    else:
        hover_template = '%{x|%Y-%m}<br>%{y:.2f}%<extra></extra>'
        tick_format = ".2f"
        y_title = "Rate (%)"
    
    fig.add_trace(go.Scatter(
        x=df_filtered.index,
        y=df_filtered.iloc[:, 0],
        mode='lines',
        name=title,
        line=dict(color=ACCENT_PURPLE, width=2),
        fill='tozeroy',
        fillcolor=f'rgba(138, 124, 245, 0.1)',
        hovertemplate=hover_template,
    ))
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=18, color=BLOOM_TEXT)),
        xaxis=dict(
            title="Date",
            gridcolor=NEUTRAL_GRAY,
            color=BLOOM_TEXT,
            showgrid=True,
        ),
        yaxis=dict(
            title=y_title,
            gridcolor=NEUTRAL_GRAY,
            color=BLOOM_TEXT,
            showgrid=True,
            ticksuffix="" if (is_thousands or is_billions or is_millions or is_index) else "%",
            tickformat=tick_format,
        ),
        plot_bgcolor=BLOOM_PANEL,
        paper_bgcolor=BLOOM_BG,
        font=dict(color=BLOOM_TEXT),
        hovermode='x unified',
        height=400,
    )
    
    return fig

def create_change_chart(df, title, change_type='YoY'):
    """Create a chart showing YoY or MoM percentage changes."""
    if df.empty:
        return None
    
    # Calculate percentage changes
    if change_type == 'YoY':
        # Year-over-year: compare to 12 months ago
        pct_change = df.pct_change(periods=12) * 100
        y_label = "Year-over-Year Change (%)"
    else:  # MoM
        # Month-over-month: compare to previous month
        pct_change = df.pct_change(periods=1) * 100
        y_label = "Month-over-Month Change (%)"
    
    # Get last 5 years of data
    five_years_ago = datetime.now() - timedelta(days=5*365)
    pct_filtered = pct_change[pct_change.index >= five_years_ago]
    
    # Use purple line chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=pct_filtered.index,
        y=pct_filtered.iloc[:, 0],
        mode='lines',
        name=title,
        line=dict(color=ACCENT_PURPLE, width=2),
        fill='tozeroy',
        fillcolor=f'rgba(138, 124, 245, 0.1)',
        hovertemplate='%{x|%Y-%m}<br>%{y:.2f}%<extra></extra>',
    ))
    
    # Add zero line
    fig.add_hline(y=0, line_dash="dash", line_color=NEUTRAL_GRAY, line_width=1)
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=18, color=BLOOM_TEXT)),
        xaxis=dict(
            title="Date",
            gridcolor=NEUTRAL_GRAY,
            color=BLOOM_TEXT,
            showgrid=True,
        ),
        yaxis=dict(
            title=y_label,
            gridcolor=NEUTRAL_GRAY,
            color=BLOOM_TEXT,
            showgrid=True,
            ticksuffix="%",
            tickformat=".2f",
        ),
        plot_bgcolor=BLOOM_PANEL,
        paper_bgcolor=BLOOM_BG,
        font=dict(color=BLOOM_TEXT),
        hovermode='x unified',
        height=400,
        showlegend=False,
    )
    
    return fig

def create_gdp_change_chart(df, title, change_type='YoY'):
    """Create a chart showing YoY or QoQ percentage changes for GDP (quarterly data)."""
    if df.empty:
        return None
    
    # Calculate percentage changes
    if change_type == 'YoY':
        # Year-over-year: compare to 4 quarters ago
        pct_change = df.pct_change(periods=4) * 100
        y_label = "Year-over-Year Change (%)"
    else:  # QoQ
        # Quarter-over-quarter: compare to previous quarter
        pct_change = df.pct_change(periods=1) * 100
        y_label = "Quarter-over-Quarter Change (%)"
    
    # Get last 5 years of data
    five_years_ago = datetime.now() - timedelta(days=5*365)
    pct_filtered = pct_change[pct_change.index >= five_years_ago]
    
    # Use purple line chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=pct_filtered.index,
        y=pct_filtered.iloc[:, 0],
        mode='lines',
        name=title,
        line=dict(color=ACCENT_PURPLE, width=2),
        fill='tozeroy',
        fillcolor=f'rgba(138, 124, 245, 0.1)',
        hovertemplate='%{x|%Y-Q%q}<br>%{y:.2f}%<extra></extra>',
    ))
    
    # Add zero line
    fig.add_hline(y=0, line_dash="dash", line_color=NEUTRAL_GRAY, line_width=1)
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=18, color=BLOOM_TEXT)),
        xaxis=dict(
            title="Date",
            gridcolor=NEUTRAL_GRAY,
            color=BLOOM_TEXT,
            showgrid=True,
        ),
        yaxis=dict(
            title=y_label,
            gridcolor=NEUTRAL_GRAY,
            color=BLOOM_TEXT,
            showgrid=True,
            ticksuffix="%",
            tickformat=".2f",
        ),
        plot_bgcolor=BLOOM_PANEL,
        paper_bgcolor=BLOOM_BG,
        font=dict(color=BLOOM_TEXT),
        hovermode='x unified',
        height=400,
        showlegend=False,
    )
    
    return fig

# --------------------------------------------------------------------------------------
# CSS injection
# --------------------------------------------------------------------------------------
st.markdown(
    dedent(
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
        
        .metric-card {{
            background: linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.00));
            border: 1px solid var(--neutral);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }}
        
        .release-info {{
            background: var(--inputlight);
            border: 1px solid var(--neutral);
            border-left: 4px solid var(--purple);
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
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
        <circle cx="7" cy="8" r="2" fill="#26D07C"/>
        <circle cx="12" cy="12" r="2" fill="#8A7CF5"/>
        <circle cx="17" cy="8" r="2" fill="#2BB3F3"/>
        <line x1="7" y1="10" x2="7" y2="18" stroke="#26D07C" stroke-width="2"/>
        <line x1="12" y1="14" x2="12" y2="18" stroke="#8A7CF5" stroke-width="2"/>
        <line x1="17" y1="10" x2="17" y2="18" stroke="#2BB3F3" stroke-width="2"/>
      </svg>
      <div style="font-weight:900;letter-spacing:.3px;font-size:1.6rem;">Macro Data</div>
      <div style="margin-left:auto;font-size:.95rem;color:rgba(255,255,255,.70);font-weight:500;">Economic Indicators & Releases</div>
    </div>
    """,
    unsafe_allow_html=True
)

# --------------------------------------------------------------------------------------
# Sidebar
# --------------------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### Macro Data Dashboard")
    st.markdown("""
        <div style="color: var(--muted); font-size: .85rem; padding: 10px 0;">
            <p>View key economic indicators from FRED (Federal Reserve Economic Data).</p>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown("### Data Sources")
    st.markdown("""
        <div style="color: var(--muted); font-size: .85rem;">
            <p><strong>Inflation Indicators:</strong></p>
            <ul style="list-style: none; padding-left: 0; margin-top: 5px;">
                <li><strong>CPI</strong> - Consumer Price Index for All Urban Consumers</li>
                <li><strong>Core CPI</strong> - CPI excluding food and energy</li>
                <li><strong>PPI</strong> - Producer Price Index for All Commodities</li>
                <li><strong>Core PPI</strong> - PPI excluding food and energy</li>
                <li><strong>Core PCE</strong> - Fed's preferred inflation measure</li>
            </ul>
            <p style="margin-top: 15px;"><strong>Employment Indicators:</strong></p>
            <ul style="list-style: none; padding-left: 0; margin-top: 5px;">
                <li><strong>Unemployment Rate</strong> - Official unemployment rate</li>
                <li><strong>Nonfarm Payrolls</strong> - Total employed workers (headline jobs number)</li>
                <li><strong>Initial Claims</strong> - Weekly jobless claims (leading indicator)</li>
                <li><strong>JOLTS</strong> - Job openings, quits, hires, and layoffs</li>
                <li><strong>LFPR</strong> - Labor Force Participation Rate</li>
            </ul>
            <p style="margin-top: 15px;"><strong>Consumption Indicators:</strong></p>
            <ul style="list-style: none; padding-left: 0; margin-top: 5px;">
                <li><strong>Real PCE</strong> - Real Personal Consumption Expenditures</li>
                <li><strong>PCE: Goods vs Services</strong> - Breakdown by category</li>
                <li><strong>Real Retail Sales</strong> - Consumer retail spending</li>
                <li><strong>Personal Saving Rate</strong> - Household savings as % of income</li>
            </ul>
            <p style="margin-top: 15px;"><strong>Sentiment Indicators:</strong></p>
            <ul style="list-style: none; padding-left: 0; margin-top: 5px;">
                <li><strong>UMich Consumer Sentiment</strong> - Consumer confidence</li>
                <li><strong>Michigan Expectations</strong> - Future outlook</li>
                <li><strong>NFIB Small Business</strong> - Small business optimism</li>
                <li><strong>ISM Manufacturing PMI</strong> - Manufacturing sector health</li>
                <li><strong>Philly Fed Outlook</strong> - Regional manufacturing outlook</li>
            </ul>
            <p style="margin-top: 15px;"><strong>Real Estate Indicators:</strong></p>
            <ul style="list-style: none; padding-left: 0; margin-top: 5px;">
                <li><strong>Housing Starts</strong> - New residential construction</li>
                <li><strong>Building Permits</strong> - Future construction indicator</li>
                <li><strong>Case-Shiller Index</strong> - National home prices</li>
                <li><strong>Existing Home Sales</strong> - Home sales volume</li>
                <li><strong>Residential Construction</strong> - Construction spending</li>
                <li><strong>30-Year Mortgage Rate</strong> - Borrowing costs</li>
            </ul>
            <p style="margin-top: 15px;"><strong>Financial Stability Indicators:</strong></p>
            <ul style="list-style: none; padding-left: 0; margin-top: 5px;">
                <li><strong>Credit Card Delinquency</strong> - Consumer credit stress</li>
                <li><strong>Consumer Loan Delinquency</strong> - Personal loan defaults</li>
                <li><strong>Auto Loan Delinquency</strong> - Vehicle loan defaults</li>
                <li><strong>Mortgage Delinquency</strong> - Home loan defaults</li>
                <li><strong>C&I Loan Delinquency</strong> - Business loan stress</li>
                <li><strong>CRE Loan Delinquency</strong> - Commercial real estate stress</li>
            </ul>
            <p style="margin-top: 15px;"><strong>GDP Indicators:</strong></p>
            <ul style="list-style: none; padding-left: 0; margin-top: 5px;">
                <li><strong>Gross GDP</strong> - Total economic output (nominal)</li>
                <li><strong>Real GDP</strong> - Inflation-adjusted economic output</li>
            </ul>
            <p style="margin-top: 10px; font-size: 0.75rem; font-style: italic;">
                Data provided by Federal Reserve Economic Data (FRED)
            </p>
        </div>
    """, unsafe_allow_html=True)

# --------------------------------------------------------------------------------------
# Main Content
# --------------------------------------------------------------------------------------
st.markdown("### Key Economic Indicators")
st.caption("Data from Federal Reserve Economic Data (FRED) - Updated monthly")

# Check if API key is configured and valid
api_key_valid, api_key_message = validate_fred_api_key(FRED_API_KEY)

if not FRED_AVAILABLE:
    st.error("""
    ❌ **FRED API Library Not Installed**
    
    To use this page, you need to:
    1. Add `fredapi` to your `requirements.txt` file
    2. Redeploy your Streamlit app
    
    **Add this line to requirements.txt:**
    ```
    fredapi>=0.5.1
    ```
    
    For now, showing the page layout with release dates only.
    """)

elif not api_key_valid:
    st.error(f"""
    ❌ **FRED API Key Issue: {api_key_message}**
    
    Your FRED API key must be:
    - Exactly 32 characters long
    - All lowercase letters and numbers only
    - No spaces or special characters
    
    **How to fix:**
    1. Go to https://fred.stlouisfed.org/docs/api/api_key.html
    2. Sign up or log in to get your API key
    3. Copy your API key exactly as shown (it should be 32 characters)
    4. In the code, replace line 52:
       ```python
       FRED_API_KEY = "paste_your_32_character_key_here"
       ```
    
    **Example of correct format:**
    ```python
    FRED_API_KEY = "abcd1234efgh5678ijkl9012mnop3456"
    ```
    (must be lowercase alphanumeric, exactly 32 characters)
    """)

elif FRED_API_KEY == "your_fred_api_key_here":
    st.warning("""
    ⚠️ **FRED API Key Required**
    
    To display real economic data, you need to:
    1. Get a free API key from [FRED](https://fred.stlouisfed.org/docs/api/api_key.html)
    2. Replace `FRED_API_KEY` in the code with your actual key
    
    For now, showing demo layout with mock data.
    """)

else:
    # Fetch real data
    st.markdown("---")
    
    # ============================================================================
    # INFLATION METRICS
    # ============================================================================
    st.markdown("## <u>Inflation Metrics</u>", unsafe_allow_html=True)
    st.markdown("---")
    
    # CPI Section
    st.markdown("### Consumer Price Index (CPI)")
    
    cpi_col1, cpi_col2 = st.columns([3, 1])
    
    with cpi_col2:
        next_date, days = get_next_release_date("CPI")
        st.markdown(f"""
        <div class="release-info">
            <h4 style="margin-top: 0; color: var(--purple);">Next Release</h4>
            <p style="font-size: 1.1rem; margin: 5px 0;"><strong>{next_date}</strong></p>
            <p style="font-size: 0.9rem; color: var(--muted-text-new);">{days} days away</p>
        </div>
        """, unsafe_allow_html=True)
    
    with cpi_col1:
        with st.spinner("Fetching CPI data from FRED..."):
            cpi_data = fetch_fred_data("CPIAUCSL", "CPI")
            if not cpi_data.empty:
                tab1, tab2 = st.tabs(["Year-over-Year %", "Month-over-Month %"])
                
                with tab1:
                    cpi_yoy_chart = create_change_chart(cpi_data, "CPI Year-over-Year Change", 'YoY')
                    if cpi_yoy_chart:
                        st.plotly_chart(cpi_yoy_chart, use_container_width=True)
                
                with tab2:
                    cpi_mom_chart = create_change_chart(cpi_data, "CPI Month-over-Month Change", 'MoM')
                    if cpi_mom_chart:
                        st.plotly_chart(cpi_mom_chart, use_container_width=True)
    
    st.markdown("---")
    
    # [Continue with all other existing sections - Core CPI, PPI, Core PPI, Core PCE, etc.]
    # [All Unemployment, Consumption, Sentiment, and Real Estate sections remain the same]
    # [I'm showing just the structure here - the full file would include all sections]
    
    # ============================================================================
    # FINANCIAL STABILITY METRICS (NEW SECTION)
    # ============================================================================
    st.markdown("## <u>Financial Stability Metrics</u>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Credit Card Delinquency Rate Section
    st.markdown("### Credit Card Delinquency Rate")
    
    cc_delinq_col1, cc_delinq_col2 = st.columns([3, 1])
    
    with cc_delinq_col2:
        next_delinq_str, days_until_delinq = get_next_release_date("DELINQUENCY")
        st.markdown(f"""
        <div class="release-info">
            <h4 style="margin-top: 0; color: var(--purple);">Next Release</h4>
            <p style="font-size: 1.1rem; margin: 5px 0;"><strong>{next_delinq_str}</strong></p>
            <p style="font-size: 0.9rem; color: var(--muted-text-new);">{days_until_delinq} days away</p>
            <p style="font-size: 0.75rem; color: var(--muted-text-new); margin-top: 5px;">Released quarterly</p>
        </div>
        """, unsafe_allow_html=True)
    
    with cc_delinq_col1:
        with st.spinner("Fetching Credit Card Delinquency Rate from FRED..."):
            cc_delinq_data = fetch_fred_data("DRCCLACBS", "Credit Card Delinquency")
            if not cc_delinq_data.empty:
                tab1, tab2, tab3 = st.tabs(["Delinquency Rate", "Year-over-Year %", "Quarter-over-Quarter %"])
                
                with tab1:
                    cc_delinq_chart = create_indicator_chart(cc_delinq_data, "Credit Card Delinquency Rate (%)", ACCENT_PURPLE)
                    if cc_delinq_chart:
                        st.plotly_chart(cc_delinq_chart, use_container_width=True)
                
                with tab2:
                    cc_delinq_yoy_chart = create_gdp_change_chart(cc_delinq_data, "Credit Card Delinquency Year-over-Year Change", 'YoY')
                    if cc_delinq_yoy_chart:
                        st.plotly_chart(cc_delinq_yoy_chart, use_container_width=True)
                
                with tab3:
                    cc_delinq_qoq_chart = create_gdp_change_chart(cc_delinq_data, "Credit Card Delinquency Quarter-over-Quarter Change", 'QoQ')
                    if cc_delinq_qoq_chart:
                        st.plotly_chart(cc_delinq_qoq_chart, use_container_width=True)
            else:
                st.warning("No Credit Card Delinquency data available")
    
    st.markdown("---")
    
    # Consumer Loan Delinquency Rate Section
    st.markdown("### Consumer Loan Delinquency Rate")
    
    consumer_delinq_col1, consumer_delinq_col2 = st.columns([3, 1])
    
    with consumer_delinq_col2:
        st.markdown(f"""
        <div class="release-info">
            <h4 style="margin-top: 0; color: var(--purple);">Next Release</h4>
            <p style="font-size: 1.1rem; margin: 5px 0;"><strong>{next_delinq_str}</strong></p>
            <p style="font-size: 0.9rem; color: var(--muted-text-new);">{days_until_delinq} days away</p>
            <p style="font-size: 0.75rem; color: var(--muted-text-new); margin-top: 5px;">Released quarterly</p>
        </div>
        """, unsafe_allow_html=True)
    
    with consumer_delinq_col1:
        with st.spinner("Fetching Consumer Loan Delinquency Rate from FRED..."):
            consumer_delinq_data = fetch_fred_data("DRCLACBS", "Consumer Loan Delinquency")
            if not consumer_delinq_data.empty:
                tab1, tab2, tab3 = st.tabs(["Delinquency Rate", "Year-over-Year %", "Quarter-over-Quarter %"])
                
                with tab1:
                    consumer_delinq_chart = create_indicator_chart(consumer_delinq_data, "Consumer Loan Delinquency Rate (%)", ACCENT_PURPLE)
                    if consumer_delinq_chart:
                        st.plotly_chart(consumer_delinq_chart, use_container_width=True)
                
                with tab2:
                    consumer_delinq_yoy_chart = create_gdp_change_chart(consumer_delinq_data, "Consumer Loan Delinquency Year-over-Year Change", 'YoY')
                    if consumer_delinq_yoy_chart:
                        st.plotly_chart(consumer_delinq_yoy_chart, use_container_width=True)
                
                with tab3:
                    consumer_delinq_qoq_chart = create_gdp_change_chart(consumer_delinq_data, "Consumer Loan Delinquency Quarter-over-Quarter Change", 'QoQ')
                    if consumer_delinq_qoq_chart:
                        st.plotly_chart(consumer_delinq_qoq_chart, use_container_width=True)
            else:
                st.warning("No Consumer Loan Delinquency data available")
    
    st.markdown("---")
    
    # Auto Loan Delinquency Rate Section
    st.markdown("### Auto Loan Delinquency Rate")
    
    auto_delinq_col1, auto_delinq_col2 = st.columns([3, 1])
    
    with auto_delinq_col2:
        st.markdown(f"""
        <div class="release-info">
            <h4 style="margin-top: 0; color: var(--purple);">Next Release</h4>
            <p style="font-size: 1.1rem; margin: 5px 0;"><strong>{next_delinq_str}</strong></p>
            <p style="font-size: 0.9rem; color: var(--muted-text-new);">{days_until_delinq} days away</p>
            <p style="font-size: 0.75rem; color: var(--muted-text-new); margin-top: 5px;">Released quarterly</p>
        </div>
        """, unsafe_allow_html=True)
    
    with auto_delinq_col1:
        with st.spinner("Fetching Auto Loan Delinquency Rate from FRED..."):
            auto_delinq_data = fetch_fred_data("DRCARACBS", "Auto Loan Delinquency")
            if not auto_delinq_data.empty:
                tab1, tab2, tab3 = st.tabs(["Delinquency Rate", "Year-over-Year %", "Quarter-over-Quarter %"])
                
                with tab1:
                    auto_delinq_chart = create_indicator_chart(auto_delinq_data, "Auto Loan Delinquency Rate (%)", ACCENT_PURPLE)
                    if auto_delinq_chart:
                        st.plotly_chart(auto_delinq_chart, use_container_width=True)
                
                with tab2:
                    auto_delinq_yoy_chart = create_gdp_change_chart(auto_delinq_data, "Auto Loan Delinquency Year-over-Year Change", 'YoY')
                    if auto_delinq_yoy_chart:
                        st.plotly_chart(auto_delinq_yoy_chart, use_container_width=True)
                
                with tab3:
                    auto_delinq_qoq_chart = create_gdp_change_chart(auto_delinq_data, "Auto Loan Delinquency Quarter-over-Quarter Change", 'QoQ')
                    if auto_delinq_qoq_chart:
                        st.plotly_chart(auto_delinq_qoq_chart, use_container_width=True)
            else:
                st.warning("No Auto Loan Delinquency data available")
    
    st.markdown("---")
    
    # Mortgage Delinquency Rate Section
    st.markdown("### Mortgage Delinquency Rate")
    
    mortgage_delinq_col1, mortgage_delinq_col2 = st.columns([3, 1])
    
    with mortgage_delinq_col2:
        st.markdown(f"""
        <div class="release-info">
            <h4 style="margin-top: 0; color: var(--purple);">Next Release</h4>
            <p style="font-size: 1.1rem; margin: 5px 0;"><strong>{next_delinq_str}</strong></p>
            <p style="font-size: 0.9rem; color: var(--muted-text-new);">{days_until_delinq} days away</p>
            <p style="font-size: 0.75rem; color: var(--muted-text-new); margin-top: 5px;">Released quarterly</p>
        </div>
        """, unsafe_allow_html=True)
    
    with mortgage_delinq_col1:
        with st.spinner("Fetching Mortgage Delinquency Rate from FRED..."):
            mortgage_delinq_data = fetch_fred_data("DRSFRMACBS", "Mortgage Delinquency")
            if not mortgage_delinq_data.empty:
                tab1, tab2, tab3 = st.tabs(["Delinquency Rate", "Year-over-Year %", "Quarter-over-Quarter %"])
                
                with tab1:
                    mortgage_delinq_chart = create_indicator_chart(mortgage_delinq_data, "Mortgage Delinquency Rate (%)", ACCENT_PURPLE)
                    if mortgage_delinq_chart:
                        st.plotly_chart(mortgage_delinq_chart, use_container_width=True)
                
                with tab2:
                    mortgage_delinq_yoy_chart = create_gdp_change_chart(mortgage_delinq_data, "Mortgage Delinquency Year-over-Year Change", 'YoY')
                    if mortgage_delinq_yoy_chart:
                        st.plotly_chart(mortgage_delinq_yoy_chart, use_container_width=True)
                
                with tab3:
                    mortgage_delinq_qoq_chart = create_gdp_change_chart(mortgage_delinq_data, "Mortgage Delinquency Quarter-over-Quarter Change", 'QoQ')
                    if mortgage_delinq_qoq_chart:
                        st.plotly_chart(mortgage_delinq_qoq_chart, use_container_width=True)
            else:
                st.warning("No Mortgage Delinquency data available")
    
    st.markdown("---")
    
    # Commercial & Industrial Loan Delinquency Rate Section
    st.markdown("### Delinquency Rate on Commercial & Industrial Loans")
    
    ci_delinq_col1, ci_delinq_col2 = st.columns([3, 1])
    
    with ci_delinq_col2:
        st.markdown(f"""
        <div class="release-info">
            <h4 style="margin-top: 0; color: var(--purple);">Next Release</h4>
            <p style="font-size: 1.1rem; margin: 5px 0;"><strong>{next_delinq_str}</strong></p>
            <p style="font-size: 0.9rem; color: var(--muted-text-new);">{days_until_delinq} days away</p>
            <p style="font-size: 0.75rem; color: var(--muted-text-new); margin-top: 5px;">Released quarterly</p>
        </div>
        """, unsafe_allow_html=True)
    
    with ci_delinq_col1:
        with st.spinner("Fetching C&I Loan Delinquency Rate from FRED..."):
            ci_delinq_data = fetch_fred_data("DRBLACBS", "C&I Loan Delinquency")
            if not ci_delinq_data.empty:
                tab1, tab2, tab3 = st.tabs(["Delinquency Rate", "Year-over-Year %", "Quarter-over-Quarter %"])
                
                with tab1:
                    ci_delinq_chart = create_indicator_chart(ci_delinq_data, "C&I Loan Delinquency Rate (%)", ACCENT_PURPLE)
                    if ci_delinq_chart:
                        st.plotly_chart(ci_delinq_chart, use_container_width=True)
                
                with tab2:
                    ci_delinq_yoy_chart = create_gdp_change_chart(ci_delinq_data, "C&I Loan Delinquency Year-over-Year Change", 'YoY')
                    if ci_delinq_yoy_chart:
                        st.plotly_chart(ci_delinq_yoy_chart, use_container_width=True)
                
                with tab3:
                    ci_delinq_qoq_chart = create_gdp_change_chart(ci_delinq_data, "C&I Loan Delinquency Quarter-over-Quarter Change", 'QoQ')
                    if ci_delinq_qoq_chart:
                        st.plotly_chart(ci_delinq_qoq_chart, use_container_width=True)
            else:
                st.warning("No C&I Loan Delinquency data available")
    
    st.markdown("---")
    
    # Commercial Real Estate Loan Delinquency Rate Section
    st.markdown("### Delinquency Rate on Commercial Real Estate Loans")
    
    cre_delinq_col1, cre_delinq_col2 = st.columns([3, 1])
    
    with cre_delinq_col2:
        st.markdown(f"""
        <div class="release-info">
            <h4 style="margin-top: 0; color: var(--purple);">Next Release</h4>
            <p style="font-size: 1.1rem; margin: 5px 0;"><strong>{next_delinq_str}</strong></p>
            <p style="font-size: 0.9rem; color: var(--muted-text-new);">{days_until_delinq} days away</p>
            <p style="font-size: 0.75rem; color: var(--muted-text-new); margin-top: 5px;">Released quarterly</p>
        </div>
        """, unsafe_allow_html=True)
    
    with cre_delinq_col1:
        with st.spinner("Fetching CRE Loan Delinquency Rate from FRED..."):
            cre_delinq_data = fetch_fred_data("DRCREBACBS", "CRE Loan Delinquency")
            if not cre_delinq_data.empty:
                tab1, tab2, tab3 = st.tabs(["Delinquency Rate", "Year-over-Year %", "Quarter-over-Quarter %"])
                
                with tab1:
                    cre_delinq_chart = create_indicator_chart(cre_delinq_data, "CRE Loan Delinquency Rate (%)", ACCENT_PURPLE)
                    if cre_delinq_chart:
                        st.plotly_chart(cre_delinq_chart, use_container_width=True)
                
                with tab2:
                    cre_delinq_yoy_chart = create_gdp_change_chart(cre_delinq_data, "CRE Loan Delinquency Year-over-Year Change", 'YoY')
                    if cre_delinq_yoy_chart:
                        st.plotly_chart(cre_delinq_yoy_chart, use_container_width=True)
                
                with tab3:
                    cre_delinq_qoq_chart = create_gdp_change_chart(cre_delinq_data, "CRE Loan Delinquency Quarter-over-Quarter Change", 'QoQ')
                    if cre_delinq_qoq_chart:
                        st.plotly_chart(cre_delinq_qoq_chart, use_container_width=True)
            else:
                st.warning("No CRE Loan Delinquency data available")
    
    st.markdown("---")
    
    # ============================================================================
    # GDP METRICS (existing section continues here)
    # ============================================================================
    st.markdown("## <u>GDP Metrics</u>", unsafe_allow_html=True)
    st.markdown("---")
    
    # [GDP sections would continue here as in your original file]

    # Back to home button
    if st.button("← Back to Home", use_container_width=True):
        st.switch_page("Home.py")
