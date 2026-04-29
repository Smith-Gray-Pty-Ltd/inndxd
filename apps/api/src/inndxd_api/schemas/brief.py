from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class BriefCreate(BaseModel):
    project_id: UUID
    natural_language: str = Field(
        min_length=10,
        description="Free-text description of what data to collect and structure",
    )


class BriefRead(BaseModel):
    id: UUID
    project_id: UUID
    tenant_id: UUID
    natural_language: str
    status: str


class BriefList(BaseModel):
    briefs: list[BriefRead]
