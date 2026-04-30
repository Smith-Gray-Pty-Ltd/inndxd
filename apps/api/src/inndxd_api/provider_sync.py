"""Sync DB provider configs into the runtime LLM config."""
from __future__ import annotations

import json
import logging

from inndxd_agents.llm import set_llm_config
from inndxd_core.db import async_session_factory
from inndxd_core.domain.llm_provider import LLMConfig, LLMProviderConfig
from inndxd_core.models.llm_provider import LLMProvider
from sqlalchemy import select

logger = logging.getLogger(__name__)


def _build_default() -> LLMConfig:
    from inndxd_core.config import settings as core_settings

    return LLMConfig(
        default_provider="ollama",
        providers={
            "ollama": LLMProviderConfig(
                name="ollama",
                base_url=core_settings.ollama_base_url,
                api_key="ollama",
                default_model=core_settings.ollama_model,
                models=[core_settings.ollama_model],
            ),
        },
    )


async def sync_providers_for_tenant(tenant_id: str) -> LLMConfig:
    async with async_session_factory() as session:
        result = await session.execute(
            select(LLMProvider)
            .where(LLMProvider.tenant_id == tenant_id, LLMProvider.is_active)
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
