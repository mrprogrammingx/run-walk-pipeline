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

2. Put CSV files in `data/raw/`.

Makefile (recommended)
----------------------

This repository includes a small `Makefile` with convenient targets for local development. Using `make` is the easiest way to create the venv, download the dataset (via the downloader), run ingestion and run tests.

Common targets:

```bash
# create and activate the virtualenv and install deps
make venv

# download dataset into data/raw/ (uses .env KAGGLE_API_TOKEN or ~/.kaggle)
make download

# run the ingestion step (CSV -> Parquet)
make ingest

# run the test suite (pytest)
make test
```

If you don't have `make` available you can use the equivalent commands shown elsewhere in this README (for example `python -m ingestion.download_kaggle` and `python -m ingestion.ingest`).

Dataset source
---------------

The dataset used for this project is available on Kaggle:

https://www.kaggle.com/datasets/vmalyi/run-or-walk/data

Download the dataset manually from the above URL and place the CSV files into `data/raw/`.

Note: an optional helper script `ingestion/download_kaggle.py` exists to automate the download if you prefer (it requires Kaggle API credentials). Manual placement is the recommended approach if you don't want to store or configure credentials.

Automated download (Kaggle)
---------------------------

If you'd like to download the dataset programmatically instead of placing files into `data/raw/` manually, this repo includes a small helper script at `ingestion/download_kaggle.py`.

1. Create a `.env` file in the repository root with your Kaggle token:

```text
KAGGLE_API_TOKEN=KGAT_<base64(username:api_key)>
# Example (do not commit this file to git):
# KAGGLE_API_TOKEN=KGAT_abcd1234...
```

If you prefer the standard Kaggle credentials file, you can also place `kaggle.json` in `~/.kaggle/`.

2. Run the downloader using the project's virtualenv Python (recommended):

```bash
source .venv/bin/activate
python -m ingestion.download_kaggle
```

The script will create `~/.kaggle/kaggle.json` for the current user (derived from the token when possible), call the `kaggle` CLI to download and unzip the dataset into `data/raw/`, and list the downloaded files.

Security note: keep your `.env` file out of version control (add `.env` to `.gitignore` if necessary).

3. Run the ingestion step manually:

The ingestion script imports the repository-level `config` module, so it's easiest
to run it as a module from the repository root which ensures the package import
paths are correct:

```bash
python -m ingestion.ingest --raw-dir data/raw --out lake/parquet/runs.parquet
```

Alternatively, you can run the script directly but must ensure the repository
root is on `PYTHONPATH` (or run from the repo root with `-m` as above):

```bash
# from repo root
PYTHONPATH=. python ingestion/ingest.py --raw-dir data/raw --out lake/parquet/runs.parquet
```

The `-m` approach is recommended because it avoids needing to set `PYTHONPATH`.

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

