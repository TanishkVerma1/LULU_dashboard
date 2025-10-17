import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

from utils import load_data, quality_checks, filter_data, simulate_rows
from plots import (
    kpi_cards, time_series, category_mix_treemap, stacked_bar_category_month,
    heatmap_hour_day, scatter_price_qty, city_ranked_bar, inventory_stockout_table,
    returns_bar, loyalty_vs_revenue, discount_vs_conversion
)

# Fallback if streamlit-plotly-events isn't available
try:
    from streamlit_plotly_events import plotly_events
except Exception:
    def plotly_events(fig, **kwargs):
        # Render and return empty click data
        st.plotly_chart(fig, use_container_width=True)
        return []

st.set_page_config(page_title="Lulu UAE – Executive Dashboard", page_icon=":bar_chart:", layout="wide")

# --- Robust CSS loader (works on Streamlit Cloud too) ---
BASE_DIR = Path(__file__).resolve().parent
css_path = BASE_DIR / "assets" / "styles.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

# --- SIDEBAR ---
st.sidebar.image(str(BASE_DIR / "assets" / "logo.png"), width=140)
st.sidebar.title("Filters")

data_path = BASE_DIR / "data" / "lulu_uae_master_2000.csv"
df = load_data(str(data_path))

# Optionally simulate larger dataset for a richer demo
simulate = st.sidebar.checkbox("Simulate larger dataset (for demo)", value=False)
if simulate:
    target_rows = st.sidebar.slider("Target rows", 5000, 20000, 10000, step=1000)
    df = simulate_rows(df, target_rows=target_rows)

min_date = pd.to_datetime(df["order_datetime"]).min()
max_date = pd.to_datetime(df["order_datetime"]).max()

