"""User repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from inndxd_core.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: UUID) -> User | None:
        return await self.session.get(User, user_id)

    async def create(self, email: str, hashed_password: str, tenant_id: str | None = None) -> User:
        user = User(
            email=email,
            hashed_password=hashed_password,
            tenant_id=UUID(tenant_id) if tenant_id else None,
        )
        self.session.add(user)
        await self.session.flush()
        return user
