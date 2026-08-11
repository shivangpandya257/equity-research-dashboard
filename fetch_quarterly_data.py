import sqlite3
import yfinance as yf
import pandas as pd
import datetime

# -----------------------------------------------------------------------------
# 1. DEFINE YOUR 50+ COVERAGE UNIVERSE (NSE Tickers)
# -----------------------------------------------------------------------------
COVERAGE_UNIVERSE = [
    "JYOTICNC.NS", "AXISBANK.NS", "RELIANCE.NS", "LT.NS",
    "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "BHARTIARTL.NS", "ITC.NS", "SBIN.NS", "HINDUNILVR.NS"
    # Add all 50+ tickers here...
]

DB_NAME = "coverage_hub.db"

# -----------------------------------------------------------------------------
# 2. INITIALIZE DATABASE TABLES
# -----------------------------------------------------------------------------
def setup_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Create table for raw quarterly financials
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quarterly_financials (
            ticker TEXT,
            quarter_date TEXT,
            revenue REAL,
            ebitda REAL,
            net_profit REAL,
            last_updated TEXT,
            PRIMARY KEY (ticker, quarter_date)
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully.")

# -----------------------------------------------------------------------------
# 3. FETCH & STORE QUARTERLY DATA
# -----------------------------------------------------------------------------
def update_quarterly_results():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    
    for ticker_symbol in COVERAGE_UNIVERSE:
        print(f"🔄 Fetching quarterly data for: {ticker_symbol}...")
        try:
            stock = yf.Ticker(ticker_symbol)
            # Pull income statement on a quarterly basis
            quarterly_df = stock.quarterly_financials
            
            if quarterly_df.empty:
                print(f"⚠️ No quarterly data found for {ticker_symbol}")
                continue
            
            # Transpose dataframe so dates become rows
            df_t = quarterly_df.T
            
            for index, row in df_t.iterrows():
                quarter_date = index.strftime("%Y-%m-%d")
                
                # Fetch metrics safely with fallbacks
                revenue = row.get("Total Revenue", row.get("Operating Revenue", 0.0))
                ebitda = row.get("EBITDA", row.get("Normalized EBITDA", 0.0))
                net_profit = row.get("Net Income", row.get("Net Income Common Stockholders", 0.0))
                
                # Insert or update database records
                cursor.execute("""
                    INSERT INTO quarterly_financials (ticker, quarter_date, revenue, ebitda, net_profit, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(ticker, quarter_date) DO UPDATE SET
                        revenue = excluded.revenue,
                        ebitda = excluded.ebitda,
                        net_profit = excluded.net_profit,
                        last_updated = excluded.last_updated
                """, (ticker_symbol, quarter_date, float(revenue), float(ebitda), float(net_profit), today_str))
                
            print(f"  └─ Successfully updated {ticker_symbol}")
            
        except Exception as e:
            print(f"❌ Failed to fetch {ticker_symbol}: {e}")
            
    conn.commit()
    conn.close()
    print("\n🎉 All 50+ stock quarterly results updated into coverage_hub.db!")

# -----------------------------------------------------------------------------
# 4. SCRIPT EXECUTION
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    setup_database()
    update_quarterly_results()
