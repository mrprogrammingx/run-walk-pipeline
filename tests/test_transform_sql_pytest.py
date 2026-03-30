import os
import duckdb


def test_transform_sql_executes_and_creates_run_summary():
    parquet = os.path.join("lake", "parquet", "runs.parquet")
    assert os.path.exists(parquet), "runs.parquet must exist for this test"

    con = duckdb.connect(":memory:")
    try:
        con.execute(f"CREATE VIEW runs AS SELECT * FROM read_parquet('{parquet}')")
        # execute transform SQL
        with open("transform/transform.sql", "r") as f:
            sql = f.read()
        con.execute(sql)

        # ensure daily_user_summary table exists and has rows
        cnt = con.execute("SELECT COUNT(*) FROM daily_user_summary").fetchone()[0]
        assert cnt > 0

        # check expected columns
        # DESCRIBE returns rows like (column_name, type, ...)
        cols = [c[0] for c in con.execute("DESCRIBE daily_user_summary").fetchall()]
        for expected in ("date", "username", "samples", "avg_accel_magnitude"):
            assert expected in cols
    finally:
        con.close()
