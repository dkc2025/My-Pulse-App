# ===================== IMPORTS =====================
import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, time
import pytz
from streamlit_autorefresh import st_autorefresh

# ===================== PAGE CONFIG =====================
st.set_page_config(
    page_title="DKC Intraday Pulse",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===================== MARKET STATUS =====================
def market_live():
    tz = pytz.timezone("Asia/Kolkata")
    now = datetime.now(tz)
    return now.weekday() < 5 and time(9,15) <= now.time() <= time(15,30)

IS_LIVE = market_live()

# ===================== STOCK LIST =====================
STOCKS = [
    "RELIANCE.NS","TCS.NS","HDFCBANK.NS","ICICIBANK.NS","INFY.NS",
    "SBIN.NS","ITC.NS","LT.NS","BHARTIARTL.NS","TATAMOTORS.NS",
    "AXISBANK.NS","MARUTI.NS","ADANIENT.NS","BAJFINANCE.NS","WIPRO.NS"
]

# ===================== CSS =====================
st.markdown("""
<style>
html,body,.stApp{background:#f8fafc;font-family:Arial}
[data-testid="stSidebar"]{background:#ffffff;border-right:1px solid #e5e7eb}
.badge{display:inline-block;padding:4px 10px;border-radius:20px;
font-size:10px;font-weight:700;margin-top:6px}
.live{background:#dcfce7;color:#166534}
.closed{background:#fee2e2;color:#991b1b}
div[data-testid="stDataFrame"]{
    background:white;border-radius:10px;border:1px solid #e5e7eb
}
</style>
""", unsafe_allow_html=True)

# ===================== SIDEBAR =====================
with st.sidebar:
    st.markdown("### DKC Intraday Pulse")
    st.caption("Trading Dashboard")

    st.markdown(
        f"<span class='badge {'live' if IS_LIVE else 'closed'}'>"
        f"● {'LIVE MARKET' if IS_LIVE else 'MARKET CLOSED'}</span>",
        unsafe_allow_html=True
    )

    st.markdown("---")

    MENU = st.radio(
        "MENU",
        [
            "Market Wise",
            "Trade Flow",
            "TradeX (Live Signals)",
            "Stock-On",
            "Swing Spectrum",
            "Option Clock",
            "Index Mover"
        ],
        label_visibility="collapsed"
    )

    st.markdown("---")

    if st.button("🔁 Manual Refresh"):
        st.cache_data.clear()
        st.experimental_rerun()

    AUTO = st.checkbox("⚡ Auto Refresh", value=True)
    INTERVAL = st.slider("Seconds", 5, 60, 15)

# ===================== DATA FETCH =====================
@st.cache_data(ttl=60)
def fetch_data():
    return yf.download(
        tickers=STOCKS,
        period="5d",
        interval="1m",
        group_by="ticker",
        progress=False,
        threads=True
    )

def calculate_metrics(data, symbol):
    try:
        if symbol not in data.columns.levels[0]:
            return None

        df = data[symbol].dropna()
        if len(df) < 2:
            return None

        last = df.iloc[-1]
        prev = df.iloc[-2]

        ltp = float(last["Close"])
        chg = ((ltp - prev["Close"]) / prev["Close"]) * 100
        vol_avg = df["Volume"].mean() or 1
        xf = last["Volume"] / vol_avg
        confidence = min(100, abs(chg) * 30 + xf * 15)

        return {
            "SYMBOL": symbol.replace(".NS",""),
            "LTP": ltp,
            "CHANGE": chg,
            "VOL": int(last["Volume"]),
            "X_FACTOR": f"{xf:.2f}x",
            "CONFIDENCE": round(confidence,1),
            "TIME": last.name.strftime("%H:%M")
        }
    except:
        return None

# ===================== MAIN DATA =====================
data = fetch_data()
rows = []

if data is not None:
    for s in STOCKS:
        r = calculate_metrics(data, s)
        if r:
            rows.append(r)

df = pd.DataFrame(rows)

# ===================== STOCK SIGNAL LOGIC (LIVE) =====================
def stock_signal(row):
    xf = float(row["X_FACTOR"].replace("x",""))
    if row["CHANGE"] > 0.8 and xf >= 1.5:
        return "🟢 STRONG BUY"
    elif row["CHANGE"] < -0.8 and xf >= 1.5:
        return "🔴 STRONG SELL"
    elif xf >= 1.5:
        return "🟡 WATCH"
    else:
        return ""

if not df.empty:
    df["STOCK_SIGNAL"] = df.apply(stock_signal, axis=1)

# ===================== STYLE =====================
def style_df(df):
    return (
        df.style
        .applymap(lambda x:"color:#2563eb;font-weight:700",subset=["SYMBOL"])
        .applymap(lambda x:"color:green" if x>0 else "color:red",subset=["CHANGE"])
        .applymap(
            lambda x:"color:green;font-weight:700" if x>=70 else
                     "color:orange;font-weight:700" if x>=40 else
                     "color:red;font-weight:700",
            subset=["CONFIDENCE"]
        )
        .format({"LTP":"₹{:.2f}","CHANGE":"{:+.2f}%","VOL":"{:,}"})
    )

# ===================== PAGES =====================
if MENU == "Market Wise":
    st.subheader("🚀 Market Wise")
    c1, c2 = st.columns(2)
    with c1:
        st.write("Gainers")
        st.dataframe(style_df(df[df["CHANGE"] > 0]),
                     use_container_width=True, hide_index=True)
    with c2:
        st.write("Losers")
        st.dataframe(style_df(df[df["CHANGE"] < 0]),
                     use_container_width=True, hide_index=True)

elif MENU == "Trade Flow":
    st.subheader("🌊 Trade Flow (High Volume)")
    st.dataframe(
        style_df(df.sort_values("VOL", ascending=False)),
        use_container_width=True,
        hide_index=True
    )

elif MENU == "TradeX (Live Signals)":
    st.subheader("📢 Live Stock Signals (Intraday)")
    sig_df = df[df["STOCK_SIGNAL"] != ""]

    if sig_df.empty:
        st.info("⏳ No strong stock signal yet")
    else:
        st.dataframe(
            style_df(sig_df),
            use_container_width=True,
            hide_index=True
        )

elif MENU == "Stock-On":
    st.subheader("📌 Stock-On")
    st.info("Breakout candidates (logic expandable)")

elif MENU == "Swing Spectrum":
    st.subheader("📈 Swing Spectrum")
    st.info("Swing trend strength (coming soon)")

elif MENU == "Option Clock":
    st.subheader("🕒 Option Clock – Live Intraday Bias")

    avg_change = df["CHANGE"].mean() if not df.empty else 0

    if avg_change > 0.3:
        bias = "🟢 BULLISH (Put Writing Likely)"
        color = "#22c55e"
    elif avg_change < -0.3:
        bias = "🔴 BEARISH (Call Writing Likely)"
        color = "#ef4444"
    else:
        bias = "🟡 SIDEWAYS / WAIT"
        color = "#facc15"

    st.markdown(
        f"<h2 style='color:{color}'>{bias}</h2>",
        unsafe_allow_html=True
    )
    st.caption("Based on live price behaviour (safe intraday proxy)")

elif MENU == "Index Mover":
    st.subheader("📊 Index Mover")
    st.dataframe(
        style_df(df.sort_values("CHANGE", ascending=False)),
        use_container_width=True,
        hide_index=True
    )

# ===================== AUTO REFRESH =====================
if AUTO:
    st_autorefresh(interval=INTERVAL * 1000, key="auto_refresh")
