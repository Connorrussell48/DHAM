# 3_Current_Data.py - Current Market Data Dashboard
from __future__ import annotations
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from textwrap import dedent

# --------------------------------------------------------------------------------------
# Page setup
# --------------------------------------------------------------------------------------
st.set_page_config(
    page_title="Current Data - D-HAM",
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
      <div style="font-weight:900;letter-spacing:.3px;font-size:1.6rem;">Current Data</div>
      <div style="margin-left:auto;font-size:.95rem;color:rgba(255,255,255,.70);font-weight:500;">Real-Time Market Overview</div>
    </div>
    """,
    unsafe_allow_html=True
)

# --------------------------------------------------------------------------------------
# Sidebar
# --------------------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### Current Data Dashboard")
    st.markdown("""
        <div style="color: var(--muted); font-size: .85rem; padding: 10px 0;">
            <p>View real-time market data, recent price movements, and current trading conditions.</p>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown("### Data Settings")
    st.markdown("""
        <div style="color: var(--muted); font-size: .85rem;">
            <p>Configure data refresh intervals and display preferences here.</p>
        </div>
    """, unsafe_allow_html=True)

# --------------------------------------------------------------------------------------
# Main Content
# --------------------------------------------------------------------------------------
st.markdown("### 📊 Current Market Data")
st.caption("Real-time market overview and recent trading activity")

st.markdown("---")

# Placeholder for future content
st.info("🚧 This page is under construction. Market data widgets and charts will be added here.")

st.markdown("""
### Coming Soon:
- **Live Price Feeds** - Real-time price data for major indices
- **Volume Analysis** - Current trading volumes and trends  
- **Volatility Metrics** - Latest VIX and implied volatility data
- **Sector Performance** - Real-time sector rotation analysis
- **News Feed** - Latest market-moving news and events
""")

st.markdown("---")

# Back to home button
if st.button("← Back to Home", use_container_width=True):
    st.switch_page("Home.py")
