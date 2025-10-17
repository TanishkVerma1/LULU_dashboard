import streamlit as st
import pandas as pd
from pathlib import Path

from utils import load_data, data_quality, apply_filters, business_goal_from_point, generate_insights
from plots import (
    kpis, daily_revenue, category_treemap, brand_bar, revenue_by_city, store_revenue,
    heat_hour_day, discount_vs_qty, returns_by_category, age_bucket_bar, gender_pie, nationality_bar
)

try:
    from streamlit_plotly_events import plotly_events
except Exception:
    def plotly_events(fig, **kwargs):
        st.plotly_chart(fig, use_container_width=True)
        return []

st.set_page_config(page_title='Lulu Sales Dashboard Pro v3', page_icon=':bar_chart:', layout='wide')

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

show_city = len(cities) != 1
show_store = len(stores) != 1
show_brand = len(cats) == 1
show_category_mix = not show_brand

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
c4.markdown(f'<div class="kpi"><div class="t">Loyalty Orders</div><div class="v">{members if members is not None else "—"}</div></div>', unsafe_allow_html=True)

st.markdown('---')

col1, col2 = st.columns((2,1))
with col1:
    fig = daily_revenue(fdf)
    ev = plotly_events(fig, click_event=True, select_event=False)
    st.plotly_chart(fig, use_container_width=True)
    if ev:
        st.markdown(f'<div class="goal-box">📌 {business_goal_from_point("hour_day_heat", ev[0])}</div>', unsafe_allow_html=True)
with col2:
    if show_city:
        fig = revenue_by_city(fdf)
        ev = plotly_events(fig, click_event=True, select_event=False)
        st.plotly_chart(fig, use_container_width=True)
        if ev:
            st.markdown(f'<div class="goal-box">📌 {business_goal_from_point("city_revenue", ev[0])}</div>', unsafe_allow_html=True)
    else:
        fig = store_revenue(fdf) if show_store else returns_by_category(fdf)
        st.plotly_chart(fig, use_container_width=True)

col3, col4 = st.columns(2)
with col3:
    if show_brand:
        base = fdf[fdf['category']==cats[0]] if len(cats)==1 else fdf
        fig = brand_bar(base)
        ev = plotly_events(fig, click_event=True, select_event=False)
        st.plotly_chart(fig, use_container_width=True)
        if ev:
            st.markdown(f'<div class="goal-box">📌 {business_goal_from_point("category_revenue", ev[0])}</div>', unsafe_allow_html=True)
    elif show_category_mix:
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

st.markdown("### Customer Demographics")
d1c, d2c, d3c = st.columns(3)
with d1c:
    st.plotly_chart(age_bucket_bar(fdf), use_container_width=True)
with d2c:
    gp = gender_pie(fdf)
    ev = plotly_events(gp, click_event=True, select_event=False)
    st.plotly_chart(gp, use_container_width=True)
    if ev:
        st.markdown(f'<div class="goal-box">📌 {business_goal_from_point("demographic", ev[0])}</div>', unsafe_allow_html=True)
with d3c:
    st.plotly_chart(nationality_bar(fdf), use_container_width=True)

r1, r2 = st.columns(2)
with r1:
    st.plotly_chart(heat_hour_day(fdf), use_container_width=True)
with r2:
    if 'returned' in fdf.columns and (fdf['returned'].sum() > 0):
        st.plotly_chart(returns_by_category(fdf), use_container_width=True)

st.markdown("### Insights & Recommended Actions")
for txt in generate_insights(fdf):
    st.markdown(f'<div class="insight">💡 {txt}</div>', unsafe_allow_html=True)

st.markdown('---')
st.subheader('Ask-to-Compare (Choose a question)')

questions = [
    'Compare revenue across selected cities over time',
    'Compare top categories within the selected city (or overall if none)',
    'Compare revenue by store formats across selected filters',
    'Compare loyalty vs non-loyalty AOV',
    'Compare return value across chosen categories'
]
q = st.selectbox('Question', questions, index=0)

import plotly.express as px

if q == questions[0]:
    g = fdf.groupby([pd.Grouper(key='order_datetime', freq='W'), 'city'])['line_value_aed'].sum().reset_index()
    st.plotly_chart(px.line(g, x='order_datetime', y='line_value_aed', color='city', title='Weekly Revenue by City'), use_container_width=True)
elif q == questions[1]:
    base = fdf if len(cities)==0 else fdf[fdf['city'].isin(cities)]
    g = base.groupby('category')['line_value_aed'].sum().sort_values(ascending=False).head(10).reset_index()
    st.plotly_chart(px.bar(g, x='category', y='line_value_aed', title='Top Categories (Contextual)'), use_container_width=True)
elif q == questions[2]:
    g = fdf.groupby('store_format')['line_value_aed'].sum().reset_index()
    st.plotly_chart(px.bar(g, x='store_format', y='line_value_aed', title='Revenue by Store Format'), use_container_width=True)
elif q == questions[3]:
    if 'loyalty_member' in fdf.columns:
        g = fdf.groupby('loyalty_member')['line_value_aed'].mean().reset_index()
        g['segment'] = g['loyalty_member'].map({1:'Member',0:'Non-member'})
        st.plotly_chart(px.bar(g, x='segment', y='line_value_aed', title='AOV: Loyalty vs Non-Loyalty'), use_container_width=True)
    else:
        st.info('Loyalty data not available.')
elif q == questions[4]:
    if 'returned' in fdf.columns:
        g = fdf.groupby('category')['return_value_aed'].sum().sort_values(ascending=False).head(10).reset_index()
        st.plotly_chart(px.bar(g, x='category', y='return_value_aed', title='Return Value by Category (Top 10)'), use_container_width=True)
    else:
        st.info('Return data not available.')

st.caption('© Lulu Sales Dashboard Pro v3 – Conditional, Insightful, Global-ready.')
