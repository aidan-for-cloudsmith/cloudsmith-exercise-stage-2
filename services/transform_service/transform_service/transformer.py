from __future__ import annotations

from transform_service.parser import parse_raw_data
from transform_service.storage import save_transformed_record
from transform_service.models import TransformedRecord


def transform_record(raw_data: dict[str, object]) -> TransformedRecord:
    """Transform raw data into a standardized TransformedRecord.
    
    Args:
        raw_data: Raw event data dictionary.
    
    Returns:
        TransformedRecord with normalized data.
    """
    parsed = parse_raw_data(raw_data)
    record = TransformedRecord(
        event_id=(str(parsed.get("event_id")) if parsed.get("event_id") is not None else None),
        tenant_id=str(parsed.get("tenant_id", "")),
        action=str(parsed.get("action", "")),
        package=str(parsed.get("package", "")),
        version=str(parsed.get("version", "")),
        timestamp=str(parsed.get("timestamp", "")),
        actor=(str(parsed.get("actor")) if parsed.get("actor") is not None else None),
    )
    return save_transformed_record(record)
