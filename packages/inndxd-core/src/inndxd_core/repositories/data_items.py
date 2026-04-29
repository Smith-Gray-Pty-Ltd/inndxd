# packages/inndxd-core/src/inndxd_core/repositories/data_items.py

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from inndxd_core.models.data_item import DataItem


class DataItemRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_by_tenant(
        self,
        tenant_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[DataItem]:
        stmt = (
            select(DataItem)
            .where(DataItem.tenant_id == tenant_id)
            .order_by(DataItem.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_project(
        self,
        project_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[DataItem]:
        stmt = (
            select(DataItem)
            .where(DataItem.project_id == project_id)
            .order_by(DataItem.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_brief(self, brief_id: UUID) -> list[DataItem]:
        stmt = (
            select(DataItem)
            .where(DataItem.brief_id == brief_id)
            .order_by(DataItem.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def bulk_insert(self, items: list[dict]) -> list[DataItem]:
        instances = [DataItem(**item) for item in items]
        self.session.add_all(instances)
        return instances
