import logging
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from inndxd_api.dependencies import get_db, get_tenant_id
from inndxd_api.schemas.brief import BriefCreate, BriefRead
from inndxd_core.models.brief import Brief

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=BriefRead, status_code=status.HTTP_201_CREATED)
async def create_brief(
    body: BriefCreate,
    background_tasks: BackgroundTasks,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    brief = Brief(
        tenant_id=tenant_id,
        project_id=body.project_id,
        natural_language=body.natural_language,
        status="pending",
    )
    db.add(brief)
    await db.commit()
    await db.refresh(brief)

    background_tasks.add_task(
        _run_research_task,
        brief.id,
        tenant_id,
        body.project_id,
        body.natural_language,
    )

    return brief


@router.get("/", response_model=list[BriefRead])
async def list_briefs(
    project_id: UUID | None = None,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Brief)
        .where(Brief.tenant_id == tenant_id)
        .order_by(Brief.created_at.desc())
    )
    if project_id:
        stmt = stmt.where(Brief.project_id == project_id)

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def _run_research_task(
    brief_id: UUID,
    tenant_id: UUID,
    project_id: UUID,
    natural_language: str,
):
    try:
        from inndxd_agents.swarm import run_research_swarm
        from inndxd_core.db import async_session_factory

        logger.info("Starting research for brief %s", brief_id)
        await run_research_swarm(brief_id, tenant_id, project_id, natural_language)

        async with async_session_factory() as session:
            brief = await session.get(Brief, brief_id)
            if brief:
                brief.status = "completed"
                session.add(brief)
                await session.commit()
            logger.info("Research completed for brief %s", brief_id)
    except Exception:
        async with async_session_factory() as session:
            brief = await session.get(Brief, brief_id)
            if brief:
                brief.status = "failed"
                session.add(brief)
                await session.commit()
        logger.exception("Research failed for brief %s", brief_id)
