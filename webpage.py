import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from PIL import Image
from datetime import datetime
import os
import base64
import streamlit.components.v1 as components
import json

# --- Streamlit Configuration and Styling ---
st.set_page_config(
    page_title="Monthly QA Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- Page Background Styling (Light Violet) ---
st.markdown("""
    <style>
        /* Overall page background */
       body, .main, .stApp {
    background: linear-gradient(to right, #f1edf7, #d4c7f0 ) !important;
    color: #fff !important;  /* Set text color to white for contrast */
    min-height: 100vh;
}

        /* Headings */
        h1, h2, h3, h4 {
            color: #290660 !important;
        }

        

        /* Optional hover effect for subtle feedback */
        .element-container:has(.stMetric):hover {
            box-shadow: 0 6px 14px rgba(0, 0, 0, 0.08);
        }

        /* Optional: adjust label text inside metric */
        .stMetric label {
            color: #290660;  /* Deep Indigo for labels */
            font-weight: 600;
        }

        /* Buttons */
        .stButton>button {
            background-color: #0d6efd !important;
            color: #000 !important;
            border: none;
            border-radius: 5px;
        }

        .stButton>button:hover {
            background-color: #290660 !important;
            color: #fff !important;
        }

        /* Dropdown/select box */
        .stSelectbox, .stDropdown {
            background-color: #f8f9fa !important;
        }

        /* Sidebar */
        .css-6qob1r, .css-1d391kg {  /* Sidebar background class */
            background-color: #290660 !important;
            color: #fff !important;
        }

        /* Plot titles */
        .js-plotly-plot .plotly .title {
            color: #290660 !important;
        }
    </style>
""", unsafe_allow_html=True)



st.markdown("""
<style>
    .big-font {
        font-size:30px !important;
        font-weight: bold;
    }
    .stSelectbox {
        margin-top: -30px;
    }
    
</style>
""", unsafe_allow_html=True)
st.markdown("""
<style>
/* Main selectbox wrapper */
div[data-testid="stSelectbox"] {
    background-color: transparent !important;
    padding: 0 !important;
    border-radius: 8px !important;
}

/* Remove background of the select container inside */
div[data-testid="stSelectbox"] > div {
    background-color: transparent !important;
    box-shadow: none !important;
}

/* Customize the actual select element appearance */
div[data-testid="stSelectbox"] .css-1d391kg,  /* Older versions */
div[data-testid="stSelectbox"] .st-cw {        /* Newer versions */
    background-color: transparent !important;
    color: #290660 !important; /* Accent text color */
    font-weight: 600;
}

/* Arrow dropdown icon */
div[data-testid="stSelectbox"] svg {
    color: #290660 !important;
}

/* Remove any outline/border if focused */
div[data-testid="stSelectbox"] *:focus {
    outline: none !important;
    box-shadow: none !important;
}
</style>
""", unsafe_allow_html=True)


# --- Data Loading ---
sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQfmDvoHtr58LTd1MhYyI2s3uJqt6YbXklFt6JZ2pm6aQtriz1vz4kwGtHoY1-a9EH0M4cMnD74gk7O/pub?gid=2104660007&single=true&output=csv"
@st.cache_data(ttl=600)
def load_data(url, skip_rows=0):
    try:
        df = pd.read_csv(url, on_bad_lines='skip', engine='python', skiprows=skip_rows)
    except Exception as e:
        st.error(f"⚠️ Error loading data from URL: {e}")
        st.stop()
    return df

df = load_data(sheet_url)

# --- Department Selector (added early before filtering)
selected_dept = st.radio(
    "Select Department:",
    options=["QC", "QA"],
    index=0,
    horizontal=True
)
# --- Preprocessing ---
df.columns = [col.strip() for col in df.columns]

project_col = "Project Name as per the SOW"
date_col = "File come for QA Date"
status_col = "QA Status"
feed_site_col = "Feed(Site) Name"
qa_col = "QA Name"
dept_col = "Department"
qa_status_date_col = "QA status - Date"
frequency_col = "Frequency"


required_cols = [project_col, date_col, status_col, feed_site_col, qa_col, dept_col, qa_status_date_col]
missing = [col for col in required_cols if col not in df.columns]
if missing:
    st.error(f"🚫 Required columns are missing in the data: {missing}")
    st.stop()

df = df[df[dept_col].astype(str).str.strip().str.upper() == selected_dept.upper()].copy()
df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
df[qa_status_date_col] = pd.to_datetime(df[qa_status_date_col], errors='coerce')
df = df.dropna(subset=[date_col, qa_status_date_col])

df["Month"] = df[date_col].dt.to_period("M").astype(str)
df[status_col] = df[status_col].astype(str).str.strip().str.lower()

done_str = "qa done"
reject_str = "qa rejected"
revised_str = "qa done/revised"

available_months = sorted(df["Month"].unique())
if not available_months:
    st.warning(f"🧐 No valid months found after filtering for {selected_dept} department.")
    st.stop()

# --- Function: Convert Image to Base64 ---
def image_to_base64(img_path):
    with open(img_path, "rb") as img_file:
        b64_string = base64.b64encode(img_file.read()).decode()
    return b64_string

# --- Header & Logo ---
col_left, col_right = st.columns([0.80, 0.20])

with col_left:
    st.markdown("""
        <div style='font-size: 40px; font-weight: bold; color: #4B0082; margin-bottom: 0px;'>
            📈 Monthly Quality Assurance Dashboard
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div style='font-size: 19px; color: #666; margin-top: 2px;'>
            A monthly overview of <strong>{selected_dept}</strong> department activity, status distribution, and individual performance.
        </div>
    """, unsafe_allow_html=True)

with col_right:
    image_path = "D:/KSDB NANDAN/QA Desbord/monthy_web/logo2.jpg"
    if os.path.exists(image_path):
        img_b64 = image_to_base64(image_path)
        st.markdown(f"""
            <style>
                .img_b64 {{
                    transition: transform 0.8s ease-in-out;
                    transform-origin: center;
                }}
                .img_b64:hover {{
                    transform: scale(2);
                }}
            </style>

            <div style="display: flex; justify-content: center;">
                <img class="img_b64" src="data:image/jpeg;base64,{img_b64}" width="150"
                     style="border-radius: 50%; box-shadow: 0 2px 6px rgba(0,0,0,0.1); cursor: pointer;">
            </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ Logo image not found.")




# --- Month Selector ---
col1, col2 = st.columns([0.2, 0.8])
with col1:
    selected_month = st.selectbox(
        "Select a Month",
        options=available_months,
        index=len(available_months) - 1
    )

filtered = df[df["Month"] == selected_month]
# --- Stop if no data
if filtered.empty:
    st.info(f"No QA records found for **{selected_month}** in the {selected_dept} department.")
    st.stop()
# --- Count each status ---
done_count = (filtered[status_col] == done_str).sum()
revised_count = (filtered[status_col] == revised_str).sum()
reject_count = (filtered[status_col] == reject_str).sum()
total = len(filtered)

# --- Calculate percentages
qa_done_pr = (done_count / total * 100) if total else 0
done_revised_pr = (revised_count / total * 100) if total else 0
reject_pr = (reject_count / total * 100) if total else 0


done_counts = (
    filtered[filtered[status_col] == done_str][qa_col]
    .value_counts().rename("Done Count")
)

reject_counts = (
    filtered[filtered[status_col] == reject_str][qa_col]
    .value_counts().rename("Reject Count")
)

revised_counts = (
    filtered[filtered[status_col] == revised_str][qa_col]
    .value_counts().rename("Revised Count")
)

qa_summary = pd.concat([done_counts, reject_counts, revised_counts], axis=1).fillna(0).reset_index()
qa_summary.rename(columns={"index": "QA Name"}, inplace=True)

qa_summary['Total'] = qa_summary['Done Count'] + qa_summary['Reject Count'] + qa_summary['Revised Count']
qa_summary['Rejection Rate (%)'] = np.where(
    qa_summary['Total'] > 0,
    (qa_summary['Reject Count'] / qa_summary['Total']) * 100,
    0.0
).round(1)

qa_summary = qa_summary.sort_values(by='Total', ascending=True)


# --- Now you can build the 4 KPI cards ---
# Define your colors
CARD_BG = "#f9f9f9"
ACCENT_COLOR_DONE = "#28a745"     # Green
ACCENT_COLOR_REJECT = "#dc3545"   # Red
ACCENT_COLOR_REVISED = "#ffcc00"  # Yellow
ACCENT_COLOR_TOTAL = "#4B0082"    # Indigo

# ✅ Hover card CSS
st.markdown("""
    <style>
        /* Base KPI Card Style */
        .kpi-card {
            box-shadow: 0 4px 8px rgba(0,0,0,0.05);
            transition: all 0.3s ease-in-out;
        }

        /* Hover Effect */
        .kpi-card:hover {
            box-shadow: 0 8px 16px rgba(0,0,0,0.2); /* Deeper shadow */
            transform: translateY(-4px);           /* Lift effect */
        }

        /* Ensure headers are reset */
        .kpi-card h4 {
            margin-bottom: 8px !important; 
        }
        .kpi-card h2 {
            margin: 0 !important;
        }
    </style>
""", unsafe_allow_html=True)
# KPI layout
month_date = datetime.strptime(selected_month, "%Y-%m")
pretty_month = month_date.strftime("%B - %Y")
st.subheader(f"📅 Monthly Overview for **{pretty_month}**")
k1, k2, k3, k4 = st.columns(4)

st.markdown(f"""
<style>
  .spotlight-card {{
      position: relative;
      border-radius: 15px;
      overflow: hidden;
      padding: 25px 20px;
      box-shadow: 0 4px 15px rgba(0,0,0,0.15);
      transition: all 0.4s ease-in-out;
      cursor: default;
      background-color: {CARD_BG}; /* same bg for all */
      color: #333; /* text color */
  }}

  .spotlight-card::before {{
      content: "";
      position: absolute;
      top: -100px;
      left: -100px;
      width: 300px;
      height: 300px;
      border-radius: 50%;
      transform: scale(0);
      transition: transform 0.6s ease-out;
      pointer-events: none;
      z-index: 1;
  }}

  .spotlight-card:hover::before {{
      transform: scale(1);
  }}

  .spotlight-card:hover {{
      transform: translateY(-4px);
      box-shadow: 0 6px 18px rgba(0,0,0,0.25);
  }}

  /* Individual border-left colors */
  .spotlight-total {{
      border-left: 5px solid {ACCENT_COLOR_TOTAL};
  }}
  .spotlight-done {{
      border-left: 5px solid {ACCENT_COLOR_DONE};
  }}
  .spotlight-reject {{
      border-left: 5px solid {ACCENT_COLOR_REJECT};
  }}
  .spotlight-revised {{
      border-left: 5px solid {ACCENT_COLOR_REVISED};
  }}

  /* Text styling */
  .spotlight-title {{
      font-size: 18px;
      font-weight: 600;
      z-index: 2;
      position: relative;
      margin-bottom: 8px;
  }}

  .spotlight-value {{
      font-size: 32px;
      font-weight: 700;
      margin-top: 8px;
      z-index: 2;
      position: relative;
  }}

  .spotlight-subvalue {{
      font-size: 16px;
      margin-left: 8px;
      color: inherit;
      opacity: 0.7;
  }}

  /* Hover glow colors */
  .spotlight-total::before {{
      background: radial-gradient(circle, rgba(99,102,241,0.25) 0%, transparent 70%);
  }}
  .spotlight-done::before {{
      background: radial-gradient(circle, rgba(34,197,94,0.3) 0%, transparent 70%); /* green */
  }}
  .spotlight-reject::before {{
      background: radial-gradient(circle, rgba(239,68,68,0.3) 0%, transparent 70%); /* red */
  }}
  .spotlight-revised::before {{
      background: radial-gradient(circle, rgba(234,179,8,0.3) 0%, transparent 70%); /* yellow */
  }}

  /* Text color overrides for colored accents */
  .spotlight-total .spotlight-value {{
      color: {ACCENT_COLOR_TOTAL};
  }}
  .spotlight-done .spotlight-value {{
      color: {ACCENT_COLOR_DONE};
  }}
  .spotlight-reject .spotlight-value {{
      color: {ACCENT_COLOR_REJECT};
  }}
  .spotlight-revised .spotlight-value {{
      color: {ACCENT_COLOR_REVISED};
  }}
</style>
""", unsafe_allow_html=True)


with k1:
    st.markdown(f"""
        <div class="spotlight-card spotlight-total">
            <h4 class="spotlight-title">📊 Total Files ({selected_dept})</h4>
            <h2 class="spotlight-value">{total}</h2>
        </div>
    """, unsafe_allow_html=True)

with k2:
    st.markdown(f"""
        <div class="spotlight-card spotlight-done">
            <h4 class="spotlight-title">{selected_dept} Done ✅</h4>
            <h2 class="spotlight-value">
                {done_count}
                <span class="spotlight-subvalue">({qa_done_pr:.1f}%)</span>
            </h2>
        </div>
    """, unsafe_allow_html=True)

with k3:
    st.markdown(f"""
        <div class="spotlight-card spotlight-reject">
            <h4 class="spotlight-title">Rejected ❌</h4>
            <h2 class="spotlight-value">
                {reject_count}
                <span class="spotlight-subvalue">({reject_pr:.1f}%)</span>
            </h2>
        </div>
    """, unsafe_allow_html=True)

with k4:
    st.markdown(f"""
        <div class="spotlight-card spotlight-revised">
            <h4 class="spotlight-title">Done/Revised 📝</h4>
            <h2 class="spotlight-value">
                {revised_count}
                <span class="spotlight-subvalue">({done_revised_pr:.1f}%)</span>
            </h2>
        </div>
    """, unsafe_allow_html=True)


st.markdown("---")



# 📅 Daily QA Files Trend
st.markdown(f"#### 📅 Daily {selected_dept} Files Trend")

filtered[qa_status_date_col] = pd.to_datetime(filtered[qa_status_date_col], errors='coerce')
filtered = filtered.dropna(subset=[qa_status_date_col]).copy()
filtered["QA Status Date Only"] = filtered[qa_status_date_col].dt.date
filtered["QA Status Month"] = filtered[qa_status_date_col].dt.to_period("M").astype(str)
filtered_month_only = filtered[filtered["QA Status Month"] == selected_month]

daily_counts = (
    filtered_month_only
    .groupby("QA Status Date Only")
    .size()
    .reset_index(name='File Count')
)

fig_daily = px.bar(
    daily_counts,
    x="QA Status Date Only",
    y="File Count",
    color="File Count",
    color_continuous_scale="Blues",
    text="File Count",
    labels={"QA Status Date Only": "Date", "File Count": "Number of Files"},
    title=""
)

fig_daily.update_layout(
    height=400,
    xaxis=dict(
        tickangle=-45,
        tickformat="%b %d",  # Example: Oct 01
        dtick="D1",  # Show every day (1-day interval)
        tickfont=dict(size=10)
    ),
    margin=dict(t=30, b=50, l=30, r=30),
    showlegend=False,
    coloraxis_showscale=False
)

fig_daily.update_traces(textposition='outside')
st.plotly_chart(fig_daily, use_container_width=True)

# Summary and Preventive Actions
left_spacer, content_col, right_spacer = st.columns([1, 2, 1])
with content_col:
    col1, col2 = st.columns(2)

    with col1:
        if not daily_counts.empty:
            max_date = daily_counts.loc[daily_counts["File Count"].idxmax(), "QA Status Date Only"]
            total_files = total
            avg_files = daily_counts["File Count"].mean()
        else:
            max_date = "N/A"
            total_files = 0
            avg_files = 0.0

        st.markdown(f"""
            <style>
                .hover-card:hover {{
                    box-shadow: 4px 6px 20px rgba(0,0,0,0.15);
                    transform: scale(1.02);
                    transition: all 0.3s ease-in-out;
                }}
            </style>
            <div class='hover-card' style='
                background-color: #e8f0fe;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 2px 2px 8px rgba(0,0,0,0.05);
                transition: all 0.3s ease-in-out;
            '>
            <h4 style='color: #290660;'>📋 Graph Summary</h4>
            <ul style='color: #333; font-size: 16px;'>
                <li>Highest {selected_dept} file count on <strong>{max_date}</strong></li>
                <li>Total {selected_dept} files: <strong>{total_files}</strong></li>
                <li>Average per day: <strong>{avg_files:.1f}</strong></li>
            </ul>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
            <div class='hover-card' style='
                background-color: #fef3c7;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 2px 2px 8px rgba(0,0,0,0.05);
                transition: all 0.3s ease-in-out;
            '>
            <h4 style='color: #290660;'>🛡️ Preventive Action</h4>
            <ul style='color: #333; font-size: 16px;'>
                <li>Monitor {selected_dept} workload spikes to avoid overload</li>
                <li>Cross-train {selected_dept} to handle peak days</li>
                <li>Review rejected files for recurring issues</li>
            </ul>
            </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# 📊 New Chart: Daily Count of Done vs Rejected (Side-by-Side with Counts)
st.markdown(f"""
    <div style='background-color: #e0e7ff; padding: 10px 15px; border-radius: 8px; 
                margin-bottom: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.08);
                transition: all 0.5s ease-in-out;'>
        <h5 style='margin: 0; color: #290660; font-weight: 600;'>
            🗓️ Daily {selected_dept} Status Breakdown (Done vs Rejected)
        </h5>
    </div>
""", unsafe_allow_html=True)


# Define custom colors
CARD_BG = "rgba(255, 255, 255, 255)"
PLOT_BG = "#e6f0ff"
DEEP_VIOLET = "#290660"
DONE_COLOR = "#0d6efd"
REJECTED_COLOR = "#ff5733"
AVG_COLOR = "#9b59b6"  # Purple line for Average

# Prepare data (only for selected QA Status Month)
daily_status_breakdown = (
    filtered_month_only
    .groupby(["QA Status Date Only", status_col])
    .size()
    .reset_index(name="Count")
)

# Filter relevant statuses
daily_status_breakdown = daily_status_breakdown[
    daily_status_breakdown[status_col].isin([done_str, reject_str])
]

# Pivot for plotting
pivot_daily = daily_status_breakdown.pivot(
    index="QA Status Date Only",
    columns=status_col,
    values="Count"
).fillna(0)

# Ensure expected columns
for col in [done_str, reject_str]:
    if col not in pivot_daily.columns:
        pivot_daily[col] = 0

# ✅ Calculate Average line
pivot_daily["Average"] = pivot_daily.mean(axis=1)
# Calculate totals for donut chart
total_done = pivot_daily[done_str].sum()
total_rejected = pivot_daily[reject_str].sum()
avg_total = pivot_daily["Average"].sum()

fig_group = go.Figure()

# FTR bar
fig_group.add_trace(go.Bar(
    x=pivot_daily.index,
    y=pivot_daily[done_str],
    name="FTR",
    marker_color=DONE_COLOR,
    text=pivot_daily[done_str],
    textposition='outside',
    hovertemplate='Date: %{x}<br>FTR: %{y}<extra></extra>'
))

# Iteration Count bar
fig_group.add_trace(go.Bar(
    x=pivot_daily.index,
    y=pivot_daily[reject_str],
    name="Iteration count",
    marker_color=REJECTED_COLOR,
    text=pivot_daily[reject_str],
    textposition='outside',
    hovertemplate='Date: %{x}<br>Iteration: %{y}<extra></extra>'
))

# Average line
fig_group.add_trace(go.Scatter(
    x=pivot_daily.index,
    y=pivot_daily["Average"],
    mode="lines+markers",
    name="Average",
    line=dict(color=AVG_COLOR, width=3, shape="spline"),
    marker=dict(size=8, color="white", line=dict(width=2, color=AVG_COLOR)),
    hovertemplate='Date: %{x}<br>Average: %{y:.1f}<extra></extra>'
))



# Layout for combined chart
fig_group.update_layout(
    barmode='group',
    xaxis_title="Date",
    yaxis_title="File Count",
    plot_bgcolor=PLOT_BG,
    paper_bgcolor=CARD_BG,
    height=420,
    xaxis=dict(
        tickangle=-45,
        tickformat="%b %d",
        dtick="D1",
        tickfont=dict(size=10),
        showgrid=True,
        gridcolor='#f0f0f0'
    ),
    yaxis=dict(
        showgrid=True,
        gridcolor='#f0f0f0'
    ),
    legend=dict(
        orientation="v",
        yanchor="top",
        y=1,
        xanchor="left",
        x=1.02,
        font=dict(color=DEEP_VIOLET),
        bgcolor="rgba(255,255,255,0)"
    ),
    margin=dict(t=40, r=100, b=50, l=50),  # increased right margin to make space for donut
    uniformtext_minsize=8,
    uniformtext_mode='show'
)

# Streamlit display
st.plotly_chart(fig_group, use_container_width=True)


# 📊 Summary and Action Points for Done vs Rejected Chart
left_spacer2, content_col2, right_spacer2 = st.columns([1, 2, 1])
with content_col2:
    col3, col4 = st.columns(2)

    with col3:
        if not pivot_daily.empty:
            max_done_date = pivot_daily[done_str].idxmax()
            max_reject_date = pivot_daily[reject_str].idxmax()
            total_done = done_count
            total_rejected = revised_count
        else:
            max_done_date = "N/A"
            max_reject_date = "N/A"
            total_done = 0
            total_rejected = 0

        st.markdown(f"""
            <div class='hover-card' style='
                background-color: #d1fae5;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 2px 2px 8px rgba(0,0,0,0.05);
                transition: all 0.3s ease-in-out;
            '>
            <h4 style='color: #065f46;'>📈 Done vs Rejected Summary</h4>
            <ul style='color: #333; font-size: 16px;'>
                <li>Most FTR on: <strong>{max_done_date}</strong></li>
                <li>Most Rejections on: <strong>{max_reject_date}</strong></li>
                <li>Total FTR: <strong>{total_done}</strong></li>
                <li>Total Rejected: <strong>{total_rejected}</strong></li>
            </ul>
            </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
            <div class='hover-card' style='
                background-color: #fee2e2;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 2px 2px 8px rgba(0,0,0,0.05);
                transition: all 0.3s ease-in-out;
            '>
            <h4 style='color: #7f1d1d;'>⚠️ Suggested Actions</h4>
            <ul style='color: #333; font-size: 16px;'>
                <li>Investigate high rejection days</li>
                <li>Compare rejection reasons with {selected_dept} logs</li>
                <li>Provide feedback to reduce repeated mistakes</li>
            </ul>
            </div>
        """, unsafe_allow_html=True)

st.markdown("---")



# Create a 2-column layout
col1, col2 = st.columns([0.35, 0.65])

# === 📊 PART 1 — Donut Chart (Left Side) ===
with col1:
    st.markdown(f"""
        <div style='background-color: #e0e7ff; padding: 5px 8px; border-radius: 8px; margin-bottom: 5px;'>
            <h5 style='margin: 0; color: #1e3a8a;'> 🎯 {selected_dept} Status Distribution</h5>
        </div>
    """, unsafe_allow_html=True)

    highcharts_code = f"""
    <div id="container" style="height: 400px; width: 100%;"></div>
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/highcharts-3d.js"></script>
    <script>
    Highcharts.chart('container', {{
        chart: {{
            type: 'pie',
            backgroundColor: '#f8f9fc',
            options3d: {{
                enabled: true,
                alpha: 45,
                beta: 0
            }}
        }},
        title: {{
            text: ''
        }},
        tooltip: {{
            pointFormat: '{{series.name}}: <b>{{point.y}}</b>'
        }},
        plotOptions: {{
            pie: {{
                allowPointSelect: true,
                cursor: 'pointer',
                depth: 45,
                innerSize: 100,
                dataLabels: {{
                    enabled: true,
                    format: '{{point.name}}: {{point.y}}'
                }}
            }}
        }},
        series: [{{
            name: 'Files',
            data: [
                {{ name: 'Done', y: {done_count}, color: '#28a745' }},
                {{ name: 'Reject', y: {reject_count}, color: '#dc3545' }},
                {{ name: '{selected_dept} Done/Revised', y: {revised_count}, color: '#ffc107' }}
            ]
        }}]
    }});
    </script>
    """

    components.html(highcharts_code, height=450)


# === 📊 PART 2 — QA-wise Summary Bar Chart (Right Side) ===
with col2:
    st.markdown(f"""
        <div style='background-color: #e0f7fa; padding: 5px 8px;border-radius: 8px; margin-bottom: 5px;'>
            <h5 style='margin: 0; color: #006064;'> 🧑‍💻 {selected_dept}-wise Work Summary</h5>
        </div>
    """, unsafe_allow_html=True)

    if not qa_summary.empty:
        # Prepare dynamic values
        qa_names = qa_summary['QA Name'].tolist()
        done_data = qa_summary['Done Count'].tolist()
        reject_data = qa_summary['Reject Count'].tolist()

        # Convert Python lists to JavaScript array format
        js_categories = json.dumps(qa_names)
        js_done = json.dumps(done_data)
        js_reject = json.dumps(reject_data)

        highcharts_code = f"""
        <div id="container" style="height: 450px; width: 100%;"></div>
        <script src="https://code.highcharts.com/highcharts.js"></script>
        <script src="https://code.highcharts.com/modules/exporting.js"></script>
        <script>
        Highcharts.chart('container', {{
            chart: {{
                type: 'bar',
                backgroundColor: '#f9f9fc'
            }},
            title: {{
                text: '',
                align: 'left'
            }},
            xAxis: {{
                categories: {js_categories},
                title: {{
                    text: null
                }},
                labels: {{
                    style: {{
                        fontSize: '13px'
                    }}
                }}
            }},
            yAxis: {{
                min: 0,
                title: {{
                    text: 'Count of Files',
                    align: 'high'
                }},
                labels: {{
                    overflow: 'justify'
                }}
            }},
            tooltip: {{
                valueSuffix: ' files'
            }},
            plotOptions: {{
                bar: {{
                 pointWidth: 20,  
                 groupPadding: 0.2, // gap between groups of bars (like "Done" and "Reject")
                 pointPadding: 0.1,
                    dataLabels: {{
                        enabled: true
                    }}
                    
                }},
                series: {{
                    stacking: 'normal'
                }}
            }},
            legend: {{
                    enabled: false
                }},

            credits: {{
                enabled: false
            }},
            series: [{{
                name: 'Reject',
                data: {js_reject},
                color: '#dc3545'
            }}, {{
                name: 'Done',
                data: {js_done},
                color: '#28a745'
            }}]
        }});
        </script>
        """

        components.html(highcharts_code, height=500)
    else:
        st.info("No individual QA activity found for this month.")






# Use a slightly more robust check for division
if total_files > 0:
    done_pct = qa_done_pr
    reject_pct = reject_pr
    revised_pct = done_revised_pr
else:
    done_pct = reject_pct = revised_pct = 0

rework_pct = reject_pct + revised_pct

# ✅ Hover card & General CSS Styles
st.markdown("""
    <style>
        /* General Streamlit tweaks for a cleaner look */
        .stContainer, .st-emotion-cache-1pxn41c {
            gap: 1rem; /* Better spacing between rows */
        }

        /* Hover Card Effect */
        .hover-card {
            box-shadow: 0 2px 8px rgba(0,0,0,0.08); /* Initial subtle shadow */
            border: 1px solid rgba(0,0,0,0.05); /* Soft border */
            transition: all 0.3s ease-in-out;
        }
        .hover-card:hover {
            box-shadow: 4px 6px 20px rgba(0,0,0,0.15);
            transform: scale(1.02);
        }

        /* Consistent List Styling for better alignment */
        .hover-card ul {
            padding-left: 20px;
            margin-top: 5px; /* Reduce margin above list */
            margin-bottom: 5px; /* Reduce margin below list */
            font-size: 15px; /* Slightly smaller font for points */
        }
        .hover-card ul li {
            margin-bottom: 5px;
        }

        /* Consistent Header Styling */
        .hover-card h4 {
            margin-top: 0;
            padding-bottom: 5px;
            border-bottom: 1px solid rgba(0,0,0,0.1);
        }
    </style>
""", unsafe_allow_html=True)

# ---------------- ROW 1 (The 3 main metrics) ----------------
st.subheader(f"{selected_dept} File Status Breakdown")
row1_col1, row1_col2, row1_col3 = st.columns(3)

# 🟦 Card: QA Done
with row1_col1:
    left_points = ["Files passed in first iteration.", "Clean implementation.", "SOW understood."]
    # The original logic for splitting points is fine, but for simplicity with 3 points, we'll keep it simple.
    # The points can be displayed in a single column for this small list.

    st.markdown(f"""
        <div class='hover-card' style='
            background-color: #e0f7fa; /* Light Cyan */
            padding: 20px;
            border-radius: 10px;
            color: #000;
        '>
        <h4 style='color: #004d40;'>✅ {selected_dept} Done - {done_count:,} files ({done_pct:.1f}%)</h4>
        <div style="display: flex;">
            <ul style='flex: 1;'>{''.join(f'<li>{pt}</li>' for pt in left_points)}</ul>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 🟥 Card: QA Rejected
with row1_col2:
    left_points = ["Wrong platform logic", "Missing data points", "SOW mismatch"]
    # Removed the complex `right_points` logic for visual simplicity in the card.

    st.markdown(f"""
        <div class='hover-card' style='
            background-color: #ffebee; /* Light Red */
            padding: 20px;
            border-radius: 10px;
            color: #000;
        '>
        <h4 style='color: #b71c1c;'>❌ {selected_dept} Rejected - {reject_count:,} files ({reject_pct:.1f}%)</h4>
        <div style="display: flex;">
            <ul style='flex: 1;'>
                {''.join(f"<li>{point}</li>" for point in left_points)}
            </ul>
        </div>
        </div>
    """, unsafe_allow_html=True)

# 🟧 Card: QA Revised
with row1_col3:
    left_points = ["Files resubmitted after correction.", "Revalidation impacts FTR.", "Second review required."]
    # Removed the complex `right_points` logic for visual simplicity in the card.

    st.markdown(f"""
        <div class='hover-card' style='
            background-color: #fff3e0; /* Light Orange */
            padding: 20px;
            border-radius: 10px;
            color: #000;
        '>
        <h4 style='color: #e65100;'>🔄 {selected_dept} Revised - {revised_count:,} files ({revised_pct:.1f}%)</h4>
        <div style="display: flex;">
            <ul style='flex: 1;'>
                {''.join(f"<li>{point}</li>" for point in left_points)}
            </ul>
        </div>
        </div>
    """, unsafe_allow_html=True)


# ---------------- ROW 2 (Summary and Action Points) ----------------

# Using st.columns(2) directly for cleaner code structure without an outer container
row2_col1, row2_col2 = st.columns(2)

# 🧠 Card Part 1: FTR % and Rework %
with row2_col1:
    ftr_pct = done_pct
    st.markdown(f"""
        <div class='hover-card' style='
            background-color: #f3e5f5;
            padding: 20px;
            border-radius: 10px;
            margin-top: 25px;
        '>
        <h4 style='color: #4a148c;'>📌 Key Performance Indicators</h4>
        <ul style='color: #333;'>
            <li><strong>First Time Right (FTR):</strong> <span style='font-size: 18px; color: #004d40;'>{ftr_pct:.1f}%</span></li>
            <li><strong>Rework Required:</strong> <span style='font-size: 18px; color: #b71c1c;'>{rework_pct:.1f}%</span></li>
            <li><strong>Total Files Reviewed:</strong> <span style='font-size: 18px;'>{total_files:,}</span></li>
        </ul>
        </div>
    """, unsafe_allow_html=True)

# 🛠️ Card Part 2: Developer Action Points
with row2_col2:
    st.markdown(f"""
        <div class='hover-card' style='
            background-color: #f3e5f5;
            padding: 20px;
            border-radius: 10px;
            margin-top: 25px;
        '>
        <h4 style='color: #4a148c;'>🛠️ Action Plan & Focus Areas</h4>
        <ul style='color: #333;'>
            <li><strong>SOW Alignment:</strong> Clarify complex or ambiguous Statement of Work expectations.</li>
            <li><strong>Root Cause Analysis:</strong> Investigate recurring "Rejected" issues with development team.</li>
            <li><strong>Pre-{selected_dept} Checks:</strong> Implement developer-side validation steps to catch basic errors.</li>
        </ul>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")


# Columns expected: Frequency, QA Status
# --- 🧹 Clean and standardize status column ---
filtered[status_col] = filtered[status_col].astype(str).str.strip().str.lower()
filtered[frequency_col] = filtered[frequency_col].astype(str).str.strip()

# --- 🧮 Group by Frequency and count Done/Reject ---
summary = (
    filtered
    .groupby(frequency_col)[status_col]
    .value_counts()
    .unstack(fill_value=0)
    .reset_index()
)

# --- ✅ Add missing columns if not present ---
for col in ["qa done", "qa rejected"]:
    if col not in summary.columns:
        summary[col] = 0

# --- ✅ Calculate totals and percentages (no decimals) ---
summary["Total File"] = summary[["qa done", "qa rejected"]].sum(axis=1)
summary["FTR%"] = (summary["qa done"] / summary["Total File"] * 100).round(0).astype(int)
summary["Iteration%"] = (summary["qa rejected"] / summary["Total File"] * 100).round(0).astype(int)

# --- 💬 Add comment based on volume ---
def volume_comment(x):
    if x > 100:
        return "🔵 High volume"
    elif x > 50:
        return "🟢 Medium volume"
    else:
        return "🟠 Low volume"

summary["Comment on Volume"] = summary["Total File"].apply(volume_comment)

# --- ✨ Add footer row with totals ---
footer = pd.DataFrame({
    "Frequency (Sheet Name)": ["Total"],
    "Total File": [summary["Total File"].sum()],
    "FTR %": [""],  # optional: leave blank
    "Iteration %": [""],  # optional: leave blank
    "Comment on Volume": [""]
})

# --- ✨ Final formatted table ---
summary_table = summary.rename(columns={
    frequency_col: "Frequency (Sheet Name)",
    "Total File": "Total File",
    "FTR%": "FTR %",
    "Iteration%": "Iteration %",
    "Comment on Volume": "Comment on Volume"
})[["Frequency (Sheet Name)", "Total File", "FTR %", "Iteration %", "Comment on Volume"]]

# Append footer
summary_table = pd.concat([summary_table, footer], ignore_index=True)

# Apply background color
styled_table = summary_table.style.set_properties(**{
    'background-color': '#f0f8ff',  # light blue
    'color': 'black',
    'border-color': 'black'
})

# --- 🎨 Layout: Table (left) + Chart (right)
col1, col2 = st.columns([1, 1])

# --- LEFT: Table ---
with col1:
    st.markdown("### 📋 Frequency Summary Table")
    table_height = int(38 * len(summary_table))  # approximate row height
    st.dataframe(styled_table, height=table_height)



# --- RIGHT: Bar Chart ---
with col2:
    st.markdown("### 📊 FTR% vs Iteration% by Frequency")

    fig = go.Figure()

    # ✅ FTR% Bar
    fig.add_trace(go.Bar(
        y=summary[frequency_col],
        x=summary["FTR%"],  # <-- Using original column name
        name="FTR %",
        orientation='h',
        marker_color="#28a745",
        text=summary["FTR%"].astype(str) + "%",
        textposition='outside'
    ))

    # ✅ Iteration% Bar
    fig.add_trace(go.Bar(
        y=summary[frequency_col],
        x=summary["Iteration%"],
        name="Iteration %",
        orientation='h',
        marker_color="#ff5733",
        text=summary["Iteration%"].astype(str) + "%",
        textposition='outside'
    ))

    # --- Chart layout styling ---
    fig.update_layout(
        barmode='group',
        height=450,
        plot_bgcolor='rgba(240,248,255,0.8)',
        paper_bgcolor='rgba(255,255,255,0.8)',
        xaxis_title="Percentage (%)",
        yaxis_title="",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5
        ),
        margin=dict(l=40, r=20, t=40, b=40)
    )

    st.plotly_chart(fig, use_container_width=True)


st.markdown("---")

# --- Footer Logo & Caption ---
footer_img_path = "D:/KSDB NANDAN/QA Desbord/monthy_web/img-2.png"
if os.path.exists(footer_img_path):
    footer_b64 = image_to_base64(footer_img_path)
    st.markdown(f"""
        <style>
            .footer-logo {{
                transition: transform 0.8s ease-in-out;
                transform-origin: center;
            }}
            .footer-logo:hover {{
                transform: scale(3);
            }}
        </style>

        <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.85rem; color: #4B0082;">
            <div style="opacity: 0.7;">
                📊 Data loaded from Google Sheets and filtered for the '<strong>{selected_dept}</strong>' Department.
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
                <img class="footer-logo" src="data:image/png;base64,{footer_b64}" width="60" height="60" 
                     style="margin-top: 1px; border-radius: 50%; cursor: pointer;">
            </div>
        </div>

        <hr style="margin-top: 20px; margin-bottom: 10px;">
    """, unsafe_allow_html=True)







