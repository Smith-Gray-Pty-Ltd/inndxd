from __future__ import annotations

from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from inndxd_core.models.base import Base, TimestampMixin, UUIDMixin


class DataItem(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "data_items"

    project_id: Mapped[UUID] = mapped_column(
        PGUUID(), ForeignKey("projects.id"), index=True, nullable=False
    )
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(), index=True, nullable=False)
    brief_id: Mapped[UUID] = mapped_column(PGUUID(), ForeignKey("briefs.id"), nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    raw_payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    structured_payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)
