"""Audit log repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from inndxd_core.models.audit_log import AuditLog


class AuditLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def log(
        self,
        tenant_id: UUID,
        event_type: str,
        actor: str,
        details: dict | None = None,
        brief_id: UUID | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            tenant_id=tenant_id,
            brief_id=brief_id,
            event_type=event_type,
            actor=actor,
            details=details or {},
        )
        self.session.add(entry)
        await self.session.flush()
        return entry

    async def list_by_tenant(self, tenant_id: UUID, limit: int = 100) -> list[AuditLog]:
        result = await self.session.execute(
            select(AuditLog)
            .where(AuditLog.tenant_id == tenant_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
