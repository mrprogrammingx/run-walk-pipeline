import os
import duckdb


def test_run_transform_writes_duckdb(tmp_path, monkeypatch):
    # Monkeypatch the DB_PATH used by the run_transform module so it writes
    # to our temporary directory.
    import transform.run_transform as rt

    expected_db_dir = tmp_path / "warehouse"
    expected_db_dir.mkdir(parents=True)
    expected_db = expected_db_dir / "analytics.duckdb"

    # monkeypatch the DB_PATH in the module
    monkeypatch.setattr(rt, "DB_PATH", str(expected_db))

    # Ensure parquet exists and call run_transform
    rt.run_transform()

    assert expected_db.exists(), f"Expected DB at {expected_db}"

    con = duckdb.connect(str(expected_db))
    try:
        tables = [r[0] for r in con.execute("SHOW TABLES").fetchall()]
        assert "daily_user_summary" in tables
    finally:
        con.close()
