import streamlit as st
import pandas as pd
import yfinance as yf
import time as tlib
from datetime import datetime, time
import pytz
import plotly.graph_objects as go

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="IntradayPulse Pro", layout="wide", initial_sidebar_state="expanded")

# Initialize Session State
if 'last_update' not in st.session_state:
    st.session_state['last_update'] = datetime.now().strftime('%H:%M:%S')

# --- 2. SUPER PREMIUM CSS (BOLD & DARK) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    html, body, .stApp { background-color: #f3f4f6; font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e5e7eb; }
    
    /* LOGO */
    .logo-container { display: flex; align-items: center; margin-bottom: 25px; }
    .logo-icon {
        background: #2563eb; color: white; width: 40px; height: 40px; border-radius: 8px;
        display: flex; align-items: center; justify-content: center; font-size: 22px; font-weight: bold; margin-right: 12px;
    }
    .logo-text { font-size: 19px; font-weight: 800; color: #111827; letter-spacing: -0.5px; }
    
    /* MARKET STATUS PILL */
    .status-pill {
        padding: 6px 15px; border-radius: 6px; font-size: 11px; font-weight: 700;
        display: block; margin-bottom: 20px; width: 100%; text-align: center;
        text-transform: uppercase; letter-spacing: 0.5px;
    }
    
    /* METRICS STRIP */
    .metric-row { display: flex; gap: 15px; margin-bottom: 20px; }
    .metric-box {
        background: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 15px;
        flex: 1; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .m-label { font-size: 11px; color: #6b7280; font-weight: 700; text-transform: uppercase; margin-bottom: 5px; }
    .m-val { font-size: 20px; font-weight: 800; color: #1f2937; }
    
    /* HEADERS */
    .header-card {
        background: white; padding: 15px 20px; border-radius: 8px 8px 0 0;
        display: flex; justify-content: space-between; align-items: center;
        margin-top: 20px; border-bottom: 1px solid #f0f0f0;
        box-shadow: 0 -2px 5px rgba(0,0,0,0.02);
    }
    .h-green { border-top: 4px solid #10b981; }
    .h-red { border-top: 4px solid #ef4444; }
    .h-blue { border-top: 4px solid #3b82f6; }
    .h-title { font-weight: 800; color: #374151; font-size: 14px; text-transform: uppercase; }
    .live-badge { background: #ef4444; color: white; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: bold; margin-left: 8px; }

    /* DATAFRAME STYLING (The "Gahra Kala" Look) */
    div[data-testid="stDataFrame"] {
        background: white; padding: 0 20px 20px 20px; border-radius: 0 0 8px 8px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    div[data-testid="stDataFrame"] table {
        color: #111827 !important; font-weight: 600 !important; font-size: 14px !important;
    }
    
    /* OI CARDS */
    .oi-card { padding: 15px; border-radius: 10px; color: white; text-align: center; margin-bottom: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .oi-red { background: linear-gradient(135deg, #ef4444, #b91c1c); }
    .oi-green { background: linear-gradient(135deg, #10b981, #047857); }
    .oi-lbl { font-size: 11px; font-weight: 700; opacity: 0.9; text-transform: uppercase; }
    .oi-big { font-size: 22px; font-weight: 800; margin: 4px 0; }
    
    /* SECTOR CARDS */
    .sector-card { background: white; padding: 10px; border-radius: 6px; border: 1px solid #e5e7eb; text-align: center; margin-bottom: 10px; }
    .sec-name { color: #6b7280; font-size: 11px; font-weight: 700; text-transform: uppercase; margin-bottom: 4px; }

    /* BUTTONS */
    div.stButton > button { width: 100%; background-color: #f9fafb; border: 1px solid #d1d5db; color: #374151; font-weight: 600; border-radius: 6px; }
    div.stButton > button:hover { background-color: #2563eb; color: white; border-color: #2563eb; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---

def get_market_status():
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    if now.weekday() < 5 and (time(9,15) <= now.time() <= time(15,30)):
        return '<div class="status-pill" style="background:#dcfce7; color:#16a34a; border:1px solid #86efac;">● MARKET OPEN</div>'
    return '<div class="status-pill" style="background:#fee2e2; color:#b91c1c; border:1px solid #fca5a5;">● MARKET CLOSED</div>'

def color_signals(val):
    s = str(val).lower()
    if any(x in s for x in ['buy', 'bull', 'up', 'high', 'puller', 'support', '↗', '📈']): return 'color: #10b981; font-weight: 800;'
    if any(x in s for x in ['sell', 'bear', 'down', 'low', 'dragger', 'resist', '↘', '📉']): return 'color: #ef4444; font-weight: 800;'
    if 'x' in s: return 'color: #2563eb; font-weight: 800;'
    return 'color: #111827; font-weight: 700;'

@st.cache_data(ttl=5)
def fetch_data(tickers):
    # Fetching 5m interval to get intraday timestamps
    try: return yf.download(tickers, period="5d", interval="5m", group_by='ticker', progress=False)
    except: return None

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("""
        <div class="logo-container">
            <div class="logo-icon">↗</div>
            <div class="logo-text">Intraday<br>Pulse</div>
        </div>
    """, unsafe_allow_html=True)
    st.markdown(get_market_status(), unsafe_allow_html=True)
    if st.button("🔄 REFRESH DATA"):
        st.session_state['last_update'] = datetime.now().strftime('%H:%M:%S')
        st.rerun()
    st.markdown("---")
    menu_options = ["Market Wise", "Option Clock", "Trade Flow", "Stock-On", "Swing Spectrum", "TradeX", "Trade Brahmand", "Index Mover"]
    view = st.radio("NAVIGATION", menu_options, index=0, label_visibility="collapsed")
    st.markdown("---")
    auto_ref = st.checkbox("Auto Refresh", value=True)
    refresh_rate = st.slider("Speed (s)", 5, 60, 30) if auto_ref else 30

# --- 5. DATA ENGINE ---
ALL_TICKERS = [
    "^NSEI", "^NSEBANK", "^INDIAVIX",
    "TECHNOE.NS", "RRKABEL.NS", "PFC.NS", "NTPC.NS", "MEDANTA.NS", "DELHIVERY.NS", "CONCOR.NS", "CGPOWER.NS", "BIOCON.NS", "BALRAMCHIN.NS",
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "TRIDENT.NS", "TITAGARH.NS", "SOLARINDS.NS", "RVNL.NS", "RITES.NS", "RAILTEL.NS", "NUVAMA.NS"
]

data = fetch_data(ALL_TICKERS)

def get_idx(sym):
    try:
        df = data[sym].dropna()
        return df.iloc[-1]['Close'], ((df.iloc[-1]['Close']-df.iloc[-2]['Close'])/df.iloc[-2]['Close'])*100
    except: return 0.0, 0.0

# --- 6. TOP STRIP ---
if view in ["Market Wise", "Option Clock", "Index Mover"]:
    n_ltp, n_chg = get_idx("^NSEI")
    b_ltp, b_chg = get_idx("^NSEBANK")
    v_ltp, v_chg = get_idx("^INDIAVIX")
    pcr = 0.95 + (n_chg/10)
    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-box"><div class="m-label">NIFTY 50</div><div class="m-val">{n_ltp:.0f}</div><div style="color:{'#10b981' if n_chg>=0 else '#ef4444'};font-weight:700;">{n_chg:+.2f}%</div></div>
        <div class="metric-box"><div class="m-label">BANK NIFTY</div><div class="m-val">{b_ltp:.0f}</div><div style="color:{'#10b981' if b_chg>=0 else '#ef4444'};font-weight:700;">{b_chg:+.2f}%</div></div>
        <div class="metric-box"><div class="m-label">INDIA VIX</div><div class="m-val">{v_ltp:.2f}</div><div style="color:{'#ef4444' if v_chg>=0 else '#10b981'};font-weight:700;">{v_chg:+.2f}%</div></div>
        <div class="metric-box"><div class="m-label">PCR RATIO</div><div class="m-val">{pcr:.2f}</div><div style="color:{'#10b981' if pcr>1 else '#ef4444'};font-weight:700;">{'BULLISH' if pcr>1 else 'BEARISH'}</div></div>
    </div>""", unsafe_allow_html=True)

# --- 7. MAIN MODULES ---

if view == "Market Wise":
    gainers, losers = [], []
    if data is not None:
        for t in ALL_TICKERS:
            if "^" in t: continue
            try:
                df = data[t].dropna()
                if df.empty: continue
                
                # --- ACTUAL MARKET TIME LOGIC ---
                last_row = df.iloc[-1]
                prev_row = df.iloc[-2]
                
                # Fetching actual trade time from index
                trade_time = df.index[-1].strftime('%H:%M:%S')
                
                ltp = float(last_row['Close'])
                prev = float(prev_row['Close'])
                chg = ((ltp - prev)/prev)*100
                
                sig = "↗" if chg > 0 else "↘"
                chart_icon = "📈" if chg > 0 else "📉"
                
                avg_vol = df['Volume'].tail(5).mean()
                vol_curr = last_row['Volume']
                xf = round(vol_curr/avg_vol, 2) if avg_vol > 0 else 0.0
                
                row = {"SYMBOL": t.replace(".NS",""), "CHART": chart_icon, "LTP": ltp, "%CHANGE": chg/100, "X FACTOR": f"{xf}x", "SIGNAL": sig, "TIME": trade_time}
                if chg >= 0: gainers.append(row)
                else: losers.append(row)
            except: continue

    st.markdown(f'<div class="header-card h-green"><span class="h-title">MARKET WISE GAINERS</span><span class="live-badge">LIVE</span></div>', unsafe_allow_html=True)
    if gainers:
        df_g = pd.DataFrame(gainers).sort_values(by="%CHANGE", ascending=False).head(10)
        st.dataframe(df_g.style.map(color_signals, subset=['SIGNAL', 'X FACTOR', 'CHART', 'SYMBOL']), use_container_width=True, hide_index=True, 
                     column_config={
                         "SYMBOL": st.column_config.TextColumn("Symbol", width="medium"),
                         "CHART": st.column_config.TextColumn("Trend", width="small"),
                         "LTP": st.column_config.NumberColumn("LTP", format="₹ %.2f"), 
                         "%CHANGE": st.column_config.NumberColumn("% Change", format="%.2f %%"),
                         "TIME": st.column_config.TextColumn("Trade Time", width="small") # New Real Time Column
                     })

    st.markdown(f'<div class="header-card h-red"><span class="h-title">MARKET WISE LOSERS</span><span class="live-badge">LIVE</span></div>', unsafe_allow_html=True)
    if losers:
        df_l = pd.DataFrame(losers).sort_values(by="%CHANGE", ascending=True).head(10)
        st.dataframe(df_l.style.map(color_signals, subset=['SIGNAL', 'X FACTOR', 'CHART', 'SYMBOL']), use_container_width=True, hide_index=True, 
                     column_config={
                         "SYMBOL": st.column_config.TextColumn("Symbol", width="medium"),
                         "CHART": st.column_config.TextColumn("Trend", width="small"),
                         "LTP": st.column_config.NumberColumn("LTP", format="₹ %.2f"), 
                         "%CHANGE": st.column_config.NumberColumn("% Change", format="%.2f %%"),
                         "TIME": st.column_config.TextColumn("Trade Time", width="small")
                     })

elif view == "Option Clock":
    st.markdown(f'<div class="header-card h-green"><span class="h-title">OPTION CHAIN CLOCK</span></div>', unsafe_allow_html=True)
    col_table, col_cards = st.columns([3, 1])
    with col_cards:
        fig = go.Figure(go.Indicator(mode = "gauge+number", value = 0.66, title = {'text': "PCR Sentiment"}, gauge = {'axis': {'range': [0, 2]}, 'bar': {'color': "#ef4444"}, 'steps': [{'range': [0, 1], 'color': '#fee2e2'}, {'range': [1, 2], 'color': '#dcfce7'}]}))
        fig.update_layout(height=220, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("""<div class="oi-card oi-red"><div class="oi-lbl">Call OI (Resist)</div><div class="oi-big">34.5 Cr</div><div>@ 25,000</div></div><div class="oi-card oi-green"><div class="oi-lbl">Put OI (Support)</div><div class="oi-big">21.2 Cr</div><div>@ 24,800</div></div>""", unsafe_allow_html=True)
    with col_table:
        oi_data = [
            {"🟢 PUT OI": 10, "STRIKE": 24800, "🔴 CALL OI": 90, "TREND": "Resistance"},
            {"🟢 PUT OI": 20, "STRIKE": 24850, "🔴 CALL OI": 80, "TREND": "Resistance"},
            {"🟢 PUT OI": 30, "STRIKE": 24900, "🔴 CALL OI": 60, "TREND": "Weak"},
            {"🟢 PUT OI": 50, "STRIKE": 24950, "🔴 CALL OI": 50, "TREND": "Fight"},
            {"🟢 PUT OI": 70, "STRIKE": 25000, "🔴 CALL OI": 20, "TREND": "Support"},
            {"🟢 PUT OI": 90, "STRIKE": 25050, "🔴 CALL OI": 10, "TREND": "Strong Support"},
        ]
        st.dataframe(pd.DataFrame(oi_data).style.map(color_signals, subset=['TREND']), use_container_width=True, hide_index=True, height=600,
            column_config={"🟢 PUT OI": st.column_config.ProgressColumn("🟢 Put OI (Support)", format="%d L", min_value=0, max_value=150),
                           "STRIKE": st.column_config.TextColumn("Strike", width="small"),
                           "🔴 CALL OI": st.column_config.ProgressColumn("🔴 Call OI (Resist)", format="%d L", min_value=0, max_value=150)})

elif view == "Trade Flow":
    st.markdown(f'<div class="header-card h-green"><span class="h-title">MARKET ROCKERS</span></div>', unsafe_allow_html=True)
    st.info("High Volume Movers...")
    st.markdown(f'<div class="header-card h-red"><span class="h-title">MARKET SHOCKERS</span></div>', unsafe_allow_html=True)
    st.info("High Volume Losers...")

elif view == "Stock-On":
    st.markdown(f'<div class="header-card h-blue"><span class="h-title">STOCK-ON 52W</span></div>', unsafe_allow_html=True)
    st.info("Breakouts...")

elif view == "Swing Spectrum":
    st.markdown(f'<div class="header-card h-blue"><span class="h-title">SWING SETUPS</span></div>', unsafe_allow_html=True)
    st.info("Momentum Analysis...")

elif view == "TradeX":
    st.markdown(f'<div class="header-card h-blue"><span class="h-title">TRADEX SIGNALS</span></div>', unsafe_allow_html=True)
    st.info("Generating Signals...")

elif view == "Trade Brahmand":
    st.markdown(f'<div class="header-card h-green"><span class="h-title">SECTOR HEATMAP</span></div>', unsafe_allow_html=True)
    sectors = [{"Name": "NIFTY BANK", "Val": "+0.45%"}, {"Name": "NIFTY IT", "Val": "+1.20%"}, {"Name": "NIFTY METAL", "Val": "-0.80%"}]
    cols = st.columns(3)
    for i, sec in enumerate(sectors):
        col = cols[i % 3]
        color_class = "m-delta-g" if "+" in sec['Val'] else "m-delta-r"
        with col:
            st.markdown(f"""<div class="sector-card"><div class="sec-name">{sec['Name']}</div><div style="color:{'#10b981' if '+' in sec['Val'] else '#ef4444'};font-weight:800;font-size:15px;">{sec['Val']}</div></div>""", unsafe_allow_html=True)

elif view == "Index Mover":
    st.markdown(f'<div class="header-card h-green"><span class="h-title">INDEX MOVERS</span></div>', unsafe_allow_html=True)
    st.info("Pullers vs Draggers...")

if auto_ref:
    tlib.sleep(refresh_rate)
    st.rerun()