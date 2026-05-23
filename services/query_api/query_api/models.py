from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class RecordResponse(BaseModel):
    id: str
    timestamp: str
    source: str


class ActionType(StrEnum):
    DOWNLOAD = "download"
    UPLOAD = "upload"
    DELETE = "delete"


class EventResponse(BaseModel):
    event_id: str | None
    tenant_id: str
    action: ActionType | str
    package: str
    version: str
    timestamp: datetime | str
    actor: str | None


class EventListResponse(BaseModel):
    events: list[EventResponse]
    count: int


class RetentionResponse(BaseModel):
    tenant: str
    retention_days: int
    deleted: int
