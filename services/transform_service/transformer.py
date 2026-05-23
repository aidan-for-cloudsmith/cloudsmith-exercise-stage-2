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
        id=str(parsed.get("id", "")),
        timestamp=str(parsed.get("timestamp", "")),
        source=str(parsed.get("source", "")),
        processed_at=str(parsed.get("processed_at", "")),
        version=int(parsed.get("version", 1)),
    )
    return save_transformed_record(record)
