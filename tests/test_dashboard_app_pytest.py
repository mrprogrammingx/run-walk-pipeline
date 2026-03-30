import os
import json
import duckdb
import tempfile

import pytest


def test_query_db_no_db_file(monkeypatch, tmp_path):
    # Ensure DB path points to a non-existent file
    from dashboard import app as dash

    monkeypatch.setattr(dash, "DB_PATH", str(tmp_path / "no_such.duckdb"))

    rows = dash.query_db("SELECT 1")
    assert rows == []


def test_query_db_with_table_and_summary_endpoint(tmp_path):
    # Create a DuckDB file with a daily_user_summary table
    db_path = tmp_path / "analytics.duckdb"
    con = duckdb.connect(str(db_path))
    try:
        con.execute("CREATE TABLE daily_user_summary (date DATE, username VARCHAR, samples INTEGER, avg_accel_magnitude DOUBLE)")
        con.execute("INSERT INTO daily_user_summary VALUES ('2026-01-01', 'alice', 10, 0.12)")
        con.close()

        from dashboard import app as dash
        dash_app = dash.app.test_client()

        # monkeypatch DB_PATH after importing app
        dash.DB_PATH = str(db_path)

        resp = dash_app.get("/summary")
        assert resp.status_code == 200
        data = json.loads(resp.get_data(as_text=True))
        assert isinstance(data, list)
        assert any(r["username"] == "alice" for r in data)
    finally:
        try:
            con.close()
        except Exception:
            pass


def test_query_db_when_db_locked(monkeypatch, tmp_path):
    # Simulate duckdb.connect throwing to exercise error path returning 503
    from dashboard import app as dash

    db_path = tmp_path / "analytics.duckdb"
    # Create empty file so query_db will attempt to open it
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with open(db_path, "w") as fh:
        fh.write("")

    monkeypatch.setattr(dash, "DB_PATH", str(db_path))

    def fake_connect(path):
        raise RuntimeError("cannot open DB")

    monkeypatch.setattr(duckdb, "connect", fake_connect)

    client = dash.app.test_client()
    resp = client.get("/summary")
    assert resp.status_code == 503
    payload = json.loads(resp.get_data(as_text=True))
    assert "error" in payload
