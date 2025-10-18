
import streamlit as st
import pandas as pd
import numpy as np
from utils import standardize_columns, infer_columns, engineer_features, kpis, safe_num
import plots

st.set_page_config(page_title="Lulu Executive Dashboard", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv("data/lulu_uae_master_2000.csv")
    df = standardize_columns(df)
    col_map = infer_columns(df)
    df = engineer_features(df, col_map)
    return df, col_map

df, col_map = load_data()

st.title("🛒 Lulu Executive Dashboard")
st.caption("Interactive analytics with auto-generated business outcomes below every chart.")

# Filters
with st.sidebar:
    st.header("Filters")
    # dynamic filter controls
    # city, department, category, brand, channel, gender, age_group
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
    def apply(col, sel):
        if col and sel and "All" not in sel:
            return df[df[col].astype(str).isin(sel)]
        return df
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

# Chart 1: Revenue by Department
if rev_col and col_map.get('department'):
    fig, note = plots.bar_by(filtered, rev_col, col_map['department'], "Revenue by Department", "Identify top-selling departments.")
    st.plotly_chart(fig, use_container_width=True)
    st.caption(note)

# Chart 2: Revenue by Category (stacked by Gender if available)
if rev_col and col_map.get('category'):
    if col_map.get('gender'):
        fig, note = plots.stacked_bar_by(filtered, rev_col, col_map['category'], col_map['gender'], "Revenue by Category by Gender", "Category-gender mix analysis.")
    else:
        fig, note = plots.bar_by(filtered, rev_col, col_map['category'], "Revenue by Category", "Category mix analysis.")
    st.plotly_chart(fig, use_container_width=True)
    st.caption(note)

# Chart 3: Monthly Revenue Trend
if rev_col and ('order_month' in filtered.columns):
    fig, note = plots.timeseries_monthly(filtered, col_map.get('order_datetime','order_date'), rev_col, "Monthly Revenue Trend", "Seasonality and trend.")
    st.plotly_chart(fig, use_container_width=True)
    st.caption(note)

# Chart 4: Gender x Age Group revenue
if rev_col and col_map.get('gender') and col_map.get('age_group'):
    fig, note = plots.gender_age_breakdown(filtered, rev_col, col_map['gender'], col_map['age_group'], "Revenue by Gender & Age Group", "Cohort contribution analysis.")
    st.plotly_chart(fig, use_container_width=True)
    st.caption(note)

# Chart 5: Revenue by City
if rev_col and col_map.get('city'):
    fig, note = plots.bar_by(filtered, rev_col, col_map['city'], "Revenue by City", "Geographic contribution.")
    st.plotly_chart(fig, use_container_width=True)
    st.caption(note)

# Chart 6: AOV by Channel / Store Format
if rev_col and col_map.get('channel'):
    fig, note = plots.aov_by(filtered, rev_col, col_map['channel'], "Average Order Value by Channel", "Basket quality by channel.")
    st.plotly_chart(fig, use_container_width=True)
    st.caption(note)
if rev_col and col_map.get('store_format'):
    fig, note = plots.aov_by(filtered, rev_col, col_map['store_format'], "Average Order Value by Store Format", "Basket quality by format.")
    st.plotly_chart(fig, use_container_width=True)
    st.caption(note)

# Chart 7: Price vs Quantity (elasticity proxy) if both exist
price_col = col_map.get('unit_price'); qty_col = col_map.get('quantity')
if price_col and qty_col:
    fig, note = plots.scatter_price_qty(filtered, price_col, qty_col, "Price vs Quantity (Elasticity Proxy)", "Price sensitivity analysis.")
    st.plotly_chart(fig, use_container_width=True)
    st.caption(note)

st.markdown("---")
st.caption("© 2025 — Auto-generated dashboard. Replace logo in assets/ and deploy to Streamlit Cloud.")
