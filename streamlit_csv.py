# streamlit_csv.py — Member Health Records Dashboard (CSV Version)
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
from typing import Optional
import base64
import os

st.set_page_config(page_title="Kansas Member Health Record Dashboard", layout="wide")

# ---------- Logo ----------
def load_logo():
    try:
        with open("Stellarus_logo_2C_whiteype.png", "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return ""

logo_base64 = load_logo()

# ---------- Brand ----------
BRAND = {
    "primary":     "#436DB3",
    "light_blue":  "#BFD0EE",
    "danger":      "#F4454E",
    "bg_soft":     "#F7F3EF",
    "border":      "#EDEDED",
    "ink":         "#0B1221",
    "ok":          "#1A8E3B",
    "link_blue":   "#0071BC",
}
BLUES = ["#436DB3", "#5B84C7", "#87A9DA", "#AFC5E8", "#D3E1F5"]
CHART_TITLE_SIZE = 18
PLOT_HEIGHT = 380

# ---------- CSS ----------
st.markdown(f"""
<style>
@import url("https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap");
html, body, [class*="css"] {{
  font-family:"Roboto", system-ui, -apple-system, Segoe UI, Arial, sans-serif !important;
  color:{BRAND["ink"]}; background:{BRAND["bg_soft"]};
}}
.block-container {{ padding-top: 3rem; }}

.header {{
  background:#2B2F36; color:#fff; border-radius:12px; padding:18px 16px; margin: 8px 0 16px 0;
}}
.header .title {{ font-weight:700; font-size:18px; line-height:22px; margin:0; }}
.header .sub   {{ opacity:.9; font-size:13px; }}

.kpi-tile {{
  background:#fff; border:1px solid {BRAND["border"]}; border-radius:12px; padding:12px 14px; margin-bottom:10px;
}}
.kpi-label {{ font-size:12px; color:#445268; display:flex; gap:8px; align-items:center; }}
.kpi-value {{ font-weight:700; font-size:26px; color:{BRAND["ink"]}; }}
.kpi-delta {{ font-size:12px; margin-top:2px; }}

.left-radio .stRadio > div {{ gap:6px; }}
.left-radio label {{ font-weight:600; color:#0B2648; }}

.stPlotlyChart {{ margin-top:0 !important; }}
.chart-wrap {{ margin:0; padding:0; }}
</style>
""", unsafe_allow_html=True)

# ---------- Plotly helpers ----------
px.defaults.template = "plotly_white"

def style_layout(fig, title=None, *, legend_pos="top-right", hide_grid=True, bottom_legend=False, height=PLOT_HEIGHT):
    if bottom_legend:
        legend = dict(orientation="h", y=-0.25, x=0.5, xanchor="center"); bmargin = 70
    elif legend_pos == "top-right":
        legend = dict(orientation="h", y=1.02, x=1.0, xanchor="right"); bmargin = 10
    else:
        legend = dict(orientation="h", y=1.02, x=0.0, xanchor="left"); bmargin = 10

    fig.update_layout(
        title=title,
        title_font=dict(size=CHART_TITLE_SIZE, family="Roboto", color=BRAND["ink"]),
        font=dict(family="Roboto", size=12, color=BRAND["ink"]),
        plot_bgcolor="#fff", paper_bgcolor="#fff",
        margin=dict(l=8, r=8, t=45, b=bmargin),
        legend=legend,
        height=height
    )
    fig.update_xaxes(showgrid=(not hide_grid), gridcolor=BRAND["border"])
    fig.update_yaxes(showgrid=(not hide_grid), gridcolor=BRAND["border"])
    return fig

# ---------- Data Loading ----------
@st.cache_data
def load_data_from_csv():
    """Load data from CSV file."""
    try:
        df = pd.read_csv("data.csv")
        
        # Parse date column
        if 'event_date' in df.columns:
            df['event_date'] = pd.to_datetime(df['event_date'], format='%m/%d/%y', errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Error loading CSV: {str(e)}")
        return pd.DataFrame()

# ---------- Data Processing ----------
def compute_counts(df):
    """Compute KPI metrics."""
    crossovers = len(df[df['event_type'] == 'crossover'])
    clicks = len(df[df['event_type'] == 'link_click'])
    conversion = (clicks / crossovers * 100) if crossovers > 0 else 0
    return crossovers, clicks, conversion

# ---------- Header ----------
st.markdown(f"""
<div class="header" style="display:flex; justify-content:space-between; align-items:center;">
  <div>
    <div class="title">Kansas Member Health Record Dashboard</div>
    <div class="sub">Analytics Overview — CSV Data Source</div>
  </div>
  {'<img src="data:image/png;base64,' + logo_base64 + '" style="height:40px;"/>' if logo_base64 else ''}
</div>
""", unsafe_allow_html=True)

# ---------- Load Data ----------
df = load_data_from_csv()

if df.empty:
    st.warning("No data loaded. Please ensure data.csv exists in the application directory.")
    st.stop()

st.success(f"✓ Data loaded successfully: {len(df):,} records")

# ---------- Filters ----------
st.markdown("### Filters")
col_f1, col_f2 = st.columns(2)

with col_f1:
    min_date = df['event_date'].min()
    max_date = df['event_date'].max()
    date_range = st.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

with col_f2:
    browsers = ['All'] + sorted(df['browser'].dropna().unique().tolist())
    selected_browser = st.selectbox("Browser", browsers)

# Apply filters
df_filtered = df.copy()
if len(date_range) == 2:
    df_filtered = df_filtered[
        (df_filtered['event_date'] >= pd.Timestamp(date_range[0])) &
        (df_filtered['event_date'] <= pd.Timestamp(date_range[1]))
    ]
if selected_browser != 'All':
    df_filtered = df_filtered[df_filtered['browser'] == selected_browser]

# ---------- KPIs ----------
crossovers, clicks, conversion = compute_counts(df_filtered)

st.markdown("### Key Metrics")
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(f"""
    <div class="kpi-tile">
      <div class="kpi-label">Website Crossovers</div>
      <div class="kpi-value">{crossovers:,}</div>
    </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
    <div class="kpi-tile">
      <div class="kpi-label">Link Clicks</div>
      <div class="kpi-value">{clicks:,}</div>
    </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
    <div class="kpi-tile">
      <div class="kpi-label">Click Conversion Rate</div>
      <div class="kpi-value">{conversion:.1f}%</div>
    </div>
    """, unsafe_allow_html=True)

# ---------- Tabs ----------
tab1, tab2, tab3 = st.tabs(["📊 Executive Overview", "🔀 Website Crossovers", "🔗 Link Clicks"])

with tab1:
    st.markdown("#### Event Trends Over Time")
    
    daily = df_filtered.groupby([df_filtered['event_date'].dt.date, 'event_type']).size().reset_index(name='count')
    daily.columns = ['date', 'event_type', 'count']
    
    fig = px.line(daily, x='date', y='count', color='event_type',
                  labels={'count': 'Events', 'date': 'Date', 'event_type': 'Event Type'},
                  color_discrete_sequence=BLUES)
    fig = style_layout(fig, "Daily Event Trends", bottom_legend=True)
    st.plotly_chart(fig, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Events by Browser")
        browser_counts = df_filtered['browser'].value_counts().head(5).reset_index()
        browser_counts.columns = ['browser', 'count']
        
        fig = px.bar(browser_counts, x='browser', y='count',
                     labels={'count': 'Events', 'browser': 'Browser'},
                     color_discrete_sequence=[BRAND["primary"]])
        fig = style_layout(fig)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### Events by Device")
        device_counts = df_filtered['device_type'].value_counts().reset_index()
        device_counts.columns = ['device_type', 'count']
        
        fig = px.pie(device_counts, values='count', names='device_type',
                     color_discrete_sequence=BLUES)
        fig = style_layout(fig)
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown("#### Website Crossovers Analysis")
    
    crossover_df = df_filtered[df_filtered['event_type'] == 'crossover']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### Crossovers by City")
        city_counts = crossover_df['city'].value_counts().head(10).reset_index()
        city_counts.columns = ['city', 'count']
        
        fig = px.bar(city_counts, x='count', y='city', orientation='h',
                     labels={'count': 'Crossovers', 'city': 'City'},
                     color_discrete_sequence=[BRAND["primary"]])
        fig = style_layout(fig)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("##### Crossovers by Traffic Source")
        source_counts = crossover_df['traffic_source'].value_counts().head(10).reset_index()
        source_counts.columns = ['traffic_source', 'count']
        
        fig = px.bar(source_counts, x='count', y='traffic_source', orientation='h',
                     labels={'count': 'Crossovers', 'traffic_source': 'Traffic Source'},
                     color_discrete_sequence=[BRAND["link_blue"]])
        fig = style_layout(fig)
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("##### Daily Crossover Trend")
    daily_crossovers = crossover_df.groupby(crossover_df['event_date'].dt.date).size().reset_index(name='count')
    daily_crossovers.columns = ['date', 'count']
    
    fig = px.line(daily_crossovers, x='date', y='count',
                  labels={'count': 'Crossovers', 'date': 'Date'},
                  markers=True,
                  color_discrete_sequence=[BRAND["primary"]])
    fig = style_layout(fig)
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.markdown("#### Link Clicks Analysis")
    
    clicks_df = df_filtered[df_filtered['event_type'] == 'link_click']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### Clicks by Page Path")
        page_counts = clicks_df['page_path'].value_counts().head(10).reset_index()
        page_counts.columns = ['page_path', 'count']
        
        fig = px.bar(page_counts, x='count', y='page_path', orientation='h',
                     labels={'count': 'Clicks', 'page_path': 'Page Path'},
                     color_discrete_sequence=[BRAND["danger"]])
        fig = style_layout(fig)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("##### Clicks by Campaign")
        campaign_counts = clicks_df['utm_campaign'].value_counts().head(10).reset_index()
        campaign_counts.columns = ['utm_campaign', 'count']
        
        fig = px.bar(campaign_counts, x='count', y='utm_campaign', orientation='h',
                     labels={'count': 'Clicks', 'utm_campaign': 'Campaign'},
                     color_discrete_sequence=[BRAND["ok"]])
        fig = style_layout(fig)
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("##### Daily Click Trend")
    daily_clicks = clicks_df.groupby(clicks_df['event_date'].dt.date).size().reset_index(name='count')
    daily_clicks.columns = ['date', 'count']
    
    fig = px.line(daily_clicks, x='date', y='count',
                  labels={'count': 'Link Clicks', 'date': 'Date'},
                  markers=True,
                  color_discrete_sequence=[BRAND["danger"]])
    fig = style_layout(fig)
    st.plotly_chart(fig, use_container_width=True)

# ---------- Footer ----------
st.markdown("---")
st.caption("Kansas Member Health Records Dashboard | Powered by Stellarus")
