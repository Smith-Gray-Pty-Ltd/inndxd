from __future__ import annotations

from uuid import UUID
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from inndxd_core.models.base import Base, TimestampMixin, UUIDMixin


class Brief(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "briefs"

    project_id: Mapped[UUID] = mapped_column(
        PGUUID(), ForeignKey("projects.id"), index=True, nullable=False
    )
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(), index=True, nullable=False)
    natural_language: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False
    )