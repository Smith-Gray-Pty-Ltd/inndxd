"""JWT authentication dependencies."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from inndxd_core.auth import decode_access_token
from inndxd_core.db import async_session_factory
from inndxd_core.models.user import User

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(security),
    x_tenant_id: str | None = Header(None, alias="X-Tenant-ID"),
) -> dict[str, Any]:
    if credentials:
        token = credentials.credentials
        try:
            payload = decode_access_token(token)
            return {"user_id": payload["sub"], "tenant_id": payload.get("tenant_id")}
        except Exception as err:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            ) from err
    if x_tenant_id:
        try:
            UUID(x_tenant_id)
            return {"user_id": None, "tenant_id": x_tenant_id}
        except ValueError:
            pass
    return {"user_id": None, "tenant_id": None}


async def require_admin(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )
    async with async_session_factory() as session:
        user = await session.get(User, UUID(user_id))
        if not user or not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
            )
    return current_user
