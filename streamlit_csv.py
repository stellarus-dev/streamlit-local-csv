# my_dashboard.py — Member Health Records Dashboard (API Version)
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
import requests
from typing import Optional
import base64

st.set_page_config(page_title="Kansas Member Health Record Dashboard", layout="wide")

# ---------- Logo ----------
import os

def load_logo():
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(script_dir, "Stellarus_logo_2C_whiteype.png")
        with open(logo_path, "rb") as f:
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
PLOT_HEIGHT = 380  # same height for paired charts

# ---------- CSS: compact, no "white strip" ----------
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

/* remove any stray vertical gap around Plotly charts */
.stPlotlyChart {{ margin-top:0 !important; }}
/* no cards/borders around charts — just charts */
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
    fig.update_xaxes(
        showgrid=(not hide_grid), 
        gridcolor=BRAND["border"],
        dtick="M1",
        tickformat="%b %Y"
    )
    fig.update_yaxes(showgrid=(not hide_grid), gridcolor=BRAND["border"])
    return fig

# ---------- Data loader from CSV ----------
@st.cache_data
def load_data_from_csv() -> pd.DataFrame:
    """Load data from API"""
    try:
        response = requests.get('https://dev-analytics-api-lwapp-stlus-ncus.azurewebsites.net/events')
        response.raise_for_status()  # Raise an error for bad status codes
        data = response.json()
        df = pd.DataFrame(data['events'])
    except Exception as e:
        st.error(f"Error loading data from API: {str(e)}")
        return pd.DataFrame()
    
    if df.empty:
        return df
    
    # ---------- Data cleaning and normalization ----------
    def make_unique(cols):
        seen, out = {}, []
        for c in cols:
            c = str(c).strip()
            if c not in seen: seen[c]=1; out.append(c)
            else: seen[c]+=1; out.append(f"{c}_{seen[c]}")
        return out
    
    def lower_unique(cols):
        seen, out = {}, []
        for c in cols:
            lc = c.lower().strip()
            if lc not in seen: seen[lc]=1; out.append(lc)
            else: seen[lc]+=1; out.append(f"{lc}_{seen[lc]}")
        return out
    
    df.columns = lower_unique(make_unique(df.columns))
    
    # Coalesce columns
    for new_col, candidates in [
        ("state", ["state", "member_state", "state_code"]),
        ("city", ["city", "member_city"]),
        ("zipcode", ["zipcode", "zip", "member_zip"]),
    ]:
        found = [c for c in candidates if c in df.columns]
        if found:
            df[new_col] = df[found].bfill(axis=1).iloc[:, 0] if len(found) > 1 else df[found[0]]
        elif new_col not in df.columns:
            df[new_col] = pd.NA
    
    if "state" in df.columns:
        df["state"] = df["state"].astype("string")
    if "city" in df.columns:
        df["city"] = df["city"].astype("string")
    
    if "weight" in df.columns and "height" in df.columns:
        with np.errstate(divide="ignore", invalid="ignore"):
            df["bmi"] = df["weight"] / (df["height"]**2)
    
    for c in ["event_type","traffic_source","utm_campaign","device_type","browser",
              "zipcode","retention_status","program_activity","user_id","program_destination"]:
        if c not in df.columns: df[c] = pd.NA
        df[c] = df[c].astype("string")
    
    df["event_date"] = pd.to_datetime(df["event_date"], errors="coerce")
    if "event_timestamp" in df.columns:
        df["event_timestamp"] = pd.to_datetime(df["event_timestamp"], errors="coerce")
    if "event_type" in df.columns:
        # Normalize incoming event types to our canonical set
        # Map variants like IN_BOUND_CROSSOVER -> crossover, CARE_PROGRAM_CLICKED -> link_click
        mapping = {
            "IN_BOUND_CROSSOVER": "crossover",
            "CARE_PROGRAM_CLICKED": "link_click",
        }
        et = df["event_type"].astype("string").str.strip()
        normalized = et.str.upper().map(mapping).fillna(et.str.lower())
        df["event_type"] = normalized
    
    return df

# ---------- Load data ----------
data = load_data_from_csv()

if data.empty:
    st.error("❌ No data available from CSV file")
    st.stop()


