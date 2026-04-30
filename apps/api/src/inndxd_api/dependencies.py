from collections.abc import AsyncGenerator
from uuid import UUID

from fastapi import Header, HTTPException, status
from inndxd_core.db import async_session_factory
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from inndxd_api.middleware.tenant import current_tenant_id


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        await session.execute(
            text("SELECT set_config('app.current_tenant_id', :tid, false)"),
            {"tid": str(current_tenant_id.get())},
        )
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
        ) from None
    current_tenant_id.set(tenant_id)
    return tenant_id
