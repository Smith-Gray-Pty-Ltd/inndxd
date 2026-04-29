from __future__ import annotations

from uuid import UUID
from pydantic import BaseModel


class AgentState(BaseModel):
    brief_id: UUID
    tenant_id: UUID
    project_id: UUID
    natural_language: str
    messages: list[str]
    plan: str | None
    collected_data: list[dict]
    structured_items: list[dict]
    errors: list[str]