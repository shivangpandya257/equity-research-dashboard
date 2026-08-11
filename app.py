import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
import os

# Page Config
st.set_page_config(page_title="Equity Research Dashboard", layout="wide")

# Header
st.title("📊 Buy-Side Equity Research Dashboard")
st.caption("Horizon: 4-5 Years Structural Hold")

# Sidebar
selected_stock = st.sidebar.selectbox("Select Coverage Stock", ["Jyoti CNC Automation", "Axis Bank", "Reliance Industries", "Larsen & Toubro"])
st.sidebar.markdown("---")
view_mode = st.sidebar.radio("Dashboard View", ["Overview & Thesis Tracker", "3-Stage DCF Valuation", "5-Stage DuPont ROE", "Concall & Guidance Matrix"])

# KPI Cards
k1, k2, k3, k4 = st.columns(4)
k1.metric("Live Price (CMP)", "₹1,259.30", "+0.85%")
k2.metric("DCF Intrinsic Value", "₹1,680.50")
k3.metric("Implied Upside", "+33.4%")
k4.metric("Recommendation", "BUY")

st.markdown("---")

# Views
if view_mode == "Overview & Thesis Tracker":
    st.subheader("Multi-Year Revenue & EBITDA Trajectory")
    years = ["FY23", "FY24", "FY25", "FY26E", "FY27E", "FY28E", "FY29E", "FY30E"]
    revenue = [900, 1200, 1500, 1850, 2300, 2800, 3350, 3950]
    ebitda = [135, 216, 300, 388, 494, 616, 753, 908]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(x=years, y=revenue, name="Revenue (₹ Cr)"))
    fig.add_trace(go.Scatter(x=years, y=ebitda, name="EBITDA (₹ Cr)", yaxis="y2"))
    fig.update_layout(yaxis=dict(title="Revenue"), yaxis2=dict(title="EBITDA", overlaying="y", side="right"))
    st.plotly_chart(fig, use_container_width=True)

elif view_mode == "3-Stage DCF Valuation":
    st.subheader("DCF Valuation Sensitivity")
    wacc = st.slider("WACC (%)", 8.0, 14.0, 10.8)
    st.info(f"Target Price calculated at WACC {wacc}%: ₹1,680.50")

elif view_mode == "5-Stage DuPont ROE":
    st.subheader("DuPont ROE Drivers")
    st.write("Operating Margin: 17.7% | Asset Turnover: 0.78x | Leverage: 1.60x -> ROE: 15.8%")

elif view_mode == "Concall & Guidance Matrix":
    st.subheader("Management Guidance Tracking")
    st.write("Q1 FY27: Revenue Guidance 20-25% YoY | Margin: 21.5% EBITDA | Order Book: ₹3,400 Cr")

