
import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
from utils import standardize_columns, infer_columns, engineer_features, kpis, safe_num
import plots

st.set_page_config(page_title="Lulu Executive Dashboard", layout="wide")

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DEFAULT_DATA_FILE = DATA_DIR / "lulu_uae_master_2000.csv"

@st.cache_data
def load_data(user_file=None):
    # Resolve file path
    if user_file is not None:
        df = pd.read_csv(user_file)
    else:
        # Try file relative to this script
        if DEFAULT_DATA_FILE.exists():
            df = pd.read_csv(DEFAULT_DATA_FILE)
        else:
            # Also try repo-root "data" in case app is run from repo root with nested app path
            alt_path = Path("data") / "lulu_uae_master_2000.csv"
            if alt_path.exists():
                df = pd.read_csv(alt_path)
            else:
                raise FileNotFoundError(f"Could not find data file at {DEFAULT_DATA_FILE} or {alt_path}. "
                                        "Ensure your repository includes /lulu_executive_dashboard/data/lulu_uae_master_2000.csv "
                                        "or upload a CSV using the control in the sidebar.")
    df = standardize_columns(df)
    col_map = infer_columns(df)
    df = engineer_features(df, col_map)
    return df, col_map

st.title("🛒 Lulu Executive Dashboard")
st.caption("Interactive analytics with auto-generated business outcomes below every chart.")

with st.sidebar:
    st.header("Data Source")
    st.write("If the packaged data file isn't found, upload your CSV here:")
    uploaded = st.file_uploader("Upload CSV", type=["csv"], key="user_csv", help="Your transactional dataset")

try:
    df, col_map = load_data(uploaded)
except Exception as e:
    st.error(f"{e}")
    st.stop()

# Filters
with st.sidebar:
    st.header("Filters")
    def pick(col_key, label):
        col = col_map.get(col_key) or (col_key if col_key in df.columns else None)
        if col and col in df.columns:
            vals = ["All"] + sorted([str(x) for x in df[col].dropna().unique()])
            return col, st.multiselect(label, vals, default=["All"])
        return None, None

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

# Download filtered data
with st.sidebar:
    st.download_button(
        "⬇️ Download filtered CSV",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="filtered_export.csv",
        mime="text/csv"
    )

# KPI tiles
rev_col = col_map.get('line_value')
qty_col = col_map.get('quantity')
st.subheader("Key Performance Indicators")
k = kpis(filtered, col_map)
cols = st.columns(len(k) or 1)
for (name, val), c in zip(k.items(), cols):
    c.metric(name, safe_num(val))

st.markdown("---")

def show_chart(fig, note, filename):
    st.plotly_chart(fig, use_container_width=True)
    st.caption(note)
    # Export image
    try:
        png = fig.to_image(format="png")
        st.download_button("Download chart PNG", data=png, file_name=filename, mime="image/png")
    except Exception:
        st.info("Install 'kaleido' in requirements to enable PNG downloads.")

# Chart 1: Revenue by Department
if rev_col and col_map.get('department'):
    fig, note = plots.bar_by(filtered, rev_col, col_map['department'], "Revenue by Department", "Identify top-selling departments.")
    show_chart(fig, note, "revenue_by_department.png")

# Chart 2: Revenue by Category (stacked by Gender if available)
if rev_col and col_map.get('category'):
    if col_map.get('gender'):
        fig, note = plots.stacked_bar_by(filtered, rev_col, col_map['category'], col_map['gender'], "Revenue by Category by Gender", "Category-gender mix analysis.")
    else:
        fig, note = plots.bar_by(filtered, rev_col, col_map['category'], "Revenue by Category", "Category mix analysis.")
    show_chart(fig, note, "revenue_by_category.png")

# Chart 3: Monthly Revenue Trend
if rev_col and ('order_month' in filtered.columns):
    fig, note = plots.timeseries_monthly(filtered, col_map.get('order_datetime','order_date'), rev_col, "Monthly Revenue Trend", "Seasonality and trend.")
    show_chart(fig, note, "monthly_revenue_trend.png")

# Chart 4: Gender x Age Group revenue
if rev_col and col_map.get('gender') and col_map.get('age_group'):
    fig, note = plots.gender_age_breakdown(filtered, rev_col, col_map['gender'], col_map['age_group'], "Revenue by Gender & Age Group", "Cohort contribution analysis.")
    show_chart(fig, note, "gender_age_revenue.png")

# Chart 5: Revenue by City
if rev_col and col_map.get('city'):
    fig, note = plots.bar_by(filtered, rev_col, col_map['city'], "Revenue by City", "Geographic contribution.")
    show_chart(fig, note, "revenue_by_city.png")

# Chart 6: AOV by Channel / Store Format
if rev_col and col_map.get('channel'):
    fig, note = plots.aov_by(filtered, rev_col, col_map['channel'], "Average Order Value by Channel", "Basket quality by channel.")
    show_chart(fig, note, "aov_by_channel.png")
if rev_col and col_map.get('store_format'):
    fig, note = plots.aov_by(filtered, rev_col, col_map['store_format'], "Average Order Value by Store Format", "Basket quality by format.")
    show_chart(fig, note, "aov_by_format.png")

# New Chart 7: Top Brands by Revenue
if rev_col and col_map.get('brand'):
    fig, note = plots.bar_by(filtered, rev_col, col_map['brand'], "Top Brands by Revenue", "Brand contribution and focus.")
    show_chart(fig, note, "revenue_by_brand.png")

# New Chart 8: Daypart x Day-of-Week Heatmap (if time engineered)
if rev_col and ('day_of_week' in filtered.columns) and ('hour_of_day' in filtered.columns):
    import plotly.express as px
    pivot = filtered.pivot_table(values=rev_col, index='day_of_week', columns='hour_of_day', aggfunc='sum', fill_value=0)
    order_days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    pivot = pivot.reindex(order_days)
    fig = px.imshow(pivot, aspect='auto', title="Revenue Heatmap: Day-of-Week × Hour")
    note = "Highlight peak dayparts to optimize staffing, replenishment, and time-bound promotions."
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"**Business outcome idea:** {note} (Context: Concentrate labor and flash deals on hot dayparts.)")

st.markdown("---")
st.caption("© 2025 — Auto-generated dashboard. Replace logo in assets/ and deploy to Streamlit Cloud.")
