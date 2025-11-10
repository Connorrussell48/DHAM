import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib
matplotlib.use("Agg")  # non-GUI backend for Streamlit
import matplotlib.pyplot as plt
import streamlit as st
from datetime import date
from textwrap import dedent
import json
import os
import io, math  # fixed-size export + label placement

# --- Page config ---
st.set_page_config(
    page_title="Slope Convexity Strategy",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Theme tokens ---
BLOOM_BG      = "#0B0F14"
BLOOM_PANEL   = "#121820"
BLOOM_TEXT    = "#FFFFFF"
BLOOM_MUTED   = "rgba(255,255,255,0.70)"
BLOOM_ACCENT  = "#26D07C"     # bullish teal
BLOOM_NEG     = "#D9534F"     # muted red
NEUTRAL_GRAY  = "#4A5B6E"     # borders/text
INPUT_BG      = "#2E3A46"     # dark gray inputs (sidebar)
INPUT_BG_LIGHT= "#3A4654"     # light gray inputs (main area)
DARK_PURPLE   = "#3A2A6A"     # lighter purple for clearer gradient

SIDEBAR_WIDTH = 450
WATCHLIST_PATH = "watchlist.json"

def apply_dark_bloomberg_theme():
    st.markdown(
        dedent(f"""
        <style>
        :root {{
          --bg:{BLOOM_BG}; --panel:{BLOOM_PANEL}; --text:{BLOOM_TEXT}; --muted:{BLOOM_MUTED};
          --teal:{BLOOM_ACCENT}; --red:{BLOOM_NEG}; --neutral:{NEUTRAL_GRAY};
          --input:{INPUT_BG}; --inputlight:{INPUT_BG_LIGHT};
          --shadow:0 4px 6px rgba(0,0,0,.10);
        }}

        /* Black -> lighter purple gradient */
        html, body {{
          height:100%;
          background: linear-gradient(135deg, var(--bg) 0%, {DARK_PURPLE} 100%) fixed !important;
        }}
        .stApp {{ background: transparent !important; color: var(--text); }}
        .block-container {{ max-width:1500px; padding-top:.6rem; padding-bottom:2rem; }}

        header[data-testid="stHeader"] {{ background:transparent!important; height:2.5rem!important; }}
        [data-testid="stDecoration"] {{ background:transparent!important; }}

        /* Sidebar shell */
        section[data-testid="stSidebar"], aside[data-testid="stSidebar"] {{
          min-width:{SIDEBAR_WIDTH}px!important; max-width:{SIDEBAR_WIDTH}px!important;
          background:var(--panel)!important;
          border-right:1px solid var(--neutral); box-shadow:var(--shadow);
        }}
        section[data-testid="stSidebar"] *, aside[data-testid="stSidebar"] * {{ color:var(--text)!important; }}

        /* Sidebar inputs */
        section[data-testid="stSidebar"] input,
        section[data-testid="stSidebar"] textarea,
        section[data-testid="stSidebar"] .stTextArea textarea,
        section[data-testid="stSidebar"] [data-testid="stTextInput"] input,
        section[data-testid="stSidebar"] [data-testid="stNumberInput"] input {{
          background:var(--input)!important; border:1px solid var(--neutral)!important; color:var(--text)!important;
        }}
        input::placeholder, textarea::placeholder {{ color:rgba(255,255,255,.65)!important; }}

        /* Sidebar selects */
        section[data-testid="stSidebar"] [data-baseweb="select"] > div {{
          background:var(--input)!important; border-color:var(--neutral)!important; color:var(--text)!important;
        }}
        [data-baseweb="select"] input {{ background:transparent!important; color:var(--text)!important; }}
        [data-baseweb="select"] svg   {{ fill:var(--text)!important; }}

        /* Sidebar triggers/buttons */
        section[data-testid="stSidebar"] :is(button, div[role="button"]) {{
          background:var(--input)!important; color:var(--text)!important; border:1px solid var(--neutral)!important;
          box-shadow:var(--shadow); border-radius:10px;
        }}

        /* Popovers & menus */
        [data-baseweb="popover"] div[role="dialog"],
        [data-baseweb="menu"], div[role="listbox"] {{
          background:var(--panel)!important; color:var(--text)!important; border:1px solid var(--neutral)!important; box-shadow:var(--shadow);
        }}
        [data-baseweb="popover"] :is(input, textarea) {{
          background:var(--input)!important; color:var(--text)!important; border:1px solid var(--neutral)!important;
        }}
        div[role="option"] {{ color:var(--text)!important; }}

        /* KPI metric cards: white bg + dark text */
        div[data-testid="stMetric"] {{
          background:#FFFFFF!important; color:#0B0F14!important; border:1px solid var(--neutral)!important;
          border-radius:12px!important; padding:12px 14px!important; box-shadow:var(--shadow)!important;
        }}
        div[data-testid="stMetric"] * {{ color:#0B0F14!important; }}

        /* Main-area inputs & selects: light grey background */
        div[data-testid="stAppViewContainer"] input,
        div[data-testid="stAppViewContainer"] textarea {{
          background:var(--inputlight)!important; color:var(--text)!important; border:1px solid var(--neutral)!important;
        }}
        div[data-testid="stAppViewContainer"] [data-baseweb="select"] > div {{
          background:var(--inputlight)!important; color:var(--text)!important; border:1px solid var(--neutral)!important;
        }}
        div[data-testid="stAppViewContainer"] label {{ color:var(--text)!important; }}

        /* Buttons (download etc.) */
        div[data-testid="stAppViewContainer"] .stButton>button,
        .stDownloadButton > button,
        div[data-testid="stAppViewContainer"] .stForm button {{
          background:var(--input)!important; color:var(--text)!important;
          border:1px solid var(--neutral)!important; border-radius:10px!important; box-shadow:var(--shadow)!important;
        }}

        /* Dataframe/editor backgrounds -> light grey */
        div[data-testid="stDataFrame"] div[role="grid"],
        div[data-testid="stDataFrame"] canvas {{ background: var(--inputlight)!important; }}

        /* Hide row-index in editors (best-effort) */
        div[data-testid="stDataFrame"] [data-testid="stTable"] [data-testid="stRowHeader"] {{ display:none!important; }}

        /* Transparent matplotlib backgrounds */
        .element-container:has(canvas) {{ background:transparent!important; }}

        /* Hide fullscreen icons */
        [data-testid="StyledFullScreenButton"], button[title="View fullscreen"] {{ display:none!important; }}
        </style>
        """),
        unsafe_allow_html=True
    )

st.markdown("""
<style>
/* ---- File uploader: unify look in sidebar AND main area ---- */

/* Dropzone container */
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"],
div[data-testid="stAppViewContainer"] [data-testid="stFileUploaderDropzone"] {
  background: var(--input) !important;      /* dark grey to match theme */
  color: var(--text) !important;
  border: 1px solid var(--neutral) !important;
  border-radius: 12px !important;
}

/* Text & icons inside the dropzone */
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] *,
div[data-testid="stAppViewContainer"] [data-testid="stFileUploaderDropzone"] * {
  color: var(--text) !important;
  fill: var(--text) !important;
}

/* “Browse files” button (idle/hover/focus) */
section[data-testid="stSidebar"] [data-testid="stFileUploader"] :is(button, div[role="button"], label[for^="upload"]),
div[data-testid="stAppViewContainer"] [data-testid="stFileUploader"] :is(button, div[role="button"], label[for^="upload"]) {
  background: var(--input) !important;      /* white text on grey, like other buttons */
  color: var(--text) !important;
  border: 1px solid var(--neutral) !important;
  border-radius: 10px !important;
  box-shadow: var(--shadow) !important;
}

/* Optional: subtle highlight on hover */
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"]:hover,
div[data-testid="stAppViewContainer"] [data-testid="stFileUploaderDropzone"]:hover {
  border-color: var(--teal) !important;
}
</style>
""", unsafe_allow_html=True)


apply_dark_bloomberg_theme()

# ---- Extra UI fixes (expander + dropdown menus in main area) ----
st.markdown("""
<style>
/* Expander header: gray bg + white text */
div[data-testid="stExpander"] > details > summary {
  background: var(--inputlight) !important;
  color: var(--text) !important;
  border: 1px solid var(--neutral) !important;
  border-radius: 10px !important;
  padding: 8px 12px !important;
}
/* Expander body edge */
div[data-testid="stExpander"] > details > div[role="region"] {
  border-left: 1px solid var(--neutral) !important;
  border-right: 1px solid var(--neutral) !important;
  border-bottom: 1px solid var(--neutral) !important;
  border-radius: 0 0 10px 10px !important;
  background: transparent !important;
}
/* Dropdown menus (main area) */
div[data-testid="stAppViewContainer"] [data-baseweb="menu"] {
  background: var(--inputlight) !important; color: var(--text) !important; border: 1px solid var(--neutral) !important;
}
div[data-testid="stAppViewContainer"] [data-baseweb="menu"] div[role="option"] { color: var(--text) !important; }
</style>
""", unsafe_allow_html=True)

# ---------------- Header ----------------
st.markdown(
    """
    <div style="display:flex;align-items:center;gap:12px;padding:12px 20px;margin:0 0 8px 0;border-bottom:1px solid var(--neutral);">
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
        <rect x="2" y="3" width="20" height="18" rx="3" stroke="#2BB3F3" stroke-width="1.5"/>
        <polyline points="5,15 9,11 12,13 17,7 19,9" stroke="#26D07C" stroke-width="2" fill="none" />
        <circle cx="19" cy="9" r="1.8" fill="#26D07C"/>
      </svg>
      <div style="font-weight:900;letter-spacing:.3px;font-size:1.6rem;">Slope Convexity Strategy</div>
      <div style="margin-left:auto;font-size:.95rem;color:rgba(255,255,255,.70);font-weight:500;">Advanced Market Sentiment Analysis</div>
    </div>
    """,
    unsafe_allow_html=True
)

# --- Quote under header ---
st.markdown(
    """
    <div style="text-align:center; font-size:1.1rem; font-style:italic; color:rgba(255,255,255,0.80); margin:-4px 0 16px 0;">
      "You're either a smart-fella or fart smella" – Confucius
    </div>
    """,
    unsafe_allow_html=True
)

# ---------------- Session state defaults ----------------
if 'sector_map' not in st.session_state:
    st.session_state['sector_map'] = {}

if 'watchlist' not in st.session_state:
    if os.path.exists(WATCHLIST_PATH):
        try:
            with open(WATCHLIST_PATH, "r") as f:
                st.session_state['watchlist'] = json.load(f)
        except Exception:
            st.session_state['watchlist'] = []
    else:
        st.session_state['watchlist'] = []

def save_watchlist_to_disk():
    try:
        with open(WATCHLIST_PATH, "w") as f:
            json.dump(st.session_state['watchlist'], f, indent=2)
    except Exception as e:
        st.toast(f"Failed to save watchlist: {e}", icon="⚠️")

def sync_watchlist_sector():
    wl_tickers = [row.get("Ticker","").upper().strip() for row in st.session_state['watchlist'] if row.get("Ticker")]
    wl_tickers = [t for t in wl_tickers if t]
    seen = set(); uniq = []
    for t in wl_tickers:
        if t not in seen:
            seen.add(t); uniq.append(t)
    st.session_state['sector_map']["Watchlist"] = ", ".join(uniq)

sync_watchlist_sector()

def parse_tickers(text: str) -> list:
    parts = [p.strip().upper() for line in (text or "").splitlines() for p in line.replace(",", " ").split()]
    return [p for p in parts if p]

def build_ticker_to_sector_map(sector_map: dict) -> dict:
    mapping = {}
    for sec, txt in sector_map.items():
        for tk in parse_tickers(txt):
            mapping[tk] = sec
    return mapping

# ---------------- Sidebar ----------------
with st.sidebar:
    st.header("Settings")
    st.subheader("Sectors")

    with st.popover("➕ Add sector"):
        new_sector = st.text_input("Sector name", placeholder="e.g., Tech")
        new_tickers = st.text_area("Tickers for this sector", placeholder="AAPL, MSFT, NVDA …")
        if st.button("Add", key="add_sector_btn"):
            name = (new_sector or "").strip()
            if name:
                st.session_state.sector_map[name] = new_tickers
                st.toast(f"Added sector '{name}'", icon="✅")

    if st.session_state.sector_map:
        for sec in sorted(st.session_state.sector_map.keys()):
            c1, c2 = st.columns([0.78, 0.22])
            with c1: st.markdown(f"**{sec}**")
            with c2:
                with st.popover("⚙️"):
                    ta_key = f"ta_{sec}"
                    cur_val = st.session_state.sector_map.get(sec, "")
                    updated = st.text_area(f"Tickers for {sec}", value=cur_val, key=ta_key)
                    if st.button(f"Save '{sec}'", key=f"save_{sec}"):
                        st.session_state.sector_map[sec] = updated
                        st.toast(f"Updated tickers for '{sec}'", icon="🛠️")

    scope_options = ["All", "All but"] + sorted(st.session_state.sector_map.keys())
    run_scope = st.selectbox("Run scope", options=scope_options)

    excluded_sectors = []
    if run_scope == "All but" and st.session_state.sector_map:
        excluded_sectors = st.multiselect("Exclude sectors", options=sorted(st.session_state.sector_map.keys()))

    st.markdown("---")
    # Intervals: remove 60m; keep 1h
    intervals = st.multiselect("Intervals", ["5m", "15m", "30m", "1h", "1d"], default=["5m", "15m", "30m"])

    st.markdown("---")
    st.subheader("Indicator Params")
    ma_period = st.slider("MA period", 50, 300, 200, step=10)
    lookback = st.slider("Lookback (convexity window)", 5, 60, 30, step=1)

    st.markdown("---")
    st.subheader("Filter Indications By Date")
    only_today = st.checkbox("Only show hits for today", value=True)
    selected_date = st.date_input("Or pick a start date", value=date.today(), disabled=only_today)
    days_to_screen = 1
    if not only_today:
        days_to_screen = st.number_input("Number of business days to screen", min_value=1, max_value=30, value=1, step=1)

    st.markdown("---")
    sl1, sl2 = st.columns(2)
    with sl1:
        sectors_json = pd.Series(st.session_state.sector_map).to_json()
        st.download_button(
            label="Download sectors.json",
            data=sectors_json.encode(),
            file_name="sectors.json",
            mime="application/json",
            key="dl_sectors_json"
        )
    with sl2:
        up = st.file_uploader("Load sectors.json", type=["json"], label_visibility="visible")
        if up is not None:
            try:
                st.session_state.sector_map = json.load(up)
                st.success("Sectors loaded.")
            except Exception as e:
                st.error(f"Failed to load JSON: {e}")

    st.markdown("---")
    run_scan = st.button("Run", use_container_width=True)

# ---------------- Data + Indicator Logic ----------------
def collect_tickers(scope: str, excluded: list) -> list:
    smap = st.session_state.sector_map
    if scope == "All":
        tickers = []
        for sec, txt in smap.items():
            tickers.extend(parse_tickers(txt))
        return sorted(list(dict.fromkeys(tickers)))
    elif scope == "All but":
        tickers = []
        for sec, txt in smap.items():
            if sec not in excluded:
                tickers.extend(parse_tickers(txt))
        return sorted(list(dict.fromkeys(tickers)))
    else:
        txt = smap.get(scope, "")
        return sorted(list(dict.fromkeys(parse_tickers(txt))))

def _default_period_for_interval(interval: str) -> str:
    interval = interval.lower()
    if interval in ("5m", "15m", "30m"): return "30d"
    if interval in ("1h",):              return "60d"
    if interval in ("1d",):              return "2y"
    return "1mo"

@st.cache_data(ttl=24*60*60, show_spinner=True)
def fetch_one(ticker: str, interval: str) -> pd.DataFrame:
    period = _default_period_for_interval(interval)
    df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True, threads=True)
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.sort_index()
    for col in ["Open","High","Low","Close","Adj Close","Volume"]:
        if col in df.columns:
            vals = df[col].to_numpy()
            if vals.ndim > 1: df[col] = np.squeeze(vals)
    return df

