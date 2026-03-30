import os
import pandas as pd
import pytest


def test_ingest_csvs_to_parquet_calls_to_parquet(monkeypatch, tmp_path):
    # Create two small CSV files
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    f1 = raw_dir / "a.csv"
    f2 = raw_dir / "b.csv"
    f1.write_text("x,y\n1,2\n3,4\n")
    f2.write_text("x,y\n5,6\n")

    out_path = tmp_path / "out.parquet"

    # Track calls to to_parquet
    called = {}

    def fake_to_parquet(self, path, index=False):
        # ensure path matches expected
        called['path'] = path
        called['index'] = index

    monkeypatch.setattr(pd.DataFrame, "to_parquet", fake_to_parquet)

    from ingestion.ingest import ingest_csvs_to_parquet

    rows = ingest_csvs_to_parquet(str(raw_dir), str(out_path))

    # We expect 3 rows total
    assert rows == 3
    assert called.get('path') == str(out_path)
    assert called.get('index') is False
