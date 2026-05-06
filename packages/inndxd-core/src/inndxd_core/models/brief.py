from __future__ import annotations

from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from inndxd_core.models.base import Base, TimestampMixin, UUIDMixin


class Brief(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "briefs"

    project_id: Mapped[UUID] = mapped_column(
        PGUUID(), ForeignKey("projects.id"), index=True, nullable=False
    )
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(), index=True, nullable=False)
    natural_language: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    parent_brief_id: Mapped[UUID | None] = mapped_column(
        PGUUID(), ForeignKey("briefs.id"), index=True, nullable=True
    )
