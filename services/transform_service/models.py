from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TransformedRecord:
    event_id: str | None 
    tenant_id: str
    action: str
    package: str
    version: str
    timestamp: str
    actor: str | None


@dataclass
class FailedRecord:
    """Represents a record that failed validation or transformation."""
    raw_data: str
    error_code: str
    event_id: str | None = None
    