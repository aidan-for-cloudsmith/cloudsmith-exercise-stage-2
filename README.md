# Cloudsmith Exercise

Small Python project with two services:

- `transform_service`: reads raw `events.jsonl`, validates/transforms it, and writes processed data.
- `query_api`: FastAPI service for querying the processed event data.

MinIO is used as a local stub for the datalake. The transformer writes processed data into MinIO, and the API reads it back from there.

## Requirements

- Python 3.12
- Poetry
- Docker
- Docker Compose

## Install dependencies

Each service has its own Poetry environment.

```bash
cd services/transform_service
poetry install

cd ../query_api
poetry install
```

## Run locally with Poetry

Start MinIO first:

```bash
docker compose up -d minio
```

Run the transformer:

```bash
cd services/transform_service
MINIO_ENDPOINT=localhost:9000 poetry run python -m transform_service.main
```

Run the API:

```bash
cd services/query_api
MINIO_ENDPOINT=localhost:9000 poetry run python -m query_api.main
```

The API runs at `http://localhost:8000`.

## Run with Docker Compose

From the repo root:

```bash
docker compose up --build
```

This starts:

- `minio` on `http://localhost:9000`
- MinIO console on `http://localhost:9001`
- `query_api` on `http://localhost:8000`
- `transform_service`, which runs the transform job

Default MinIO credentials are:

```text
user: minio
password: minio123
```

## Tests and linting

Run transformer tests and lint checks:

```bash
cd services/transform_service
poetry run pytest
poetry run ruff check .
```

Run API tests and lint checks:

```bash
cd services/query_api
poetry run pytest
poetry run ruff check .
```

## End-to-end integration test

From the repo root:

```bash
./integration_tests
```

The script rebuilds the Docker Compose stack, waits for the transformer to finish, waits for the API to be healthy, then runs the API smoke tests.
