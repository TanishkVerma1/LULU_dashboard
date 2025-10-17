
import pandas as pd
import numpy as np

def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df['order_datetime'] = pd.to_datetime(df['order_datetime'], errors='coerce')
    if 'hour_of_day' not in df.columns:
        df['hour_of_day'] = df['order_datetime'].dt.hour
    if 'day_of_week' not in df.columns:
        df['day_of_week'] = df['order_datetime'].dt.day_name()
    if 'order_month' not in df.columns:
        df['order_month'] = df['order_datetime'].dt.to_period('M').astype(str)
    nums = ['base_unit_price_aed','discount_aed','unit_price_after_discount_aed','quantity','line_value_aed','return_value_aed','basket_size_items','age']
    for n in nums:
        if n in df.columns:
            df[n] = pd.to_numeric(df[n], errors='coerce')
    for b in ['promo_used','returned','stock_out_flag','loyalty_member']:
        if b in df.columns:
            df[b] = df[b].map({True:1, False:0, 'Yes':1, 'No':0, 'Y':1, 'N':0}).fillna(df[b]).astype('float').astype('Int64')
    return df

def data_quality(df: pd.DataFrame):
    issues = []
    miss = df.isna().sum()
    miss = miss[miss>0]
    if not miss.empty:
        issues.append(f"Missing values: {dict(miss.sort_values(ascending=False))}")
    if 'unit_price_after_discount_aed' in df and (df['unit_price_after_discount_aed'] < 0).any():
        issues.append('Negative final prices detected')
    if {'discount_aed','base_unit_price_aed'}.issubset(df.columns):
        bad = (df['discount_aed'] > df['base_unit_price_aed']).sum()
        if bad>0:
            issues.append(f'Discount greater than base price rows: {bad}')
    return issues

def apply_filters(df, date_range=None, city=None, category=None, store=None):
    f = df.copy()
    if date_range:
        start, end = date_range
        f = f[(f['order_datetime'] >= start) & (f['order_datetime'] <= end)]
    if city:
        f = f[f['city'].isin(city)]
    if category:
        f = f[f['category'].isin(category)]
    if store:
        f = f[f['store_format'].isin(store)]
    return f

def business_goal_from_point(kind: str, point: dict) -> str:
    if kind == 'category_revenue':
        cat = point.get('label') or point.get('hovertext') or point.get('id') or point.get('x')
        return f'Grow {cat}: secure supply, negotiate better terms, and expand assortment to lift revenue share.'
    if kind == 'discount_vs_qty':
        x = point.get('x'); y = point.get('y'); name = point.get('hovertext') or point.get('text') or point.get('customdata') or ''
        if x is not None and y is not None:
            if x>0 and y<=point.get('y_median', 0):
                return f'Optimize discounts for {name}: test lower discount tiers with better placement to improve conversion.'
            elif x>0 and y>point.get('y_median', 0):
                return f'Sustain promo for {name}: discount appears effective—A/B test smaller discounts to protect margin.'
        return f'Tune promo strategy for {name} to balance volume and margin.'
    if kind == 'city_revenue':
        city = point.get('x') or point.get('label')
        return f'City focus: double down in {city} with localized campaigns and ensure high-velocity SKUs are never out of stock.'
    if kind == 'hour_day_heat':
        hour = point.get('x'); day = point.get('y')
        try:
            hour = int(hour)
        except Exception:
            pass
        return f'Peak operations: staff and run timed offers on {day} at {hour:02d}:00 to capture demand spikes.'
    return 'Use this selection to define a measurable goal (owner, timeline, KPI baseline → target).'