date_range = st.sidebar.date_input("Date range", (min_date.date(), max_date.date()))
if isinstance(date_range, tuple) or isinstance(date_range, list):
    start_dt = pd.to_datetime(date_range[0])
    end_dt = pd.to_datetime(date_range[1]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
else:
    start_dt = min_date
    end_dt = max_date

cities = st.sidebar.multiselect("City", sorted(df["city"].dropna().unique().tolist()))
categories = st.sidebar.multiselect("Category", sorted(df["category"].dropna().unique().tolist()))
stores = st.sidebar.multiselect("Store format", sorted(df["store_format"].dropna().unique().tolist()))
topn = st.sidebar.slider("Top-N (tables/charts)", 5, 30, 10)

page = st.sidebar.selectbox("Section", ["Overview (KPI)", "Sales & Revenue", "Customer Segments & Behavior", "Inventory / Stock", "Geography / City Insights", "Actions & Recommendations"])

# Apply filters
fdf = filter_data(df, date_range=(start_dt, end_dt), cities=cities, categories=categories, stores=stores)

# Data quality panel
with st.expander("Data Quality & Anomaly Checks", expanded=False):
    issues = quality_checks(fdf)
    if issues:
        for i in issues:
            st.markdown(f"- {i}")
    else:
        st.markdown(":white_check_mark: No major data issues detected.")

# --- KPI Row ---
kpis = kpi_cards(fdf)
col1, col2, col3, col4, col5 = st.columns(5)
col1.markdown('<div class="kpi-card"><div class="kpi-title">Total Revenue (AED)</div><div class="kpi-value">{:,.0f}</div></div>'.format(kpis["total_rev"]), unsafe_allow_html=True)
col2.markdown('<div class="kpi-card"><div class="kpi-title">Avg Basket / Order (AED)</div><div class="kpi-value">{:,.0f}</div></div>'.format(kpis["avg_basket"]), unsafe_allow_html=True)
col3.markdown('<div class="kpi-card"><div class="kpi-title">Avg Discount Rate</div><div class="kpi-value">{:.1%}</div></div>'.format(kpis["avg_discount_rate"]), unsafe_allow_html=True)
col4.markdown('<div class="kpi-card"><div class="kpi-title">Orders</div><div class="kpi-value">{:,.0f}</div></div>'.format(kpis["orders"]), unsafe_allow_html=True)
col5.markdown('<div class="kpi-card"><div class="kpi-title">Unique Customers</div><div class="kpi-value">{}</div></div>'.format(kpis["unique_customers"] if kpis["unique_customers"] is not None else "—"), unsafe_allow_html=True)

def show_contextual_msg(click_data, entity_label:str):
    if click_data:
        pt = click_data[0]
        label = pt.get("label") or pt.get("x") or pt.get("y") or pt.get("hovertext") or str(pt)
        st.info(f"Recommendation for **{entity_label}: {label}** → If high discount but low quantity, reduce discount depth and improve visibility. If high revenue & frequent stock-outs, prioritize replenishment and expand assortment.")
    else:
        st.caption("Tip: Click chart elements to see contextual recommendations.")

# --- PAGES ---
if page == "Overview (KPI)":
    c1, c2 = st.columns((2,1), gap="large")
    with c1:
        fig_ts = time_series(fdf)
        ev = plotly_events(fig_ts, click_event=True, select_event=False, override_height=450, override_width="100%")
        # If fallback is in use, plotly_events already rendered the chart.
        if ev == []:
            pass
        else:
            st.plotly_chart(fig_ts, use_container_width=True)
        show_contextual_msg(ev, "Time Slice")
    with c2:
        fig_pie = loyalty_vs_revenue(fdf)
        ev = plotly_events(fig_pie, click_event=True, select_event=False, override_height=450, override_width="100%")
        if ev == []:
            pass
        else:
            st.plotly_chart(fig_pie, use_container_width=True)
        show_contextual_msg(ev, "Loyalty Segment")

    colA, colB = st.columns(2)
    with colA:
        fig_cat_month = stacked_bar_category_month(fdf)
        ev = plotly_events(fig_cat_month, click_event=True, select_event=False)
        if ev == []:
            pass
        else:
            st.plotly_chart(fig_cat_month, use_container_width=True)
        show_contextual_msg(ev, "Category/Month")
    with colB:
        fig_returns = returns_bar(fdf)
        ev = plotly_events(fig_returns, click_event=True, select_event=False)
        if ev == []:
            pass
        else:
            st.plotly_chart(fig_returns, use_container_width=True)
        show_contextual_msg(ev, "Category (Returns)")

elif page == "Sales & Revenue":
    col1, col2 = st.columns(2)
    with col1:
        fig1 = category_mix_treemap(fdf)
        ev = plotly_events(fig1, click_event=True, select_event=False)
        if ev == []:
            pass
        else:
            st.plotly_chart(fig1, use_container_width=True)
        show_contextual_msg(ev, "Category")
    with col2:
        fig2 = discount_vs_conversion(fdf)
        ev = plotly_events(fig2, click_event=True, select_event=False)
        if ev == []:
            pass
        else:
            st.plotly_chart(fig2, use_container_width=True)
        show_contextual_msg(ev, "Category (Discount vs Qty)")

    st.plotly_chart(scatter_price_qty(fdf), use_container_width=True)

elif page == "Customer Segments & Behavior":
    col1, col2 = st.columns(2)
    with col1:
        if "age" in fdf.columns:
            g = fdf.copy()
            g["age_bucket"] = pd.cut(g["age"], bins=[0,18,25,35,45,60,120], labels=["<18","18-25","26-35","36-45","46-60","60+"])
            gg = g.groupby("age_bucket", as_index=False)["line_value_aed"].sum()
            import plotly.express as px
            fig = px.bar(gg, x="age_bucket", y="line_value_aed", title="Revenue by Age Bucket")
            ev = plotly_events(fig, click_event=True, select_event=False)
            if ev == []:
                pass
            else:
                st.plotly_chart(fig, use_container_width=True)
            show_contextual_msg(ev, "Age Bucket")
    with col2:
        if "gender" in fdf.columns:
            import plotly.express as px
            gg = fdf.groupby("gender", as_index=False)["line_value_aed"].sum()
            fig = px.pie(gg, names="gender", values="line_value_aed", title="Revenue by Gender")
            ev = plotly_events(fig, click_event=True, select_event=False)
            if ev == []:
                pass
            else:
                st.plotly_chart(fig, use_container_width=True)
            show_contextual_msg(ev, "Gender")

    st.plotly_chart(heatmap_hour_day(fdf), use_container_width=True)

elif page == "Inventory / Stock":
    st.subheader("Stock-outs & High-Velocity SKUs")
    tbl = inventory_stockout_table(fdf, top_n=topn)
    if not tbl.empty:
        st.dataframe(tbl, use_container_width=True)
    else:
        st.info("No stock-out data available.")

    st.plotly_chart(returns_bar(fdf), use_container_width=True)

elif page == "Geography / City Insights":
    st.plotly_chart(city_ranked_bar(fdf), use_container_width=True)

    g = fdf.groupby(["city","category"], as_index=False)["line_value_aed"].sum()
    top_cities = g.groupby("city")["line_value_aed"].sum().sort_values(ascending=False).head(topn).index.tolist()
    gg = g[g["city"].isin(top_cities)]
    import plotly.express as px
    fig = px.bar(gg, x="city", y="line_value_aed", color="category", barmode="stack", title="Top Cities – Revenue by Category")
    ev = plotly_events(fig, click_event=True, select_event=False)
    if ev == []:
        pass
    else:
        st.plotly_chart(fig, use_container_width=True)
    show_contextual_msg(ev, "City/Category")

elif page == "Actions & Recommendations":
    st.markdown("### Top Data-Driven Actions (based on current filters)")
    actions = []
    cat_share = fdf.groupby("category")["line_value_aed"].sum().sort_values(ascending=False)
    if len(cat_share)>0:
        top_share = cat_share.head(3).sum()/cat_share.sum()
        if top_share>0.5:
            actions.append(f"- Top 3 categories contribute {top_share:.0%} of revenue → Secure supply & expand assortment in these categories.")
    if "stock_out_flag" in fdf.columns and fdf["stock_out_flag"].sum()>0:
        actions.append("- Frequent stock-outs observed → Increase safety stock and improve replenishment cadence for high-velocity SKUs.")
    if {"discount_aed","quantity"}.issubset(fdf.columns):
        corr = fdf["discount_aed"].corr(fdf["quantity"])
        if pd.notna(corr):
            actions.append(f"- Discount ↔ Quantity correlation = {corr:.2f} → Optimize discount depth (test tiered discounts).")
    if {"day_of_week","hour_of_day"}.issubset(fdf.columns):
        grid = fdf.groupby(["day_of_week","hour_of_day"])["line_value_aed"].sum().reset_index()
        if not grid.empty:
            peak = grid.sort_values("line_value_aed", ascending=False).iloc[0]
            actions.append(f"- Peak demand at {peak['day_of_week']} {int(peak['hour_of_day']):02d}:00 → Align staffing & timed promotions.")
    if "city" in fdf.columns:
        city_rev = fdf.groupby("city")["line_value_aed"].sum()
        if len(city_rev)>=2 and city_rev.max() > 2*city_rev.mean():
            top_city = city_rev.idxmax()
            actions.append(f"- Revenue concentrated in {top_city} → Run localized campaigns in underpenetrated cities.")

    if not actions:
        actions = ["- No strong signals under current filters. Broaden the selection."]
    for a in actions:
        st.markdown(a)

    md = "# Exported Insights\n\n" + "\n".join(actions)
    st.download_button("Export Insights (Markdown)", data=md, file_name="insights_export.md", mime="text/markdown")

st.caption("© Lulu UAE Executive Dashboard – Streamlit")