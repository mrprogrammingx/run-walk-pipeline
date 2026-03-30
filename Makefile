SHELL := /bin/bash

# Defaults (can be overridden on the make command line)
RAW_DIR ?= data/raw
OUT ?= lake/parquet/runs.parquet
PY ?= python

.PHONY: help venv download ingest test

help:
	@echo "Makefile targets:"
	@echo "  make download    - download Kaggle dataset (uses ingestion.download_kaggle)"
	@echo "  make ingest      - ingest CSVs from $(RAW_DIR) to $(OUT)"
	@echo "  make test        - run tests (pytest)"
	@echo "  make venv        - create a local .venv and install requirements"

venv:
	@echo "Creating virtualenv in .venv and installing requirements..."
	$(PY) -m venv .venv
	. .venv/bin/activate && pip install --upgrade pip
	. .venv/bin/activate && pip install -r requirements.txt || true
	. .venv/bin/activate && pip install -r requirements-dev.txt || true

.PHONY: airflow-install airflow-run-scheduler

airflow-install:
	@echo "Installing Airflow into .venv (this may take a few minutes)..."
	@. .venv/bin/activate && \
	AIRFLOW_VERSION=3.0.6; \
	PY_VER=3.9; \
	CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PY_VER}.txt"; \
	. .venv/bin/activate && pip install "apache-airflow==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"

airflow-run-scheduler:
	@echo "Starting Airflow scheduler from .venv (runs in foreground). Use Ctrl-C to stop."
	@. .venv/bin/activate && airflow db reset --yes || true
	@. .venv/bin/activate && airflow scheduler


.PHONY: airflow-docker-init airflow-docker-up airflow-docker-down

airflow-docker-init:
	@echo "Initializing docker-compose Airflow stack (pulls images)..."
	@docker compose pull
	@docker compose up -d postgres
	@sleep 3
	@docker compose run --rm airflow airflow db migrate
	@docker compose run --rm airflow airflow users create --username admin --firstname Admin --lastname User --role Admin --email admin@example.com --password admin || true

airflow-docker-up:
	@echo "Starting docker-compose Airflow stack (webserver)"
	@docker compose up -d
	@echo "Airflow webserver should be available at http://localhost:8080"

airflow-docker-down:
	@echo "Stopping docker-compose Airflow stack"
	@docker compose down

download:
	@echo "Running downloader (will use KAGGLE_API_TOKEN from env or .env)"
	$(PY) -m ingestion.download_kaggle

ingest:
	@echo "Ingesting CSVs from $(RAW_DIR) -> $(OUT)"
	$(PY) -m ingestion.ingest --raw-dir $(RAW_DIR) --out $(OUT)

test:
	@echo "Running pytest..."
	$(PY) -m pytest -q


.PHONY: ci
ci:
	@python scripts/create_sample_parquet.py
	$(PY) -m pytest -q
