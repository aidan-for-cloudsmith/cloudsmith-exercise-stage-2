from __future__ import annotations

import logging
from pathlib import Path

from transform_service.models import FailedRecord, TransformedRecord
from transform_service.parser import parse_jsonl_file
from transform_service.storage import quarantine_bad_record, save_transformed_record


logger = logging.getLogger(__name__)

parent_dir = Path(__file__).resolve().parent
events_file_path = parent_dir / "events.jsonl"


def main() -> None:
    """Main entry point for the transform service.

    Reads event.jsonl file and processes each line.
    """
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    logger.info("Transform service started")

    if not events_file_path.exists():
        logger.error("Event file not found: %s", events_file_path)
        return

    for record in parse_jsonl_file(str(events_file_path)):
        if isinstance(record, TransformedRecord):
            saved = save_transformed_record(record)
            logger.info("Saved transformed record %s for tenant %s", saved.event_id, saved.tenant_id)
        elif isinstance(record, FailedRecord):
            quarantine_bad_record(record, record.error_code)
            logger.warning("Quarantined bad record: %s", record.error_code)
        else:
            logger.error("Unknown record type encountered: %s", type(record))

    logger.info("Transform service finished processing %s", events_file_path)


if __name__ == "__main__":
    main()
