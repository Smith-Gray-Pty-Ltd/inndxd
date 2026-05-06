from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from inndxd_core.models.base import Base, TimestampMixin, UUIDMixin


class Conversation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "conversations"

    tenant_id: Mapped[UUID] = mapped_column(PGUUID(), index=True, nullable=False)
    project_id: Mapped[UUID | None] = mapped_column(
        PGUUID(), ForeignKey("projects.id"), index=True, nullable=True
    )
    brief_id: Mapped[UUID | None] = mapped_column(
        PGUUID(), ForeignKey("briefs.id"), index=True, nullable=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
