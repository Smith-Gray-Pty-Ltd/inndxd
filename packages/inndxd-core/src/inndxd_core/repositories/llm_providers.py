"""LLM Provider repository."""
from __future__ import annotations

import json
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from inndxd_core.models.llm_provider import LLMProvider


class LLMProviderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_by_tenant(self, tenant_id: UUID) -> list[LLMProvider]:
        result = await self.session.execute(
            select(LLMProvider)
            .where(LLMProvider.tenant_id == tenant_id)
            .order_by(LLMProvider.priority.desc())
        )
        return list(result.scalars().all())

    async def get_active_for_tenant(self, tenant_id: UUID) -> list[LLMProvider]:
        result = await self.session.execute(
            select(LLMProvider)
            .where(LLMProvider.tenant_id == tenant_id, LLMProvider.is_active)
            .order_by(LLMProvider.priority.desc())
        )
        return list(result.scalars().all())

    async def create(
        self,
        tenant_id: UUID,
        name: str,
        provider_type: str,
        base_url: str,
        api_key: str,
        default_model: str,
        available_models: list[str],
        priority: int,
    ) -> LLMProvider:
        provider = LLMProvider(
            tenant_id=tenant_id,
            name=name,
            provider_type=provider_type,
            base_url=base_url,
            api_key=api_key,
            default_model=default_model,
            available_models=json.dumps(available_models),
            priority=priority,
            is_active=True,
        )
        self.session.add(provider)
        await self.session.flush()
        return provider

    async def delete(self, provider: LLMProvider) -> None:
        await self.session.delete(provider)
        await self.session.flush()
