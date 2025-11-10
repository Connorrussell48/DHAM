# home.py - Updated for Market Summary Layout
from __future__ import annotations
import json
from pathlib import Path
from textwrap import dedent
from datetime import datetime
import os # Required for file counting

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
# Theme / CSS (Enhanced for Professional & Dynamic Look)
# --------------------------------------------------------------------------------------
BLOOM_BG       = "#0B0F14"    # Primary Background: Deep Black/Navy
BLOOM_PANEL    = "#121820"    # Component Background: Dark Panel
BLOOM_TEXT     = "#FFFFFF"    # Primary Text
BLOOM_MUTED    = "rgba(255,255,255,0.70)" # Muted Text
NEUTRAL_GRAY   = "#4A5B6E"    # Borders/Separators
INPUT_BG       = "#2E3A46"    # Dark Gray Input (Sidebar)
INPUT_BG_LIGHT = "#3A4654"    # Lighter Input/Container (Main)
ACCENT_BLUE    = "#2BB3F3"    # Secondary Accent (Flashes)
ACCENT_GREEN   = "#26D07C"    # Bullish (Vibrant Teal)
ACCENT_PURPLE  = "#8A7CF5"    # Tertiary Accent (Vibrant Purple)
DARK_PURPLE    = "#3A2A6A"    # Gradient End Point

st.markdown(
    dedent(
        f"""
        <style>
        :root {{
          --bg:{BLOOM_BG}; --panel:{BLOOM_PANEL}; --text:{BLOOM_TEXT}; --muted:{BLOOM_MUTED};
          --neutral:{NEUTRAL_GRAY}; --input:{INPUT_BG}; --inputlight:{INPUT_BG_LIGHT};
          --blue:{ACCENT_BLUE}; --green:{ACCENT_GREEN}; --purple:{ACCENT_PURPLE};
          --green-accent: #26D07C;
          --red-neg: #D9534F; /* Softened Red for contrast */
        }}
        html, body {{
          height:100%;
          /* Enhanced Radial Gradient for Depth */
          background: radial-gradient(1200px 600px at 15% -10%, rgba(43,179,243,0.15), transparent 60%),
                      radial-gradient(1200px 600px at 85% 110%, rgba(138,124,245,0.15), transparent 60%),
                      linear-gradient(135deg, var(--bg) 0%, {DARK_PURPLE} 100%) fixed !important;
        }}
        .stApp {{ background:transparent!important; color:var(--text); }}
        .block-container {{ max-width: 1500px; padding-top: .6rem; padding-bottom: 2rem; }}
        header[data-testid="stHeader"] {{ background:transparent!important; height:2.5rem!important; }}
        [data-testid="stDecoration"] {{ background:transparent!important; }}

        /* Strategy Navigation Card: More pronounced hover */
        .strategy-link-card {{
            background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.00));
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,.4);
            transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94); /* Smoother transition */
        }}
        .strategy-link-card:hover {{
            border-color: var(--green-accent);
            transform: translateY(-5px); /* Lift higher on hover */
            box-shadow: 0 15px 40px rgba(38, 208, 124, 0.3);
        }}
        .strategy-link-title {{ 
            font-weight: 800; 
            font-size: 1.25rem; 
            letter-spacing: .5px; 
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .strategy-link-desc {{ color: var(--muted); font-size: .88rem; margin-top: 4px; }}

        /* KPI / Metric Cards (Market Summary) */
        .kpi {{
          background: linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.00));
          border: 1px solid rgba(255,255,255,0.10);
          border-radius: 14px;
          padding: 12px 14px;
          text-align: left;
          transition: border-color 0.2s;
        }}
        .kpi .h {{ font-size: .85rem; color: var(--muted); margin-bottom: 4px; }}
        .kpi .v {{ font-size: 1.45rem; font-weight: 800; }}
        
        /* Quick Action Button Styling (Modern, contained look) */
        div[data-testid="stAppViewContainer"] .stButton>button {{
          background: var(--inputlight)!important; 
          color: var(--text)!important;
          border: 1px solid var(--neutral)!important; 
          border-radius: 8px!important; 
          box-shadow: 0 2px 4px rgba(0,0,0,.2);
          transition: background 0.2s;
        }}
        div[data-testid="stAppViewContainer"] .stButton>button:hover {{
            background: rgba(138,124,245,0.2) !important; /* Subtle purple hover */
            border-color: var(--purple)!important;
        }}

        .small-muted {{ color: var(--muted); font-size: .86rem; }}
        .pill {{
          display:inline-block; padding: 4px 8px; border-radius: 999px; font-size: .78rem;
          border: 1px solid rgba(255,255,255,0.18);
          background: rgba(255,255,255,0.06);
        }}
        </style>
        """
    ),
    unsafe_allow_html=True,
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
    unsafe_allow_html=True,
)

# Fun one-liner
st.markdown(
    """
    <div style="text-align:center; font-size:1.05rem; font-style:italic; color:rgba(255,255,255,0.80); margin:-4px 0 18px 0;">
      "You're either a smart-fella or fart smella" – Confucius
    </div>
    """,
    unsafe_allow_html=True,
)

