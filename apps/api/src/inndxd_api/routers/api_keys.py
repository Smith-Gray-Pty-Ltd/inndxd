"""API Key management router."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from inndxd_core.repositories.api_keys import APIKeyRepository
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from inndxd_api.auth_deps import get_current_user
from inndxd_api.dependencies import get_db

router = APIRouter()


@router.get("/")
async def list_keys(
    user: dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Any]:
    user_id = user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    repo = APIKeyRepository(db)
    keys = await repo.list_for_user(UUID(user_id))
    return [
        {
            "id": str(k.id),
            "name": k.name,
            "key_prefix": k.key_prefix,
            "is_active": k.is_active,
            "created_at": str(k.created_at),
            "last_used_at": str(k.last_used_at) if k.last_used_at else None,
        }
        for k in keys
    ]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_key(
    name: str,
    user: dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    user_id = user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    repo = APIKeyRepository(db)
    key, raw = await repo.create(UUID(user_id), name)
    await db.commit()
    return {"id": str(key.id), "name": key.name, "raw_key": raw, "key_prefix": key.key_prefix}


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_key(
    key_id: UUID,
    user: dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    from inndxd_core.models.api_key import APIKey as APIKeyModel

    key_model = await db.get(APIKeyModel, key_id)
    if not key_model or str(key_model.user_id) != user["user_id"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    repo = APIKeyRepository(db)
    await repo.revoke(key_model)
    await db.commit()


@router.post("/{key_id}/rotate")
async def rotate_key(
    key_id: UUID,
    user: dict[str, Any] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    from inndxd_core.models.api_key import APIKey as APIKeyModel

    key_model = await db.get(APIKeyModel, key_id)
    if not key_model or str(key_model.user_id) != user["user_id"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    repo = APIKeyRepository(db)
    _, raw = await repo.rotate(key_model)
    await db.commit()
    return {"id": str(key_model.id), "key_prefix": key_model.key_prefix, "raw_key": raw}
