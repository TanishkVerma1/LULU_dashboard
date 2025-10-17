import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def kpi_cards(df: pd.DataFrame):
    total_rev = df["line_value_aed"].sum()
    avg_basket = df["line_value_aed"].sum() / max(df["order_id"].nunique(), 1)
    avg_discount_rate = (df["discount_aed"].sum() / max(df["base_unit_price_aed"].sum(), 1)) if "base_unit_price_aed" in df.columns else 0
    return {
        "total_rev": total_rev,
        "avg_basket": avg_basket,
        "avg_discount_rate": avg_discount_rate,
        "orders": df["order_id"].nunique(),
        "unique_customers": df["user_id"].nunique() if "user_id" in df.columns else None
    }

def time_series(df: pd.DataFrame):
    g = df.groupby(pd.Grouper(key="order_datetime", freq="D"), dropna=False)["line_value_aed"].sum().reset_index()
    fig = px.line(g, x="order_datetime", y="line_value_aed", markers=True, title="Daily Revenue Trend")
    fig.update_layout(hovermode="x unified")
    return fig

def category_mix_treemap(df: pd.DataFrame):
    g = df.groupby(["department","category"], as_index=False)["line_value_aed"].sum()
    fig = px.treemap(g, path=["department","category"], values="line_value_aed", title="Category Mix (Revenue)")
    return fig

def stacked_bar_category_month(df: pd.DataFrame):
    g = df.groupby(["order_month","category"], as_index=False)["line_value_aed"].sum()
    fig = px.bar(g, x="order_month", y="line_value_aed", color="category", title="Revenue by Month & Category", barmode="stack")
    return fig

def heatmap_hour_day(df: pd.DataFrame):
    g = df.groupby(["day_of_week","hour_of_day"], as_index=False)["line_value_aed"].sum()
    pivot = g.pivot(index="day_of_week", columns="hour_of_day", values="line_value_aed").fillna(0)
    order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    pivot = pivot.reindex(order)
    fig = go.Figure(data=go.Heatmap(z=pivot.values, x=list(pivot.columns), y=list(pivot.index), coloraxis="coloraxis"))
    fig.update_layout(title="Revenue Heatmap (Hour × Day)", coloraxis_colorscale="Blues")
    return fig

def scatter_price_qty(df: pd.DataFrame):
    if {"unit_price_after_discount_aed","quantity"}.issubset(df.columns):
        fig = px.scatter(df, x="unit_price_after_discount_aed", y="quantity",
                         size="line_value_aed", color="discount_aed",
                         title="Price vs Quantity (Bubble size = Revenue)",
                         hover_data=["category","brand"] if "brand" in df.columns else ["category"])
        return fig
    return go.Figure()

def city_ranked_bar(df: pd.DataFrame):
    g = df.groupby("city", as_index=False)["line_value_aed"].sum().sort_values("line_value_aed", ascending=False)
    fig = px.bar(g, x="city", y="line_value_aed", title="Revenue by City")
    fig.update_layout(xaxis_tickangle=-30)
    return fig

def inventory_stockout_table(df: pd.DataFrame, top_n:int=20):
    if "stock_out_flag" in df.columns:
        g = df.groupby(["sku_id","category"], as_index=False).agg(
            stockouts=("stock_out_flag","sum"),
            revenue=("line_value_aed","sum"),
            qty=("quantity","sum")
        ).sort_values(["stockouts","revenue"], ascending=[False,False]).head(top_n)
        return g
    return pd.DataFrame()

def returns_bar(df: pd.DataFrame):
    if "returned" in df.columns:
        g = df.groupby("category", as_index=False).agg(
            return_value=("return_value_aed","sum"),
            return_count=("returned","sum"),
            revenue=("line_value_aed","sum")
        )
        fig = px.bar(g.sort_values("return_value", ascending=False),
                     x="category", y="return_value", title="Return Value by Category")
        return fig
    return go.Figure()

def loyalty_vs_revenue(df: pd.DataFrame):
    if "loyalty_member" in df.columns:
        g = df.groupby("loyalty_member", as_index=False)["line_value_aed"].sum()
        g["loyalty_member"] = g["loyalty_member"].map({1:"Member",0:"Non-member"})
        fig = px.pie(g, names="loyalty_member", values="line_value_aed", title="Revenue Split: Loyalty Members")
        return fig
    return go.Figure()

def discount_vs_conversion(df: pd.DataFrame):
    g = df.groupby("category", as_index=False).agg(
        avg_discount=("discount_aed","mean"),
        total_qty=("quantity","sum"),
        revenue=("line_value_aed","sum")
    )
    fig = plot = px.scatter(g, x="avg_discount", y="total_qty", size="revenue",
                     hover_name="category", title="Discount vs Quantity (by Category)")
    return fig
