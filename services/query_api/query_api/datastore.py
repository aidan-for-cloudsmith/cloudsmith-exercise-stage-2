from __future__ import annotations

import os
import re
from datetime import UTC, datetime, timedelta
from typing import Any

import duckdb
from duckdb import IOException
from minio import Minio
from minio.error import S3Error

DEFAULT_BUCKET = os.environ.get("MINIO_BUCKET", "cloudsmith-events")
MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "minio")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "minio123")
EVENT_RETENTION_DAYS = int(os.environ.get("EVENT_RETENTION_DAYS", "90"))

_TENANT_SEGMENT_RE = re.compile(r"^[A-Za-z0-9_.=-]+$")
_DT_PARTITION_RE = re.compile(r"/dt=([^/]+)/")


class InvalidTenantError(ValueError):
    pass


def fetch_events(
    *,
    tenant: str,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    action_type: str | None = None,
    package_name: str | None = None,
) -> list[dict[str, Any]]:
    """Read transformed event records from MinIO using DuckDB."""
    _validate_tenant(tenant)

    path = _event_path(tenant)
    filters = ["tenant_id = ?"]
    params: list[Any] = [tenant]

    if start_time is not None:
        filters.append("try_cast(timestamp AS TIMESTAMP) >= ?")
        params.append(_naive_utc(start_time))
    if end_time is not None:
        filters.append("try_cast(timestamp AS TIMESTAMP) <= ?")
        params.append(_naive_utc(end_time))
    if action_type is not None:
        filters.append("action = ?")
        params.append(action_type)
    if package_name is not None:
        filters.append('"package" = ?')
        params.append(package_name)

    query = f"""
        SELECT
            event_id,
            tenant_id,
            action,
            "package",
            version,
            timestamp,
            actor
        FROM read_json_auto({_sql_literal(path)}, union_by_name = true)
        WHERE {" AND ".join(filters)}
        ORDER BY try_cast(timestamp AS TIMESTAMP) DESC
    """

    conn = _get_duckdb_connection()
    try:
        result = conn.execute(query, params)
        columns = [column[0] for column in result.description]
        return [dict(zip(columns, row, strict=True)) for row in result.fetchall()]
    except IOException as exc:
        if "No files found" in str(exc):
            return []
        raise
    finally:
        conn.close()


def cleanup_expired_events(*, tenant: str, retention_days: int = EVENT_RETENTION_DAYS) -> int:
    """Delete event objects older than the retention threshold."""
    _validate_tenant(tenant)
    if retention_days < 1:
        raise ValueError("retention_days must be greater than 0")

    cutoff = datetime.now(UTC) - timedelta(days=retention_days)
    client = _get_minio_client()
    prefix = f"processed/vendor={tenant}/dataset=events/"
    deleted = 0

    try:
        objects = client.list_objects(DEFAULT_BUCKET, prefix=prefix, recursive=True)
        for obj in objects:
            event_time = _partition_datetime(obj.object_name)
            if event_time is not None and event_time < cutoff:
                client.remove_object(DEFAULT_BUCKET, obj.object_name)
                deleted += 1
    except S3Error as exc:
        if exc.code == "NoSuchBucket":
            return 0
        raise

    return deleted


def _get_duckdb_connection() -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(database=":memory:")
    conn.execute("INSTALL httpfs")
    conn.execute("LOAD httpfs")
    conn.execute(f"SET s3_endpoint = {_sql_literal(MINIO_ENDPOINT)}")
    conn.execute(f"SET s3_access_key_id = {_sql_literal(MINIO_ACCESS_KEY)}")
    conn.execute(f"SET s3_secret_access_key = {_sql_literal(MINIO_SECRET_KEY)}")
    conn.execute("SET s3_use_ssl = false")
    conn.execute("SET s3_url_style = 'path'")
    return conn


def _get_minio_client() -> Minio:
    return Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False,
    )


def _event_path(tenant: str) -> str:
    return f"s3://{DEFAULT_BUCKET}/processed/vendor={tenant}/dataset=events/**/*.json"


def _validate_tenant(tenant: str) -> None:
    if not tenant or not _TENANT_SEGMENT_RE.fullmatch(tenant):
        raise InvalidTenantError("tenant must be a valid MinIO path segment")


def _partition_datetime(object_name: str) -> datetime | None:
    match = _DT_PARTITION_RE.search(f"/{object_name}")
    if match is None:
        return None

    raw_dt = match.group(1).replace("_", ":")
    try:
        parsed = datetime.fromisoformat(raw_dt)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _naive_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(UTC).replace(tzinfo=None)


def _sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"
