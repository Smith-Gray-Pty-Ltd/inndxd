"""Brief repository for data access."""

from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from inndxd_core.models.brief import Brief


class BriefRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, brief_id: UUID) -> Brief | None:
        return await self.session.get(Brief, brief_id)

    async def update_status(self, brief_id: UUID, status: str) -> None:
        stmt = update(Brief).where(Brief.id == brief_id).values(status=status)
        await self.session.execute(stmt)
