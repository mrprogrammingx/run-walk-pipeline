from flask import Flask, jsonify, render_template_string
import duckdb
import os

from typing import List, Dict, Any

app = Flask(__name__)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(PROJECT_ROOT, "warehouse", "analytics.duckdb")

SIMPLE_PAGE = """
<!doctype html>
<title>Run-Walk Pipeline — Dashboard</title>
<h1>Run-Walk Pipeline — Dashboard</h1>
<p>Available endpoints:</p>
<ul>
    <li><a href="/summary">/summary</a> — JSON daily summary (from daily_user_summary table)</li>
</ul>
"""


def query_db(sql: str) -> List[Dict[str, Any]]:
    """Execute SQL against the DuckDB file and return list of dict rows.

    If the DB file cannot be opened (for example another client holds a lock),
    return a single-row list with an ``error`` key so callers can return a
    friendly 503 response instead of raising a 500.
    """
    if not os.path.exists(DB_PATH):
        return []
    try:
        con = duckdb.connect(DB_PATH)
    except Exception as exc:
        return [{"error": f"Could not open analytics DB: {exc}"}]

    try:
        result = con.execute(sql).fetchall()
        cols = [c[0] for c in con.description]
        rows = [dict(zip(cols, r)) for r in result]
    finally:
        con.close()
    return rows


@app.route("/")
def index():
    return render_template_string(SIMPLE_PAGE)


@app.route("/summary")
def summary():
    sql = "SELECT * FROM daily_user_summary ORDER BY date DESC LIMIT 100;"
    rows = query_db(sql)
    # If query_db returned an error row, return a 503 with the message
    if rows and isinstance(rows, list) and isinstance(rows[0], dict) and "error" in rows[0]:
        return jsonify(rows[0]), 503
    return jsonify(rows)


if __name__ == "__main__":
    # For local development only. Use a proper WSGI server in production.
    app.run(host="0.0.0.0", port=8080, debug=True)
