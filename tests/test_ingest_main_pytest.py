import os
import sys
import subprocess
import pytest


def test_ingest_main_no_csv(tmp_path, monkeypatch):
    # Create an empty raw directory
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    out_path = tmp_path / "out.parquet"

    env = os.environ.copy()
    env["DEFAULT_RAW"] = str(raw_dir)
    env["DEFAULT_OUT"] = str(out_path)

    # Run the module as a script
    proc = subprocess.run([sys.executable, "-m", "ingestion.ingest"], env=env, capture_output=True, text=True)

    assert proc.returncode == 0
    # The ingest function prints this message when no CSVs are found
    assert "No CSV files found" in proc.stdout