def indicators(df: pd.DataFrame, ma_period: int = 200, lookback: int = 30) -> pd.DataFrame:
    df = df.copy()
    if df.empty or "Close" not in df.columns: return pd.DataFrame()
    df["MA200"] = df["Close"].rolling(window=ma_period).mean()
    price = df["Close"].to_numpy().reshape(-1)
    ma200 = df["MA200"].to_numpy().reshape(-1)
    n = len(df)
    slopes = np.zeros(n); convexity = np.zeros(n)
    start_idx = ma_period + lookback
    for i in range(start_idx, n):
        ma_window = ma200[i - lookback : i + 1]
        t_window = np.arange(lookback + 1)
        start_ma, end_ma = ma_window[0], ma_window[-1]
        slope = (end_ma - start_ma) / lookback
        secant = start_ma + slope * t_window
        area = float(np.trapz(secant - ma_window, t_window))  # NumPy (no SciPy)
        normalized_area = (area / price[i]) * lookback if price[i] != 0 else 0.0
        slopes[i]    = 100.0 * np.tanh(float((slope / ma200[i]) * 100.0 * lookback)) if ma200[i] != 0 else 0.0
        convexity[i] = 100.0 * np.tanh(float(normalized_area))
    return pd.DataFrame({
        'datetime': df.index[start_idx:], 'convexity': convexity[start_idx:], 'slope': slopes[start_idx:],
        'price': price[start_idx:], 'ma': ma200[start_idx:]
    }).set_index('datetime')

