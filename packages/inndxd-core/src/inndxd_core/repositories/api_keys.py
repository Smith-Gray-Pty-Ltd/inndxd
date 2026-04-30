"""API Key repository."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from inndxd_core.models.api_key import APIKey


class APIKeyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_user(self, user_id: UUID) -> list[APIKey]:
        result = await self.session.execute(select(APIKey).where(APIKey.user_id == user_id))
        return list(result.scalars().all())

    async def create(self, user_id: UUID, name: str) -> tuple[APIKey, str]:
        raw, prefix, key_hash = APIKey.generate_key()
        key = APIKey(user_id=user_id, key_prefix=prefix, key_hash=key_hash, name=name)
        self.session.add(key)
        await self.session.flush()
        return key, raw

    async def revoke(self, key: APIKey) -> None:
        key.is_active = False
        await self.session.flush()

    async def rotate(self, key: APIKey) -> tuple[APIKey, str]:
        raw, prefix, key_hash = APIKey.generate_key()
        key.key_prefix = prefix
        key.key_hash = key_hash
        key.last_rotated_at = datetime.now(UTC)
        await self.session.flush()
        return key, raw
