
import streamlit as st
import pandas as pd
from pathlib import Path

from utils import load_data, data_quality, apply_filters, business_goal_from_point
from plots import kpis, daily_revenue, category_treemap, revenue_by_city, heat_hour_day, discount_vs_qty, returns_by_category

try:
    from streamlit_plotly_events import plotly_events
except Exception:
    def plotly_events(fig, **kwargs):
        st.plotly_chart(fig, use_container_width=True)
        return []

st.set_page_config(page_title='Lulu Sales Dashboard Pro', page_icon=':chart_with_upwards_trend:', layout='wide')

BASE = Path(__file__).resolve().parent
css = (BASE / 'assets' / 'styles.css')
if css.exists():
    st.markdown(f"<style>{css.read_text()}</style>", unsafe_allow_html=True)

st.sidebar.image(str(BASE / 'assets' / 'logo.png'), width=120)
st.sidebar.header('Filters')

df = load_data(str(BASE / 'data' / 'lulu_uae_master_2000.csv'))
mind = pd.to_datetime(df['order_datetime']).min().date()
maxd = pd.to_datetime(df['order_datetime']).max().date()

dr = st.sidebar.date_input('Date range', (mind, maxd))
if isinstance(dr, (tuple, list)):
    d1, d2 = dr
else:
    d1, d2 = mind, maxd

cities = st.sidebar.multiselect('City', sorted(df['city'].dropna().unique().tolist()))
cats = st.sidebar.multiselect('Category', sorted(df['category'].dropna().unique().tolist()))
stores = st.sidebar.multiselect('Store', sorted(df['store_format'].dropna().unique().tolist()))

fdf = apply_filters(df, date_range=(pd.to_datetime(d1), pd.to_datetime(d2) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)),
                    city=cities, category=cats, store=stores)

with st.expander('Data Quality & Anomalies', expanded=False):
    issues = data_quality(fdf)
    if issues:
        for i in issues:
            st.markdown(f"- {i}")
    else:
        st.caption('No major issues found.')

tot, orders, aov, members = kpis(fdf)
c1, c2, c3, c4 = st.columns(4)
c1.markdown(f'<div class="kpi"><div class="t">Total Revenue (AED)</div><div class="v">{tot:,.0f}</div></div>', unsafe_allow_html=True)
c2.markdown(f'<div class="kpi"><div class="t">Orders</div><div class="v">{orders:,}</div></div>', unsafe_allow_html=True)
c3.markdown(f'<div class="kpi"><div class="t">Avg Order Value</div><div class="v">{aov:,.0f}</div></div>', unsafe_allow_html=True)
c4.markdown(f'<div class="kpi"><div class="t">Loyalty Members (orders)</div><div class="v">{members if members is not None else "—"}</div></div>', unsafe_allow_html=True)

st.markdown('---')

col1, col2 = st.columns((2,1))
with col1:
    fig = daily_revenue(fdf)
    ev = plotly_events(fig, click_event=True, select_event=False)
    st.plotly_chart(fig, use_container_width=True)
    if ev:
        st.markdown(f'<div class="goal-box">📌 {business_goal_from_point("hour_day_heat", ev[0])}</div>', unsafe_allow_html=True)
with col2:
    fig = revenue_by_city(fdf)
    ev = plotly_events(fig, click_event=True, select_event=False)
    st.plotly_chart(fig, use_container_width=True)
    if ev:
        st.markdown(f'<div class="goal-box">📌 {business_goal_from_point("city_revenue", ev[0])}</div>', unsafe_allow_html=True)

col3, col4 = st.columns(2)
with col3:
    fig = category_treemap(fdf)
    ev = plotly_events(fig, click_event=True, select_event=False)
    st.plotly_chart(fig, use_container_width=True)
    if ev:
        st.markdown(f'<div class="goal-box">📌 {business_goal_from_point("category_revenue", ev[0])}</div>', unsafe_allow_html=True)
with col4:
    fig = discount_vs_qty(fdf)
    ev = plotly_events(fig, click_event=True, select_event=False)
    st.plotly_chart(fig, use_container_width=True)
    if ev:
        ev[0]['y_median'] = fdf.groupby('category')['quantity'].sum().median()
        st.markdown(f'<div class="goal-box">📌 {business_goal_from_point("discount_vs_qty", ev[0])}</div>', unsafe_allow_html=True)

col5, col6 = st.columns(2)
with col5:
    fig = returns_by_category(fdf)
    st.plotly_chart(fig, use_container_width=True)
with col6:
    fig = heat_hour_day(fdf)
    ev = plotly_events(fig, click_event=True, select_event=False)
    st.plotly_chart(fig, use_container_width=True)
    if ev:
        st.markdown(f'<div class="goal-box">📌 {business_goal_from_point("hour_day_heat", ev[0])}</div>', unsafe_allow_html=True)

st.caption('© Lulu Sales Dashboard Pro – Simple. Informative. Actionable.')
