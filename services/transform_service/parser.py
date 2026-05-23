from __future__ import annotations

import json
import logging
from typing import Generator

from services.transform_service.models import FailedRecord, TransformedRecord


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

            try:
                data = json.loads(line)
                if not isinstance(data, dict):
                    yield FailedRecord(
                        raw_data=line,
                        error_code=f"invalid_type_line_{line_num}",
                    )
                    logger.warning(f"Line {line_num}: JSON parsed but not a dict")
                    continue

                yield TransformedRecord(
                    event_id=(str(data.get("event_id")) if data.get("event_id") is not None else None),
                    tenant_id=str(data.get("tenant_id", "")),
                    action=str(data.get("action", "")),
                    package=str(data.get("package", "")),
                    version=str(data.get("version", "")),
                    timestamp=str(data.get("timestamp", "")),
                    actor=(str(data.get("actor")) if data.get("actor") is not None else None),
                )
            except json.JSONDecodeError as e:
                yield FailedRecord(
                    raw_data=line,
                    error_code=f"json_decode_error_line_{line_num}",
                )
                logger.warning(
                    f"Line {line_num}: Failed to parse JSON: {str(e)[:100]}"
                )
            except Exception as e:
                yield FailedRecord(
                    raw_data=line,
                    error_code=f"parse_error_line_{line_num}",
                )
                logger.error(f"Line {line_num}: Unexpected error: {str(e)[:100]}")


def parse_raw_data(raw_data: dict[str, object]) -> dict[str, object]:
    """Parse raw ingestion data into a normalized dictionary.
    
    Args:
        raw_data: Raw data dictionary.
    
    Returns:
        Normalized data dictionary.
    """
    return raw_data.copy()
