import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import plotly.graph_objects as go
import yfinance as yf

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Institutional Equity Research Hub (50+ Coverage)",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    div[data-testid="stMetric"] {
        background-color: #1E293B !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        padding: 15px !important;
    }
    div[data-testid="stMetricValue"] { color: #F8FAFC !important; font-weight: bold; }
    div[data-testid="stMetricLabel"] { color: #94A3B8 !important; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

DB_NAME = "coverage_hub.db"

# -----------------------------------------------------------------------------
# 2. DATABASE UTILITY FUNCTIONS
# -----------------------------------------------------------------------------
def get_db_connection():
    return sqlite3.connect(DB_NAME)

def load_stock_universe():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM stock_universe ORDER BY company_name ASC", conn)
    conn.close()
    return df

def load_latest_concall_data(ticker):
    conn = get_db_connection()
    query = """
        SELECT * FROM concall_logs 
        WHERE ticker_symbol = ? 
        ORDER BY timestamp DESC
    """
    df = pd.read_sql_query(query, conn, params=(ticker,))
    conn.close()
    return df

def seed_initial_universe_if_empty():
    """Seeds default stock universe if DB is brand new."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_universe (
            ticker_symbol TEXT PRIMARY KEY,
            company_name TEXT,
            sector TEXT,
            base_target_price REAL,
            base_wacc REAL,
            base_terminal_g REAL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS concall_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker_symbol TEXT,
            quarter TEXT,
            rev_guidance TEXT,
            margin_guidance TEXT,
            management_tone TEXT,
            analyst_notes TEXT,
            adj_wacc REAL,
            adj_growth REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("SELECT COUNT(*) FROM stock_universe")
    count = cursor.fetchone()[0]
    
    if count == 0:
        default_stocks = [
            ("JYOTICNC.NS", "Jyoti CNC Automation", "Capital Goods", 1680.50, 10.8, 4.5),
            ("AXISBANK.NS", "Axis Bank", "Banking & Financials", 1480.00, 11.5, 5.0),
            ("RELIANCE.NS", "Reliance Industries", "Energy / Retail / Telecom", 3550.00, 9.5, 4.5),
            ("LT.NS", "Larsen & Toubro", "Engineering & EPC", 4250.00, 10.2, 4.5),
            ("TCS.NS", "Tata Consultancy Services", "IT Services", 4500.00, 9.0, 5.0),
            ("INFY.NS", "Infosys", "IT Services", 2100.00, 9.2, 4.8),
            ("HDFCBANK.NS", "HDFC Bank", "Banking & Financials", 2000.00, 10.5, 5.2)
        ]
        cursor.executemany("INSERT INTO stock_universe VALUES (?,?,?,?,?,?)", default_stocks)
        conn.commit()
    conn.close()

seed_initial_universe_if_empty()

# -----------------------------------------------------------------------------
# 3. SIDEBAR NAVIGATION & 50+ STOCK SELECTOR
# -----------------------------------------------------------------------------
st.sidebar.image("https://img.icons8.com/color/96/000000/line-chart.png", width=60)
st.sidebar.title("Buy-Side Research Hub")

df_universe = load_stock_universe()
stock_dict = dict(zip(df_universe['company_name'], df_universe['ticker_symbol']))

selected_company = st.sidebar.selectbox("Select Coverage Stock", list(stock_dict.keys()))
selected_ticker = stock_dict[selected_company]

# Extract current stock base record
stock_info = df_universe[df_universe['ticker_symbol'] == selected_ticker].iloc[0]

view_mode = st.sidebar.radio(
    "Dashboard View",
    ["Overview & Thesis Tracker", "Interactive Concall & Guidance Matrix", "3-Stage DCF Valuation"]
)

# Fetch Live CMP via yfinance
try:
    live_stock = yf.Ticker(selected_ticker)
    cmp = live_stock.info.get("currentPrice") or live_stock.info.get("regularMarketPrice") or 1000.0
    prev_close = live_stock.info.get("previousClose") or cmp
    day_change_pct = ((cmp - prev_close) / prev_close) * 100
except Exception:
    cmp, day_change_pct = 1000.0, 0.0

# -----------------------------------------------------------------------------
# 4. DYNAMIC VALUATION CALCULATION (Driven by Concall Adjustments)
# -----------------------------------------------------------------------------
df_concalls = load_latest_concall_data(selected_ticker)

# If analyst logged custom assumptions in recent concall, override base valuation
if not df_concalls.empty and pd.notnull(df_concalls.iloc[0]['adj_wacc']):
    latest_log = df_concalls.iloc[0]
    active_wacc = latest_log['adj_wacc']
    active_growth = latest_log['adj_growth']
    
    # Dynamic valuation adjustment relative to base parameters
    wacc_diff = (stock_info['base_wacc'] - active_wacc) / 100.0
    g_diff = (active_growth - stock_info['base_terminal_g']) / 100.0
    
    # Adjusted Target Price Formula
    dcf_target = stock_info['base_target_price'] * (1 + (g_diff * 1.5) + (wacc_diff * 2.0))
    valuation_status = f"Adjusted via Concall ({latest_log['quarter']})"
else:
    active_wacc = stock_info['base_wacc']
    active_growth = stock_info['base_terminal_g']
    dcf_target = stock_info['base_target_price']
    valuation_status = "Base Model Value"

upside_pct = ((dcf_target - cmp) / cmp) * 100
recommendation = "BUY" if upside_pct > 15 else ("SELL" if upside_pct < -10 else "HOLD")

# -----------------------------------------------------------------------------
# 5. DASHBOARD HEADER & KPI CARDS
# -----------------------------------------------------------------------------
st.title(f"📊 {selected_company} ({selected_ticker.replace('.NS', '')})")
st.caption(f"Sector: {stock_info['sector']} | Valuation Mode: {valuation_status}")

k1, k2, k3, k4 = st.columns(4)
with k1: st.metric("Live Price (CMP)", f"₹{cmp:,.2f}", f"{day_change_pct:+.2f}%")
with k2: st.metric("Dynamic DCF Target", f"₹{dcf_target:,.2f}")
with k3: st.metric("Implied Upside", f"{upside_pct:+.1f}%")
with k4: st.metric("Recommendation", recommendation)

st.markdown("---")

# -----------------------------------------------------------------------------
# 6. VIEW MODES
# -----------------------------------------------------------------------------

# --- VIEW: CONCALL & GUIDANCE MATRIX (LOGGING ENGINE) ---
if view_mode == "Interactive Concall & Guidance Matrix":
    st.subheader(f"📝 Concall Notes & Dynamic Valuation Driver - {selected_company}")
    
    # Form to log new quarterly call takeaways
    with st.form("concall_entry_form"):
        st.markdown("### Log New Quarterly Concall Takeaways")
        c1, c2 = st.columns(2)
        with c1:
            quarter = st.text_input("Quarter Period", "Q3 FY27")
            rev_guidance = st.text_input("Revenue Guidance", "18-20% YoY Growth")
            margin_guidance = st.text_input("EBITDA / Margin Guidance", "21.5% EBITDA")
            tone = st.selectbox("Management Tone", ["Very Bullish", "Confident", "Cautious", "Bearish"])
        
        with c2:
            st.markdown("**Adjust Valuation Parameters based on Call:**")
            adj_wacc = st.number_input("Discount Rate / WACC (%)", 5.0, 20.0, float(active_wacc), 0.1)
            adj_growth = st.number_input("Terminal Growth Rate (%)", 1.0, 10.0, float(active_growth), 0.1)
            analyst_notes = st.text_area("Key Analyst Concall Notes & Takeaways")
            
        submit = st.form_submit_button("💾 Save Concall Note & Update Intrinsic Target Price")
        
        if submit:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO concall_logs (ticker_symbol, quarter, rev_guidance, margin_guidance, management_tone, analyst_notes, adj_wacc, adj_growth)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (selected_ticker, quarter, rev_guidance, margin_guidance, tone, analyst_notes, adj_wacc, adj_growth))
            conn.commit()
            conn.close()
            st.success(f"Concall takeaways for {quarter} logged! Intrinsic Target Price updated across app.")
            st.rerun()

    st.markdown("---")
    st.subheader("📜 Historical Concall Logs")
    if not df_concalls.empty:
        st.dataframe(df_concalls[['quarter', 'management_tone', 'rev_guidance', 'margin_guidance', 'adj_wacc', 'adj_growth', 'analyst_notes', 'timestamp']], use_container_width=True)
    else:
        st.info("No concall notes logged yet for this stock. Fill the form above to add your first note.")

# --- VIEW: OVERVIEW & THESIS TRACKER ---
elif view_mode == "Overview & Thesis Tracker":
    st.subheader(f"Financial Growth Trajectory & Notes - {selected_company}")
    st.info(f"**Latest Management Tone:** {df_concalls.iloc[0]['management_tone'] if not df_concalls.empty else 'Not Logged'}")
    
    # Read quarterly results stored in DB by Step 1
    conn = get_db_connection()
    df_q = pd.read_sql_query("SELECT * FROM quarterly_financials WHERE ticker = ? ORDER BY quarter_date ASC", conn, params=(selected_ticker,))
    conn.close()
    
    if not df_q.empty:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df_q['quarter_date'], y=df_q['revenue']/1e7, name="Revenue (₹ Cr)", marker_color="#1B365D"))
        fig.add_trace(go.Scatter(x=df_q['quarter_date'], y=df_q['net_profit']/1e7, name="Net Profit (₹ Cr)", yaxis="y2", line=dict(color="#28A745", width=3)))
        fig.update_layout(
            title="Automated Quarterly Results Trajectory (Fetched by Step 1)",
            yaxis=dict(title="Revenue (₹ Cr)"),
            yaxis2=dict(title="Net Profit (₹ Cr)", overlaying="y", side="right"),
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No quarterly automated data found in DB yet. Run `python fetch_quarterly_data.py` to populate.")

# --- VIEW: 3-STAGE DCF VALUATION ---
elif view_mode == "3-Stage DCF Valuation":
    st.subheader(f"Dynamic DCF Sensitivity - {selected_company}")
    st.write(f"**Active WACC:** {active_wacc}% | **Active Terminal Growth:** {active_growth}%")
    
    wacc_range = np.linspace(active_wacc - 1.0, active_wacc + 1.0, 5)
    g_range = np.linspace(active_growth - 0.5, active_growth + 0.5, 5)
    
    matrix = []
    for w in wacc_range:
        row = []
        for g in g_range:
            val = dcf_target * (1 + (g - active_growth)/100.0 - (w - active_wacc)/50.0)
            row.append(f"₹{val:,.1f}")
        matrix.append(row)
        
    df_matrix = pd.DataFrame(matrix, index=[f"WACC {w:.1f}%" for w in wacc_range], columns=[f"g {g:.1f}%" for g in g_range])
    st.dataframe(df_matrix, use_container_width=True)
