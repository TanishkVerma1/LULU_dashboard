
import pandas as pd
import numpy as np
from dateutil import parser

def standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    # Strip and lower columns
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]
    return df

def infer_columns(df: pd.DataFrame) -> dict:
    cols = df.columns.tolist()
    def find(patterns):
        import re
        for pat in patterns:
            for c in cols:
                if re.fullmatch(pat, c, flags=re.IGNORECASE):
                    return c
        return None
    col_map = {}
    col_map['order_datetime'] = find([r'(order[_\s-]?datetime|order[_\s-]?date|txn[_\s-]?date|date)'])
    col_map['customer_id'] = find([r'(customer[_\s-]?id|cust[_\s-]?id|customer)'])
    col_map['gender'] = find([r'(gender|sex)'])
    col_map['age'] = find([r'(age|age[_\s-]?years)'])
    col_map['age_group'] = find([r'(age[_\s-]?group|agegroup)'])
    col_map['city'] = find([r'(city|location|region)'])
    col_map['store_format'] = find([r'(store[_\s-]?format|format|store[_\s-]?type)'])
    col_map['department'] = find([r'(department|dept)'])
    col_map['category'] = find([r'(category|product[_\s-]?category)'])
    col_map['brand'] = find([r'(brand)'])
    col_map['sku_id'] = find([r'(sku[_\s-]?id|sku|product[_\s-]?id|item[_\s-]?id)'])
    col_map['quantity'] = find([r'(quantity|qty|units)'])
    col_map['unit_price'] = find([r'(unit[_\s-]?price[_\s-]?after[_\s-]?discount[_\s-]?aed|unit[_\s-]?price|price)'])
    col_map['discount'] = find([r'(discount[_\s-]?aed|discount|promo|markdown)'])
    col_map['line_value'] = find([r'(line[_\s-]?value[_\s-]?aed|net[_\s-]?sales|revenue|sales|amount|total[_\s-]?price)'])
    col_map['channel'] = find([r'(channel)'])
    col_map['payment'] = find([r'(payment|tender|method)'])
    col_map['nationality_group'] = find([r'(nationality[_\s-]?group|nationality)'])
    return col_map

def engineer_features(df: pd.DataFrame, col_map: dict) -> pd.DataFrame:
    df = df.copy()
    odt = col_map.get('order_datetime')
    if odt is not None:
        try:
            df[odt] = pd.to_datetime(df[odt])
        except Exception:
            # best-effort parse
            df[odt] = df[odt].apply(lambda x: parser.parse(str(x)) if pd.notnull(x) else pd.NaT)
        df['order_date'] = df[odt].dt.date
        df['order_month'] = df[odt].dt.to_period('M').astype(str)
        df['day_of_week'] = df[odt].dt.day_name()
        df['hour_of_day'] = df[odt].dt.hour
    # revenue fallback
    rev = col_map.get('line_value')
    if rev is None:
        q = col_map.get('quantity'); p = col_map.get('unit_price'); d = col_map.get('discount')
        if q and p:
            df['line_value'] = df[q].astype(float) * df[p].astype(float)
            if d and df[d].dtype.kind in 'biufc':
                df['line_value'] = df['line_value'] - df[d].astype(float)
            col_map['line_value'] = 'line_value'
    # age group
    ag = col_map.get('age_group'); a = col_map.get('age')
    if ag is None and a is not None:
        bins = [0,17,24,34,44,54,64,120]
        labels = ['<18','18-24','25-34','35-44','45-54','55-64','65+']
        df['age_group'] = pd.cut(df[a].astype(float), bins=bins, labels=labels, right=True, include_lowest=True)
        col_map['age_group'] = 'age_group'
    return df

def kpis(df: pd.DataFrame, col_map: dict) -> dict:
    revenue_col = col_map.get('line_value')
    quantity_col = col_map.get('quantity')
    cust_col = col_map.get('customer_id')
    k = {}
    if revenue_col:
        k['Total Revenue (AED)'] = float(df[revenue_col].sum())
        k['Avg Order Value (AED)'] = float(df[revenue_col].mean())
    if quantity_col:
        k['Total Units Sold'] = float(df[quantity_col].sum())
        k['Avg Units per Order'] = float(df[quantity_col].mean())
    if cust_col:
        k['Unique Customers'] = int(df[cust_col].nunique())
        # simple repeat-rate proxy: customers appearing >1 times
        rc = (df.groupby(cust_col).size()>1).mean()
        k['Repeat Customer Rate'] = float(rc)
    return k

def explain_lift(df: pd.DataFrame, group_col: str, value_col: str) -> str:
    g = df.groupby(group_col)[value_col].sum().sort_values(ascending=False)
    if g.empty:
        return "No data available for this breakdown."
    top = g.index[0]; top_val = g.iloc[0]; total = g.sum()
    share = (top_val/total)*100 if total else 0
    return f"Top contributor: **{top}** at **{share:.1f}%** of {value_col}."

def outcome_sentence(context: str, action: str) -> str:
    return f"**Business outcome idea:** {action} (Context: {context})."

def compare_two_groups(df: pd.DataFrame, group_col: str, value_col: str):
    g = df.groupby(group_col)[value_col].sum().sort_values(ascending=False)
    if len(g)>=2:
        rel = g.iloc[0]/max(g.iloc[1], 1e-9)
        return f"{g.index[0]} outperforms {g.index[1]} by {rel:.2f}× on {value_col}."
    elif len(g)==1:
        return f"{g.index[0]} is the only group with measurable {value_col}."
    return "Insufficient groups to compare."

def safe_num(x):
    return f"{x:,.0f}" if isinstance(x,(int,float)) else str(x)
