from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from inndxd_core.models.base import Base, TimestampMixin, UUIDMixin


class ProjectContext(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "project_contexts"

    project_id: Mapped[UUID] = mapped_column(
        PGUUID(), ForeignKey("projects.id"), unique=True, index=True, nullable=False
    )
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(), index=True, nullable=False)
    context_data: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
