"""LLM provider configuration model."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from inndxd_core.models.base import Base, TimestampMixin, UUIDMixin


class LLMProvider(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "llm_providers"

    tenant_id: Mapped[UUID] = mapped_column(PGUUID(), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    provider_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="openai_compatible"
    )
    base_url: Mapped[str] = mapped_column(Text, nullable=False)
    api_key: Mapped[str] = mapped_column(Text, nullable=False, default="")
    default_model: Mapped[str] = mapped_column(String(100), nullable=False)
    available_models: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