def find_transitions(ind_df: pd.DataFrame) -> pd.DataFrame:
    if ind_df.empty: return pd.DataFrame()
    s = ind_df['slope']; c = ind_df['convexity']; p = ind_df['price']; m = ind_df['ma']
    bullish = (s.shift(1) < 0) & (s > 0) & (c > 0) & (p > m)
    bearish = (s.shift(1) > 0) & (s < 0) & (c < 0) & (p < m)
    rows = []
    for ts, row in ind_df[bullish].iterrows():
        rows.append({'Datetime': pd.to_datetime(ts), 'Sentiment':'Bullish','Slope':row['slope'],
                     'Convexity':row['convexity'],'Price':row['price'],'MA':row['ma']})
    for ts, row in ind_df[bearish].iterrows():
        rows.append({'Datetime': pd.to_datetime(ts), 'Sentiment':'Bearish','Slope':row['slope'],
                     'Convexity':row['convexity'],'Price':row['price'],'MA':row['ma']})
    return pd.DataFrame(rows)

# ---------------- Run Scan + Display Prep ----------------
results = []
sector_label_for_ticker = build_ticker_to_sector_map(st.session_state.sector_map)

if 'last_scope' not in st.session_state: st.session_state['last_scope'] = None
if 'last_excluded' not in st.session_state: st.session_state['last_excluded'] = []

