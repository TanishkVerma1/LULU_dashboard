
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
from utils import standardize_columns, infer_columns, engineer_features, kpis, safe_num, per_order_metrics, new_vs_repeat_by_month
import plots

st.set_page_config(page_title="Lulu Executive Dashboard", layout="wide")

# High-contrast, readable outcome card
st.markdown(
    """
    <style>
    .outcome-card {
        background: #fff9e6;
        border-left: 8px solid #f59e0b;
        padding: 12px 14px;
        border-radius: 10px;
        margin: 8px 0 24px 0;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
        font-size: 1rem;
        color: #1f2937;
        line-height: 1.35;
    }
    .outcome-card strong { color: #1f2937; }
    </style>
    """,
    unsafe_allow_html=True
)

def outcome_card(note_text):
    st.markdown(f"""<div class="outcome-card">📌 <strong>Business outcome idea:</strong> {note_text}</div>""", unsafe_allow_html=True)

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DEFAULT_DATA_FILE = DATA_DIR / "lulu_uae_master_2000.csv"

@st.cache_data
def load_data():
    if DEFAULT_DATA_FILE.exists():
        df = pd.read_csv(DEFAULT_DATA_FILE)
    else:
        alt_path = Path("data") / "lulu_uae_master_2000.csv"
        if alt_path.exists():
            df = pd.read_csv(alt_path)
        else:
            raise FileNotFoundError("Data file not found. Ensure it exists at lulu_executive_dashboard/data/.")
    df = standardize_columns(df)
    col_map = infer_columns(df)
    df = engineer_features(df, col_map)
    return df, col_map

st.title("🛒 Lulu Executive Dashboard")
st.caption("Executive-ready insights with clear, readable outcome suggestions.")

df, col_map = load_data()

# Sidebar filters
with st.sidebar:
    st.header("Filters")
def pick(col_key, label):
    col = col_map.get(col_key) or (col_key if col_key in df.columns else None)
    if col and col in df.columns:
        vals = ["All"] + sorted([str(x) for x in df[col].dropna().unique()])
        return col, st.multiselect(label, vals, default=["All"])
    return None, None

with st.sidebar:
    col_city, f_city = pick('city', "City")
    col_dept, f_dept = pick('department', "Department")
    col_cat, f_cat = pick('category', "Category")
    col_brand, f_brand = pick('brand', "Brand")
    col_channel, f_channel = pick('channel', "Channel")
    col_gender, f_gender = pick('gender', "Gender")
    col_ageg, f_ageg = pick('age_group', "Age Group")
    col_store_format, f_store = pick('store_format', "Store Format")
    col_nat, f_nat = pick('nationality_group', "Nationality Group")

def apply_filters(df):
    def apply(d, col, sel):
        if col and sel and "All" not in sel:
            return d[d[col].astype(str).isin(sel)]
        return d
    d = df
    d = apply(d, col_city, f_city)
    d = apply(d, col_dept, f_dept)
    d = apply(d, col_cat, f_cat)
    d = apply(d, col_brand, f_brand)
    d = apply(d, col_channel, f_channel)
    d = apply(d, col_gender, f_gender)
    d = apply(d, col_ageg, f_ageg)
    d = apply(d, col_store_format, f_store)
    d = apply(d, col_nat, f_nat)
    return d

filtered = apply_filters(df)

# KPIs
rev_col = col_map.get('line_value')
qty_col = col_map.get('quantity')
st.subheader("Key Performance Indicators")
k = kpis(filtered, col_map)
cols = st.columns(len(k) or 1)
for (name, val), c in zip(k.items(), cols):
    c.metric(name, safe_num(val))
st.markdown("---")

def render(fig, note):
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)
        outcome_card(note)

# Core views (kept)
if rev_col and col_map.get('department'):
    fig, note = plots.bar_by(filtered, rev_col, col_map['department'], "Revenue by Department", "Identify top-selling departments.")
    render(fig, note)
