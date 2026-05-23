from __future__ import annotations

from services.transform_service.models import TransformedRecord


def save_transformed_record(record: TransformedRecord) -> TransformedRecord:
    """Persist transformed records and return the stored object."""
    return record


def quarantine_bad_record(record: TransformedRecord) -> None:
    """Handle records that fail validation or transformation."""
    print(f"Quarantining bad record: {record}")