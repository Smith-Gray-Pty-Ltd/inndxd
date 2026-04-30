"""LLMProvider CRUD domain models."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LLMProviderCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    provider_type: str = Field(default="openai_compatible")
    base_url: str
    api_key: str = ""
    default_model: str
    available_models: list[str] = Field(default_factory=list)
    is_active: bool = True
    priority: int = 0


class LLMProviderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    name: str
    provider_type: str
    base_url: str
    default_model: str
    available_models: str
    is_active: bool
    priority: int
    created_at: datetime
    updated_at: datetime


class LLMProviderUpdate(BaseModel):
    name: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    default_model: str | None = None
    available_models: list[str] | None = None
    is_active: bool | None = None
    priority: int | None = None


class NodeModelAssignment(BaseModel):
    planner_model: str | None = None
    collector_model: str | None = None
    structurer_model: str | None = None
