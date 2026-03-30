import os
import sys
import duckdb
import pandas as pd
from typing import Optional
from functools import lru_cache

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# Ensure repo root is on sys.path so imports like `from run_walk_constants` work
if PROJECT_ROOT not in sys.path:
    # don't rely on this alone; provide a robust fallback below
    sys.path.insert(0, PROJECT_ROOT)

try:
    from run_walk_constants import ACTIVITY_LABELS, WRIST_LABELS
except Exception:
    # Fallback: load the module directly from the file location so imports
    # work reliably whether pytest, Streamlit, or other runtimes are used.
    import importlib.util

    constants_path = os.path.join(PROJECT_ROOT, "run_walk_constants.py")
    spec = importlib.util.spec_from_file_location("run_walk_constants", constants_path)
    if spec is None or spec.loader is None:
        raise
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    ACTIVITY_LABELS = getattr(module, "ACTIVITY_LABELS")
    WRIST_LABELS = getattr(module, "WRIST_LABELS")

DB_PATH = os.path.join(PROJECT_ROOT, "warehouse", "analytics.duckdb")
PARQUET_PATH = os.path.join(PROJECT_ROOT, "lake", "parquet", "runs.parquet")


@lru_cache(maxsize=1)
def load_daily_summary() -> pd.DataFrame:
    # Try read-only DuckDB first
    if os.path.exists(DB_PATH):
        try:
            con = duckdb.connect(DB_PATH, read_only=True)
            try:
                df = con.execute("SELECT * FROM daily_user_summary").df()
                return df
            finally:
                con.close()
        except Exception:
            # fall back to parquet
            pass

    # parquet fallback (in-memory DuckDB)
    if os.path.exists(PARQUET_PATH):
        con = duckdb.connect(":memory:")
        try:
            con.execute(f"CREATE VIEW runs AS SELECT * FROM read_parquet('{PARQUET_PATH}')")
            df = con.execute("SELECT date::DATE AS date, username, COUNT(*) AS samples, AVG(sqrt(acceleration_x*acceleration_x + acceleration_y*acceleration_y + acceleration_z*acceleration_z)) AS avg_accel_magnitude FROM runs GROUP BY date::DATE, username").df()
            return df
        finally:
            con.close()

    return pd.DataFrame()


@lru_cache(maxsize=1)
def load_activity_counts() -> pd.DataFrame:
    if os.path.exists(DB_PATH):
        try:
            con = duckdb.connect(DB_PATH, read_only=True)
            try:
                return con.execute("SELECT * FROM daily_activity_counts").df()
            finally:
                con.close()
        except Exception:
            pass
    if os.path.exists(PARQUET_PATH):
        con = duckdb.connect(":memory:")
        try:
            con.execute(f"CREATE VIEW runs AS SELECT * FROM read_parquet('{PARQUET_PATH}')")
            return con.execute("SELECT date::DATE AS date, username, activity, COUNT(*) AS cnt FROM runs GROUP BY date::DATE, username, activity").df()
        finally:
            con.close()
    return pd.DataFrame()


def main():
    # import Streamlit and Plotly inside main to avoid side-effects on import
    import streamlit as st
    import plotly.express as px

    st.set_page_config(page_title="Run-Walk Dashboard", layout="wide")
    st.title("Run-Walk Pipeline — Dashboard (Streamlit)")

    df = load_daily_summary()
    if df.empty:
        st.warning("No analytics data found. Run the transform script to generate summaries.")
        return

    # filters
    users = sorted(df["username"].unique())
    user = st.selectbox("User", options=["All"] + users)
    date_range = st.date_input("Date range", value=(df["date"].min(), df["date"].max()))

    # apply filters
    sel = df
    if user != "All":
        sel = sel[sel["username"] == user]
    start, end = date_range
    sel = sel[(sel["date"] >= pd.to_datetime(start)) & (sel["date"] <= pd.to_datetime(end))]

    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Days", sel["date"].nunique())
    c2.metric("Users", sel["username"].nunique())
    c3.metric("Samples", int(sel["samples"].sum()))
    c4.metric("Avg accel mag", float(sel["avg_accel_magnitude"].mean()))

    # time series
    fig = px.line(sel.sort_values("date"), x="date", y="samples", color="username" if user == "All" else None, title="Samples over time")
    st.plotly_chart(fig, use_container_width=True)

    # activity distribution
    act = load_activity_counts()
    if not act.empty:
        if user != "All":
            act = act[act["username"] == user]
        act_sel = act[(act["date"] >= pd.to_datetime(start)) & (act["date"] <= pd.to_datetime(end))]
        # map numeric activity codes to labels if present
        if act_sel["activity"].dtype in ("int64", "int32", "int8") or pd.api.types.is_integer_dtype(act_sel["activity"]):
            act_sel = act_sel.copy()
            act_sel["activity_label"] = act_sel["activity"].map(ACTIVITY_LABELS).fillna(act_sel["activity"].astype(str))
            agg = act_sel.groupby("activity_label")["cnt"].sum().reset_index().rename(columns={"activity_label": "activity"})
        else:
            agg = act_sel.groupby("activity")["cnt"].sum().reset_index()
        fig2 = px.pie(agg, names="activity", values="cnt", title="Activity distribution")
        st.plotly_chart(fig2, use_container_width=True)

    # Map activity and wrist codes to labels for the table view (if columns exist)
    display_df = sel.copy()
    if "activity" in display_df.columns:
        if display_df["activity"].dtype in ("int64", "int32", "int8") or pd.api.types.is_integer_dtype(display_df["activity"]):
            display_df["activity"] = display_df["activity"].map(ACTIVITY_LABELS).fillna(display_df["activity"].astype(str))
    if "wrist" in display_df.columns:
        if display_df["wrist"].dtype in ("int64", "int32", "int8") or pd.api.types.is_integer_dtype(display_df["wrist"]):
            display_df["wrist"] = display_df["wrist"].map(WRIST_LABELS).fillna(display_df["wrist"].astype(str))

    st.dataframe(display_df.sort_values(["date", "username"]) , height=400)


if __name__ == "__main__":
    main()
