import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import random
import requests

# ===================== 1. PAGE CONFIG =====================
st.set_page_config(page_title="Dkc Interday Ai Stock", layout="wide", initial_sidebar_state="expanded")

if 'search_val' not in st.session_state: st.session_state.search_val = ""

# ===================== 2. TIMING ENGINE (INDIAN MARKET) =====================
ist = pytz.timezone('Asia/Kolkata')
now = datetime.now(ist)
current_time = now.time()
is_weekday = now.weekday() < 5 

is_pre_market = is_weekday and (datetime.strptime("09:00", "%H:%M").time() <= current_time < datetime.strptime("09:15", "%H:%M").time())
is_live_market = is_weekday and (datetime.strptime("09:15", "%H:%M").time() <= current_time <= datetime.strptime("15:30", "%H:%M").time())
is_mcx_live = is_weekday and (datetime.strptime("09:00", "%H:%M").time() <= current_time <= datetime.strptime("23:55", "%H:%M").time())

if is_live_market: display_time = now.strftime("%H:%M:%S")
else: display_time = "15:30:00"

# ===================== 3. CSS & SVG (YOUR MASTERPIECE) =====================
CHART_SVG = """<svg width="24" height="24" viewBox="0 0 24 24" fill="none"><rect x="4" y="12" width="3" height="8" rx="1" fill="#4169E1" opacity="0.8"/><rect x="10" y="8" width="3" height="12" rx="1" fill="#2ed573" opacity="0.8"/><rect x="16" y="14" width="3" height="6" rx="1" fill="#ffa502" opacity="0.8"/><path d="M3 13 L9 7 L15 11 L21 4" stroke="#8e8e93" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>"""

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, .stApp {background-color: #f8f9fa; font-family: 'Inter', sans-serif;}
    header {visibility: hidden;} #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    
    /* 🔴 BLINKING ANIMATION 🔴 */
    @keyframes pulse-blink {
        0% { opacity: 1; }
        50% { opacity: 0.3; }
        100% { opacity: 1; }
    }
    
    /* 📱 NEW iOS STYLE SIDEBAR - LOCKED */
    [data-testid="stSidebar"] {
        background: #ffffff !important; 
        border-right: 1px solid #e2e8f0 !important;
        width: 280px !important;
    }
    .sidebar-logo-box {display: flex; align-items: center; gap: 12px; padding: 25px 15px 15px 20px;}
    .logo-icon {background: #4169E1; color: white; width: 35px; height: 35px; border-radius: 8px; display: flex; justify-content: center; align-items: center; font-size: 18px; font-weight: 800;}
    
    .market-status-box {padding: 0 20px; margin-bottom: 20px;}
    .status-pill {border-radius: 20px; padding: 5px 12px; font-size: 10px; font-weight: 700; display: inline-flex; align-items: center; gap: 6px;}
    .status-closed {background: #fff; color: #ff3b30; border: 1px solid #ffcccc;}
    .status-live {background: #fff; color: #00b050; border: 1px solid #cce8d5;}
    .status-pre {background: #fff; color: #f39c12; border: 1px solid #f9e79f;}
    .dot {width: 6px; height: 6px; border-radius: 50%;}
    .dot-closed {background: #ff3b30;}
    
    /* Blinking Live Dot */
    .dot-live {background: #00b050; box-shadow: 0 0 6px #00b050; animation: pulse-blink 1.5s infinite;}
    .dot-pre {background: #f39c12; box-shadow: 0 0 4px #f39c12;}

    /* general radio label (more modern shape) */
    div[role="radiogroup"] label {padding: 10px 15px !important; margin: 3px 10px !important; border-radius: 8px !important; transition: 0.2s cubic-bezier(0.4, 0, 0.2, 1);}
    
    /* 🔴 COLORFUL ACTIVE LINK IN SIDEBAR (GRADIENT) 🔴 */
    div[role="radiogroup"] label[data-checked="true"] {
        background: linear-gradient(135deg, #6c5ce7 0%, #4169E1 100%) !important;
        box-shadow: 0 4px 10px rgba(108, 92, 231, 0.2);
    }
    
    /* TEXT STYLING FOR ACTIVE LINK (WHITE) */
    div[role="radiogroup"] label p { font-size: 13.5px !important; font-weight: 600 !important; color: #4b5563 !important;}
    div[role="radiogroup"] label[data-checked="true"] p {color: #ffffff !important; font-weight: 700 !important;}

    /* HIDE DEFAULT RADIO BUBBLE for a clean look */
    div[role="radiogroup"] label span[data-baseweb="radio"] { display: none !important; }

    /* MASTER SEARCH BOX LOCK */
    [data-testid="stTextInput"] div[data-baseweb="input"] {border-radius: 24px !important; border: 1px solid #e0e0e5 !important; background: #ffffff !important; padding: 6px 18px; box-shadow: 0 2px 10px rgba(0,0,0,0.02); font-size: 14px;}
    
    [data-testid="stSelectbox"] div[data-baseweb="select"] {border-radius: 20px !important; border: 1px solid #e0e0e5 !important; background: #ffffff !important; box-shadow: 0 2px 8px rgba(0,0,0,0.02); font-size: 14px; font-weight: 600;}
    
    .stButton>button {background: #f8f9fa; color: #4b5563; border-radius: 12px; font-weight: 600; width: 100%; height: 42px; border: 1px solid #e0e0e5; font-size: 14px; transition: 0.2s;}

    /* TABLES & AVATARS */
    .table-container {background: white; border-radius:12px; margin-bottom: 30px; padding:15px; border:1px solid #eef0f5; box-shadow: 0 2px 10px rgba(0,0,0,0.01);}
    .table-header-title {font-size: 15px; font-weight: 800; text-transform: uppercase; color: #1c1c1e; display: flex; align-items: center; gap: 8px; margin-bottom: 8px;}
    
    /* Blinking LIVE Badge */
    .live-badge {background: #ff3b30; color: white; font-size: 9px; padding: 3px 6px; border-radius: 4px; font-weight: 800; animation: pulse-blink 2s infinite;}
    
    .thick-line-green {height: 3px; background: #00b050; width: 100%; border-radius: 2px;}
    .thick-line-red {height: 3px; background: #ff3b30; width: 100%; border-radius: 2px;}
    .stats-text {font-size: 11px; font-weight: 600; margin-top: 10px; margin-bottom: 15px;}
    
    .custom-table {width: 100%; border-collapse: collapse;}
    .custom-table th {font-size: 10px; color: #8e8e93; font-weight: 600; padding: 10px 15px; border-bottom: 1px solid #eef0f5; text-align: center; text-transform: uppercase;}
    .custom-table th:first-child {text-align: left;}
    .custom-table td {padding: 12px 15px; font-size: 13px; font-weight: 700; color: #1c1c1e; text-align: center; border-bottom: 1px solid #f8f9fa;}
    .custom-table td:first-child {text-align: left;}
    .custom-table tr:hover {background-color: #fafbfc;}
    .sort-icon {font-size: 11px; color: #d1d1d6; margin-left: 4px;}
    
    .avatar {width: 32px; height: 32px; border-radius: 6px; color: white; display: flex; justify-content: center; align-items: center; font-size: 11px; font-weight: 800;}
    .pill-up {color: #00b050; background: #e6f7ec; padding: 5px 12px; border-radius: 4px; font-size: 12px; font-weight: 700;}
    .pill-down {color: #ff3b30; background: #ffebeb; padding: 5px 12px; border-radius: 4px; font-size: 12px; font-weight: 700;}
    .trend-icon-up {color: #00b050; font-size: 18px; font-weight: 900;}
    .trend-icon-down {color: #ff3b30; font-size: 18px; font-weight: 900;}

    /* VISUALS */
    .css-donut {
        width: 300px; height: 300px; border-radius: 50%;
        background: conic-gradient(#ff3b30 0deg 60deg, transparent 60deg 62deg, #ff3b30 62deg 130deg, transparent 130deg 132deg, #00b050 132deg 190deg, transparent 190deg 192deg, #ff3b30 192deg 260deg, transparent 260deg 262deg, #ff3b30 262deg 320deg, transparent 320deg 322deg, #00b050 322deg 360deg);
        display: flex; justify-content: center; align-items: center; position: relative; margin: 0 auto;
    }
    .css-donut-hole {width: 170px; height: 170px; background: white; border-radius: 50%;}
    </style>
""", unsafe_allow_html=True)

# ===================== 4. SIDEBAR (STATIC, DOES NOT REFRESH) =====================
with st.sidebar:
    st.markdown("""<div class="sidebar-logo-box"><div class="logo-icon">📈</div><div><div style="font-weight:800; font-size:18px; color:#1c1c1e;">Dkc Interday Ai Stock</div><div style="font-size:11px; color:#8e8e93; font-weight:500;">Trading Dashboard</div></div></div>""", unsafe_allow_html=True)
    
    if is_pre_market: st.markdown('<div class="market-status-box"><div class="status-pill status-pre"><div class="dot dot-pre"></div> PRE-OPEN MARKET</div></div>', unsafe_allow_html=True)
    elif is_live_market: st.markdown('<div class="market-status-box"><div class="status-pill status-live"><div class="dot dot-live"></div> MARKET LIVE</div></div>', unsafe_allow_html=True)
    else: st.markdown('<div class="market-status-box"><div class="status-pill status-closed"><div class="dot dot-closed"></div> MARKET CLOSED</div></div>', unsafe_allow_html=True)
    
    if st.button("🔄 Manual Refresh", use_container_width=True): st.cache_data.clear(); st.rerun()
    st.write("---")
    auto_ref = st.toggle("⚡ Auto Update", value=True)
    ref_sec = st.slider("Refresh Rate (seconds)", min_value=5, max_value=120, value=15, step=5)
    st.write("---")
    MENU = st.radio("Navigation", ["🔊 Market Wise", "📈 Trade Flow", "📊 Stock-On", "📉 Swing Spectrum", "⚡ TradeX", "🌌 Trade Brahmand", "🕒 Option Clock", "🎯 Index Mover", "🛢️ MCX Live"])

# ===================== 5. TOP BAR (OUTSIDE FRAGMENT = NO FLICKER) =====================
c1, c2, c3 = st.columns([5, 2, 2])
selected_index = "NIFTY 50" # Default

with c2: 
    if MENU != "🛢️ MCX Live":
        selected_index = st.selectbox("Select Index", ["NIFTY 50", "NIFTY BANK", "FINNIFTY", "SENSEX"], label_visibility="collapsed")
        
with c3: 
    search_val = st.text_input("Search", value="", placeholder="🔍 Search Stock...", label_visibility="collapsed")


# ===================== 6. API ENGINE (SUPER FAST CACHING) =====================
TOKEN = "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiI1OUNGQUgiLCJqdGkiOiI2OWFkNGY4YmYyM2VhZTMyM2YwMmJiZjciLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaWF0IjoxNzcyOTY1NzcxLCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE3NzMwMDcyMDB9.p9-JnYbPa3jl5wyvSkVjv6QyV6Kbz1SnHLQWe3TzyL8"
HEADERS = {'Accept': 'application/json', 'Authorization': f'Bearer {TOKEN}'}

# Reduced TTL to 2 seconds for instant menu clicks
@st.cache_data(ttl=2)
def fetch_api_data():
    try:
        instruments = "NSE_INDEX|Nifty 50,NSE_INDEX|Nifty Bank,NSE_INDEX|Nifty Fin Service,BSE_INDEX|SENSEX,NSE_EQ|INE002A01018,NSE_EQ|INE467B01029,NSE_EQ|INE040A01034"
        url = f"https://api.upstox.com/v2/market-quote/quotes?instrument_key={instruments}"
        res = requests.get(url, headers=HEADERS, timeout=3).json()
        return res.get('data', {})
    except: return {}

# ===================== 7. 🌟 THE MAGIC FRAGMENT (ZERO FLICKER) 🌟 =====================
# This completely replaces st_autorefresh! It only refreshes this specific block.
refresh_time = f"{ref_sec}s" if auto_ref else None

@st.fragment(run_every=refresh_time)
def render_live_dashboard(menu_choice, index_choice, search_query):
    
    api_data = fetch_api_data()
    
    # Process Indices
    index_prices = {
        "NIFTY 50": {"ltp": 24825.45, "chg": -495.20, "pct": "-1.96%"},
        "NIFTY BANK": {"ltp": 51230.15, "chg": +120.40, "pct": "+0.24%"},
        "FINNIFTY": {"ltp": 22840.50, "chg": -85.10, "pct": "-0.37%"},
        "SENSEX": {"ltp": 80430.20, "chg": -1200.50, "pct": "-1.45%"}
    }
    for name, key in [("NIFTY 50", "NSE_INDEX|Nifty 50"), ("NIFTY BANK", "NSE_INDEX|Nifty Bank"), ("FINNIFTY", "NSE_INDEX|Nifty Fin Service"), ("SENSEX", "BSE_INDEX|SENSEX")]:
        if key in api_data:
            ltp = api_data[key]['last_price']
            close = api_data[key].get('close', ltp)
            chg = ltp - close
            pct = (chg/close)*100 if close else 0
            index_prices[name] = {"ltp": ltp, "chg": round(chg,2), "pct": f"{'+' if pct>0 else ''}{pct:.2f}%"}

    current_ltp = index_prices[index_choice]["ltp"]
    current_chg = index_prices[index_choice]["chg"]
    current_pct = index_prices[index_choice]["pct"]
    chg_color = "#ff3b30" if current_chg < 0 else "#00b050"

    # Process Equities
    stock_map = {"NSE_EQ|INE002A01018": "RELIANCE", "NSE_EQ|INE467B01029": "TCS", "NSE_EQ|INE040A01034": "HDFCBANK"}
    colors = ["#4169E1", "#8cc63f", "#d946ef", "#22c55e", "#a855f7"]
    live_stocks = []
    for k, sym in stock_map.items():
        d = api_data.get(k, {})
        if d:
            ltp = d.get('last_price', 0)
            close = d.get('close', ltp)
            pct = ((ltp-close)/close)*100 if close else 0
            live_stocks.append({"SYM": sym, "LTP": ltp, "CHG": pct, "EXTRA": f"{random.uniform(1.0, 5.0):.2f}x", "COLOR": random.choice(colors)})
    
    # Fallback mock data if API is empty right now
    if not live_stocks:
        live_stocks = [
            {"SYM":"RELIANCE", "LTP":2540.50, "CHG":1.20, "EXTRA":"3.2x", "COLOR":"#4169E1"},
            {"SYM":"TCS", "LTP":4120.10, "CHG":-0.85, "EXTRA":"1.8x", "COLOR":"#ff3b30"},
            {"SYM":"HDFCBANK", "LTP":1685.00, "CHG":2.35, "EXTRA":"4.5x", "COLOR":"#8cc63f"}
        ]

    live_stocks.sort(key=lambda x: x["CHG"], reverse=True)
    gainer_data = [s for s in live_stocks if s["CHG"] > 0]
    loser_data = [s for s in live_stocks if s["CHG"] <= 0]

    # --- RENDER LOGIC ---
    def render_double_tables(title1, title2, data1, data2, col_name="X FACTOR"):
        def build_table(title, data, theme):
            line = "thick-line-green" if theme == "up" else "thick-line-red"
            up_count = sum(1 for d in data if d["CHG"] > 0)
            dn_count = len(data) - up_count
            total = len(data) if len(data)>0 else 1
            stats = f"<span style='color:#00b050;'>● {up_count} stocks ({(up_count/total)*100:.2f}% Up)</span> &nbsp;&nbsp; <span style='color:#ff3b30;'>● {dn_count} stocks ({(dn_count/total)*100:.2f}% Down)</span>"
            
            html_blocks = [
                f'<div class="table-container" style="padding:0;"><div style="padding:15px;"><div class="table-header-title">{title} <span class="live-badge">LIVE</span></div><div class="{line}"></div><div class="stats-text">{stats}</div></div>',
                '<table class="custom-table"><thead><tr><th>SYMBOL <span class="sort-icon">⇅</span></th><th>LTP <span class="sort-icon">⇅</span></th><th>%CHANGE <span class="sort-icon">⇅</span></th>',
                f'<th>{col_name} <span class="sort-icon">⇅</span></th><th>SIGNAL <span class="sort-icon">⇅</span></th><th>TIME <span class="sort-icon">⇅</span></th></tr></thead><tbody>'
            ]
            for r in data:
                if search_query and search_query.upper() not in r["SYM"]: continue
                pill = f"pill-up" if r["CHG"] > 0 else f"pill-down"
                arrow = "▲" if r["CHG"] > 0 else "▼"
                trend = f"<span class='trend-icon-up'>↗</span>" if r["CHG"] > 0 else f"<span class='trend-icon-down'>↘</span>"
                html_blocks.append(f'<tr><td style="width:300px;"><div style="display:flex; align-items:center; justify-content:space-between; padding-right:20px;"><div style="display:flex; align-items:center; gap:15px;"><div class="avatar" style="background:{r["COLOR"]};">{r["SYM"][:2]}</div><div style="line-height:1.2;"><div style="font-weight:700; color:#1c1c1e; font-size:14px;">{r["SYM"]}</div><div style="font-size:11px; color:#8e8e93; font-weight:500; margin-top:2px;">{r["SYM"]}</div></div></div><div>{CHART_SVG}</div></div></td><td style="width:120px;">₹{r["LTP"]:,.2f}</td><td style="width:140px;"><span class="{pill}">{arrow} {abs(r["CHG"]):.2f}%</span></td><td style="width:120px; color:#8e8e93; font-weight:500;">{r["EXTRA"]}</td><td style="width:100px;">{trend}</td><td style="width:120px; color:#8e8e93; font-size:12px; font-weight:500;">{display_time}</td></tr>')
            html_blocks.append('</tbody></table></div>')
            st.markdown("".join(html_blocks), unsafe_allow_html=True)
        build_table(title1, data1, "up")
        build_table(title2, data2, "down")

    # --- MENU ROUTING INSIDE FRAGMENT ---
    if menu_choice in ["🔊 Market Wise", "📈 Trade Flow", "📊 Stock-On", "📉 Swing Spectrum"]:
        t1 = "MARKET WISE GAINERS" if menu_choice == "🔊 Market Wise" else ("MARKET ROCKERS" if menu_choice == "📈 Trade Flow" else ("STOCK-ON 52 WEEK HIGH" if menu_choice == "📊 Stock-On" else "10 DAY BO"))
        t2 = "MARKET WISE LOSERS" if menu_choice == "🔊 Market Wise" else ("MARKET SHOCKERS" if menu_choice == "📈 Trade Flow" else ("STOCK-ON 52 WEEK LOW" if menu_choice == "📊 Stock-On" else "50 DAY BO"))
        render_double_tables(t1, t2, gainer_data, loser_data, "X FACTOR" if menu_choice in ["🔊 Market Wise", "📈 Trade Flow"] else "DISTANCE")

    elif menu_choice == "⚡ TradeX":
        base_spot = int(current_ltp/50)*50
        pivots = [base_spot + (i*50) for i in range(-2, 3)]
        
        st.markdown(f"<div style='font-size:18px; font-weight:800; color:#1c1c1e; margin-bottom:20px; display:flex; justify-content:space-between;'><div>TRADEX Advanced Technical <span style='color:#8e8e93; margin-left:10px; font-size:14px;'>{index_choice}</span></div><div style='background:#f0f4ff; padding:6px 15px; border-radius:20px; border:1px solid #d0d7ff;'><span style='color:#4169E1; font-size:12px; font-weight:800;'>SPOT: ₹{current_ltp:,.2f}</span></div></div>", unsafe_allow_html=True)
        html_tx = '<div class="table-container" style="padding:0;"><div style="padding:15px; display:flex; align-items:center; gap:10px; border-bottom: 1px solid #eef0f5;"><div class="table-header-title" style="margin:0; font-size:16px;">CRITICAL MOMENTUM LEVELS</div><span class="live-badge">LIVE</span></div><table class="custom-table" style="margin-top:0;"><thead><tr><th>SPOT <span class="sort-icon">⇅</span></th><th>SIGNAL <span class="sort-icon">⇅</span></th><th>MOMENTUM LEVELS <span class="sort-icon">⇅</span></th><th>AI MESSAGE (DIRECTION)</th><th>PRIORITY <span class="sort-icon">⇅</span></th></tr></thead><tbody>'
        for level in pivots:
            if level > current_ltp: direction, color = f"<span class='trend-icon-up'>↗</span> Bullish Above", "#00b050"
            elif level < current_ltp: direction, color = f"<span class='trend-icon-down'>↘</span> Bearish Below", "#ff3b30"
            else: direction, color = f"<b>NEUTRAL</b> Near", "#f39c12"
            priority = '<span style="background:#fff4e6; color:#e67e22; border:1px solid #ffe8cc; padding:4px 10px; border-radius:20px; font-size:10px; font-weight:800;">⚠ High</span>' if abs(current_ltp - level) < 15 else '<span style="background:#eef2ff; color:#4169E1; border:1px solid #d0d7ff; padding:4px 10px; border-radius:20px; font-size:10px; font-weight:800;">ⓘ Medium</span>'
            html_tx += f'<tr><td style="font-weight:800; color:#1c1c1e;">{current_ltp:,.2f}</td><td><span style="background:#f0f0f5; color:#555; padding:5px 12px; border-radius:6px; font-size:11px; font-weight:800;">PIVOT</span></td><td style="font-size:15px; font-weight:800; color:#1c1c1e;">₹{level}</td><td style="text-align:left; color:{color}; font-weight:600; text-transform:uppercase;">{direction} {level}</td><td>{priority}</td></tr>'
        st.markdown(html_tx + "</tbody></table></div>", unsafe_allow_html=True)

    elif menu_choice == "🎯 Index Mover":
        st.markdown("<div style='font-size:20px; font-weight:800; margin-bottom:20px; color:#1c1c1e;'>Index Mover</div>", unsafe_allow_html=True)
        dynamic_stocks = [("HDFCBANK", "-124.50", "#4169E1"), ("SBIN", "-48.34", "#e1b12c"), ("ICICIBANK", "+32.35", "#00b050")]
        html_index = f"""<div style="display:flex; gap:40px; flex-wrap: wrap;">
            <div style="flex:1; min-width:350px; background:white; padding:40px; border-radius:20px; border:1px solid #eef0f5; display:flex; justify-content:center; align-items:center; position:relative; box-shadow:0 2px 10px rgba(0,0,0,0.01);">
                <div style="position:absolute; top:30px; left:30px; background:linear-gradient(135deg, #6c5ce7, #4169E1); color:white; padding:20px 25px; border-radius:15px; box-shadow:0 8px 20px rgba(108,92,231,0.3); z-index:10;"><div style="font-size:14px; font-weight:800; opacity:0.9;">{index_choice}</div><div style="font-size:24px; font-weight:800; margin-top:10px;">{current_ltp:,.2f}</div><div style="color:{chg_color}; font-size:14px; font-weight:700; margin-top:4px;">{current_chg} ({current_pct})</div></div>
                <div class="css-donut"><div class="css-donut-hole"></div></div>
            </div>
            <div style="flex:1; min-width:350px;">
                <div style="font-weight:700; font-size:14px; margin-bottom:10px; color:#1c1c1e;">Market Breadth</div>
                <div style="height:10px; background:#f0f0f5; border-radius:5px; display:flex; overflow:hidden;"><div style="width:30%; background:#00b050;"></div><div style="width:70%; background:#ff3b30;"></div></div>
                <div style="display:flex; justify-content:space-between; margin-top:8px; font-size:12px; font-weight:700; margin-bottom:30px;"><span style='color:#00b050;'>15 Gainers</span><span style='color:#ff3b30;'>35 Losers</span></div>
                <div style="font-weight:800; margin-bottom:15px; font-size:16px; color:#1c1c1e;">Top Contributors</div>"""
        for sym, chg, col in dynamic_stocks:
            bor_col = "#00b050" if "+" in chg else "#ff3b30"
            html_index += f'<div style="background:white; padding:18px 20px; border-radius:12px; border-left:4px solid {bor_col}; margin-bottom:12px; display:flex; justify-content:space-between; align-items:center; box-shadow:0 2px 8px rgba(0,0,0,0.02); border:1px solid #eef0f5;"><div style="display:flex; align-items:center; gap:15px;"><div class="avatar" style="background:{col};">{sym[:2]}</div><div style="line-height:1.2;"><b style="color:#1c1c1e; font-size:14px;">{sym}</b></div></div><b style="color:{bor_col}; font-size:15px;">{chg}</b></div>'
        st.markdown(html_index + "</div></div>", unsafe_allow_html=True)

    elif menu_choice == "🕒 Option Clock":
        st.markdown(f"<div style='font-size:18px; font-weight:800; color:#1c1c1e; margin-bottom:20px; display:flex; align-items:center; justify-content:space-between;'><div>Option Chain Clock <span style='color:#8e8e93; margin-left:10px; font-size:14px;'>{index_choice}</span></div> <div style='background:#eef2ff; padding:6px 15px; border-radius:20px; border:1px solid #d0d7ff;'><span style='color:#4169E1; font-size:12px; font-weight:800;'>SPOT: ₹{current_ltp:,.2f}</span></div></div>", unsafe_allow_html=True)
        col_chain, col_stats = st.columns([2.5, 1])
        with col_chain:
            base_step = 100 if index_choice in ["NIFTY BANK", "SENSEX"] else 50
            atm_strike = int(round(current_ltp / base_step) * base_step)
            strikes = [atm_strike + (i * base_step) for i in range(-5, 6)]
            opt_html = ['<div style="background: white; border-radius: 12px; padding: 20px; border: 1px solid #eef0f5; box-shadow: 0 2px 10px rgba(0,0,0,0.01);"><div style="display:flex; gap:25px; margin-bottom: 20px; font-size: 11px; font-weight: 700; color: #8e8e93; text-transform:uppercase;"><div style="display:flex; align-items:center; gap:6px;"><div style="width:16px; height:8px; border-radius:4px; background:#ff3b30;"></div> Put OI</div><div style="display:flex; align-items:center; gap:6px;"><div style="width:16px; height:8px; border-radius:4px; background:#00b050;"></div> Call OI</div></div>']
            for strike in strikes:
                put_oi, call_oi = round(random.uniform(1.0, 99.9), 1), round(random.uniform(1.0, 99.9), 1)
                pcr = round(put_oi / call_oi if call_oi > 0 else 0, 2)
                bg_box = "#fff9c4" if strike == atm_strike else "#ffffff"
                border_box = "1px solid #fadd85" if strike == atm_strike else "1px solid #eef0f5"
                opt_html.append(f'<div style="display: flex; align-items: center; justify-content: center; padding: 6px 0; border-bottom: 1px solid #f8f9fa;"><div style="width: 50px; text-align: left; font-size: 12px; font-weight: 700; color: #1c1c1e;">{put_oi}L</div><div style="width: 140px; display: flex; justify-content: flex-end; padding-right: 15px;"><div style="height: 16px; width: {min(put_oi, 100)}%; background-color: #ff3b30; border-radius: 4px;"></div></div><div style="width: 90px; text-align: center; background: {bg_box}; padding: 6px; border-radius: 8px; border: {border_box}; box-shadow: 0 1px 3px rgba(0,0,0,0.05);"><div style="font-weight: 800; font-size: 14px; color: #1c1c1e;">{strike}</div><div style="font-size: 9px; color: #8e8e93; font-weight: 600; margin-top:2px;">PCR: {pcr}</div></div><div style="width: 140px; display: flex; justify-content: flex-start; padding-left: 15px;"><div style="height: 16px; width: {min(call_oi, 100)}%; background-color: #00b050; border-radius: 4px;"></div></div><div style="width: 50px; text-align: right; font-size: 12px; font-weight: 700; color: #1c1c1e;">{call_oi}L</div></div>')
            opt_html.append('</div>')
            st.markdown("".join(opt_html), unsafe_allow_html=True)
        with col_stats:
            st.markdown(f'<div style="background: white; border-radius: 12px; padding: 20px; border: 1px solid #eef0f5; box-shadow: 0 2px 10px rgba(0,0,0,0.01); text-align:center;"><div style="font-weight: 800; font-size: 14px; color: #1c1c1e; margin-bottom: 15px; display:flex; justify-content:center; gap:8px; align-items:center;">Market Distribution <span style="background:#ffebeb; color:#ff3b30; padding:2px 8px; border-radius:4px; font-size:10px;">BEARISH</span></div><div style="width: 130px; height: 130px; border-radius: 50%; background: conic-gradient(#00b050 0% 34%, #ff3b30 34% 100%); margin: 0 auto; display: flex; justify-content: center; align-items: center;"><div style="width: 100px; height: 100px; background: white; border-radius: 50%; display: flex; justify-content: center; align-items: center; flex-direction: column; box-shadow: inset 0 2px 5px rgba(0,0,0,0.05);"><div style="font-size: 11px; color: #8e8e93; font-weight: 700;">PCR</div><div style="font-size: 26px; font-weight: 900; color: #ff3b30; margin-top:-2px;">0.66</div></div></div><div style="display:flex; justify-content:space-between; margin-top:20px; padding:0 10px;"><div style="background:#ffebeb; padding:8px 15px; border-radius:8px;"><div style="font-size:10px; color:#ff3b30; font-weight:800;">BEARS (PE)</div><div style="font-size:14px; font-weight:800; color:#1c1c1e;">35.75%</div></div><div style="background:#e6f7ec; padding:8px 15px; border-radius:8px;"><div style="font-size:10px; color:#00b050; font-weight:800;">BULLS (CE)</div><div style="font-size:14px; font-weight:800; color:#1c1c1e;">64.25%</div></div></div></div>', unsafe_allow_html=True)

    elif menu_choice == "🌌 Trade Brahmand":
        st.markdown('<div class="table-header-title">SECTOR HEATMAP <span class="live-badge">LIVE</span></div>', unsafe_allow_html=True)
        heatmap_html = '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 12px; margin-bottom: 30px;">'
        sectors = [("NIFTY ENERGY", "+0.13%", "#2ed573"), ("NIFTY IT", "+0.04%", "#2ed573"), ("NIFTY MNC", "-0.03%", "#f1948a"), ("NIFTY FMCG", "-0.06%", "#f1948a"), ("NIFTY REALTY", "-2.08%", "#c0392b"), ("NIFTY BANK", "-2.15%", "#922b21")]
        for name, val, color in sectors: heatmap_html += f'<div style="background:{color}; padding: 15px; border-radius: 8px; color: white; display: flex; flex-direction: column; justify-content: space-between; height: 80px;"><div style="font-size: 11px; font-weight: 700; text-transform: uppercase;">{name}</div><div style="font-size: 18px; font-weight: 800;">{val}</div></div>'
        st.markdown(heatmap_html + '</div>', unsafe_allow_html=True)

    elif menu_choice == "🛢️ MCX Live":
        st.markdown("<div style='font-size:20px; font-weight:800; margin-bottom:20px; color:#1c1c1e;'>MCX Live Dashboard</div>", unsafe_allow_html=True)
        mcx_data = [
            {"SYM":"CRUDE OIL", "LTP":6420.00 + random.uniform(-10, 10), "CHG":random.uniform(-1.5, 1.5), "EXTRA":"High", "COLOR":"#1c1c1e"},
            {"SYM":"CRUDE OIL MINI", "LTP":642.00 + random.uniform(-1, 1), "CHG":random.uniform(-1.5, 1.5), "EXTRA":"High", "COLOR":"#34495e"},
            {"SYM":"NATURAL GAS", "LTP":215.40 + random.uniform(-2, 2), "CHG":random.uniform(-2.5, 2.5), "EXTRA":"Medium", "COLOR":"#e1b12c"},
            {"SYM":"NATURAL GAS MINI", "LTP":21.54 + random.uniform(-0.5, 0.5), "CHG":random.uniform(-2.5, 2.5), "EXTRA":"Medium", "COLOR":"#f39c12"},
            {"SYM":"SILVER", "LTP":84320.00 + random.uniform(-50, 50), "CHG":random.uniform(-0.8, 0.8), "EXTRA":"High", "COLOR":"#7f8c8d"},
            {"SYM":"GOLD", "LTP":72450.00 + random.uniform(-40, 40), "CHG":random.uniform(-0.5, 0.5), "EXTRA":"Low", "COLOR":"#f1c40f"}
        ]
        html_mcx = '<div class="table-container" style="padding:0;"><div style="padding:15px;"><div class="table-header-title">COMMODITIES <span class="live-badge">LIVE</span></div><div class="thick-line-green"></div></div><table class="custom-table"><thead><tr><th>COMMODITY <span class="sort-icon">⇅</span></th><th>LTP <span class="sort-icon">⇅</span></th><th>%CHANGE <span class="sort-icon">⇅</span></th><th>VOLATILITY <span class="sort-icon">⇅</span></th><th>TREND <span class="sort-icon">⇅</span></th><th>TIME <span class="sort-icon">⇅</span></th></tr></thead><tbody>'
        for r in mcx_data:
            if search_query and search_query.upper() not in r["SYM"]: continue
            pill = f"pill-up" if r["CHG"] > 0 else f"pill-down"
            arrow = "▲" if r["CHG"] > 0 else "▼"
            trend = f"<span class='trend-icon-up'>↗</span>" if r["CHG"] > 0 else f"<span class='trend-icon-down'>↘</span>"
            html_mcx += f'<tr><td style="width:300px;"><div style="display:flex; align-items:center; gap:15px;"><div class="avatar" style="background:{r["COLOR"]};">{r["SYM"][:2]}</div><div style="font-weight:700; color:#1c1c1e; font-size:14px;">{r["SYM"]}</div></div></td><td style="width:120px;">₹{r["LTP"]:,.2f}</td><td style="width:140px;"><span class="{pill}">{arrow} {abs(r["CHG"]):.2f}%</span></td><td style="width:120px; color:#8e8e93; font-weight:500;">{r["EXTRA"]}</td><td style="width:100px;">{trend}</td><td style="width:120px; color:#8e8e93; font-size:12px; font-weight:500;">{display_time}</td></tr>'
        html_mcx += '</tbody></table></div>'
        st.markdown(html_mcx, unsafe_allow_html=True)

# CALLING THE MAGIC FRAGMENT
render_live_dashboard(MENU, selected_index, search_val)