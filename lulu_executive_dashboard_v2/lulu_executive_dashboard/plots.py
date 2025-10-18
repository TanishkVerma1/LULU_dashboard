
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils import explain_lift, outcome_sentence

def bar_by(df, value_col, group_col, title, note_context, top_n=15):
    g = df.groupby(group_col, dropna=False)[value_col].sum().nlargest(top_n).reset_index()
    fig = px.bar(g, x=group_col, y=value_col, title=title)
    fig.update_layout(xaxis_title=group_col.replace('_',' ').title(), yaxis_title=value_col.replace('_',' ').title())
    note = explain_lift(df, group_col, value_col)
    # Actionable idea template
    action = f"Allocate shelf space, promotions, and inventory toward top {group_col} while testing targeted offers to lift the long tail."
    return fig, outcome_sentence(note_context + ' ' + note, action)

def stacked_bar_by(df, value_col, group_col, color_col, title, note_context, top_n=12):
    g = df.groupby([group_col, color_col], dropna=False)[value_col].sum().reset_index()
    # keep top_n groups
    tops = g.groupby(group_col)[value_col].sum().nlargest(top_n).index
    g = g[g[group_col].isin(tops)]
    fig = px.bar(g, x=group_col, y=value_col, color=color_col, title=title, barmode='stack')
    fig.update_layout(xaxis_title=group_col.replace('_',' ').title(), yaxis_title=value_col.replace('_',' ').title(), legend_title=color_col.replace('_',' ').title())
    note = f"{group_col} mix varies by {color_col}. Focus on underpenetrated segments within high-value {group_col}."
    action = f"Run segment-specific bundles/assortment tests to close gaps across {color_col} within top {group_col}."
    return fig, outcome_sentence(note_context + ' ' + note, action)

def timeseries_monthly(df, date_col, value_col, title, note_context):
    s = df.groupby('order_month')[value_col].sum().reset_index() if 'order_month' in df.columns else df.copy()
    if 'order_month' in s.columns:
        fig = px.line(s, x='order_month', y=value_col, markers=True, title=title)
        fig.update_layout(xaxis_title="Month", yaxis_title=value_col.replace('_',' ').title())
        note = "Identify seasonal peaks and plan inventory and staffing accordingly."
        action = "Forward-buy for peak months; schedule labor and replenishment to match demand."
        return fig, outcome_sentence(note_context + ' ' + note, action)
    else:
        fig = go.Figure()
        fig.update_layout(title=title)
        return fig, outcome_sentence("No month column found.", "Ensure datetime parsing is correct to enable seasonality planning.")

def gender_age_breakdown(df, value_col, gender_col, age_group_col, title, note_context):
    g = df.groupby([gender_col, age_group_col], dropna=False)[value_col].sum().reset_index()
    fig = px.bar(g, x=age_group_col, y=value_col, color=gender_col, barmode='group', title=title)
    fig.update_layout(xaxis_title="Age Group", yaxis_title=value_col.replace('_',' ').title(), legend_title=gender_col.replace('_',' ').title())
    note = "Certain age-gender cohorts contribute disproportionately."
    action = "Personalize offers by cohort (e.g., CRM segments and creatives for top age-gender groups)."
    return fig, outcome_sentence(note_context + ' ' + note, action)

def scatter_price_qty(df, price_col, qty_col, title, note_context):
    fig = px.scatter(df, x=price_col, y=qty_col, trendline='ols', title=title, opacity=0.5)
    fig.update_layout(xaxis_title=price_col.replace('_',' ').title(), yaxis_title=qty_col.replace('_',' ').title())
    note = "Negative slope suggests price sensitivity; strong positive suggests value packs/add-on buying."
    action = "Test price ladders and pack sizes; use markdowns surgically where elasticity is highest."
    return fig, outcome_sentence(note_context + ' ' + note, action)

def aov_by(df, revenue_col, group_col, title, note_context):
    g = df.groupby(group_col, dropna=False)[revenue_col].mean().reset_index().rename(columns={revenue_col:'AOV'})
    fig = px.bar(g, x=group_col, y='AOV', title=title)
    fig.update_layout(xaxis_title=group_col.replace('_',' ').title(), yaxis_title="Average Order Value (AED)")
    note = f"AOV differs meaningfully across {group_col}; prioritize high-AOV segments for premium/up-sell."
    action = "Adjust product recommendations and minimum basket thresholds by segment to lift AOV."
    return fig, outcome_sentence(note_context + ' ' + note, action)
