from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from inndxd_api.dependencies import get_db, get_tenant_id
from inndxd_api.schemas.project import ProjectCreate, ProjectList, ProjectRead
from inndxd_core.repositories.projects import ProjectRepository

router = APIRouter()


@router.post("/", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectCreate,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    repo = ProjectRepository(db)
    project = await repo.create(
        tenant_id=tenant_id,
        name=body.name,
        description=body.description,
    )
    await db.commit()
    return project


@router.get("/", response_model=ProjectList)
async def list_projects(
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    repo = ProjectRepository(db)
    projects = await repo.list_by_tenant(tenant_id)
    return ProjectList(projects=projects)


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    repo = ProjectRepository(db)
    project = await repo.get_by_id(project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if project.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    repo = ProjectRepository(db)
    project = await repo.get_by_id(project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if project.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    await repo.delete(project)
    await db.commit()
    return None
