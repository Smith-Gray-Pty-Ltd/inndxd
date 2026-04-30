"""LLM Provider management router — admin only."""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from inndxd_core.domain.llm_provider_crud import (
    LLMProviderCreate,
    LLMProviderRead,
    LLMProviderUpdate,
    NodeModelAssignment,
)
from inndxd_core.repositories.llm_providers import LLMProviderRepository
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from inndxd_api.auth_deps import require_admin
from inndxd_api.dependencies import get_db, get_tenant_id
from inndxd_api.provider_health import check_provider_health
from inndxd_api.provider_sync import sync_providers_for_tenant

router = APIRouter()
_node_assignments: dict[str, dict[str, str | None]] = {}


@router.get("/", response_model=list[LLMProviderRead])
async def list_providers(
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
    _: dict[str, Any] = Depends(require_admin),
) -> list[LLMProviderRead]:
    repo = LLMProviderRepository(db)
    return await repo.list_by_tenant(tenant_id)  # type: ignore[return-value]


@router.post("/", response_model=LLMProviderRead, status_code=status.HTTP_201_CREATED)
async def create_provider(
    body: LLMProviderCreate,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
    _: dict[str, Any] = Depends(require_admin),
) -> LLMProviderRead:
    repo = LLMProviderRepository(db)
    provider = await repo.create(
        tenant_id=tenant_id,
        name=body.name,
        provider_type=body.provider_type,
        base_url=body.base_url,
        api_key=body.api_key,
        default_model=body.default_model,
        available_models=body.available_models,
        priority=body.priority,
    )
    await db.commit()
    return provider  # type: ignore[return-value]


@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_provider(
    provider_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: dict[str, Any] = Depends(require_admin),
) -> None:
    from inndxd_core.models.llm_provider import LLMProvider as LLMProviderModel

    provider = await db.get(LLMProviderModel, provider_id)
    if not provider:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    repo = LLMProviderRepository(db)
    await repo.delete(provider)
    await db.commit()


@router.patch("/{provider_id}", response_model=LLMProviderRead)
async def update_provider(
    provider_id: UUID,
    body: LLMProviderUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict[str, Any] = Depends(require_admin),
) -> LLMProviderRead:
    from inndxd_core.models.llm_provider import LLMProvider as LLMProviderModel

    provider = await db.get(LLMProviderModel, provider_id)
    if not provider:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    update_data = body.model_dump(exclude_unset=True)
    if "available_models" in update_data:
        update_data["available_models"] = json.dumps(update_data["available_models"])
    for key, value in update_data.items():
        setattr(provider, key, value)
    await db.commit()
    await db.refresh(provider)
    return provider  # type: ignore[return-value]


@router.post("/{provider_id}/health")
async def health_check_provider(
    provider_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    from inndxd_core.models.llm_provider import LLMProvider as LLMProviderModel

    provider_model = await db.get(LLMProviderModel, provider_id)
    if not provider_model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    healthy = await check_provider_health(
        provider_model.base_url, provider_model.api_key, provider_model.default_model
    )
    return {"provider_id": str(provider_id), "healthy": healthy}


@router.get("/node-assignments")
async def get_node_assignments(
    _: dict[str, Any] = Depends(require_admin),
) -> dict[str, dict[str, str | None]]:
    return _node_assignments


@router.put("/node-assignments")
async def set_node_assignments(
    body: NodeModelAssignment,
    tenant_id: UUID = Depends(get_tenant_id),
    _: dict[str, Any] = Depends(require_admin),
) -> dict[str, str]:
    tid = str(tenant_id)
    _node_assignments[tid] = {
        "planner": body.planner_model,
        "collector": body.collector_model,
        "structurer": body.structurer_model,
    }
    return {"status": "ok"}


@router.post("/sync")
async def sync_providers(
    tenant_id: UUID = Depends(get_tenant_id),
    _: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    config = await sync_providers_for_tenant(str(tenant_id))
    return {"status": "synced", "providers": list(config.providers.keys())}
