from __future__ import annotations

import os
import io
import json
import uuid
from datetime import datetime

from minio import Minio
from minio.error import S3Error

from services.transform_service.models import TransformedRecord

DEFAULT_BUCKET = os.environ.get("MINIO_BUCKET", "cloudsmith-events")
MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "minio")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "minio123")


def _get_minio_client() -> Minio:
    return Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False,
    )


def _ensure_bucket(client: Minio, bucket: str) -> None:
    try:
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
    except S3Error:
        raise


def _sanitize_dt(dt: str) -> str:
    return dt.replace(":", "_")


def save_transformed_record(record: TransformedRecord) -> TransformedRecord:
    """Persist transformed records and return the stored object."""
    client = _get_minio_client()
    bucket = DEFAULT_BUCKET
    _ensure_bucket(client, bucket)

    tenant = record.tenant_id
    iso_dt = record.timestamp or datetime.utcnow().isoformat()
    iso_dt = _sanitize_dt(iso_dt)
    key = f"processed/vendor={tenant}/dataset=events/dt={iso_dt}/file-{uuid.uuid4().hex}.json"

    payload = json.dumps(record.__dict__).encode("utf-8")
    try:
        client.put_object(bucket, key, io.BytesIO(payload), len(payload), content_type="application/json")
    except S3Error as e:
        print(f"Failed to save record to MinIO: {e}")
        raise

    return record


def quarantine_bad_record(record: TransformedRecord) -> None:
    """Handle records that fail validation or transformation."""
    client = _get_minio_client()
    bucket = DEFAULT_BUCKET
    _ensure_bucket(client, bucket)

    tenant = record.tenant_id
    event_id = record.event_id or uuid.uuid4().hex
    key = f"quarantine/vendor={tenant}/reason=transformation_failure/{event_id}.raw"

    payload = json.dumps(record.__dict__).encode("utf-8")
    try:
        client.put_object(bucket, key, io.BytesIO(payload), len(payload), content_type="application/octet-stream")
        print(f"Quarantined bad record to {bucket}/{key}")
    except S3Error as e:
        print(f"Failed to quarantine record to MinIO: {e}")
        raise