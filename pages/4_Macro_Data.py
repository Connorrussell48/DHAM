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
    Estimates the next release date for economic indicators.
    CPI and PPI are typically released monthly, around mid-month.
    """
    now = datetime.now()
    year = now.year
    month = now.month
    
    # Economic data is usually released around the 13th-15th of each month
    # for the previous month's data
    
    if indicator_name == "CPI":
        # CPI typically released around 13th of each month
        release_day = 13
        release_name = "Consumer Price Index"
    elif indicator_name == "PPI":
        # PPI typically released around 14th of each month  
        release_day = 14
        release_name = "Producer Price Index"
    else:
        return None, None
    
    # Calculate next release date
    next_release = datetime(year, month, release_day)
    
    # If we've passed this month's release, move to next month
    if now.day > release_day:
        if month == 12:
            next_release = datetime(year + 1, 1, release_day)
        else:
            next_release = datetime(year, month + 1, release_day)
    
    # Format the date
    days_until = (next_release - now).days
    
    return next_release.strftime("%B %d, %Y"), days_until

# --------------------------------------------------------------------------------------
# Data Fetching Functions
# --------------------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
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
    elif is_rate:
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
    
    # Show demo layout
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown("#### 📊 Consumer Price Index (CPI)")
        next_date, days = get_next_release_date("CPI")
        st.markdown(f"""
        <div class="release-info">
            <strong>Next Release:</strong> {next_date}<br>
            <strong>Days Until Release:</strong> {days} days
        </div>
        """, unsafe_allow_html=True)
        st.info("Install fredapi library to view actual CPI data")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown("#### 📈 Producer Price Index (PPI)")
        next_date, days = get_next_release_date("PPI")
        st.markdown(f"""
        <div class="release-info">
            <strong>Next Release:</strong> {next_date}<br>
            <strong>Days Until Release:</strong> {days} days
        </div>
        """, unsafe_allow_html=True)
        st.info("Install fredapi library to view actual PPI data")
        st.markdown('</div>', unsafe_allow_html=True)

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
    
    # Show demo layout
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown("#### 📊 Consumer Price Index (CPI)")
        next_date, days = get_next_release_date("CPI")
        st.markdown(f"""
        <div class="release-info">
            <strong>Next Release:</strong> {next_date}<br>
            <strong>Days Until Release:</strong> {days} days
        </div>
        """, unsafe_allow_html=True)
        st.info("Connect FRED API to view actual CPI data")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown("#### 📈 Producer Price Index (PPI)")
        next_date, days = get_next_release_date("PPI")
        st.markdown(f"""
        <div class="release-info">
            <strong>Next Release:</strong> {next_date}<br>
            <strong>Days Until Release:</strong> {days} days
        </div>
        """, unsafe_allow_html=True)
        st.info("Connect FRED API to view actual PPI data")
        st.markdown('</div>', unsafe_allow_html=True)

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
                # Create tabs for YoY and MoM only
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
    
    # Core CPI Section
    st.markdown("### Core Consumer Price Index (Core CPI)")
    
    core_cpi_col1, core_cpi_col2 = st.columns([3, 1])
    
    with core_cpi_col2:
        next_date, days = get_next_release_date("CPI")
        st.markdown(f"""
        <div class="release-info">
            <h4 style="margin-top: 0; color: var(--purple);">Next Release</h4>
            <p style="font-size: 1.1rem; margin: 5px 0;"><strong>{next_date}</strong></p>
            <p style="font-size: 0.9rem; color: var(--muted-text-new);">{days} days away</p>
        </div>
        """, unsafe_allow_html=True)
    
    with core_cpi_col1:
        with st.spinner("Fetching Core CPI data from FRED..."):
            core_cpi_data = fetch_fred_data("CPILFESL", "Core CPI")
            if not core_cpi_data.empty:
                # Create tabs for YoY and MoM only
                tab1, tab2 = st.tabs(["Year-over-Year %", "Month-over-Month %"])
                
                with tab1:
                    core_cpi_yoy_chart = create_change_chart(core_cpi_data, "Core CPI Year-over-Year Change", 'YoY')
                    if core_cpi_yoy_chart:
                        st.plotly_chart(core_cpi_yoy_chart, use_container_width=True)
                
                with tab2:
                    core_cpi_mom_chart = create_change_chart(core_cpi_data, "Core CPI Month-over-Month Change", 'MoM')
                    if core_cpi_mom_chart:
                        st.plotly_chart(core_cpi_mom_chart, use_container_width=True)
    
    st.markdown("---")
    
    # PPI Section
    st.markdown("### Producer Price Index (PPI)")
    
    ppi_col1, ppi_col2 = st.columns([3, 1])
    
    with ppi_col2:
        next_date, days = get_next_release_date("PPI")
        st.markdown(f"""
        <div class="release-info">
            <h4 style="margin-top: 0; color: var(--blue);">Next Release</h4>
            <p style="font-size: 1.1rem; margin: 5px 0;"><strong>{next_date}</strong></p>
            <p style="font-size: 0.9rem; color: var(--muted-text-new);">{days} days away</p>
        </div>
        """, unsafe_allow_html=True)
    
    with ppi_col1:
        with st.spinner("Fetching PPI data from FRED..."):
            ppi_data = fetch_fred_data("PPIACO", "PPI")
            if not ppi_data.empty:
                # Create tabs for YoY and MoM only
                tab1, tab2 = st.tabs(["Year-over-Year %", "Month-over-Month %"])
                
                with tab1:
                    ppi_yoy_chart = create_change_chart(ppi_data, "PPI Year-over-Year Change", 'YoY')
                    if ppi_yoy_chart:
                        st.plotly_chart(ppi_yoy_chart, use_container_width=True)
                
                with tab2:
                    ppi_mom_chart = create_change_chart(ppi_data, "PPI Month-over-Month Change", 'MoM')
                    if ppi_mom_chart:
                        st.plotly_chart(ppi_mom_chart, use_container_width=True)

    st.markdown("---")
    
    # Core PPI Section
    st.markdown("### Core Producer Price Index (Core PPI)")
    
    core_ppi_col1, core_ppi_col2 = st.columns([3, 1])
    
    with core_ppi_col2:
        next_date, days = get_next_release_date("PPI")
        st.markdown(f"""
        <div class="release-info">
            <h4 style="margin-top: 0; color: var(--blue);">Next Release</h4>
            <p style="font-size: 1.1rem; margin: 5px 0;"><strong>{next_date}</strong></p>
            <p style="font-size: 0.9rem; color: var(--muted-text-new);">{days} days away</p>
        </div>
        """, unsafe_allow_html=True)
    
    with core_ppi_col1:
        with st.spinner("Fetching Core PPI data from FRED..."):
            core_ppi_data = fetch_fred_data("WPSFD4131", "Core PPI")
            if not core_ppi_data.empty:
                # Create tabs for YoY and MoM only
                tab1, tab2 = st.tabs(["Year-over-Year %", "Month-over-Month %"])
                
                with tab1:
                    core_ppi_yoy_chart = create_change_chart(core_ppi_data, "Core PPI Year-over-Year Change", 'YoY')
                    if core_ppi_yoy_chart:
                        st.plotly_chart(core_ppi_yoy_chart, use_container_width=True)
                
                with tab2:
                    core_ppi_mom_chart = create_change_chart(core_ppi_data, "Core PPI Month-over-Month Change", 'MoM')
                    if core_ppi_mom_chart:
                        st.plotly_chart(core_ppi_mom_chart, use_container_width=True)

    st.markdown("---")
    
    # Core PCE Inflation Rate Section
    st.markdown("### Core PCE Inflation Rate")
    
    core_pce_col1, core_pce_col2 = st.columns([3, 1])
    
    with core_pce_col2:
        # PCE inflation is released monthly, similar timing to CPI
        next_date, days = get_next_release_date("CPI")
        st.markdown(f"""
        <div class="release-info">
            <h4 style="margin-top: 0; color: var(--purple);">Next Release</h4>
            <p style="font-size: 1.1rem; margin: 5px 0;"><strong>{next_date}</strong></p>
            <p style="font-size: 0.9rem; color: var(--muted-text-new);">{days} days away</p>
        </div>
        """, unsafe_allow_html=True)
    
    with core_pce_col1:
        with st.spinner("Fetching Core PCE Inflation data from FRED..."):
            core_pce_data = fetch_fred_data("PCEPILFE", "Core PCE")
            if not core_pce_data.empty:
                # Create tabs for YoY and MoM only
                tab1, tab2 = st.tabs(["Year-over-Year %", "Month-over-Month %"])
                
                with tab1:
                    core_pce_yoy_chart = create_change_chart(core_pce_data, "Core PCE Inflation Year-over-Year Change", 'YoY')
                    if core_pce_yoy_chart:
                        st.plotly_chart(core_pce_yoy_chart, use_container_width=True)
                
                with tab2:
                    core_pce_mom_chart = create_change_chart(core_pce_data, "Core PCE Inflation Month-over-Month Change", 'MoM')
                    if core_pce_mom_chart:
                        st.plotly_chart(core_pce_mom_chart, use_container_width=True)

    st.markdown("---")

    # ============================================================================
    # UNEMPLOYMENT METRICS
    # ============================================================================
    st.markdown("## <u>Unemployment Metrics</u>", unsafe_allow_html=True)
    st.markdown("---")

    # Unemployment Rate Section
    st.markdown("### Unemployment Rate")

    unrate_col1, unrate_col2 = st.columns([3, 1])

    with unrate_col2:
        # Unemployment data is typically released first Friday of each month
        now = datetime.now()
        year = now.year
        month = now.month
    
        # First Friday of next month
        if now.day > 7:  # If past first week, show next month
            if month == 12:
                next_month = 1
                next_year = year + 1
            else:
                next_month = month + 1
                next_year = year
        else:
            next_month = month
            next_year = year
    
        # Find first Friday
        first_day = datetime(next_year, next_month, 1)
        days_until_friday = (4 - first_day.weekday()) % 7
        first_friday = first_day + timedelta(days=days_until_friday)
    
        days_until = (first_friday - now).days
        next_release_str = first_friday.strftime("%B %d, %Y")
    
        st.markdown(f"""
        <div class="release-info">
            <h4 style="margin-top: 0; color: var(--purple);">Next Release</h4>
            <p style="font-size: 1.1rem; margin: 5px 0;"><strong>{next_release_str}</strong></p>
            <p style="font-size: 0.9rem; color: var(--muted-text-new);">{days_until} days away</p>
        </div>
        """, unsafe_allow_html=True)

    with unrate_col1:
        with st.spinner("Fetching Unemployment Rate from FRED..."):
            unrate_data = fetch_fred_data("UNRATE", "UNRATE")
            if not unrate_data.empty:
                # Create tabs for Absolute, YoY, and MoM
                tab1, tab2, tab3 = st.tabs(["Absolute Rate", "Year-over-Year %", "Month-over-Month %"])
            
                with tab1:
                    unrate_chart = create_indicator_chart(unrate_data, "Unemployment Rate", ACCENT_PURPLE)
                    if unrate_chart:
                        st.plotly_chart(unrate_chart, use_container_width=True)
            
                with tab2:
                    unrate_yoy_chart = create_change_chart(unrate_data, "Unemployment Rate Year-over-Year Change", 'YoY')
                    if unrate_yoy_chart:
                        st.plotly_chart(unrate_yoy_chart, use_container_width=True)
            
                with tab3:
                    unrate_mom_chart = create_change_chart(unrate_data, "Unemployment Rate Month-over-Month Change", 'MoM')
                    if unrate_mom_chart:
                        st.plotly_chart(unrate_mom_chart, use_container_width=True)

    st.markdown("---")

    # Nonfarm Payrolls Section
    st.markdown("### Nonfarm Payrolls")

    payems_col1, payems_col2 = st.columns([3, 1])

    with payems_col2:
        st.markdown(f"""
        <div class="release-info">
            <h4 style="margin-top: 0; color: var(--purple);">Next Release</h4>
            <p style="font-size: 1.1rem; margin: 5px 0;"><strong>{next_release_str}</strong></p>
            <p style="font-size: 0.9rem; color: var(--muted-text-new);">{days_until} days away</p>
        </div>
        """, unsafe_allow_html=True)

    with payems_col1:
        with st.spinner("Fetching Nonfarm Payrolls from FRED..."):
            payems_data = fetch_fred_data("PAYEMS", "PAYEMS")
            if not payems_data.empty:
                # Create tabs for Absolute, YoY, and MoM
                tab1, tab2, tab3 = st.tabs(["Absolute Payrolls", "Year-over-Year %", "Month-over-Month %"])
            
                with tab1:
                    payems_chart = create_indicator_chart(payems_data, "Nonfarm Payrolls (Thousands)", ACCENT_PURPLE)
                    if payems_chart:
                        st.plotly_chart(payems_chart, use_container_width=True)
            
                with tab2:
                    payems_yoy_chart = create_change_chart(payems_data, "Nonfarm Payrolls Year-over-Year Change", 'YoY')
                    if payems_yoy_chart:
                        st.plotly_chart(payems_yoy_chart, use_container_width=True)
            
                with tab3:
                    payems_mom_chart = create_change_chart(payems_data, "Nonfarm Payrolls Month-over-Month Change", 'MoM')
                    if payems_mom_chart:
                        st.plotly_chart(payems_mom_chart, use_container_width=True)

    st.markdown("---")

    # Initial Jobless Claims Section
    st.markdown("### Initial Jobless Claims")

    icsa_col1, icsa_col2 = st.columns([3, 1])

    with icsa_col2:
        # Initial Claims are released every Thursday for the prior week
        now = datetime.now()
    
        # Find next Thursday
        days_until_thursday = (3 - now.weekday()) % 7
        if days_until_thursday == 0 and now.hour >= 8:  # If it's Thursday after 8:30 AM ET
            days_until_thursday = 7
    
        next_thursday = now + timedelta(days=days_until_thursday)
        next_release_str = next_thursday.strftime("%B %d, %Y")
    
        st.markdown(f"""
        <div class="release-info">
            <h4 style="margin-top: 0; color: var(--purple);">Next Release</h4>
            <p style="font-size: 1.1rem; margin: 5px 0;"><strong>{next_release_str}</strong></p>
            <p style="font-size: 0.9rem; color: var(--muted-text-new);">{days_until_thursday} days away</p>
            <p style="font-size: 0.75rem; color: var(--muted-text-new); margin-top: 5px;">Released weekly on Thursdays</p>
        </div>
        """, unsafe_allow_html=True)

    with icsa_col1:
        with st.spinner("Fetching Initial Jobless Claims from FRED..."):
            icsa_data = fetch_fred_data("ICSA", "ICSA")
            if not icsa_data.empty:
                # Create tabs for Absolute, YoY, and MoM
                tab1, tab2, tab3 = st.tabs(["Absolute Claims", "Year-over-Year %", "Week-over-Week %"])
            
                with tab1:
                    icsa_chart = create_indicator_chart(icsa_data, "Initial Jobless Claims (Thousands)", ACCENT_PURPLE)
                    if icsa_chart:
                        st.plotly_chart(icsa_chart, use_container_width=True)
            
                with tab2:
                    icsa_yoy_chart = create_change_chart(icsa_data, "Initial Jobless Claims Year-over-Year Change", 'YoY')
                    if icsa_yoy_chart:
                        st.plotly_chart(icsa_yoy_chart, use_container_width=True)
            
                with tab3:
                    icsa_wow_chart = create_change_chart(icsa_data, "Initial Jobless Claims Week-over-Week Change", 'MoM')
                    if icsa_wow_chart:
                        st.plotly_chart(icsa_wow_chart, use_container_width=True)

    st.markdown("---")

    # Job Openings (JOLTS) Section
    st.markdown("### Job Openings and Labor Turnover Survey (JOLTS)")

    jolts_col1, jolts_col2 = st.columns([3, 1])

    with jolts_col2:
        # JOLTS data is released monthly, typically around the first Tuesday
        now = datetime.now()
        year = now.year
        month = now.month
        
        # JOLTS is released on the first Tuesday, approximately 30 days after the reference month
        # Typically released around the 1st-10th of each month
        if now.day > 10:  # If past first 10 days, show next month
            if month == 12:
                next_month = 1
                next_year = year + 1
            else:
                next_month = month + 1
                next_year = year
        else:
            next_month = month
            next_year = year
        
        # Estimate first Tuesday of the month
        first_day = datetime(next_year, next_month, 1)
        # Find first Tuesday (Tuesday = 1)
        days_until_tuesday = (1 - first_day.weekday()) % 7
        if days_until_tuesday == 0:
            days_until_tuesday = 7
        first_tuesday = first_day + timedelta(days=days_until_tuesday)
        
        days_until = (first_tuesday - now).days
        next_jolts_release_str = first_tuesday.strftime("%B %d, %Y")
        
        st.markdown(f"""
        <div class="release-info">
            <h4 style="margin-top: 0; color: var(--purple);">Next Release</h4>
            <p style="font-size: 1.1rem; margin: 5px 0;"><strong>{next_jolts_release_str}</strong></p>
            <p style="font-size: 0.9rem; color: var(--muted-text-new);">{days_until} days away</p>
            <p style="font-size: 0.75rem; color: var(--muted-text-new); margin-top: 5px;">Released monthly</p>
        </div>
        """, unsafe_allow_html=True)

    with jolts_col1:
        with st.spinner("Fetching JOLTS data from FRED..."):
            # Fetch all JOLTS data
            jolts_data = fetch_fred_data("JTSJOL", "Job Openings")
            quits_data = fetch_fred_data("JTSQUR", "Quits Rate")
            hires_data = fetch_fred_data("JTSHIR", "Hires Rate")
            layoffs_data = fetch_fred_data("JTSLDL", "Layoffs & Discharges")
            
            # Create tabs for each metric
            tab1, tab2, tab3, tab4 = st.tabs(["Job Openings", "Quits Rate", "Hires Rate", "Layoffs & Discharges"])
            
            with tab1:
                if not jolts_data.empty:
                    jolts_chart = create_indicator_chart(jolts_data, "Job Openings (Thousands)", ACCENT_PURPLE)
                    if jolts_chart:
                        st.plotly_chart(jolts_chart, use_container_width=True)
                else:
                    st.warning("No Job Openings data available")
            
            with tab2:
                if not quits_data.empty:
                    quits_chart = create_indicator_chart(quits_data, "Quits Rate (%)", ACCENT_PURPLE)
                    if quits_chart:
                        st.plotly_chart(quits_chart, use_container_width=True)
                else:
                    st.warning("No Quits Rate data available")
            
            with tab3:
                if not hires_data.empty:
                    hires_chart = create_indicator_chart(hires_data, "Hires Rate (%)", ACCENT_PURPLE)
                    if hires_chart:
                        st.plotly_chart(hires_chart, use_container_width=True)
                else:
                    st.warning("No Hires Rate data available")
            
            with tab4:
                if not layoffs_data.empty:
                    layoffs_chart = create_indicator_chart(layoffs_data, "Layoffs & Discharges (Thousands)", ACCENT_PURPLE)
                    if layoffs_chart:
                        st.plotly_chart(layoffs_chart, use_container_width=True)
                else:
                    st.warning("No Layoffs & Discharges data available")

    st.markdown("---")

    # Labor Force Participation Rate Section
    st.markdown("### Labor Force Participation Rate")

    lfpr_col1, lfpr_col2 = st.columns([3, 1])

    with lfpr_col2:
        st.markdown(f"""
        <div class="release-info">
            <h4 style="margin-top: 0; color: var(--purple);">Next Release</h4>
            <p style="font-size: 1.1rem; margin: 5px 0;"><strong>{next_release_str}</strong></p>
            <p style="font-size: 0.9rem; color: var(--muted-text-new);">{days_until} days away</p>
        </div>
        """, unsafe_allow_html=True)

    with lfpr_col1:
        with st.spinner("Fetching Labor Force Participation Rate from FRED..."):
            lfpr_data = fetch_fred_data("CIVPART", "LFPR")
            if not lfpr_data.empty:
                # Create tabs for Absolute, YoY, and MoM
                tab1, tab2, tab3 = st.tabs(["Absolute Rate", "Year-over-Year %", "Month-over-Month %"])
            
                with tab1:
                    lfpr_chart = create_indicator_chart(lfpr_data, "Labor Force Participation Rate", ACCENT_PURPLE)
                    if lfpr_chart:
                        st.plotly_chart(lfpr_chart, use_container_width=True)
            
                with tab2:
                    lfpr_yoy_chart = create_change_chart(lfpr_data, "Labor Force Participation Rate Year-over-Year Change", 'YoY')
                    if lfpr_yoy_chart:
                        st.plotly_chart(lfpr_yoy_chart, use_container_width=True)
            
                with tab3:
                    lfpr_mom_chart = create_change_chart(lfpr_data, "Labor Force Participation Rate Month-over-Month Change", 'MoM')
                    if lfpr_mom_chart:
                        st.plotly_chart(lfpr_mom_chart, use_container_width=True)

    st.markdown("---")

    # ============================================================================
    # CONSUMPTION METRICS
    # ============================================================================
    st.markdown("## <u>Consumption Metrics</u>", unsafe_allow_html=True)
    st.markdown("---")

    # Real Personal Consumption Expenditures Section
    st.markdown("### Real Personal Consumption Expenditures (Real PCE)")

    pce_col1, pce_col2 = st.columns([3, 1])

    with pce_col2:
        # PCE data is released monthly, typically around the end of the month
        now = datetime.now()
        year = now.year
        month = now.month
        
        # PCE is released approximately 30 days after the reference month
        if now.day > 28:  # If near end of month, show next month
            if month == 12:
                next_month = 1
                next_year = year + 1
            else:
                next_month = month + 1
                next_year = year
        else:
            next_month = month
            next_year = year
        
        # Estimate last business day of the month
        if next_month == 2:
            last_day = 28
        elif next_month in [4, 6, 9, 11]:
            last_day = 30
        else:
            last_day = 31
            
        next_pce_release = datetime(next_year, next_month, last_day)
        days_until = (next_pce_release - now).days
        next_pce_release_str = next_pce_release.strftime("%B %d, %Y")
        
        st.markdown(f"""
        <div class="release-info">
            <h4 style="margin-top: 0; color: var(--purple);">Next Release</h4>
            <p style="font-size: 1.1rem; margin: 5px 0;"><strong>{next_pce_release_str}</strong></p>
            <p style="font-size: 0.9rem; color: var(--muted-text-new);">{days_until} days away</p>
            <p style="font-size: 0.75rem; color: var(--muted-text-new); margin-top: 5px;">Released monthly</p>
        </div>
        """, unsafe_allow_html=True)

    with pce_col1:
        with st.spinner("Fetching Real PCE data from FRED..."):
            pce_data = fetch_fred_data("PCEC96", "Real PCE")
            if not pce_data.empty:
                # Create tabs for Value, MoM, and YoY
                tab1, tab2, tab3 = st.tabs(["Real PCE Value", "Month-over-Month %", "Year-over-Year %"])
                
                with tab1:
                    pce_chart = create_indicator_chart(pce_data, "Real Personal Consumption Expenditures (Billions, Chained 2017 Dollars)", ACCENT_PURPLE)
                    if pce_chart:
                        st.plotly_chart(pce_chart, use_container_width=True)
                
                with tab2:
                    pce_mom_chart = create_change_chart(pce_data, "Real PCE Month-over-Month Change", 'MoM')
                    if pce_mom_chart:
                        st.plotly_chart(pce_mom_chart, use_container_width=True)
                
                with tab3:
                    pce_yoy_chart = create_change_chart(pce_data, "Real PCE Year-over-Year Change", 'YoY')
                    if pce_yoy_chart:
                        st.plotly_chart(pce_yoy_chart, use_container_width=True)
            else:
                st.warning("No Real PCE data available")

    st.markdown("---")

    # Real PCE: Goods vs. Services Section
    st.markdown("### Real PCE: Goods vs. Services")

    pce_breakdown_col1, pce_breakdown_col2 = st.columns([3, 1])

    with pce_breakdown_col2:
        st.markdown(f"""
        <div class="release-info">
            <h4 style="margin-top: 0; color: var(--purple);">Next Release</h4>
            <p style="font-size: 1.1rem; margin: 5px 0;"><strong>{next_pce_release_str}</strong></p>
            <p style="font-size: 0.9rem; color: var(--muted-text-new);">{days_until} days away</p>
            <p style="font-size: 0.75rem; color: var(--muted-text-new); margin-top: 5px;">Released monthly</p>
        </div>
        """, unsafe_allow_html=True)

    with pce_breakdown_col1:
        with st.spinner("Fetching Real PCE breakdown data from FRED..."):
            # Fetch PCE breakdown data
            goods_data = fetch_fred_data("PCDG", "Goods")
            services_data = fetch_fred_data("PCES", "Services")
            
            # Create tabs for Goods and Services only
            tab1, tab2 = st.tabs(["Goods", "Services"])
            
            with tab1:
                if not goods_data.empty:
                    # Create sub-tabs for YoY and MoM
                    goods_tab1, goods_tab2 = st.tabs(["Year-over-Year %", "Month-over-Month %"])
                    
                    with goods_tab1:
                        goods_yoy_chart = create_change_chart(goods_data, "Real PCE Goods Year-over-Year Change", 'YoY')
                        if goods_yoy_chart:
                            st.plotly_chart(goods_yoy_chart, use_container_width=True)
                    
                    with goods_tab2:
                        goods_mom_chart = create_change_chart(goods_data, "Real PCE Goods Month-over-Month Change", 'MoM')
                        if goods_mom_chart:
                            st.plotly_chart(goods_mom_chart, use_container_width=True)
                else:
                    st.warning("No Goods data available")
            
            with tab2:
                if not services_data.empty:
                    # Create sub-tabs for YoY and MoM
                    services_tab1, services_tab2 = st.tabs(["Year-over-Year %", "Month-over-Month %"])
                    
                    with services_tab1:
                        services_yoy_chart = create_change_chart(services_data, "Real PCE Services Year-over-Year Change", 'YoY')
                        if services_yoy_chart:
                            st.plotly_chart(services_yoy_chart, use_container_width=True)
                    
                    with services_tab2:
                        services_mom_chart = create_change_chart(services_data, "Real PCE Services Month-over-Month Change", 'MoM')
                        if services_mom_chart:
                            st.plotly_chart(services_mom_chart, use_container_width=True)
                else:
                    st.warning("No Services data available")

    st.markdown("---")

    # Real Retail Sales Section
    st.markdown("### Real Retail Sales")

    retail_col1, retail_col2 = st.columns([3, 1])

    with retail_col2:
        st.markdown(f"""
        <div class="release-info">
            <h4 style="margin-top: 0; color: var(--purple);">Next Release</h4>
            <p style="font-size: 1.1rem; margin: 5px 0;"><strong>{next_pce_release_str}</strong></p>
            <p style="font-size: 0.9rem; color: var(--muted-text-new);">{days_until} days away</p>
            <p style="font-size: 0.75rem; color: var(--muted-text-new); margin-top: 5px;">Released monthly</p>
        </div>
        """, unsafe_allow_html=True)

    with retail_col1:
        with st.spinner("Fetching Real Retail Sales data from FRED..."):
            retail_data = fetch_fred_data("RSAFS", "Real Retail Sales")
            if not retail_data.empty:
                # Create tabs for Absolute, MoM, and YoY
                tab1, tab2, tab3 = st.tabs(["Absolute Sales", "Month-over-Month %", "Year-over-Year %"])
                
                with tab1:
                    retail_chart = create_indicator_chart(retail_data, "Real Retail Sales (Millions, Chained 2017 Dollars)", ACCENT_PURPLE)
                    if retail_chart:
                        st.plotly_chart(retail_chart, use_container_width=True)
                
                with tab2:
                    retail_mom_chart = create_change_chart(retail_data, "Real Retail Sales Month-over-Month Change", 'MoM')
                    if retail_mom_chart:
                        st.plotly_chart(retail_mom_chart, use_container_width=True)
                
                with tab3:
                    retail_yoy_chart = create_change_chart(retail_data, "Real Retail Sales Year-over-Year Change", 'YoY')
                    if retail_yoy_chart:
                        st.plotly_chart(retail_yoy_chart, use_container_width=True)
            else:
                st.warning("No Real Retail Sales data available")

    st.markdown("---")

    # Personal Saving Rate Section
    st.markdown("### Personal Saving Rate")

    saving_col1, saving_col2 = st.columns([3, 1])

    with saving_col2:
        st.markdown(f"""
        <div class="release-info">
            <h4 style="margin-top: 0; color: var(--purple);">Next Release</h4>
            <p style="font-size: 1.1rem; margin: 5px 0;"><strong>{next_pce_release_str}</strong></p>
            <p style="font-size: 0.9rem; color: var(--muted-text-new);">{days_until} days away</p>
            <p style="font-size: 0.75rem; color: var(--muted-text-new); margin-top: 5px;">Released monthly</p>
        </div>
        """, unsafe_allow_html=True)

    with saving_col1:
        with st.spinner("Fetching Personal Saving Rate from FRED..."):
            saving_data = fetch_fred_data("PSAVERT", "Personal Saving Rate")
            if not saving_data.empty:
                # Create tabs for Absolute Rate, MoM, and YoY
                tab1, tab2, tab3 = st.tabs(["Saving Rate", "Month-over-Month %", "Year-over-Year %"])
                
                with tab1:
                    saving_chart = create_indicator_chart(saving_data, "Personal Saving Rate (%)", ACCENT_PURPLE)
                    if saving_chart:
                        st.plotly_chart(saving_chart, use_container_width=True)
                
                with tab2:
                    saving_mom_chart = create_change_chart(saving_data, "Personal Saving Rate Month-over-Month Change", 'MoM')
                    if saving_mom_chart:
                        st.plotly_chart(saving_mom_chart, use_container_width=True)
                
                with tab3:
                    saving_yoy_chart = create_change_chart(saving_data, "Personal Saving Rate Year-over-Year Change", 'YoY')
                    if saving_yoy_chart:
                        st.plotly_chart(saving_yoy_chart, use_container_width=True)
            else:
                st.warning("No Personal Saving Rate data available")

    st.markdown("---")

    # ============================================================================
    # SENTIMENT METRICS
    # ============================================================================
    st.markdown("## <u>Sentiment Metrics</u>", unsafe_allow_html=True)
    st.markdown("---")

    # University of Michigan Consumer Sentiment Section
    st.markdown("### University of Michigan Consumer Sentiment")

    umich_col1, umich_col2 = st.columns([3, 1])

    with umich_col2:
        # Released monthly, typically mid-month
        now = datetime.now()
        year = now.year
        month = now.month
        
        # Estimate mid-month release (around 15th)
        if now.day > 15:
            if month == 12:
                next_month = 1
                next_year = year + 1
            else:
                next_month = month + 1
                next_year = year
        else:
            next_month = month
            next_year = year
        
        next_sentiment_release = datetime(next_year, next_month, 15)
        days_until_sentiment = (next_sentiment_release - now).days
        next_sentiment_release_str = next_sentiment_release.strftime("%B %d, %Y")
        
        st.markdown(f"""
        <div class="release-info">
            <h4 style="margin-top: 0; color: var(--purple);">Next Release</h4>
            <p style="font-size: 1.1rem; margin: 5px 0;"><strong>{next_sentiment_release_str}</strong></p>
            <p style="font-size: 0.9rem; color: var(--muted-text-new);">{days_until_sentiment} days away</p>
            <p style="font-size: 0.75rem; color: var(--muted-text-new); margin-top: 5px;">Released monthly</p>
        </div>
        """, unsafe_allow_html=True)

    with umich_col1:
        with st.spinner("Fetching UMich Consumer Sentiment from FRED..."):
            umich_data = fetch_fred_data("UMCSENT", "UMich Sentiment")
            if not umich_data.empty:
                tab1, tab2, tab3 = st.tabs(["Sentiment Index", "Month-over-Month %", "Year-over-Year %"])
                
                with tab1:
                    umich_chart = create_indicator_chart(umich_data, "University of Michigan Consumer Sentiment Index", ACCENT_PURPLE)
                    if umich_chart:
                        st.plotly_chart(umich_chart, use_container_width=True)
                
                with tab2:
                    umich_mom_chart = create_change_chart(umich_data, "UMich Sentiment Month-over-Month Change", 'MoM')
                    if umich_mom_chart:
                        st.plotly_chart(umich_mom_chart, use_container_width=True)
                
                with tab3:
                    umich_yoy_chart = create_change_chart(umich_data, "UMich Sentiment Year-over-Year Change", 'YoY')
                    if umich_yoy_chart:
                        st.plotly_chart(umich_yoy_chart, use_container_width=True)
            else:
                st.warning("No UMich Consumer Sentiment data available")

    st.markdown("---")

    # Michigan Consumer Expectations Index Section
    st.markdown("### Michigan Consumer Expectations Index")

    umich_exp_col1, umich_exp_col2 = st.columns([3, 1])

    with umich_exp_col2:
        st.markdown(f"""
        <div class="release-info">
            <h4 style="margin-top: 0; color: var(--purple);">Next Release</h4>
            <p style="font-size: 1.1rem; margin: 5px 0;"><strong>{next_sentiment_release_str}</strong></p>
            <p style="font-size: 0.9rem; color: var(--muted-text-new);">{days_until_sentiment} days away</p>
            <p style="font-size: 0.75rem; color: var(--muted-text-new); margin-top: 5px;">Released monthly</p>
        </div>
        """, unsafe_allow_html=True)

    with umich_exp_col1:
        with st.spinner("Fetching Michigan Consumer Expectations from FRED..."):
            umich_exp_data = fetch_fred_data("UMCSENT", "Michigan Expectations")  # Note: FRED may not have separate series
            if not umich_exp_data.empty:
                tab1, tab2, tab3 = st.tabs(["Expectations Index", "Month-over-Month %", "Year-over-Year %"])
                
                with tab1:
                    umich_exp_chart = create_indicator_chart(umich_exp_data, "Michigan Consumer Expectations Index", ACCENT_PURPLE)
                    if umich_exp_chart:
                        st.plotly_chart(umich_exp_chart, use_container_width=True)
                
                with tab2:
                    umich_exp_mom_chart = create_change_chart(umich_exp_data, "Michigan Expectations Month-over-Month Change", 'MoM')
                    if umich_exp_mom_chart:
                        st.plotly_chart(umich_exp_mom_chart, use_container_width=True)
                
                with tab3:
                    umich_exp_yoy_chart = create_change_chart(umich_exp_data, "Michigan Expectations Year-over-Year Change", 'YoY')
                    if umich_exp_yoy_chart:
                        st.plotly_chart(umich_exp_yoy_chart, use_container_width=True)
            else:
                st.warning("No Michigan Consumer Expectations data available")

    st.markdown("---")

    # NFIB Small Business Optimism Index Section
    st.markdown("### NFIB Small Business Optimism Index")

    nfib_col1, nfib_col2 = st.columns([3, 1])

    with nfib_col2:
        st.markdown(f"""
        <div class="release-info">
            <h4 style="margin-top: 0; color: var(--purple);">Next Release</h4>
            <p style="font-size: 1.1rem; margin: 5px 0;"><strong>{next_sentiment_release_str}</strong></p>
            <p style="font-size: 0.9rem; color: var(--muted-text-new);">{days_until_sentiment} days away</p>
            <p style="font-size: 0.75rem; color: var(--muted-text-new); margin-top: 5px;">Released monthly</p>
        </div>
        """, unsafe_allow_html=True)

    with nfib_col1:
        with st.spinner("Fetching NFIB Small Business Optimism from FRED..."):
            nfib_data = fetch_fred_data("BSCICP03USM665S", "NFIB Optimism")
            if not nfib_data.empty:
                tab1, tab2, tab3 = st.tabs(["Optimism Index", "Month-over-Month %", "Year-over-Year %"])
                
                with tab1:
                    nfib_chart = create_indicator_chart(nfib_data, "NFIB Small Business Optimism Index", ACCENT_PURPLE)
                    if nfib_chart:
                        st.plotly_chart(nfib_chart, use_container_width=True)
                
                with tab2:
                    nfib_mom_chart = create_change_chart(nfib_data, "NFIB Optimism Month-over-Month Change", 'MoM')
                    if nfib_mom_chart:
                        st.plotly_chart(nfib_mom_chart, use_container_width=True)
                
                with tab3:
                    nfib_yoy_chart = create_change_chart(nfib_data, "NFIB Optimism Year-over-Year Change", 'YoY')
                    if nfib_yoy_chart:
                        st.plotly_chart(nfib_yoy_chart, use_container_width=True)
            else:
                st.warning("No NFIB Small Business Optimism data available")

    st.markdown("---")

    # ISM Manufacturing PMI Section
    st.markdown("### ISM Manufacturing PMI")

    ism_mfg_col1, ism_mfg_col2 = st.columns([3, 1])

    with ism_mfg_col2:
        st.markdown(f"""
        <div class="release-info">
            <h4 style="margin-top: 0; color: var(--purple);">Next Release</h4>
            <p style="font-size: 1.1rem; margin: 5px 0;"><strong>{next_sentiment_release_str}</strong></p>
            <p style="font-size: 0.9rem; color: var(--muted-text-new);">{days_until_sentiment} days away</p>
            <p style="font-size: 0.75rem; color: var(--muted-text-new); margin-top: 5px;">Released monthly</p>
        </div>
        """, unsafe_allow_html=True)

    with ism_mfg_col1:
        with st.spinner("Fetching ISM Manufacturing PMI from FRED..."):
            ism_mfg_data = fetch_fred_data("MANEMP", "ISM Manufacturing PMI")
            if not ism_mfg_data.empty:
                tab1, tab2, tab3 = st.tabs(["PMI Index", "Month-over-Month %", "Year-over-Year %"])
                
                with tab1:
                    ism_mfg_chart = create_indicator_chart(ism_mfg_data, "ISM Manufacturing PMI (>50 = Expansion)", ACCENT_PURPLE)
                    if ism_mfg_chart:
                        st.plotly_chart(ism_mfg_chart, use_container_width=True)
                
                with tab2:
                    ism_mfg_mom_chart = create_change_chart(ism_mfg_data, "ISM Manufacturing PMI Month-over-Month Change", 'MoM')
                    if ism_mfg_mom_chart:
                        st.plotly_chart(ism_mfg_mom_chart, use_container_width=True)
                
                with tab3:
                    ism_mfg_yoy_chart = create_change_chart(ism_mfg_data, "ISM Manufacturing PMI Year-over-Year Change", 'YoY')
                    if ism_mfg_yoy_chart:
                        st.plotly_chart(ism_mfg_yoy_chart, use_container_width=True)
            else:
                st.warning("No ISM Manufacturing PMI data available")

    st.markdown("---")

    # Philadelphia Fed Business Outlook Section
    st.markdown("### Philadelphia Fed Business Outlook Survey")

    philly_col1, philly_col2 = st.columns([3, 1])

    with philly_col2:
        st.markdown(f"""
        <div class="release-info">
            <h4 style="margin-top: 0; color: var(--purple);">Next Release</h4>
            <p style="font-size: 1.1rem; margin: 5px 0;"><strong>{next_sentiment_release_str}</strong></p>
            <p style="font-size: 0.9rem; color: var(--muted-text-new);">{days_until_sentiment} days away</p>
            <p style="font-size: 0.75rem; color: var(--muted-text-new); margin-top: 5px;">Released monthly</p>
        </div>
        """, unsafe_allow_html=True)

    with philly_col1:
        with st.spinner("Fetching Philadelphia Fed Business Outlook from FRED..."):
            philly_data = fetch_fred_data("BSCICP02USM460S", "Philly Fed Outlook")
            if not philly_data.empty:
                tab1, tab2, tab3 = st.tabs(["Outlook Index", "Month-over-Month %", "Year-over-Year %"])
                
                with tab1:
                    philly_chart = create_indicator_chart(philly_data, "Philadelphia Fed Business Outlook Index", ACCENT_PURPLE)
                    if philly_chart:
                        st.plotly_chart(philly_chart, use_container_width=True)
                
                with tab2:
                    philly_mom_chart = create_change_chart(philly_data, "Philly Fed Outlook Month-over-Month Change", 'MoM')
                    if philly_mom_chart:
                        st.plotly_chart(philly_mom_chart, use_container_width=True)
                
                with tab3:
                    philly_yoy_chart = create_change_chart(philly_data, "Philly Fed Outlook Year-over-Year Change", 'YoY')
                    if philly_yoy_chart:
                        st.plotly_chart(philly_yoy_chart, use_container_width=True)
            else:
                st.warning("No Philadelphia Fed Business Outlook data available")

    st.markdown("---")

    # ============================================================================
    # REAL ESTATE METRICS
    # ============================================================================
    st.markdown("## <u>Real Estate Metrics</u>", unsafe_allow_html=True)
    st.markdown("---")

    # Housing Starts Section
    st.markdown("### Housing Starts")

    starts_col1, starts_col2 = st.columns([3, 1])

    with starts_col2:
        # Housing data is released monthly, typically mid-month
        now = datetime.now()
        year = now.year
        month = now.month
        
        # Estimate mid-month release (around 17th)
        if now.day > 17:
            if month == 12:
                next_month = 1
                next_year = year + 1
            else:
                next_month = month + 1
                next_year = year
        else:
            next_month = month
            next_year = year
        
        next_housing_release = datetime(next_year, next_month, 17)
        days_until_housing = (next_housing_release - now).days
        next_housing_release_str = next_housing_release.strftime("%B %d, %Y")
        
        st.markdown(f"""
        <div class="release-info">
            <h4 style="margin-top: 0; color: var(--purple);">Next Release</h4>
            <p style="font-size: 1.1rem; margin: 5px 0;"><strong>{next_housing_release_str}</strong></p>
            <p style="font-size: 0.9rem; color: var(--muted-text-new);">{days_until_housing} days away</p>
            <p style="font-size: 0.75rem; color: var(--muted-text-new); margin-top: 5px;">Released monthly</p>
        </div>
        """, unsafe_allow_html=True)

    with starts_col1:
        with st.spinner("Fetching Housing Starts from FRED..."):
            starts_data = fetch_fred_data("HOUST", "Housing Starts")
            if not starts_data.empty:
                tab1, tab2, tab3 = st.tabs(["Housing Starts", "Month-over-Month %", "Year-over-Year %"])
                
                with tab1:
                    starts_chart = create_indicator_chart(starts_data, "Housing Starts (Thousands of Units)", ACCENT_PURPLE)
                    if starts_chart:
                        st.plotly_chart(starts_chart, use_container_width=True)
                
                with tab2:
                    starts_mom_chart = create_change_chart(starts_data, "Housing Starts Month-over-Month Change", 'MoM')
                    if starts_mom_chart:
                        st.plotly_chart(starts_mom_chart, use_container_width=True)
                
                with tab3:
                    starts_yoy_chart = create_change_chart(starts_data, "Housing Starts Year-over-Year Change", 'YoY')
                    if starts_yoy_chart:
                        st.plotly_chart(starts_yoy_chart, use_container_width=True)
            else:
                st.warning("No Housing Starts data available")

    st.markdown("---")

    # Building Permits Section
    st.markdown("### Building Permits")

    permits_col1, permits_col2 = st.columns([3, 1])

    with permits_col2:
        st.markdown(f"""
        <div class="release-info">
            <h4 style="margin-top: 0; color: var(--purple);">Next Release</h4>
            <p style="font-size: 1.1rem; margin: 5px 0;"><strong>{next_housing_release_str}</strong></p>
            <p style="font-size: 0.9rem; color: var(--muted-text-new);">{days_until_housing} days away</p>
            <p style="font-size: 0.75rem; color: var(--muted-text-new); margin-top: 5px;">Released monthly</p>
        </div>
        """, unsafe_allow_html=True)

    with permits_col1:
        with st.spinner("Fetching Building Permits from FRED..."):
            permits_data = fetch_fred_data("PERMIT", "Building Permits")
            if not permits_data.empty:
                tab1, tab2, tab3 = st.tabs(["Building Permits", "Month-over-Month %", "Year-over-Year %"])
                
                with tab1:
                    permits_chart = create_indicator_chart(permits_data, "Building Permits (Thousands of Units)", ACCENT_PURPLE)
                    if permits_chart:
                        st.plotly_chart(permits_chart, use_container_width=True)
                
                with tab2:
                    permits_mom_chart = create_change_chart(permits_data, "Building Permits Month-over-Month Change", 'MoM')
                    if permits_mom_chart:
                        st.plotly_chart(permits_mom_chart, use_container_width=True)
                
                with tab3:
                    permits_yoy_chart = create_change_chart(permits_data, "Building Permits Year-over-Year Change", 'YoY')
                    if permits_yoy_chart:
                        st.plotly_chart(permits_yoy_chart, use_container_width=True)
            else:
                st.warning("No Building Permits data available")

    st.markdown("---")

    # Case-Shiller Home Price Index Section
    st.markdown("### S&P/Case-Shiller U.S. National Home Price Index")

    homeprice_col1, homeprice_col2 = st.columns([3, 1])

    with homeprice_col2:
        st.markdown(f"""
        <div class="release-info">
            <h4 style="margin-top: 0; color: var(--purple);">Next Release</h4>
            <p style="font-size: 1.1rem; margin: 5px 0;"><strong>{next_housing_release_str}</strong></p>
            <p style="font-size: 0.9rem; color: var(--muted-text-new);">{days_until_housing} days away</p>
            <p style="font-size: 0.75rem; color: var(--muted-text-new); margin-top: 5px;">Released monthly</p>
        </div>
        """, unsafe_allow_html=True)

    with homeprice_col1:
        with st.spinner("Fetching Case-Shiller Home Price Index from FRED..."):
            homeprice_data = fetch_fred_data("CSUSHPINSA", "Home Price Index")
            if not homeprice_data.empty:
                tab1, tab2, tab3 = st.tabs(["Home Price Index", "Month-over-Month %", "Year-over-Year %"])
                
                with tab1:
                    homeprice_chart = create_indicator_chart(homeprice_data, "S&P/Case-Shiller Home Price Index", ACCENT_PURPLE)
                    if homeprice_chart:
                        st.plotly_chart(homeprice_chart, use_container_width=True)
                
                with tab2:
                    homeprice_mom_chart = create_change_chart(homeprice_data, "Home Price Index Month-over-Month Change", 'MoM')
                    if homeprice_mom_chart:
                        st.plotly_chart(homeprice_mom_chart, use_container_width=True)
                
                with tab3:
                    homeprice_yoy_chart = create_change_chart(homeprice_data, "Home Price Index Year-over-Year Change", 'YoY')
                    if homeprice_yoy_chart:
                        st.plotly_chart(homeprice_yoy_chart, use_container_width=True)
            else:
                st.warning("No Home Price Index data available")

    st.markdown("---")

    # Existing Home Sales Section
    st.markdown("### Existing Home Sales")

    existingsales_col1, existingsales_col2 = st.columns([3, 1])

    with existingsales_col2:
        st.markdown(f"""
        <div class="release-info">
            <h4 style="margin-top: 0; color: var(--purple);">Next Release</h4>
            <p style="font-size: 1.1rem; margin: 5px 0;"><strong>{next_housing_release_str}</strong></p>
            <p style="font-size: 0.9rem; color: var(--muted-text-new);">{days_until_housing} days away</p>
            <p style="font-size: 0.75rem; color: var(--muted-text-new); margin-top: 5px;">Released monthly</p>
        </div>
        """, unsafe_allow_html=True)

    with existingsales_col1:
        with st.spinner("Fetching Existing Home Sales from FRED..."):
            existingsales_data = fetch_fred_data("EXHOSLUSM495S", "Existing Home Sales")
            if not existingsales_data.empty:
                tab1, tab2, tab3 = st.tabs(["Existing Sales", "Month-over-Month %", "Year-over-Year %"])
                
                with tab1:
                    existingsales_chart = create_indicator_chart(existingsales_data, "Existing Home Sales (Thousands of Units)", ACCENT_PURPLE)
                    if existingsales_chart:
                        st.plotly_chart(existingsales_chart, use_container_width=True)
                
                with tab2:
                    existingsales_mom_chart = create_change_chart(existingsales_data, "Existing Home Sales Month-over-Month Change", 'MoM')
                    if existingsales_mom_chart:
                        st.plotly_chart(existingsales_mom_chart, use_container_width=True)
                
                with tab3:
                    existingsales_yoy_chart = create_change_chart(existingsales_data, "Existing Home Sales Year-over-Year Change", 'YoY')
                    if existingsales_yoy_chart:
                        st.plotly_chart(existingsales_yoy_chart, use_container_width=True)
            else:
                st.warning("No Existing Home Sales data available")

    st.markdown("---")

    # Residential Construction Spending Section
    st.markdown("### Residential Construction Spending")

    rescon_col1, rescon_col2 = st.columns([3, 1])

    with rescon_col2:
        st.markdown(f"""
        <div class="release-info">
            <h4 style="margin-top: 0; color: var(--purple);">Next Release</h4>
            <p style="font-size: 1.1rem; margin: 5px 0;"><strong>{next_housing_release_str}</strong></p>
            <p style="font-size: 0.9rem; color: var(--muted-text-new);">{days_until_housing} days away</p>
            <p style="font-size: 0.75rem; color: var(--muted-text-new); margin-top: 5px;">Released monthly</p>
        </div>
        """, unsafe_allow_html=True)

    with rescon_col1:
        with st.spinner("Fetching Residential Construction Spending from FRED..."):
            rescon_data = fetch_fred_data("PRRESCON", "Residential Construction")
            if not rescon_data.empty:
                tab1, tab2, tab3 = st.tabs(["Construction Spending", "Month-over-Month %", "Year-over-Year %"])
                
                with tab1:
                    rescon_chart = create_indicator_chart(rescon_data, "Residential Construction Spending (Millions of Dollars)", ACCENT_PURPLE)
                    if rescon_chart:
                        st.plotly_chart(rescon_chart, use_container_width=True)
                
                with tab2:
                    rescon_mom_chart = create_change_chart(rescon_data, "Residential Construction Month-over-Month Change", 'MoM')
                    if rescon_mom_chart:
                        st.plotly_chart(rescon_mom_chart, use_container_width=True)
                
                with tab3:
                    rescon_yoy_chart = create_change_chart(rescon_data, "Residential Construction Year-over-Year Change", 'YoY')
                    if rescon_yoy_chart:
                        st.plotly_chart(rescon_yoy_chart, use_container_width=True)
            else:
                st.warning("No Residential Construction Spending data available")

    st.markdown("---")

    # 30-Year Mortgage Rate Section
    st.markdown("### 30-Year Fixed Mortgage Rate")

    mortgage_col1, mortgage_col2 = st.columns([3, 1])

    with mortgage_col2:
        st.markdown(f"""
        <div class="release-info">
            <h4 style="margin-top: 0; color: var(--purple);">Next Release</h4>
            <p style="font-size: 1.1rem; margin: 5px 0;"><strong>{next_housing_release_str}</strong></p>
            <p style="font-size: 0.9rem; color: var(--muted-text-new);">{days_until_housing} days away</p>
            <p style="font-size: 0.75rem; color: var(--muted-text-new); margin-top: 5px;">Released weekly</p>
        </div>
        """, unsafe_allow_html=True)

    with mortgage_col1:
        with st.spinner("Fetching 30-Year Mortgage Rate from FRED..."):
            mortgage_data = fetch_fred_data("MORTGAGE30US", "Mortgage Rate")
            if not mortgage_data.empty:
                tab1, tab2, tab3 = st.tabs(["Mortgage Rate", "Month-over-Month %", "Year-over-Year %"])
                
                with tab1:
                    mortgage_chart = create_indicator_chart(mortgage_data, "30-Year Fixed Mortgage Rate (%)", ACCENT_PURPLE)
                    if mortgage_chart:
                        st.plotly_chart(mortgage_chart, use_container_width=True)
                
                with tab2:
                    mortgage_mom_chart = create_change_chart(mortgage_data, "Mortgage Rate Month-over-Month Change", 'MoM')
                    if mortgage_mom_chart:
                        st.plotly_chart(mortgage_mom_chart, use_container_width=True)
                
                with tab3:
                    mortgage_yoy_chart = create_change_chart(mortgage_data, "Mortgage Rate Year-over-Year Change", 'YoY')
                    if mortgage_yoy_chart:
                        st.plotly_chart(mortgage_yoy_chart, use_container_width=True)
            else:
                st.warning("No 30-Year Mortgage Rate data available")

    st.markdown("---")

    # ============================================================================
    # GDP METRICS
    # ============================================================================
    st.markdown("## <u>GDP Metrics</u>", unsafe_allow_html=True)
    st.markdown("---")

    # Gross GDP Section
    st.markdown("### Gross Domestic Product (GDP)")

    gdp_col1, gdp_col2 = st.columns([3, 1])

    with gdp_col2:
        # GDP is released quarterly, typically around the end of the month following the quarter
        now = datetime.now()
        year = now.year
        month = now.month
    
        # Determine which quarter we're in and next release
        current_quarter = (month - 1) // 3 + 1
    
        # GDP releases are approximately: Jan 26 (Q4), Apr 25 (Q1), Jul 25 (Q2), Oct 24 (Q3)
        release_months = [1, 4, 7, 10]  # January, April, July, October
        release_day = 25
    
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
    
        next_gdp_release = datetime(next_release_year, next_release_month, release_day)
        days_until_gdp = (next_gdp_release - now).days
        next_gdp_release_str = next_gdp_release.strftime("%B %d, %Y")
    
        st.markdown(f"""
        <div class="release-info">
            <h4 style="margin-top: 0; color: var(--purple);">Next Release</h4>
            <p style="font-size: 1.1rem; margin: 5px 0;"><strong>{next_gdp_release_str}</strong></p>
            <p style="font-size: 0.9rem; color: var(--muted-text-new);">{days_until_gdp} days away</p>
            <p style="font-size: 0.75rem; color: var(--muted-text-new); margin-top: 5px;">Released quarterly</p>
        </div>
        """, unsafe_allow_html=True)

    with gdp_col1:
        with st.spinner("Fetching Gross GDP data from FRED..."):
            gdp_data = fetch_fred_data("GDP", "GDP")
            if not gdp_data.empty:
                # Create tabs for Absolute, YoY, QoQ, and MoM
                tab1, tab2, tab3 = st.tabs(["Absolute GDP", "Year-over-Year %", "Quarter-over-Quarter %"])
            
                with tab1:
                    gdp_chart = create_indicator_chart(gdp_data, "Gross Domestic Product (Billions)", ACCENT_PURPLE)
                    if gdp_chart:
                        st.plotly_chart(gdp_chart, use_container_width=True)
            
                with tab2:
                    # YoY: compare to 4 quarters ago
                    gdp_yoy_chart = create_gdp_change_chart(gdp_data, "Gross GDP Year-over-Year Change", 'YoY')
                    if gdp_yoy_chart:
                        st.plotly_chart(gdp_yoy_chart, use_container_width=True)
            
                with tab3:
                    # QoQ: compare to previous quarter
                    gdp_qoq_chart = create_gdp_change_chart(gdp_data, "Gross GDP Quarter-over-Quarter Change", 'QoQ')
                    if gdp_qoq_chart:
                        st.plotly_chart(gdp_qoq_chart, use_container_width=True)

    st.markdown("---")

    # Real GDP Section
    st.markdown("### Real Gross Domestic Product (Real GDP)")

    real_gdp_col1, real_gdp_col2 = st.columns([3, 1])

    with real_gdp_col2:
        st.markdown(f"""
        <div class="release-info">
            <h4 style="margin-top: 0; color: var(--purple);">Next Release</h4>
            <p style="font-size: 1.1rem; margin: 5px 0;"><strong>{next_gdp_release_str}</strong></p>
            <p style="font-size: 0.9rem; color: var(--muted-text-new);">{days_until_gdp} days away</p>
            <p style="font-size: 0.75rem; color: var(--muted-text-new); margin-top: 5px;">Released quarterly</p>
        </div>
        """, unsafe_allow_html=True)

    with real_gdp_col1:
        with st.spinner("Fetching Real GDP data from FRED..."):
            real_gdp_data = fetch_fred_data("GDPC1", "Real GDP")
            if not real_gdp_data.empty:
                # Create tabs for Absolute, YoY, QoQ
                tab1, tab2, tab3 = st.tabs(["Absolute Real GDP", "Year-over-Year %", "Quarter-over-Quarter %"])
            
                with tab1:
                    real_gdp_chart = create_indicator_chart(real_gdp_data, "Real Gross Domestic Product (Billions, Chained 2017 Dollars)", ACCENT_PURPLE)
                    if real_gdp_chart:
                        st.plotly_chart(real_gdp_chart, use_container_width=True)
            
                with tab2:
                    # YoY: compare to 4 quarters ago
                    real_gdp_yoy_chart = create_gdp_change_chart(real_gdp_data, "Real GDP Year-over-Year Change", 'YoY')
                    if real_gdp_yoy_chart:
                        st.plotly_chart(real_gdp_yoy_chart, use_container_width=True)
            
                with tab3:
                    # QoQ: compare to previous quarter
                    real_gdp_qoq_chart = create_gdp_change_chart(real_gdp_data, "Real GDP Quarter-over-Quarter Change", 'QoQ')
                    if real_gdp_qoq_chart:
                        st.plotly_chart(real_gdp_qoq_chart, use_container_width=True)

    st.markdown("---")

    # Additional metrics
    st.markdown("### Additional Economic Indicators")
    st.info("Coming soon: PCE, Unemployment Rate, GDP, and more economic indicators")

    st.markdown("---")

    # Back to home button
    if st.button("← Back to Home", use_container_width=True):
        st.switch_page("Home.py")
