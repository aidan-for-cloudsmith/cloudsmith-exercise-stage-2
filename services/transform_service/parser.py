from __future__ import annotations

import json
import logging
from typing import Generator


logger = logging.getLogger(__name__)


def parse_jsonl_file(
    filepath: str,
) -> Generator[tuple[dict[str, object], str | None], None, None]:
    """Parse event.jsonl file line by line with error handling.
    
    Yields tuples of (parsed_data, error_reason) where:
    - If line parses successfully: (data_dict, None)
    - If line fails to parse: ({}, error_reason_string)
    
    This generator never raises exceptions—it handles all parsing errors
    gracefully and yields them for quarantine handling.
    
    Args:
        filepath: Path to the event.jsonl file.
    
    Yields:
        Tuples of (parsed_dict, error_or_none).
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
                    yield {}, f"invalid_type_line_{line_num}"
                    logger.warning(f"Line {line_num}: JSON parsed but not a dict")
                    continue
                yield data, None
            except json.JSONDecodeError as e:
                yield {}, f"json_decode_error_line_{line_num}"
                logger.warning(
                    f"Line {line_num}: Failed to parse JSON: {str(e)[:100]}"
                )
            except Exception as e:
                yield {}, f"parse_error_line_{line_num}"
                logger.error(f"Line {line_num}: Unexpected error: {str(e)[:100]}")


def parse_raw_data(raw_data: dict[str, object]) -> dict[str, object]:
    """Parse raw ingestion data into a normalized dictionary.
    
    Args:
        raw_data: Raw data dictionary.
    
    Returns:
        Normalized data dictionary.
    """
    return raw_data.copy()
