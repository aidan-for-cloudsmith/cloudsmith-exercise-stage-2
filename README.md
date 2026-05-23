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

## Approach, trade-offs, and improvements

The solution is split the app into a small ingestion service and a query API. The ingestion service reads the JSONL file line by line, writes valid events to MinIO, and sends malformed records to a quarantine prefix so bad input does not stop the whole import. Events are stored under tenant-specific partitions such as `processed/vendor=<tenant>/dataset=events/...`.

The query API requires a tenant on every request. It validates the tenant value, reads only that tenant's object prefix, and also filters by `tenant_id` in the query. Optional filters cover time range, action type, and package name. Results are ordered newest first so out-of-order ingestion does not affect query output.

Retention is implemented as an explicit API operation. It deletes objects for one tenant at a time based on the configured retention window, which keeps cleanup scoped to the requesting tenant.

Main trade-offs:

- MinIO is used as a simple local datalake instead of introducing a database.
- DuckDB queries JSON files directly, which is easy to inspect and test but not ideal for very large datasets.
- Duplicate events are not fully de-duplicated at write time. The event id is preserved, but a production version should make writes idempotent by storing or indexing records by `event_id`.
- Authentication and authorization are out of scope for this exercise. Tenant isolation is enforced by API parameters, path validation, and tenant-scoped storage reads.

With more time, I would add tenant isolation to the the api. idempotent ingestion, stronger schema validation, scheduled retention cleanup, pagination, request authentication, and more integration tests around malformed data and cross-tenant access. I'd also fix the existing bug that writes tenant-less records into the process part of our lake (those records should be quarantined to preserve tenant isolation)
