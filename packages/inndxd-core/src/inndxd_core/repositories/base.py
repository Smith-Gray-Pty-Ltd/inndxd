# packages/inndxd-core/src/inndxd_core/repositories/base.py

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository:
    model: type

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, id: UUID) -> object | None:
        return await self.session.get(self.model, id)

    async def list_by_tenant(
        self,
        tenant_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[object]:
        stmt = (
            select(self.model)
            .where(self.model.tenant_id == tenant_id)
            .order_by(self.model.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def add(self, instance: object) -> object:
        self.session.add(instance)
        return instance

    async def delete(self, instance: object) -> None:
        await self.session.delete(instance)
