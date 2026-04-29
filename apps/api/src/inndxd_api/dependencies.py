from collections.abc import AsyncGenerator
from contextvars import ContextVar
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from inndxd_core.db import async_session_factory

current_tenant_id: ContextVar[UUID | None] = ContextVar("tenant_id", default=None)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session


def get_tenant_id(
    x_tenant_id: str = Header(..., alias="X-Tenant-ID"),
) -> UUID:
    try:
        tenant_id = UUID(x_tenant_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid X-Tenant-ID header",
        )
    current_tenant_id.set(tenant_id)
    return tenant_id
