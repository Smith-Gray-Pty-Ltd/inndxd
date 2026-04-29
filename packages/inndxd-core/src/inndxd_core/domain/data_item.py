from __future__ import annotations

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class DataItemCreate(BaseModel):
    project_id: UUID
    tenant_id: UUID
    brief_id: UUID
    source_url: str | None = None
    content_type: str
    raw_payload: dict
    structured_payload: dict


class DataItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    project_id: UUID
    tenant_id: UUID
    brief_id: UUID
    source_url: str | None
    content_type: str
    structured_payload: dict
    created_at: datetime
