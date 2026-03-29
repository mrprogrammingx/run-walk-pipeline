# run-walk-pipeline

Small example pipeline structure for ingesting run/walk data, transforming it and exposing a tiny dashboard.

Project layout

run-walk-pipeline/
├── data/ (raw data goes here)
├── lake/ (Parquet lake)
├── warehouse/ (SQLite analytics DB)
├── ingestion/ingest.py (script to convert CSV -> Parquet)
├── transform/transform.sql (SQL to create analytics table)
├── dashboard/app.py (very small Flask app to serve analytics)
├── airflow/dag.py (example Airflow DAG)
├── requirements.txt
└── README.md

Quick start (macOS / zsh)

1. Create a virtualenv and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Put CSV files in `data/raw/` (a sample file `data/raw/sample_runs.csv` is included).

3. Run the ingestion step manually:

```bash
python ingestion/ingest.py --raw-dir data/raw --out lake/parquet/runs.parquet
```

4. Transform (quick local transform, does not require Airflow):

```python
# run in a Python REPL or script
import pandas as pd
from sqlalchemy import create_engine

df = pd.read_parquet('lake/parquet/runs.parquet')
engine = create_engine('sqlite:///warehouse/analytics.db')
df.to_sql('runs', engine, if_exists='replace', index=False)
# then execute SQL in transform/transform.sql against warehouse/analytics.db
```

5. Start the dashboard (Flask):

```bash
python dashboard/app.py
# open http://localhost:8080/summary
```

Notes

- The Airflow DAG is an example and may require adjusting Python path so Airflow can import the `ingestion` package.
- This repository is intentionally minimal to be a starting point. Add CI, tests and configuration as needed.