if run_scan:
    tickers = collect_tickers(run_scope, excluded_sectors)
    st.session_state['last_scope'] = run_scope
    st.session_state['last_excluded'] = excluded_sectors
    if not tickers:
        st.warning("No tickers found. Add sectors and tickers, or change run scope.")
    else:
        progress = st.progress(0, text="Fetching & computing…")
        total = max(len(tickers) * max(1, len(intervals)), 1); done = 0
        for tk in tickers:
            for iv in (intervals or ["5m"]):
                try:
                    df = fetch_one(tk, iv)
                    if df.empty:
                        done += 1; progress.progress(min(done/total,1.0), text=f"{tk} {iv}: no data"); continue
                    ind_df = indicators(df, ma_period=ma_period, lookback=lookback)
                    trans_df = find_transitions(ind_df)
                    if not trans_df.empty:
                        trans_df.insert(0,"Ticker",tk)
                        trans_df.insert(1,"Timeframe",iv)
                        trans_df.insert(2,"Sector", sector_label_for_ticker.get(tk, "Unassigned"))
                        results.append(trans_df)
                    done += 1; progress.progress(min(done/total,1.0), text=f"{tk} {iv}: processed")
                except Exception as e:
                    done += 1; progress.progress(min(done/total,1.0), text=f"{tk} {iv}: error {e}")
        progress.empty()