# ---------- Header ----------
st.markdown(f"""
<style>
.logo-invert {{
    height: 45px;
    margin-right: 10px;
}}
</style>
<div class="header">
  <div style="display: flex; justify-content: space-between; align-items: center;">
    <div>
      <div class="title">Kansas Member Health Record Dashboard</div>
    </div>
    <div>
      <img src="data:image/png;base64,{logo_base64}" class="logo-invert" />
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ---------- Filters (Browser and Date Range only) ----------
def options_from(df, primary, fallback=None):
    if primary in df.columns and df[primary].dropna().astype("string").str.strip().ne("").any():
        vals = sorted(df[primary].dropna().astype("string").str.strip().unique().tolist())
        return ["All"] + vals
    if fallback and fallback in df.columns and df[fallback].dropna().astype("string").str.strip().ne("").any():
        vals = sorted(df[fallback].dropna().astype("string").str.strip().unique().tolist())
        return ["All"] + vals
    return ["All"]

min_d = pd.Timestamp.now() - pd.DateOffset(months=12)
max_d = pd.Timestamp.now()

frow = st.columns([1.5, 1.5, 2])
dr = frow[0].date_input("Date Range", (min_d, max_d), min_value=min_d, max_value=max_d)

# Handle incomplete date range selection - keep using default until both dates are selected
if isinstance(dr, tuple) and len(dr) == 2:
    start_d, end_d = pd.to_datetime(dr[0]), pd.to_datetime(dr[1])
else:
    # User is still selecting dates - use the full range to avoid errors
    start_d, end_d = min_d, max_d

browser = frow[1].selectbox("Browser", options_from(data, "browser"), index=0)

# base (non-date) mask — used for current and prior windows
base_mask = pd.Series(True, index=data.index)
if browser != "All" and "browser" in data.columns:
    base_mask &= data["browser"].astype("string").eq(browser)

df = data.loc[base_mask & data["event_date"].between(start_d, end_d)].copy()

# ---------- KPI + Funnel inference ----------
EXPECTED = {"crossover","link_click","signup","improvement"}

def compute_counts(frame: pd.DataFrame):
    if "event_type" in frame.columns and frame["event_type"].dropna().isin(EXPECTED).any():
        c = frame["event_type"].value_counts()
        return {
            "crossover": int(c.get("crossover", 0)),
            "link_click": int(c.get("link_click", 0)),
            "signup":    int(c.get("signup", 0)),
            "improve":   int(c.get("improvement", 0)),
        }
    total = len(frame)
    clicks = int(frame["traffic_source"].notna().sum()) if "traffic_source" in frame.columns else int(0.33*total)
    signups = int(0.05*total)
    improve = 0
    return {"crossover": total, "link_click": clicks, "signup": signups, "improve": improve}

def counts_for_window(s, e):
    frame = data.loc[base_mask & data["event_date"].between(s, e)]
    return compute_counts(frame)

cur_counts = counts_for_window(start_d, end_d)

# Calculate conversion percentage
conversion_pct = (cur_counts["link_click"] / cur_counts["crossover"] * 100) if cur_counts["crossover"] > 0 else 0

# ---------- KPI tiles (Website Crossovers, Link Clicks, and Click Conversion) ----------
KPI = [
    ("Website Crossovers", "🌐", cur_counts["crossover"], False),
    ("Link Clicks",        "🔗", cur_counts["link_click"], False),
    ("Click Conversion",   "", conversion_pct, True),
]
k1, k2, k3 = st.columns(3)
for col, (label, icon, cur, is_percent) in zip([k1, k2, k3], KPI):
    with col:
        value_display = f"{cur:.0f}%" if is_percent else f"{cur:,}"
        icon_display = f"{icon}&nbsp;&nbsp;" if icon else ""
        st.markdown(
            f"""
            <div class="kpi-tile">
              <div class="kpi-label">{icon_display}{label}</div>
              <div class="kpi-value">{value_display}</div>
            </div>
            """, unsafe_allow_html=True
        )

# ---------- Left nav ----------
left, main = st.columns([0.23, 1], gap="large")
with left:
    st.markdown('<div class="left-radio">', unsafe_allow_html=True)
    tab = st.radio("Navigation", ["Executive Overview", "Website Crossovers", "Link Clicks"], index=0)
    st.markdown('</div>', unsafe_allow_html=True)

# ---------- Helpers ----------
def get_unique_ids_by_month(frame, event_filter=None):
    """Get unique user_id counts by month, optionally filtered by event_type"""
    if event_filter and "event_type" in frame.columns:
        frame = frame[frame["event_type"].astype("string").str.lower() == event_filter.lower()]
    
    if "user_id" not in frame.columns:
        # Fallback: count rows
        monthly = (frame.assign(period=frame["event_date"].dt.to_period("M").dt.to_timestamp())
                   .groupby("period").size().reset_index(name="unique_ids"))
    else:
        monthly = (frame.assign(period=frame["event_date"].dt.to_period("M").dt.to_timestamp())
                   .groupby("period")["user_id"].nunique().reset_index(name="unique_ids"))
    return monthly

def smooth_line(df_line, y_cols, title, color_seq=None, height=PLOT_HEIGHT):
    fig = px.line(
        df_line if "period" in df_line.columns else df_line.reset_index(), 
        x="period", y=y_cols, markers=True,
        line_shape="spline",
        color_discrete_sequence=color_seq or [BRAND["primary"], BRAND["light_blue"], BRAND["danger"]]
    )
    fig.update_traces(line=dict(width=2.6))
    fig.update_xaxes(title="")
    return style_layout(fig, title, legend_pos="top-right", hide_grid=True, height=height)

# ---------- Tabs ----------
with main:
    if tab == "Executive Overview":
        # Stacked bar chart showing conversion trend (full width)
        crossover_monthly = get_unique_ids_by_month(df, "crossover")
        link_click_monthly = get_unique_ids_by_month(df, "link_click")
        
        # Merge the two dataframes
        monthly_data = crossover_monthly.merge(link_click_monthly, on="period", how="outer", suffixes=("_crossover", "_click")).fillna(0)
        monthly_data.columns = ["period", "Website Crossovers", "Link Clicks"]
        
        # Create overlapping bar chart
        fig = go.Figure()
        
        # Add Website Crossovers bars (lighter color, in the back)
        fig.add_trace(go.Bar(
            x=monthly_data["period"],
            y=monthly_data["Website Crossovers"],
            name="Website Crossovers",
            marker=dict(color=BRAND["light_blue"]),
            hovertemplate="<b>%{x|%b %Y}</b><br>Website Crossovers: %{y:,.0f}<extra></extra>"
        ))
        
        # Add Link Clicks bars (darker color, in the front, overlapping)
        fig.add_trace(go.Bar(
            x=monthly_data["period"],
            y=monthly_data["Link Clicks"],
            name="Link Clicks",
            marker=dict(color=BRAND["primary"]),
            hovertemplate="<b>%{x|%b %Y}</b><br>Link Clicks: %{y:,.0f}<extra></extra>"
        ))
        
        # Add Conversion Rate line on secondary axis
        conversion_rate = (monthly_data["Link Clicks"] / monthly_data["Website Crossovers"] * 100).fillna(0)
        fig.add_trace(go.Scatter(
            x=monthly_data["period"],
            y=conversion_rate,
            name="Click Conversion",
            line=dict(color=BRAND["danger"], width=2.6),
            mode="lines+markers",
            yaxis="y2",
            hovertemplate="<b>%{x|%b %Y}</b><br>Click Conversion: %{y:.1f}%<extra></extra>"
        ))
        
        fig.update_layout(
            barmode="overlay",
            yaxis=dict(title="Unique Users", showgrid=True, gridcolor=BRAND["border"]),
            yaxis2=dict(
                title="% Conversion Rate",
                overlaying="y",
                side="right",
                showgrid=False,
                range=[0, 100]
            ),
            margin=dict(l=60, r=90, t=60, b=100),
            xaxis=dict(tickangle=-45, showgrid=False)
        )
        
        fig = style_layout(fig, "Conversion Trend", legend_pos="top-right", hide_grid=True, height=PLOT_HEIGHT, bottom_legend=True)
        st.plotly_chart(fig, width="stretch")

    elif tab == "Website Crossovers":
        w1, w2 = st.columns([1.2, 0.9])
        
        with w1:
            # Trending line chart of website crossovers (unique IDs per month)
            crossover_monthly = get_unique_ids_by_month(df, "crossover")
            
            fig = smooth_line(crossover_monthly, ["unique_ids"], 
                            "Website Crossovers (Unique IDs per Month)", 
                            color_seq=[BRAND["primary"]], height=PLOT_HEIGHT)
            st.plotly_chart(fig, width="stretch")
        
        with w2:
            # Donut chart showing % by Browser (total count by unique IDs)
            if "browser" in df.columns and df["browser"].notna().any():
                # Filter to crossover events
                crossover_df = df[df["event_type"].astype("string").str.lower() == "crossover"] if "event_type" in df.columns else df
                
                # Count unique IDs by browser
                browser_data = (crossover_df.groupby("browser")["user_id"].nunique().reset_index(name="unique_ids")
                                             .sort_values("unique_ids", ascending=False))
            else:
                # Fallback data
                browser_data = pd.DataFrame({
                    "browser": ["Chrome", "Safari", "Edge", "Firefox"],
                    "unique_ids": [45, 30, 15, 10]
                })
            
            fig = px.pie(
                browser_data, values="unique_ids", names="browser", hole=0.62,
                color="browser",
                color_discrete_sequence=BLUES
            )
            fig.update_traces(textinfo="percent+label")
            fig = style_layout(fig, "Crossovers by Browser", bottom_legend=True, height=PLOT_HEIGHT)
            st.plotly_chart(fig, width="stretch")

    elif tab == "Link Clicks":
        a1, a2 = st.columns([1.2, 0.9])
        
        with a1:
            # Trending line chart of link clicks to Virta and Kansas using program_destination column
            link_click_df = df[df["event_type"].astype("string").str.lower() == "link_click"].copy() if "event_type" in df.columns else df.copy()
            
            if "program_destination" in link_click_df.columns and link_click_df["program_destination"].notna().any():
                # Get monthly unique IDs by program_destination
                monthly_dest = (link_click_df.assign(period=link_click_df["event_date"].dt.to_period("M").dt.to_timestamp())
                                             .groupby(["period", "program_destination"])["user_id"].nunique().reset_index(name="unique_ids"))
                
                # Pivot to get Virta and Kansas columns
                monthly_pivot = monthly_dest.pivot(index="period", columns="program_destination", values="unique_ids").fillna(0).reset_index()
                
                # Ensure we have Virta and Kansas columns
                for col in ["Virta", "Kansas"]:
                    if col not in monthly_pivot.columns:
                        monthly_pivot[col] = 0
                
                # Create line chart with custom colors
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=monthly_pivot["period"],
                    y=monthly_pivot["Kansas"],
                    name="Kansas",
                    line=dict(color=BRAND["primary"], width=2.6),
                    mode="lines+markers",
                    hovertemplate="<b>%{x|%b %Y}</b><br>Kansas: %{y:,.0f}<extra></extra>"
                ))
                
                fig.add_trace(go.Scatter(
                    x=monthly_pivot["period"],
                    y=monthly_pivot["Virta"],
                    name="Virta",
                    line=dict(color=BRAND["danger"], width=2.6),
                    mode="lines+markers",
                    hovertemplate="<b>%{x|%b %Y}</b><br>Virta: %{y:,.0f}<extra></extra>"
                ))
            else:
                # Fallback: simple line chart
                link_click_monthly = get_unique_ids_by_month(df, "link_click")
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=link_click_monthly["period"],
                    y=link_click_monthly["unique_ids"],
                    name="Link Clicks",
                    line=dict(color=BRAND["primary"], width=2.6),
                    mode="lines+markers"
                ))
            
            fig.update_layout(
                margin=dict(l=50, r=50, t=60, b=70)
            )
            fig = style_layout(fig, "Link Clicks Trends", legend_pos="top-right", hide_grid=True, height=PLOT_HEIGHT, bottom_legend=True)
            st.plotly_chart(fig, width="stretch")
        
        with a2:
            # Donut chart showing % by Virta vs Kansas using program_destination column
            link_click_df = df[df["event_type"].astype("string").str.lower() == "link_click"].copy() if "event_type" in df.columns else df.copy()
            
            if "program_destination" in link_click_df.columns and link_click_df["program_destination"].notna().any():
                # Count unique IDs by program_destination
                dest_data = (link_click_df.groupby("program_destination")["user_id"].nunique().reset_index(name="unique_ids")
                                          .sort_values("unique_ids", ascending=False))
            else:
                # Fallback data
                dest_data = pd.DataFrame({
                    "program_destination": ["Virta", "Kansas"],
                    "unique_ids": [50, 35]
                })
            
            # Custom colors matching line chart: Kansas=primary blue, Virta=danger red
            fig = px.pie(
                dest_data, values="unique_ids", names="program_destination", hole=0.62,
                color="program_destination",
                color_discrete_map={"Kansas": BRAND["primary"], "Virta": BRAND["danger"]}
            )
            fig.update_traces(
                textinfo="percent+label",
                textfont=dict(size=14),
                hovertemplate="<b>%{label}</b><br>Count: %{value:,.0f}<br>Percentage: %{percent}<extra></extra>"
            )
            fig.update_layout(
                margin=dict(l=20, r=20, t=60, b=70)
            )
            fig = style_layout(fig, "Link Clicks by Program", bottom_legend=True, height=PLOT_HEIGHT)
            st.plotly_chart(fig, width="stretch")
