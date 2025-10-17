
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def kpis(df: pd.DataFrame):
    total_rev = float(df['line_value_aed'].sum())
    orders = int(df['order_id'].nunique())
    avg_order = total_rev / orders if orders else 0.0
    members = df['loyalty_member'].fillna(0).astype(int).sum() if 'loyalty_member' in df.columns else None
    return total_rev, orders, avg_order, members

def daily_revenue(df: pd.DataFrame):
    g = df.groupby(pd.Grouper(key='order_datetime', freq='D'))['line_value_aed'].sum().reset_index()
    fig = px.line(g, x='order_datetime', y='line_value_aed', markers=True, title='Daily Revenue')
    fig.update_layout(hovermode='x unified')
    return fig

def category_treemap(df: pd.DataFrame):
    g = df.groupby(['department','category'], as_index=False)['line_value_aed'].sum()
    return px.treemap(g, path=['department','category'], values='line_value_aed', title='Category Mix (Revenue)')

def revenue_by_city(df: pd.DataFrame):
    g = df.groupby('city', as_index=False)['line_value_aed'].sum().sort_values('line_value_aed', ascending=False)
    return px.bar(g, x='city', y='line_value_aed', title='Revenue by City')

def heat_hour_day(df: pd.DataFrame):
    g = df.groupby(['day_of_week','hour_of_day'], as_index=False)['line_value_aed'].sum()
    p = g.pivot(index='day_of_week', columns='hour_of_day', values='line_value_aed').fillna(0.0)
    order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    p = p.reindex(order)
    fig = go.Figure(data=go.Heatmap(z=p.values, x=list(p.columns), y=list(p.index), coloraxis='coloraxis'))
    fig.update_layout(title='Revenue Heatmap (Hour × Day)', coloraxis_colorscale='Blues')
    return fig

def discount_vs_qty(df: pd.DataFrame):
    g = df.groupby('category', as_index=False).agg(avg_discount=('discount_aed','mean'),
                                                   qty=('quantity','sum'),
                                                   revenue=('line_value_aed','sum'))
    fig = px.scatter(g, x='avg_discount', y='qty', size='revenue', hover_name='category', title='Discount vs Quantity (by Category)')
    fig.update_traces(customdata=[g['qty'].median()]*len(g))
    return fig

def returns_by_category(df: pd.DataFrame):
    if 'returned' not in df.columns:
        return go.Figure()
    g = df.groupby('category', as_index=False).agg(returns=('returned','sum'), lost_value=('return_value_aed','sum'))
    return px.bar(g.sort_values('lost_value', ascending=False), x='category', y='lost_value', title='Return Value by Category')