# Prepare hits for KPIs and displays (shared)
hits = None
csv_view = None
if results:
    hits = pd.concat(results, ignore_index=True)
    dt_raw = pd.to_datetime(hits["Datetime"], errors='coerce', utc=True)
    dt_est = dt_raw.dt.tz_convert('America/New_York')
    hits["Date_EST_str"] = dt_est.dt.strftime('%Y-%m-%d')
    hits["Time_EST_str"] = dt_est.dt.strftime('%H:%M')

    if only_today:
        today_est = pd.Timestamp.today(tz='America/New_York').strftime('%Y-%m-%d')
        hits = hits[hits["Date_EST_str"] == today_est]
    else:
        bdays = pd.bdate_range(start=selected_date, periods=days_to_screen)
        allowed_dates = set(d.strftime('%Y-%m-%d') for d in bdays)
        hits = hits[hits["Date_EST_str"].isin(allowed_dates)]

    hits = hits.sort_values(["Ticker","Timeframe","Datetime"])
    csv_view = hits[["Ticker","Sector","Timeframe","Date_EST_str","Time_EST_str","Sentiment"]].rename(
        columns={"Date_EST_str":"Date","Time_EST_str":"Time (EST)"}
    )

# ---------------- KPI Totals ----------------
if hits is not None and not hits.empty:
    total_hits = len(hits)
    bull_hits = int((hits["Sentiment"]=="Bullish").sum())
    bear_hits = int((hits["Sentiment"]=="Bearish").sum())
    unique_tk = int(hits["Ticker"].nunique())
