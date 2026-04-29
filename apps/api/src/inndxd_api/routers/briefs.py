import logging
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends
from inndxd_core.models.brief import Brief
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from inndxd_api.dependencies import get_db, get_tenant_id
from inndxd_api.schemas.brief import BriefCreate, BriefRead

router = APIRouter()
logger = logging.getLogger(__name__)

logger.info("Briefs router initialized")


@router.post("/", response_model=BriefRead, status_code=status.HTTP_201_CREATED)
async def create_brief(
    body: BriefCreate,
    background_tasks: BackgroundTasks,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a new research brief."""
    logger.debug("Creating brief for tenant %s, project %s", tenant_id, body.project_id)

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

    logger.info("Brief created: %s", brief.id)
    return brief


@router.get("/", response_model=list[BriefRead])
async def list_briefs(
    project_id: UUID | None = None,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """List all briefs for a tenant."""
    logger.debug("Listing briefs for tenant %s", tenant_id)

    stmt = select(Brief).where(Brief.tenant_id == tenant_id).order_by(Brief.created_at.desc())
    if project_id:
        stmt = stmt.where(Brief.project_id == project_id)

    result = await db.execute(stmt)
    briefs = list(result.scalars().all())
    logger.info("Found %d briefs for tenant %s", len(briefs), tenant_id)
    return briefs


async def _update_brief_status(
    db: AsyncSession, brief_id: UUID, status: str, error: str | None = None
):
    """Update brief status with error context."""
    brief = await db.get(Brief, brief_id)
    if brief:
        brief.status = status
        db.add(brief)
        await db.commit()
        if error:
            logger.error("Brief %s set to %s: %s", brief_id, status, error)
        else:
            logger.info("Brief %s updated to %s", brief_id, status)
    else:
        logger.warning("Brief %s not found for status update", brief_id)


async def _run_research_task(
    brief_id: UUID,
    tenant_id: UUID,
    project_id: UUID,
    natural_language: str,
):
    """Run the research swarm in background with robust error handling."""
    logger.info("Starting research task for brief %s", brief_id)

    async with _get_async_session() as session:
        try:
            from inndxd_agents.swarm import run_research_swarm

            logger.info("Executing research swarm for brief %s", brief_id)
            result = await run_research_swarm(brief_id, tenant_id, project_id, natural_language)

            await _update_brief_status(session, brief_id, "completed")
            logger.info("Research completed successfully for brief %s", brief_id)
            return result

        except ImportError as exc:
            logger.error("Import error during research: %s", exc)
            await _update_brief_status(session, brief_id, "failed", "Import error: " + str(exc))
        except SQLAlchemyError as exc:
            logger.error("Database error during research: %s", exc, exc_info=True)
            await _update_brief_status(session, brief_id, "failed", "Database error: " + str(exc))
        except Exception as exc:
            logger.error("Unexpected error during research: %s", exc, exc_info=True)
            await _update_brief_status(session, brief_id, "failed", "Unexpected error: " + str(exc))


async def _get_async_session():
    """Get async session for task execution."""
    from inndxd_core.db import async_session_factory

    return async_session_factory()
