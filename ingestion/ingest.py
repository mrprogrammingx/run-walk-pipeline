"""
Simple ingestion script: concatenate CSV files under data/raw and write a Parquet output under lake/parquet.
"""

import os
import glob
import argparse
import pandas as pd


def ingest_csvs_to_parquet(raw_dir: str, out_path: str) -> int:
    """Read all CSVs from raw_dir, concatenate, and write a Parquet file to out_path.

    Returns number of rows written.
    """
    raw_dir = os.path.abspath(raw_dir)
    csv_files = sorted(glob.glob(os.path.join(raw_dir, "*.csv")))
    print(f"Found {len(csv_files)} CSV files in {raw_dir}")
    if not csv_files:
        print(f"No CSV files found in {raw_dir}")
        return 0

    dfs = []
    for f in csv_files:
        print(f"Reading {f}")
        df = pd.read_csv(f)
        dfs.append(df)

    df_all = pd.concat(dfs, ignore_index=True)
    out_dir = os.path.abspath(os.path.dirname(out_path))
    os.makedirs(out_dir, exist_ok=True)

    # Use pyarrow (if installed) for Parquet; pandas will pick an available engine.
    df_all.to_parquet(out_path, index=False)
    print(f"Wrote {len(df_all)} rows to {out_path}")
    return len(df_all)


if __name__ == "__main__":
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    # Load config values from central config module (which already loads .env)
    from config import get_env, repo_path

    env_raw = get_env("DEFAULT_RAW")
    env_out = get_env("DEFAULT_OUT")

    if env_raw:
        # if provided as relative path, make it relative to repo_root
        default_raw = os.path.abspath(env_raw) if os.path.isabs(env_raw) else repo_path(env_raw)
    else:
        default_raw = repo_path("data", "raw")

    if env_out:
        default_out = os.path.abspath(env_out) if os.path.isabs(env_out) else repo_path(env_out)
    else:
        default_out = repo_path("lake", "parquet", "runs.parquet")

    parser = argparse.ArgumentParser(description="Ingest CSVs to Parquet")
    parser.add_argument("--raw-dir", default=default_raw, help="Directory with raw CSV files")
    parser.add_argument("--out", default=default_out, help="Output Parquet file path")
    args = parser.parse_args()

    ingest_csvs_to_parquet(args.raw_dir, args.out)