# Initialize Session State if not present
if "tickers" not in st.session_state:
    st.session_state["tickers"] = ["SPY", "AAPL", "MSFT"]
if "ma_window" not in st.session_state:
    st.session_state["ma_window"] = 200
if "lookback" not in st.session_state:
    st.session_state["lookback"] = 200


# --------------------------------------------------------------------------------------
# Sidebar: Global controls (No changes here, only in main body)
# --------------------------------------------------------------------------------------
with st.sidebar:
    st.subheader("Global Settings")
    default_tickers = st.session_state.get("tickers", ["SPY", "AAPL", "MSFT"])
    tickers_str = st.text_input(
        "Tickers (comma‑separated)",
        value=",".join(default_tickers) if isinstance(default_tickers, list) else default_tickers,
        help="Applies across all pages that read session state.",
    )
    tickers = [t.strip().upper() for t in tickers_str.split(",") if t.strip()]
    st.session_state["tickers"] = tickers

    colA, colB = st.columns(2)
    with colA:
        ma_window = st.number_input("MA Window", min_value=5, max_value=500, value=int(st.session_state.get("ma_window", 200)), step=5)
    with colB:
        lookback = st.number_input("Convexity Lookback", min_value=5, max_value=500, value=int(st.session_state.get("lookback", 200)), step=5)
    st.session_state["ma_window"] = int(ma_window)
    st.session_state["lookback"]  = int(lookback)

    st.markdown("---")
    st.caption("Upload a watchlist to override the tickers above.")
    up = st.file_uploader("Upload watchlist (.json or .csv)", type=["json", "csv"])
    if up is not None:
        try:
            if up.name.endswith(".json"):
                data = json.loads(up.read().decode("utf-8"))
                if isinstance(data, dict) and "tickers" in data:
                    st.session_state["tickers"] = [x.strip().upper() for x in data["tickers"] if str(x).strip()]
                elif isinstance(data, list):
                    st.session_state["tickers"] = [str(x).strip().upper() for x in data if str(x).strip()]
                st.success(f"Loaded {len(st.session_state['tickers'])} tickers from JSON.")
            else:
                import pandas as pd
                dfu = pd.read_csv(up)
                first_col = dfu.columns[0]
                st.session_state["tickers"] = [str(x).strip().upper() for x in dfu[first_col].dropna().tolist()]
                st.success(f"Loaded {len(st.session_state['tickers'])} tickers from CSV.")
        except Exception as e:
            st.error(f"Failed to parse file: {e}")

    st.markdown("---")
    st.caption("Quick presets")
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("US Core"):
            st.session_state["tickers"] = ["SPY", "QQQ", "IWM", "TLT", "HYG"]
    with c2:
        if st.button("Mega‑Tech"):
            st.session_state["tickers"] = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META"]
    with c3:
        if st.button("Futures"):
            st.session_state["tickers"] = ["ES=F", "NQ=F", "CL=F", "GC=F", "ZN=F"]

    st.markdown("---")
    st.caption("Info & Status")
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    count_files = sum(1 for item in os.listdir(data_dir) if os.path.isfile(data_dir / item))

    st.markdown(
        f"""
        <div class="kpi" style="background:{INPUT_BG_LIGHT}; border:none;">
            <div class="h">Tracked Tickers</div><div class="v">{len(st.session_state["tickers"]):,}</div>
        </div>
        <div class="kpi" style="background:{INPUT_BG_LIGHT}; border:none; margin-top: 10px;">
            <div class="h">Local Data Files</div><div class="v">{count_files}</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.write(f":small_blue_diamond: Session started **{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}**")


# --------------------------------------------------------------------------------------
# 🌎 Market Summary Section (Dynamic Styling Applied)
# --------------------------------------------------------------------------------------
st.markdown("### 🌎 Today's Market Summary")
st.caption("High-level overview of key indices and current session status.")

# Hardcoded/Mock Market Data
SPY_PRICE = 505.21
SPY_CHANGE_PCT = 1.25
QQQ_PRICE = 435.00
QQQ_CHANGE_PCT = -0.15
VIX_PRICE = 12.50
VIX_CHANGE_PCT = 0.00

# Define colors and icons based on change (using HTML span styles)
def get_metric_html(title, price, change_pct, accent_color_token):
    if change_pct > 0.01:
        # Use ACCENT_GREEN with a solid color border
        color = "var(--green-accent)"
        icon = '↑'
        css_class = 'style="color: var(--green-accent);"'
    elif change_pct < -0.01:
        # Use ACCENT_RED with a solid color border
        color = "var(--red-neg)"
        icon = '↓'
        css_class = 'style="color: var(--red-neg);"'
    else:
        # Use PURPLE for neutral/time/VIX, with solid purple border
        color = f"var({accent_color_token})" if accent_color_token else "var(--neutral)"
        icon = '•'
        css_class = 'style="color: var(--muted);"'

    # Format change text
    change_text = f"{icon} {abs(change_pct):.2f}%"
    
    # Custom border and background highlight on hover
    return dedent(f"""
        <div class="kpi" style="border-left: 5px solid {color};"
             onmouseover="this.style.borderColor='var(--green-accent)';"
             onmouseout="this.style.borderColor='{color}';">
            <div class="h">{title}</div>
            <div class="v" style="color: {color};">
                {price:.2f}
            </div>
            <div class="text-sm font-semibold" {css_class}>{change_text}</div>
        </div>
    """)

# Row of 4 KPI Cards for Market Summary
col_spy, col_qqq, col_vix, col_time = st.columns(4)

with col_spy:
    st.markdown(get_metric_html("S&P 500 (SPY)", SPY_PRICE, SPY_CHANGE_PCT, "--green-accent"), unsafe_allow_html=True)
with col_qqq:
    st.markdown(get_metric_html("NASDAQ 100 (QQQ)", QQQ_PRICE, QQQ_CHANGE_PCT, "--red-neg"), unsafe_allow_html=True)
with col_vix:
    st.markdown(get_metric_html("VIX Index (^VIX)", VIX_PRICE, VIX_CHANGE_PCT, "--purple"), unsafe_allow_html=True)
with col_time:
    current_time = datetime.now().strftime('%H:%M:%S EST')
    st.markdown(f"""
        <div class="kpi" style="border-left: 5px solid var(--purple);">
            <div class="h">Current Time</div>
            <div class="v" style="color: var(--purple);">{current_time}</div>
            <div class="text-sm font-semibold text-gray-400">Status: Open</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# --------------------------------------------------------------------------------------
# Page navigation (Enhanced Card Design)
# --------------------------------------------------------------------------------------
st.subheader("🧭 Jump to a Strategy")

PAGE_MAPPING = {
    "📈 Slope Convexity": {"file": "1_Slope_Convexity.py", "desc": "Advanced Sentiment Scanning", "icon": "🚀"},
    "📉 Mean Reversion (draft)": {"file": "2_Mean_Reversion.py", "desc": "Z-Score-based Statistical Trading", "icon": "🔬"},
}
pages_dir = Path("pages")
available = []

for label, data in PAGE_MAPPING.items():
    rel_path = pages_dir / data["file"]
    if rel_path.exists():
        available.append((label, rel_path.as_posix(), data["desc"], data["icon"]))

if available:
    cols = st.columns(len(available))
    for i, (label, rel_path, desc, icon) in enumerate(available):
        with cols[i]:
            # Use custom HTML for the styled card structure with embedded icon
            st.markdown(
                f"""
                <div class="strategy-link-card">
                  <div class="strategy-link-title">
                    <span style="color: var(--green-accent); font-size: 1.5rem;">{icon}</span> 
                    {label}
                  </div>
                  <div class="strategy-link-desc">{desc}</div>
                  <div class="small-muted font-mono" style="margin:.25rem 0 .6rem 0;">Path: <code>{rel_path}</code></div>
                  <div style="margin-top:.6rem;"> </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.page_link(rel_path, label="Open", icon=None)
else:
    st.info("No pages detected in `pages/` yet. Add files like `1_Slope_Convexity.py` to enable navigation.")

st.markdown("---")

# --------------------------------------------------------------------------------------
# Utilities: Quick Actions & Session Snapshot (Container border refinement)
# --------------------------------------------------------------------------------------
left, right = st.columns([1.4, 1])

with left:
    st.markdown("### ⚡ Quick Actions")
    # Using st.container(border=True) which inherits the enhanced card styles
    with st.container(border=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("➕ Add VIX & VIX9D", use_container_width=True):
                cur = set(st.session_state["tickers"])
                cur.update({"^VIX", "^VIX9D"})
                st.session_state["tickers"] = sorted(cur)
                st.success("Added ^VIX and ^VIX9D to tickers.")
        with col2:
            if st.button("🧹 Clean Tickers", use_container_width=True):
                st.session_state["tickers"] = sorted({t.strip().upper() for t in st.session_state["tickers"] if t.strip()})
                st.success("Deduplicated & normalized tickers.")
        with col3:
            if st.button("🗑️ Reset to SPY/AAPL/MSFT", use_container_width=True):
                st.session_state["tickers"] = ["SPY", "AAPL", "MSFT"]
                st.session_state["ma_window"] = 200
                st.session_state["lookback"] = 200
                st.success("Reset core settings.")

with right:
    st.markdown("### 💾 Session Snapshot")
    with st.container(border=True):
        snapshot = {
            "tickers": st.session_state.get("tickers", []),
            "ma_window": st.session_state.get("ma_window", None),
            "lookback": st.session_state.get("lookback", None),
        }
        st.json(snapshot)

# --------------------------------------------------------------------------------------
# Help / Tips
# --------------------------------------------------------------------------------------
st.markdown("---")
st.subheader("Tips")
st.markdown(
    """
- All **Global Settings** (Tickers, MA Window, Lookback) are now in the **Sidebar**.
- This page (Home) now focuses on **Market Summary** and **Strategy Navigation**.
- To add more pages, drop files into `pages/` with a number prefix.
"""
)
