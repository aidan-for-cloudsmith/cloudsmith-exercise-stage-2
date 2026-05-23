from __future__ import annotations


def fetch_from_storage(record_id: str) -> dict[str, str]:
    return {"id": record_id, "timestamp": "", "source": ""}
