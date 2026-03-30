"""
A simple Airflow DAG example that runs ingestion and transformation.
This DAG expects the project to be importable by the Airflow scheduler worker.
"""
from datetime import datetime
import os
import duckdb

from airflow import DAG
from airflow.operators.python import PythonOperator

# Local helper imports (make sure Airflow's PYTHONPATH includes the project root)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
PARQUET_PATH = os.path.join(PROJECT_ROOT, "lake", "parquet", "runs.parquet")
DB_PATH = os.path.join(PROJECT_ROOT, "warehouse", "analytics.duckdb")
TRANSFORM_SQL = os.path.join(PROJECT_ROOT, "transform", "transform.sql")

# import ingestion function lazily inside task

def task_ingest(**kwargs):
    from ingestion.ingest import ingest_csvs_to_parquet
    ingest_csvs_to_parquet(RAW_DIR, PARQUET_PATH)


def task_transform(**kwargs):
    # Read parquet into pandas and write into sqlite as `runs` table, then apply transform SQL
    import pandas as pd
    if not os.path.exists(PARQUET_PATH):
        raise FileNotFoundError(f"Parquet not found at {PARQUET_PATH}")
    df = pd.read_parquet(PARQUET_PATH)

    # Ensure warehouse dir exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    # Write raw runs table into a DuckDB file and apply transform SQL
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    con = duckdb.connect(DB_PATH)
    try:
        con.register('py_df', df)
        con.execute("CREATE OR REPLACE TABLE runs AS SELECT * FROM py_df")

        if os.path.exists(TRANSFORM_SQL):
            with open(TRANSFORM_SQL, "r") as f:
                sql = f.read()
            con.execute(sql)
    finally:
        con.close()


default_args = {
    "owner": "airflow",
    "start_date": datetime(2023, 1, 1),
}

with DAG(
    dag_id="run_walk_pipeline",
    default_args=default_args,
    # Run on demand by default; change to '@daily' or cron if you want scheduling
    schedule_interval=None,
    catchup=False,
    tags=["example"],
):
    download = PythonOperator(task_id="download", python_callable=lambda **kw: __import__('ingestion.download_kaggle', fromlist=['']).download_dataset(RAW_DIR))
    ingest = PythonOperator(task_id="ingest", python_callable=task_ingest)
    transform = PythonOperator(task_id="transform", python_callable=task_transform)

    # Pipeline order: download -> ingest -> transform
    download >> ingest >> transform
