from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class RunStatus(BaseModel):
    brief_id: UUID
    status: str
    errors: list[str] | None = None
