from __future__ import annotations

from pydantic import BaseModel


class RecordResponse(BaseModel):
    id: str
    timestamp: str
    source: str
