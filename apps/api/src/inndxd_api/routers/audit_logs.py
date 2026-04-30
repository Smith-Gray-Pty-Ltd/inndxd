"""Audit log viewer — admin only."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from inndxd_core.repositories.audit_logs import AuditLogRepository
from sqlalchemy.ext.asyncio import AsyncSession

from inndxd_api.auth_deps import require_admin
from inndxd_api.dependencies import get_db, get_tenant_id

router = APIRouter()


@router.get("/")
async def list_audit_logs(
    limit: int = Query(default=100, ge=1, le=1000),
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
    _: dict[str, Any] = Depends(require_admin),
) -> list[dict[str, Any]]:
    repo = AuditLogRepository(db)
    logs = await repo.list_by_tenant(tenant_id, limit=limit)
    return [
        {
            "id": str(log.id),
            "event_type": log.event_type,
            "actor": log.actor,
            "status": log.status,
            "details": log.details,
            "created_at": str(log.created_at),
        }
        for log in logs
    ]
