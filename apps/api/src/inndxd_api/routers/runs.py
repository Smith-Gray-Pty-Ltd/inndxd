from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from inndxd_core.models.brief import Brief
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from inndxd_api.celery_app import celery_app
from inndxd_api.dependencies import get_db, get_tenant_id
from inndxd_api.schemas.run import RunStatus

router = APIRouter()


@router.get("/{brief_id}", response_model=RunStatus)
async def get_run_status(
    brief_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    brief = await db.get(Brief, brief_id)
    if brief is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if brief.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return RunStatus(brief_id=brief.id, status=brief.status)


@router.get("/{brief_id}/task-status")
async def get_task_status(brief_id: UUID):
    """Get Celery task status for a brief."""
    from celery.result import AsyncResult

    result = AsyncResult(str(brief_id), app=celery_app)
    return {
        "brief_id": str(brief_id),
        "task_id": result.id,
        "status": result.status,
        "result": str(result.result) if result.ready() else None,
    }
