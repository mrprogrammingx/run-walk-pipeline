"""
A simple Airflow DAG example that runs ingestion and transformation.
This DAG expects the project to be importable by the Airflow scheduler worker.
"""
from datetime import datetime
import os
import duckdb

HAS_AIRFLOW = True
try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
except Exception:  # pragma: no cover - environment dependent
    HAS_AIRFLOW = False

# Local helper imports (make sure Airflow's PYTHONPATH includes the project root)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
PARQUET_PATH = os.path.join(PROJECT_ROOT, "lake", "parquet", "runs.parquet")
DB_PATH = os.path.join(PROJECT_ROOT, "warehouse", "analytics.duckdb")
TRANSFORM_SQL = os.path.join(PROJECT_ROOT, "transform", "transform.sql")

# Ensure the project root is on sys.path so local imports like `ingestion` work
import sys
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

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
if HAS_AIRFLOW:
    with DAG(
        dag_id="run_walk_pipeline",
        default_args=default_args,
        # Run on demand by default; change to '@daily' or cron if you want scheduling
        schedule=None,
        catchup=False,
        tags=["example"],
        # create the DAG in an unpaused state so it's immediately runnable in dev
        is_paused_upon_creation=False,
    ):
        # The download task uses Kaggle CLI and may not be available in CI. Wrap it to
        # skip gracefully when credentials or CLI are missing so the rest of the DAG can run
        def _safe_download(**kw):
            try:
                mod = __import__('ingestion.download_kaggle', fromlist=[''])
                mod.download_dataset(RAW_DIR)
            except Exception as exc:
                # Log and continue; CI will provide sample parquet instead of downloading
                print(f"Download skipped: {exc}")

        download = PythonOperator(task_id="download", python_callable=_safe_download)
        ingest = PythonOperator(task_id="ingest", python_callable=task_ingest)
        transform = PythonOperator(task_id="transform", python_callable=task_transform)

        # Pipeline order: download -> ingest -> transform
        download >> ingest >> transform
else:
    # When Airflow is not available we skip DAG construction. The module still
    # exposes the task functions and a small CLI below for local development.
    pass


def _print_no_airflow_help():
    print("Airflow is not installed in this environment.")
    print("To run the DAG with Airflow, either:")
    print("  - run it inside an Airflow installation (pip install apache-airflow)\n  - or use the provided docker-compose setup to run Airflow containers.")
    print("\nYou can still run individual tasks manually from this script:")
    print("  python airflow/dag.py ingest    # run ingestion (CSV->Parquet)")
    print("  python airflow/dag.py transform # run transform (Parquet->DuckDB)")
    print("  python airflow/dag.py download  # run dataset download (requires Kaggle config)")


if not HAS_AIRFLOW and __name__ == "__main__":
    # lightweight CLI to run tasks without Airflow installed (for dev)
    import sys

    if len(sys.argv) < 2:
        _print_no_airflow_help()
        sys.exit(1)

    cmd = sys.argv[1].lower()
    if cmd == "ingest":
        print("Running ingest task (CSV -> Parquet)")
        task_ingest()
    elif cmd == "transform":
        print("Running transform task (Parquet -> DuckDB)")
        task_transform()
    elif cmd == "download":
        print("Running download task (may require Kaggle credentials)")
        # import and run downloader
        from ingestion.download_kaggle import download_dataset

        download_dataset(RAW_DIR)
    else:
        print(f"Unknown command: {cmd}\n")
        _print_no_airflow_help()
        sys.exit(2)
