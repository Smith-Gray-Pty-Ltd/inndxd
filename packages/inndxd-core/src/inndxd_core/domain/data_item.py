from __future__ import annotations

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from pydantic_core import JsonValue


class DataItemCreate(BaseModel):
    project_id: UUID
    tenant_id: UUID
    brief_id: UUID
    source_url: str | None = None
    content_type: str
    raw_payload: dict[str, JsonValue]
    structured_payload: dict[str, JsonValue]


class DataItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    project_id: UUID
    tenant_id: UUID
    brief_id: UUID
    source_url: str | None
    content_type: str
    structured_payload: dict[str, JsonValue]
    created_at: datetime