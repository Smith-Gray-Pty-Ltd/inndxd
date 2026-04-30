import logging
from uuid import UUID

from fastapi import APIRouter, Depends
from inndxd_core.models.brief import Brief
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from inndxd_api.dependencies import get_db, get_tenant_id
from inndxd_api.metrics import briefs_created
from inndxd_api.schemas.brief import BriefCreate, BriefRead
from inndxd_api.tasks import run_research_task

router = APIRouter()
logger = logging.getLogger(__name__)

logger.info("Briefs router initialized")


@router.post("/", response_model=BriefRead, status_code=status.HTTP_201_CREATED)
async def create_brief(
    body: BriefCreate,
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

    briefs_created.inc()

    run_research_task.delay(
        str(brief.id), str(tenant_id), str(body.project_id), body.natural_language
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
