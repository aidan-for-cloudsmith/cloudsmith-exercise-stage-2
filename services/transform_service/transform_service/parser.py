from __future__ import annotations

import json
import logging
import uuid
from typing import Generator

from transform_service.models import FailedRecord, TransformedRecord


logger = logging.getLogger(__name__)


def parse_jsonl_file(
    filepath: str,
) -> Generator[TransformedRecord | FailedRecord, None, None]:
    """Parse event.jsonl file line by line and yield service model objects.

    Yields either a TransformedRecord for successfully parsed event lines
    or a FailedRecord for malformed or invalid lines.

    This generator never raises exceptions—it handles all parsing errors
    gracefully and yields them for quarantine handling.

    Args:
        filepath: Path to the event.jsonl file.

    Yields:
        TransformedRecord or FailedRecord.
    """
    with open(filepath, encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()

            if not line:
                logger.debug(f"Skipping empty line {line_num}")
                continue

            yield parse_raw_data(line)


def confirm_required_fields(
    data: dict[str, object], line: str
) -> FailedRecord | None:
    """Return a FailedRecord if any required field is absent, otherwise None.

    Args:
        data: Parsed data dictionary.
        line: Raw JSON line stored in FailedRecord on failure.

    Returns:
        FailedRecord for the first missing field, or None if all present.
    """
    for field in ("tenant_id", "package", "version"):
        if data.get(field) is None:
            return FailedRecord(raw_data=line, error_code=f"missing_{field}")
    return None


def build_transformed_record(data: dict[str, object]) -> TransformedRecord:
    """Build a TransformedRecord from parsed data.

    Args:
        data: Parsed data dictionary.

    Returns:
        TransformedRecord.
    """
    tenant_id = data["tenant_id"]
    package = data["package"]
    version = data["version"]

    event_id_raw = data.get("event_id")
    if event_id_raw is None:
        # Generating a uuid for a missing event_id breaks idempotency and could result in duplicate records on replay.
        event_id: str | None = str(uuid.uuid4())
    else:
        event_id = str(event_id_raw)

    action_raw = data.get("action")
    action = str(action_raw) if action_raw is not None else "unknown"

    timestamp_raw = data.get("timestamp")
    timestamp = str(timestamp_raw) if timestamp_raw is not None else ""

    actor_raw = data.get("actor")
    actor = str(actor_raw) if actor_raw is not None else ""

    return TransformedRecord(
        event_id=event_id,
        tenant_id=str(tenant_id),
        action=action,
        package=str(package),
        version=str(version),
        timestamp=timestamp,
        actor=actor,
    ) 


def parse_raw_data(line: str) -> TransformedRecord | FailedRecord:
    """Parse a raw JSON line into a TransformedRecord or FailedRecord.

    Required fields: tenant_id, package, version.
    Optional fields: event_id (uuid generated if absent), action (defaults to
    "unknown"), timestamp (defaults to ""), actor (defaults to "").

    Args:
        line: Raw JSON string to parse.

    Returns:
        TransformedRecord on success, FailedRecord on validation failure or
        parse error.
    """
    try:
        data = json.loads(line)

        if not isinstance(data, dict):
            logger.warning("JSON parsed but not a dict")
            return FailedRecord(raw_data=line, error_code="invalid_type")

        if failed_record := confirm_required_fields(data, line):
            return failed_record
        return build_transformed_record(data)
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse JSON: {str(e)[:100]}")
        return FailedRecord(raw_data=line, error_code="json_decode_error")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)[:100]}")
        return FailedRecord(raw_data=line, error_code="parse_error")
