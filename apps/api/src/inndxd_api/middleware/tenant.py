from contextvars import ContextVar
from uuid import UUID

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

current_tenant_id: ContextVar[UUID | None] = ContextVar("tenant_id", default=None)


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        tenant_id = request.headers.get("X-Tenant-ID")
        if tenant_id:
            try:
                tid = UUID(tenant_id)
                current_tenant_id.set(tid)
            except ValueError:
                pass
        response = await call_next(request)
        return response
