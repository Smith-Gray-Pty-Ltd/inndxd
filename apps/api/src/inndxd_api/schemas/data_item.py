from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DataItemRead(BaseModel):
    id: UUID
    project_id: UUID
    tenant_id: UUID
    brief_id: UUID
    source_url: str | None
    content_type: str
    structured_payload: dict
    created_at: datetime


class DataItemList(BaseModel):
    data_items: list[DataItemRead]
