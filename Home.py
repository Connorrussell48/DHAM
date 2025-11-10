# home.py
from __future__ import annotations
import json
from pathlib import Path
from textwrap import dedent
from datetime import datetime

import streamlit as st
import os # <-- Added this import

# --------------------------------------------------------------------------------------
# Page setup
# --------------------------------------------------------------------------------------
st.set_page_config(
    page_title="Desk Hub",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------------------
# Theme / CSS (Bloomberg-y dark, tidy spacing, better card aesthetics)
# --------------------------------------------------------------------------------------
BLOOM_BG       = "#0B0F14"
BLOOM_PANEL    = "#121820"
BLOOM_TEXT     = "#FFFFFF"
BLOOM_MUTED    = "rgba(255,255,255,0.70)"
NEUTRAL_GRAY   = "#4A5B6E"
INPUT_BG       = "#2E3A46"
INPUT_BG_LIGHT = "#3A4654"
ACCENT_BLUE    = "#2BB3F3"
ACCENT_GREEN   = "#26D07C"
ACCENT_PURPLE  = "#8A7CF5"
DARK_PURPLE    = "#3A2A6A"

st.markdown(
    dedent(
        f"""
        <style>
        :root {{
          --bg:{BLOOM_BG}; --panel:{BLOOM_PANEL}; --text:{BLOOM_TEXT}; --muted:{BLOOM_MUTED};
          --neutral:{NEUTRAL_GRAY}; --input:{INPUT_BG}; --inputlight:{INPUT_BG_LIGHT};
          --blue:{ACCENT_BLUE}; --green:{ACCENT_GREEN}; --purple:{ACCENT_PURPLE};
        }}
        html, body {{
          height:100%;
          background: radial-gradient(1200px 600px at 15% -10%, rgba(43,179,243,0.12), transparent 60%),
                      radial-gradient(1200px 600px at 85% 110%, rgba(138,124,245,0.12), transparent 60%),
                      linear-gradient(135deg, var(--bg) 0%, {DARK_PURPLE} 100%) fixed !important;
        }}
        .stApp {{ background:transparent!important; color:var(--text); }}
        .block-container {{ max-width: 1500px; padding-top: .6rem; padding-bottom: 2rem; }}
        header[data-testid="stHeader"] {{ background:transparent!important; height:2.5rem!important; }}
        [data-testid="stDecoration"] {{ background:transparent!important; }}

        /* Cards */
        .card {{
          background: linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.00));
          border: 1px solid rgba(255,255,255,0.10);
          border-radius: 16px;
          padding: 16px 16px 14px 16px;
          box-shadow: 0 8px 24px rgba(0,0,0,.25);
        }}
        .card-title {{ font-weight: 700; font-size: 1.02rem; letter-spacing: .2px; }}
        .kpi {{
          background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.00));
          border: 1px solid rgba(255,255,255,0.10);
          border-radius: 14px;
          padding: 12px 14px;
          text-align: left;
        }}
        .kpi .h {{ font-size: .78rem; color: var(--muted); margin-bottom: 4px; }}
        .kpi .v {{ font-size: 1.25rem; font-weight: 800; }}

        /* Buttons */
        .stButton>button {{
          background: var(--input)!important; color: var(--text)!important;
          border: 1px solid var(--neutral)!important; border-radius: 10px!important;
        }}
        .stTextInput>div>div>input {{
          background: var(--inputlight)!important; color: var(--text)!important; border-radius: 8px!important;
          border: 1px solid rgba(255,255,255,0.12)!important;
        }}
        .stNumberInput input {{
          background: var(--inputlight)!important; color: var(--text)!important; border-radius: 8px!important;
          border: 1px solid rgba(255,255,255,0.12)!important;
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

# Fun one-liner (kept because it matches your vibe)
st.markdown(
    """
    <div style="text-align:center; font-size:1.05rem; font-style:italic; color:rgba(255,255,255,0.80); margin:-4px 0 18px 0;">
      "You're either a smart-fella or fart smella" – Confucius
    </div>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------------------
# Sidebar: Global controls that persist across pages
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
                # Use first column as tickers
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
    st.caption("Info")
    st.write(f":small_blue_diamond: Session started **{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}**")
    st.write(":small_blue_diamond: Settings persist while the app is running.")

# --------------------------------------------------------------------------------------
# Top row: KPIs / Status
# --------------------------------------------------------------------------------------
c1, c2, c3, c4 = st.columns([1.1, 1.1, 1.1, 1.1])
with c1:
    st.markdown('<div class="kpi"><div class="h">Tracked Tickers</div><div class="v">'
                f'{len(st.session_state["tickers"]):,}</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown('<div class="kpi"><div class="h">MA Window</div><div class="v">'
                f'{st.session_state["ma_window"]}</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown('<div class="kpi"><div class="h">Convexity Lookback</div><div class="v">'
                f'{st.session_state["lookback"]}</div></div>', unsafe_allow_html=True)
with c4:
    # --- Start of the necessary change for GitHub deployment ---
    # The Path("data") and glob * will work, but this uses os.listdir for robustness.
    data_dir_name = "data"
    data_dir = Path(data_dir_name)
    data_dir.mkdir(exist_ok=True)
    
    # Use os.listdir to robustly count files (excluding hidden/system files)
    count_files = sum(1 for item in os.listdir(data_dir) if os.path.isfile(data_dir / item))
    # --- End of the necessary change ---

    st.markdown('<div class="kpi"><div class="h">Local Data Files</div><div class="v">'
                f'{count_files}</div></div>', unsafe_allow_html=True)

st.markdown("")

# --------------------------------------------------------------------------------------
# Page navigation (auto-detect pages that actually exist)
# --------------------------------------------------------------------------------------
st.subheader("Jump to a page")

# --- Start of the necessary change for GitHub deployment ---
# Pages must be in a 'pages' directory relative to the Home.py file.
# We map the display name to the file name which we then check for existence.
PAGE_MAPPING = {
    "📈 Slope Convexity": "1_Slope_Convexity.py",
    "📉 Mean Reversion (draft)": "2_Mean_Reversion.py",
    # Add more pages here as you create them
}
pages_dir = Path("pages")
available = []

# This robustly checks for the file in the 'pages' directory
for label, filename in PAGE_MAPPING.items():
    rel_path = pages_dir / filename
    if rel_path.exists():
        available.append((label, rel_path.as_posix())) # Convert Path to string for st.page_link
# --- End of the necessary change ---

# Render as tidy link cards
if available:
    cols = st.columns(len(available))
    for i, (label, rel_path) in enumerate(available):
        with cols[i]:
            st.markdown(
                f"""
                <div class="card">
                  <div class="card-title">{label}</div>
                  <div class="small-muted" style="margin:.25rem 0 .6rem 0;">Path: <code>{rel_path}</code></div>
                  <div>{'<span class="pill">Available</span>'}</div>
                  <div style="margin-top:.6rem;"> </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            # Use the relative path for page linking
            st.page_link(rel_path, label="Open", icon=None) 
else:
    st.info("No pages detected in `pages/` yet. Add files like `1_Slope_Convexity.py` to enable navigation.")

st.markdown("---")

# --------------------------------------------------------------------------------------
# Utilities: Quick Actions & Session Snapshot
# --------------------------------------------------------------------------------------
left, right = st.columns([1.4, 1])

with left:
    st.markdown("### Quick Actions")
    with st.container(border=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("➕ Add VIX & VIX9D"):
                cur = set(st.session_state["tickers"])
                cur.update({"^VIX", "^VIX9D"})
                st.session_state["tickers"] = sorted(cur)
                st.success("Added ^VIX and ^VIX9D to tickers.")
        with col2:
            if st.button("🧹 Clean Tickers"):
                st.session_state["tickers"] = sorted({t.strip().upper() for t in st.session_state["tickers"] if t.strip()})
                st.success("Deduplicated & normalized tickers.")
        with col3:
            if st.button("🗑️ Reset to SPY/AAPL/MSFT"):
                st.session_state["tickers"] = ["SPY", "AAPL", "MSFT"]
                st.session_state["ma_window"] = 200
                st.session_state["lookback"] = 200
                st.success("Reset core settings.")

with right:
    st.markdown("### Session Snapshot")
    with st.container(border=True):
        # Keep snapshot compact but readable
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
- Your *watchlist.json* and `st.session_state` carry across pages.
- To add more pages, drop files into `pages/` with a number prefix for ordering (e.g., `1_`, `2_`).
- You can route programmatically from any page:

```python
import streamlit as st
st.switch_page("pages/1_Slope_Convexity.py")
"""
)
