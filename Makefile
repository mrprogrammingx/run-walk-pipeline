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

download:
	@echo "Running downloader (will use KAGGLE_API_TOKEN from env or .env)"
	$(PY) -m ingestion.download_kaggle

ingest:
	@echo "Ingesting CSVs from $(RAW_DIR) -> $(OUT)"
	$(PY) -m ingestion.ingest --raw-dir $(RAW_DIR) --out $(OUT)

test:
	@echo "Running pytest..."
	$(PY) -m pytest -q
