import pandas as pd

def expenses_to_df(expenses):
    if not expenses:
        return pd.DataFrame()
    df = pd.DataFrame(expenses)
    if "date" in df:
        df["date"] = pd.to_datetime(df["date"])
    return df

def summarize_by_month(df):
    if df.empty:
        return pd.DataFrame()
    df["month"] = df["date"].dt.to_period("M").dt.to_timestamp()
    return df.groupby("month")["converted_amount"].sum().reset_index()

def summarize_by_category(df):
    if df.empty:
        return pd.DataFrame()
    return df.groupby("category")["converted_amount"].sum().reset_index()
