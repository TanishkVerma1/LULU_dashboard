
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
from utils import standardize_columns, infer_columns, engineer_features, kpis, safe_num
import plots

st.set_page_config(page_title="Lulu Executive Dashboard", layout="wide")

# Simple CSS for outcome cards
st.markdown(
    """
    <style>
    .outcome-card {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        border: 1px solid #f59e0b33;
        padding: 14px 16px;
        border-radius: 14px;
        margin: 8px 0 24px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        font-size: 0.98rem;
    }
    .outcome-card strong { color: #92400e; }
    .h2-pad { margin-top: 0.5rem; }
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
def load_data(user_file=None):
    if user_file is not None:
        df = pd.read_csv(user_file)
    else:
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
st.caption("Executive-ready insights. Every chart includes a clear, action-oriented idea.")

with st.sidebar:
    st.header("Filters")

df, col_map = load_data()

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
    st.plotly_chart(fig, use_container_width=True)
    outcome_card(note)

# 1. Revenue by Department
if rev_col and col_map.get('department'):
    fig, note = plots.bar_by(filtered, rev_col, col_map['department'], "Revenue by Department", "Identify top-selling departments.")
    render(fig, note)

# 2. Revenue by Category (Gender stacked if available)
if rev_col and col_map.get('category'):
    if col_map.get('gender'):
        fig, note = plots.stacked_bar_by(filtered, rev_col, col_map['category'], col_map['gender'], "Revenue by Category by Gender", "Category-gender mix analysis.")
    else:
        fig, note = plots.bar_by(filtered, rev_col, col_map['category'], "Revenue by Category", "Category mix analysis.")
    render(fig, note)

# 3. Monthly Trend
if rev_col and ('order_month' in filtered.columns):
    fig, note = plots.timeseries_monthly(filtered, col_map.get('order_datetime','order_date'), rev_col, "Monthly Revenue Trend", "Seasonality and trend.")
    render(fig, note)

# 4. Cohorts: Gender × Age Group
if rev_col and col_map.get('gender') and col_map.get('age_group'):
    fig, note = plots.gender_age_breakdown(filtered, rev_col, col_map['gender'], col_map['age_group'], "Revenue by Gender & Age Group", "Cohort contribution analysis.")
    render(fig, note)

# 5. Geography
if rev_col and col_map.get('city'):
    fig, note = plots.bar_by(filtered, rev_col, col_map['city'], "Revenue by City", "Geographic contribution.")
    render(fig, note)

# 6. AOV by Channel / Store Format
if rev_col and col_map.get('channel'):
    fig, note = plots.aov_by(filtered, rev_col, col_map['channel'], "Average Order Value by Channel", "Basket quality by channel.")
    render(fig, note)
if rev_col and col_map.get('store_format'):
    fig, note = plots.aov_by(filtered, rev_col, col_map['store_format'], "Average Order Value by Store Format", "Basket quality by format.")
    render(fig, note)

# 7. Brands
if rev_col and col_map.get('brand'):
    fig, note = plots.bar_simple(filtered, rev_col, col_map['brand'], "Top Brands by Revenue", "Brand prioritization.")
    render(fig, note)

# 8. Day-of-Week and Hour-of-Day bars
if rev_col:
    fig, note = plots.bar_dayofweek(filtered, rev_col, "Revenue by Day of Week", "Weekly pattern analysis.")
    if fig is not None: render(fig, note)
    fig, note = plots.bar_hourofday(filtered, rev_col, "Revenue by Hour of Day", "Daypart analysis.")
    if fig is not None: render(fig, note)

# 9. Donut: Channel share
if rev_col and col_map.get('channel'):
    fig, note = plots.donut_share(filtered, rev_col, col_map['channel'], "Revenue Share by Channel", "Channel mix and growth bets.")
    render(fig, note)

# 10. Units by Category (Basket volume)
if qty_col and col_map.get('category'):
    fig, note = plots.qty_by_group(filtered, qty_col, col_map['category'], "Units Sold by Category", "Volume drivers and pack strategy.")
    render(fig, note)

# 11. Discount vs AOV (if discount column exists)
disc_candidates = [c for c in ["discount_aed", "discount", "promo", "markdown"] if c in filtered.columns]
if disc_candidates and rev_col:
    fig, note = plots.discount_vs_aov(filtered, disc_candidates[0], rev_col, "Discount Level vs Average Order Value", "Promo efficiency.")
    if fig is not None: render(fig, note)

st.markdown("---")
st.caption("© 2025 — Executive dashboard. Replace assets/logo.png for branding.")

