# packages/inndxd-core/src/inndxd_core/repositories/projects.py

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from inndxd_core.models.project import Project


class ProjectRepository:
    model = Project

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        tenant_id: UUID,
        name: str,
        description: str | None = None,
    ) -> Project:
        project = Project(tenant_id=tenant_id, name=name, description=description)
        self.session.add(project)
        await self.session.flush()
        return project

    async def get_by_id(self, id: UUID) -> Project | None:
        return await self.session.get(Project, id)

    async def list_by_tenant(self, tenant_id: UUID) -> list[Project]:
        stmt = (
            select(Project)
            .where(Project.tenant_id == tenant_id)
            .order_by(Project.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, project: Project) -> None:
        await self.session.delete(project)
        await self.session.flush()
