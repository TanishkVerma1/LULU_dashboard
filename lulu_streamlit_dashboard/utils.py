import pandas as pd
import numpy as np
from datetime import datetime

REQUIRED_COLUMNS = [
    "order_id","order_datetime","channel","store_format","city","city_zone",
    "department","category","brand","sku_id","base_unit_price_aed","discount_aed",
    "unit_price_after_discount_aed","quantity","line_value_aed","promo_used",
    "promo_code_type","ad_channel","campaign","payment_method","device_type",
    "delivery_type","basket_size_items","returned","return_reason",
    "return_value_aed","stock_out_flag","loyalty_member","user_id","age",
    "gender","nationality_group","hour_of_day","day_of_week","order_month"
]

def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Parse datetime
    if "order_datetime" in df.columns:
        df["order_datetime"] = pd.to_datetime(df["order_datetime"], errors="coerce")
    else:
        if "order_date" in df.columns:
            df["order_datetime"] = pd.to_datetime(df["order_date"], errors="coerce")
    # Derived features if missing
    if "hour_of_day" not in df.columns:
        df["hour_of_day"] = df["order_datetime"].dt.hour
    if "day_of_week" not in df.columns:
        df["day_of_week"] = df["order_datetime"].dt.day_name()
    if "order_month" not in df.columns:
        df["order_month"] = df["order_datetime"].dt.to_period("M").astype(str)

    # Numeric coercion
    for col in ["base_unit_price_aed","discount_aed","unit_price_after_discount_aed","quantity","line_value_aed","basket_size_items","return_value_aed","age"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # line_value if missing
    if "line_value_aed" in df.columns:
        missing_mask = df["line_value_aed"].isna()
        if "unit_price_after_discount_aed" in df.columns and "quantity" in df.columns:
            df.loc[missing_mask, "line_value_aed"] = df["unit_price_after_discount_aed"] * df["quantity"]

    # Standardize booleans
    for bcol in ["promo_used","returned","stock_out_flag","loyalty_member"]:
        if bcol in df.columns:
            df[bcol] = df[bcol].map({True:1, False:0, "Yes":1, "No":0, "Y":1, "N":0}).fillna(df[bcol]).astype("float").astype("Int64")

    return df

def quality_checks(df: pd.DataFrame):
    issues = []
    miss = df.isna().sum()
    high_missing = miss[miss > 0].sort_values(ascending=False)
    if not high_missing.empty:
        issues.append(f"Columns with missing values: {dict(high_missing[high_missing>0])}")

    neg_price = (df.get("base_unit_price_aed", pd.Series(dtype=float)) < 0).sum()
    if neg_price > 0:
        issues.append(f"Negative base_unit_price_aed rows: {int(neg_price)}")
    neg_final = (df.get("unit_price_after_discount_aed", pd.Series(dtype=float)) < 0).sum()
    if neg_final > 0:
        issues.append(f"Negative unit_price_after_discount_aed rows: {int(neg_final)}")

    outlier_cols = ["unit_price_after_discount_aed","quantity","line_value_aed","discount_aed","basket_size_items"]
    outlier_summary = {}
    for c in outlier_cols:
        if c in df.columns:
            s = df[c].dropna()
            if len(s) > 10:
                q1, q3 = s.quantile(0.25), s.quantile(0.75)
                iqr = q3 - q1
                upper = q3 + 1.5*iqr
                lower = q1 - 1.5*iqr
                cnt = int(((s > upper) | (s < lower)).sum())
                if cnt>0:
                    outlier_summary[c] = cnt
    if outlier_summary:
        issues.append(f"Potential outliers (IQR count): {outlier_summary}")

    if {"discount_aed","base_unit_price_aed"}.issubset(df.columns):
        cnt = int((df["discount_aed"] > df["base_unit_price_aed"]).sum())
        if cnt>0:
            issues.append(f"Discount > base price rows: {cnt}")

    if {"returned","return_value_aed"}.issubset(df.columns):
        cnt = int(((df["returned"]==1) & (df["return_value_aed"]<=0)).sum())
        if cnt>0:
            issues.append(f"Returned with non-positive value rows: {cnt}")

    return issues

def filter_data(df, date_range=None, cities=None, categories=None, stores=None):
    f = df.copy()
    if date_range and all(date_range):
        start, end = date_range
        f = f[(f["order_datetime"]>=start) & (f["order_datetime"]<=end)]
    if cities:
        f = f[f["city"].isin(cities)]
    if categories:
        f = f[f["category"].isin(categories)]
    if stores:
        f = f[f["store_format"].isin(stores)]
    return f

def simulate_rows(df: pd.DataFrame, target_rows:int=10000, seed: int=7) -> pd.DataFrame:
    if len(df) >= target_rows:
        return df
    rng = np.random.default_rng(seed)
    k = target_rows - len(df)
    sample = df.sample(n=min(k, len(df)), replace=True, random_state=seed).reset_index(drop=True)
    num_cols = df.select_dtypes(include=[np.number]).columns
    for c in num_cols:
        std = df[c].std() if df[c].std() and df[c].std()>0 else 1.0
        jitter = rng.normal(0, 0.05*std, size=len(sample))
        sample[c] = np.maximum(0, sample[c].fillna(0) + jitter)
    if "order_datetime" in sample.columns:
        jitter_days = rng.integers(-45, 45, size=len(sample))
        sample["order_datetime"] = sample["order_datetime"] + pd.to_timedelta(jitter_days, unit="D")
        sample["hour_of_day"] = sample["order_datetime"].dt.hour
        sample["day_of_week"] = sample["order_datetime"].dt.day_name()
        sample["order_month"] = sample["order_datetime"].dt.to_period("M").astype(str)
    big = pd.concat([df, sample], ignore_index=True)
    return big
