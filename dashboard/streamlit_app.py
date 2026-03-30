import os
import duckdb
import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Optional

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(PROJECT_ROOT, "warehouse", "analytics.duckdb")
PARQUET_PATH = os.path.join(PROJECT_ROOT, "lake", "parquet", "runs.parquet")


@st.cache_data
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


@st.cache_data
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
        agg = act_sel.groupby("activity")["cnt"].sum().reset_index()
        fig2 = px.pie(agg, names="activity", values="cnt", title="Activity distribution")
        st.plotly_chart(fig2, use_container_width=True)

    st.dataframe(sel.sort_values(["date", "username"]) , height=400)


if __name__ == "__main__":
    main()