if rev_col and col_map.get('category'):
    if col_map.get('gender'):
        fig, note = plots.stacked_bar_by(filtered, rev_col, col_map['category'], col_map['gender'], "Revenue by Category by Gender", "Category-gender mix analysis.")
    else:
        fig, note = plots.bar_by(filtered, rev_col, col_map['category'], "Revenue by Category", "Category mix analysis.")
    render(fig, note)
if rev_col and ('order_month' in filtered.columns):
    fig, note = plots.timeseries_monthly(filtered, col_map.get('order_datetime','order_date'), rev_col, "Monthly Revenue Trend", "Seasonality and trend.")
    render(fig, note)
if rev_col and col_map.get('gender') and col_map.get('age_group'):
    fig, note = plots.gender_age_breakdown(filtered, rev_col, col_map['gender'], col_map['age_group'], "Revenue by Gender & Age Group", "Cohort contribution analysis.")
    render(fig, note)
if rev_col and col_map.get('city'):
    fig, note = plots.bar_by(filtered, rev_col, col_map['city'], "Revenue by City", "Geographic contribution.")
    render(fig, note)
if rev_col and col_map.get('channel'):
    fig, note = plots.aov_by(filtered, rev_col, col_map['channel'], "Average Order Value by Channel", "Basket quality by channel.")
    render(fig, note)
if rev_col and col_map.get('store_format'):
    fig, note = plots.aov_by(filtered, rev_col, col_map['store_format'], "Average Order Value by Store Format", "Basket quality by format.")
    render(fig, note)

# New insights

# A) Pareto by Category (80/20)
if rev_col and col_map.get('category'):
    fig, note = plots.pareto_chart(filtered, rev_col, col_map['category'], "Pareto: Category Revenue Concentration", "Assortment concentration.")
    render(fig, note)

# B) Daypart heatmap (Day × Hour)
if rev_col and ('day_of_week' in filtered.columns) and ('hour_of_day' in filtered.columns):
    fig, note = plots.heatmap_pivot(filtered, rev_col, 'day_of_week', 'hour_of_day', "Revenue Heatmap: Day-of-Week × Hour", "Daypart optimization.")
    render(fig, note)

# C) City × Store Format heatmap
if rev_col and col_map.get('city') and col_map.get('store_format'):
    fig, note = plots.heatmap_pivot(filtered, rev_col, col_map['city'], col_map['store_format'], "Revenue Heatmap: City × Store Format", "Network mix pockets.")
    render(fig, note)

# D) AOV distribution (per-order)
per = per_order_metrics(filtered, col_map)
if per is not None and 'order_revenue' in per.columns:
    fig, note = plots.hist_distribution(per['order_revenue'], "Distribution: Order Revenue (AOV)", "Order Revenue (AED)", "Basket value dispersion.")
    render(fig, note)

# E) Units distribution (per-order if available, else line level)
if per is not None and 'order_units' in per.columns:
    fig, note = plots.hist_distribution(per['order_units'], "Distribution: Order Units", "Units per Order", "Pack size & basket depth.")
    render(fig, note)

# F) New vs Repeat customers share by month
nvr = new_vs_repeat_by_month(filtered, col_map)
if nvr is not None:
    per_orders, monthly = nvr
    import plotly.express as px
    fig = px.line(monthly, x='order_month', y='new_customer_share', markers=True, title="New Customer Share by Month")
    note = "Track the mix of new vs repeat customers; tailor acquisition vs loyalty spend accordingly."
    render(fig, note)

# G) Nationality group share (if available)
nat_col = col_map.get('nationality_group')
if rev_col and nat_col:
    fig, note = plots.donut_share(filtered, rev_col, nat_col, "Revenue Share by Nationality Group", "Offer localization & cultural moments.")
    render(fig, note)

st.markdown("---")
st.caption("© 2025 — Executive dashboard. Replace assets/logo.png for branding.")
