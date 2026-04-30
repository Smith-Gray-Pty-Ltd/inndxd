"""API Key model."""

from __future__ import annotations

import secrets
from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from inndxd_core.auth import hash_password, verify_password
from inndxd_core.models.base import Base, TimestampMixin, UUIDMixin


class APIKey(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "api_keys"

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(), ForeignKey("users.id"), index=True, nullable=False
    )
    key_prefix: Mapped[str] = mapped_column(String(12), index=True, nullable=False)
    key_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    last_rotated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    usage_count: Mapped[int] = mapped_column(default=0, nullable=False)

    @staticmethod
    def generate_key() -> tuple[str, str, str]:
        raw = "inndxd_" + secrets.token_urlsafe(32)
        prefix = raw[:12]
        return raw, prefix, hash_password(raw)

    @staticmethod
    def verify_key(raw: str, hashed: str) -> bool:
        return verify_password(raw, hashed)
