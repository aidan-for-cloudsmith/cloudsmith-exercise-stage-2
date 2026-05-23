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
