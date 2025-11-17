# 3_Macro_Data.py - Macro Data Dashboard
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
FRED_API_KEY = "your_fred_api_key_here"  # Replace with your actual API key

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
def fetch_fred_data(series_id, series_name):
    """Fetch data from FRED API."""
    if not FRED_AVAILABLE:
        return pd.DataFrame()
    
    try:
        fred = Fred(api_key=FRED_API_KEY)
        data = fred.get_series(series_id)
        df = pd.DataFrame({series_name: data})
        return df
    except Exception as e:
        st.error(f"Error fetching {series_name} data: {str(e)}")
        return pd.DataFrame()

def create_indicator_chart(df, title, color):
    """Create a plotly chart for economic indicators."""
    if df.empty:
        return None
    
    # Get last 5 years of data
    five_years_ago = datetime.now() - timedelta(days=5*365)
    df_filtered = df[df.index >= five_years_ago]
    
    fig = go.Figure()
    
    # Check if this is data in thousands or billions (not percentages)
    is_thousands = "Claims" in title or "ICSA" in title or "Payrolls" in title or "PAYEMS" in title
    is_billions = "GDP" in title or "Billions" in title
    
    if is_billions:
        hover_template = '%{x|%Y-Q%q}<br>$%{y:,.1f}B<extra></extra>'
        tick_format = ",.0f"
        y_title = "Billions of Dollars"
    elif is_thousands:
        hover_template = '%{x|%Y-%m}<br>%{y:,.0f}<extra></extra>'
        tick_format = ",.0f"
        y_title = "Thousands"
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
            ticksuffix="" if (is_thousands or is_billions) else "%",
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
            </ul>
            <p style="margin-top: 15px;"><strong>Employment Indicators:</strong></p>
            <ul style="list-style: none; padding-left: 0; margin-top: 5px;">
                <li><strong>Unemployment Rate</strong> - Official unemployment rate</li>
                <li><strong>Nonfarm Payrolls</strong> - Total employed workers (headline jobs number)</li>
                <li><strong>Initial Claims</strong> - Weekly jobless claims (leading indicator)</li>
                <li><strong>LFPR</strong> - Labor Force Participation Rate</li>
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

# Check if API key is configured
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
    st.markdown("## Inflation Metrics")
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

# ============================================================================
# UNEMPLOYMENT METRICS
# ============================================================================
st.markdown("## Unemployment Metrics")
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
# GDP METRICS
# ============================================================================
st.markdown("## GDP Metrics")
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
