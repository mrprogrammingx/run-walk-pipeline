# Airflow dev instructions

This folder contains a sample Airflow DAG and helper scripts to run Airflow locally for development.

Quick start (Docker, recommended)

1. Start Docker Desktop on your machine.
2. From the repository root:

```bash
# initialize the Airflow stack (pull images, bring up Postgres, migrate DB, create admin)
make airflow-docker-init

# start the stack (webserver + scheduler in standalone mode)
make airflow-docker-up
```

3. Open the Airflow UI: http://localhost:8080 (user: `admin`, password: `admin`).

Common commands

- List DAGs inside the container:
  docker compose exec -T airflow airflow dags list

- Trigger the pipeline manually:
  docker compose exec -T airflow airflow dags trigger run_walk_pipeline

- Check DAG import errors:
  docker compose exec -T airflow airflow dags list-import-errors

- Stop the stack:
  make airflow-docker-down

Notes

- The Compose setup uses `_PIP_ADDITIONAL_REQUIREMENTS` to install `duckdb,pandas,pyarrow` into the Airflow container at startup. This is for development only; for production build a custom image.
- The DAG `run_walk_pipeline` is set to unpaused on creation so you can trigger it immediately from the UI.
- If the DAG doesn't show up, check `docker compose logs airflow` and `airflow dags list-import-errors` for parse-time errors.

CI integration (optional)

- A simple GitHub Actions workflow (in `.github/workflows/airflow-integration.yml`) will attempt to start the docker-compose stack and run a quick smoke check. CI environments must support Docker (self-hosted or Docker-in-Docker).

