"""Sync DB provider configs into the runtime LLM config."""

from __future__ import annotations

import json
import logging
from uuid import UUID

from inndxd_agents.llm import set_llm_config
from inndxd_core.db import async_session_factory
from inndxd_core.domain.llm_provider import LLMConfig, LLMProviderConfig
from inndxd_core.models.llm_provider import LLMProvider
from sqlalchemy import select

logger = logging.getLogger(__name__)


def _build_default() -> LLMConfig:
    from inndxd_core.config import settings as core_settings

    return LLMConfig(
        default_provider=core_settings.llm_provider_name,
        providers={
            core_settings.llm_provider_name: LLMProviderConfig(
                name=core_settings.llm_provider_name,
                base_url=core_settings.llm_base_url,
                api_key=core_settings.llm_api_key,
                default_model=core_settings.llm_model,
                models=[core_settings.llm_model],
            ),
        },
    )


async def _seed_default_provider(tenant_id: UUID) -> None:
    """Insert a DB row for the default provider if none exist."""
    from inndxd_core.config import settings as core_settings
    from inndxd_core.repositories.llm_providers import LLMProviderRepository

    async with async_session_factory() as session:
        result = await session.execute(
            select(LLMProvider).where(LLMProvider.tenant_id == tenant_id).limit(1)
        )
        if result.scalar_one_or_none() is not None:
            return

        repo = LLMProviderRepository(session)
        await repo.create(
            tenant_id=tenant_id,
            name=core_settings.llm_provider_name,
            provider_type=core_settings.llm_provider_type,
            base_url=core_settings.llm_base_url,
            api_key=core_settings.llm_api_key,
            default_model=core_settings.llm_model,
            available_models=[core_settings.llm_model],
            priority=0,
        )
        await session.commit()
        logger.info(
            "Seeded default provider '%s' (%s) for tenant %s",
            core_settings.llm_provider_name,
            core_settings.llm_base_url,
            tenant_id,
        )


async def sync_providers_for_tenant(tenant_id: str) -> LLMConfig:
    try:
        tid = UUID(tenant_id)
    except ValueError:
        tid = UUID("00000000-0000-0000-0000-000000000000")

    await _seed_default_provider(tid)

    async with async_session_factory() as session:
        result = await session.execute(
            select(LLMProvider)
            .where(LLMProvider.tenant_id == tid, LLMProvider.is_active)
            .order_by(LLMProvider.priority.desc())
        )
        rows = list(result.scalars().all())

    if not rows:
        config = _build_default()
        set_llm_config(config)
        return config

    providers: dict[str, LLMProviderConfig] = {}
    for row in rows:
        try:
            available = json.loads(row.available_models)
        except (json.JSONDecodeError, TypeError):
            available = [row.default_model]
        providers[row.name] = LLMProviderConfig(
            name=row.name,
            base_url=row.base_url,
            api_key=row.api_key,
            default_model=row.default_model,
            models=available,
        )

    config = LLMConfig(default_provider=rows[0].name, providers=providers)
    set_llm_config(config)
    logger.info("Synced %d providers for tenant %s", len(providers), tenant_id)
    return config