else:
    total_hits = bull_hits = bear_hits = unique_tk = 0

k1,k2,k3,k4 = st.columns(4)
k1.metric("Total", total_hits)
k2.metric("Bullish", bull_hits)
k3.metric("Bearish", bear_hits)
k4.metric("Tickers", unique_tk)

# ---------------- Three-column layout ----------------
left_col, mid_col, right_col = st.columns([1.4, 1.6, 0.9], gap="large")

# ===== LEFT: Sector Pie Charts (rows of 2, larger pies, non-overlapping counts) =====
with left_col:
    st.markdown("### Sector Sentiment")

    if hits is None or hits.empty:
        st.info("Run a scan to populate sector charts.")
    else:
        # Render one pie with robust % placement and responsive counts
        def render_pie(bull: int, bear: int, title: str):
            PCT_FONT = 26  # % label inside donut

            total = bull + bear
            values = [bull, bear] if total > 0 else [1, 0]

            fig, ax = plt.subplots(figsize=(6.2, 6.2), dpi=144)
            wedges, _ = ax.pie(
                values,
                labels=None,
                startangle=90,
                colors=[BLOOM_ACCENT, BLOOM_NEG],
                wedgeprops=dict(width=0.34),
            )

            shown = []
            if total > 0:
                for w, val in zip(wedges, values):
                    if val <= 0:
                        continue
                    pct = 100.0 * val / total
                    if pct >= 5:
                        shown.append((w, pct))

            if len(shown) == 1:
                _, pct = shown[0]
                ax.text(0.0, 0.0, f"{pct:.0f}%", ha="center", va="center",
                        fontsize=PCT_FONT, fontweight="bold", color="white")
            else:
                for w, pct in shown:
                    theta = math.radians((w.theta2 + w.theta1) / 2.0)
                    r = 0.58
                    x, y = r * math.cos(theta), r * math.sin(theta)
                    ax.text(x, y, f"{pct:.0f}%", ha="center", va="center",
                            fontsize=PCT_FONT, fontweight="bold", color="white")

            ax.axis("equal")
            fig.patch.set_alpha(0)

            st.markdown(
                f"<div style='text-align:center; font-size:1.35rem; font-weight:800; margin:4px 0 6px 0;'>{title}</div>",
                unsafe_allow_html=True,
            )

            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=144, transparent=True, bbox_inches="tight", pad_inches=0.30)
            buf.seek(0)
            st.image(buf, use_container_width=True)


            # Responsive counts in a flex row that wraps if narrowed (prevents overlap)
            st.markdown(
                """
                <div style="
                    width:100%;
                    margin:10px auto 0;
                    display:flex;
                    justify-content:center;
                    gap:18px;
                    flex-wrap:wrap;
                    line-height:1.2;
                    text-align:center;
                ">
                  <span style="font-weight:700; font-size:clamp(16px, 1.8vw, 22px);">Bullish: """ + str(bull) + """</span>
                  <span style="font-weight:700; font-size:clamp(16px, 1.8vw, 22px);">Bearish: """ + str(bear) + """</span>
                  <span style="font-weight:700; font-size:clamp(16px, 1.8vw, 22px);">Total: """ + str(total) + """</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Totals by sector (all timeframes)
        by_sector = (
            hits.groupby(["Sector", "Sentiment"])
                .size().unstack(fill_value=0)
                .reindex(columns=["Bullish", "Bearish"], fill_value=0)
        )

        # Counts by sector + timeframe
        by_sector_tf = (
            hits.groupby(["Sector", "Timeframe", "Sentiment"])
                .size().unstack(fill_value=0)
                .reindex(columns=["Bullish", "Bearish"], fill_value=0)
        )

        tf_order = ["5m", "15m", "30m", "1h", "1d"]

        for sector in by_sector.index.tolist():
            with st.expander(sector, expanded=True):
                bull_total = int(by_sector.loc[sector, "Bullish"])
                bear_total = int(by_sector.loc[sector, "Bearish"])

                pies = [("All timeframes", bull_total, bear_total)]
                if sector in by_sector_tf.index.get_level_values(0):
                    tf_counts = by_sector_tf.loc[sector]
                    tfs_sorted = sorted(
                        list(tf_counts.index),
                        key=lambda tf: (tf_order.index(tf) if tf in tf_order else len(tf_order), str(tf))
                    )
                    for tf in tfs_sorted:
                        pies.append((
                            f"Timeframe: {tf}",
                            int(tf_counts.loc[tf, "Bullish"]),
                            int(tf_counts.loc[tf, "Bearish"]),
                        ))

                # Render rows of 2 pies
                for i in range(0, len(pies), 2):
                    row = st.columns(2, gap="large")
                    title1, b1, br1 = pies[i]
                    with row[0]:
                        render_pie(b1, br1, title1)
                    if i + 1 < len(pies):
                        title2, b2, br2 = pies[i + 1]
                        with row[1]:
                            render_pie(b2, br2, title2)

# ----- MIDDLE: Indications table + download -----
with mid_col:
    st.markdown("### Indications")
    if hits is None or hits.empty:
        st.info("Click **Run** to scan with the current settings.")
    else:
        st.dataframe(
            csv_view, use_container_width=True, height=820, hide_index=True,
            column_config={
                "Ticker": st.column_config.TextColumn(width="small"),
                "Sector": st.column_config.TextColumn(width="medium"),
                "Timeframe": st.column_config.TextColumn(width="small"),
                "Date": st.column_config.TextColumn(width="medium"),
                "Time (EST)": st.column_config.TextColumn(width="small"),
                "Sentiment": st.column_config.TextColumn(width="medium"),
            },
        )
        st.download_button("Download Indications CSV",
                           csv_view.to_csv(index=False).encode("utf-8"),
                           file_name="indications.csv", mime="text/csv")

# ----- RIGHT: Watchlist (always visible) -----
with right_col:
    st.subheader("📓 Watchlist")

    with st.form("watchlist_form", clear_on_submit=True):
        wl_ticker = st.text_input("Ticker", placeholder="e.g., NVDA").upper().strip()
        wl_rating = st.selectbox("Rating", ["Bullish", "Neutral", "Bearish"])
        wl_timeframe = st.selectbox("Timeframe", ["5m", "15m", "30m", "1h", "1d"])
        add = st.form_submit_button("Add to Watchlist")

    if add and wl_ticker:
        st.session_state['watchlist'].append({
            "Ticker": wl_ticker,
            "Rating": wl_rating,
            "Timeframe": wl_timeframe
        })
        save_watchlist_to_disk()
        sync_watchlist_sector()
        st.toast(f"Added {wl_ticker} to watchlist", icon="✅")

    wl_df = pd.DataFrame(st.session_state['watchlist'])
    if not wl_df.empty:
        edited = st.data_editor(
            wl_df,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            column_config={
                "Ticker": st.column_config.TextColumn(width="small"),
                "Rating": st.column_config.SelectboxColumn(options=["Bullish","Neutral","Bearish"], width="small"),
                "Timeframe": st.column_config.SelectboxColumn(options=["5m","15m","30m","1h","1d"], width="small"),
            },
            height=420,
        )
        if not edited.equals(wl_df):
            st.session_state['watchlist'] = edited.to_dict(orient="records")
            save_watchlist_to_disk()
            sync_watchlist_sector()

        st.markdown("<div style='margin-top:6px; font-weight:700;'>Delete a ticker</div>", unsafe_allow_html=True)
        existing_tickers = sorted({row["Ticker"] for row in st.session_state['watchlist'] if row.get("Ticker")})
        del_choice = st.selectbox("Select ticker to delete", options=existing_tickers if existing_tickers else ["(none)"])
        if st.button("Delete Selected"):
            if del_choice and del_choice != "(none)":
                st.session_state['watchlist'] = [r for r in st.session_state['watchlist'] if r.get("Ticker") != del_choice]
                save_watchlist_to_disk()
                sync_watchlist_sector()
                st.toast(f"Deleted {del_choice} from watchlist", icon="🗑️")

        if st.button("Clear Watchlist"):
            st.session_state['watchlist'] = []
            save_watchlist_to_disk()
            sync_watchlist_sector()
            st.toast("Watchlist cleared", icon="🗑️")
    else:
        st.markdown(
            "<div style='color: var(--text); opacity: .9; font-weight:600;'>No items in watchlist yet. Add a ticker above.</div>",
            unsafe_allow_html=True
        )

