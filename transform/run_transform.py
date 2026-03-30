"""
Simple local transform runner: read parquet, write runs table to sqlite and execute transform SQL.
"""
import os
import duckdb
import sys
import pandas as pd

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PARQUET_PATH = os.path.join(PROJECT_ROOT, "lake", "parquet", "runs.parquet")
DB_PATH = os.path.join(PROJECT_ROOT, "warehouse", "analytics.duckdb")
TRANSFORM_SQL = os.path.join(PROJECT_ROOT, "transform", "transform.sql")


def run_transform():
    if not os.path.exists(PARQUET_PATH):
        raise FileNotFoundError(f"Parquet not found at {PARQUET_PATH}")

    df = pd.read_parquet(PARQUET_PATH)
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    # Use DuckDB file-backed database for analytics
    # write the dataframe into a DuckDB table named `runs`
    try:
        con = duckdb.connect(DB_PATH)
    except Exception as exc:
        # Common cause: another process (DBeaver, etc.) holds a lock on the
        # DuckDB file. Provide a clear, actionable error message.
        print(f"Error opening DuckDB file {DB_PATH}: {exc}", file=sys.stderr)
        print("This is often caused by another program (for example DBeaver) holding a lock on the file.", file=sys.stderr)
        print("To resolve: close the other program, or run:\n  lsof {DB_PATH}\nthen kill the process holding the file, or choose a different DB path.", file=sys.stderr)
        sys.exit(1)
    try:
        con.register('py_df', df)
        # replace runs table
        con.execute("CREATE OR REPLACE TABLE runs AS SELECT * FROM py_df")

        # Apply SQL transform (runs -> run_summary etc.) if present
        if os.path.exists(TRANSFORM_SQL):
            with open(TRANSFORM_SQL, "r") as f:
                sql = f.read()
            con.execute(sql)
    finally:
        con.close()

    print("Transform complete. run_summary table created.")


if __name__ == "__main__":
    run_transform()
