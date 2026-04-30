"""LLM client factory supporting multiple providers with failover."""

from __future__ import annotations

import logging

from inndxd_core.domain.llm_provider import LLMConfig, LLMProviderConfig
from openai import AsyncOpenAI

from inndxd_agents.config import settings as agent_settings

logger = logging.getLogger(__name__)


def _build_default_llm_config() -> LLMConfig:
    return LLMConfig(
        default_provider="ollama",
        providers={
            "ollama": LLMProviderConfig(
                name="ollama",
                base_url=agent_settings.ollama_base_url,
                api_key="ollama",
                default_model=agent_settings.ollama_model,
                models=[agent_settings.ollama_model],
            ),
        },
    )


_current_llm_config: LLMConfig | None = None


def get_llm_config() -> LLMConfig:
    global _current_llm_config
    if _current_llm_config is None:
        _current_llm_config = _build_default_llm_config()
    return _current_llm_config


def set_llm_config(config: LLMConfig) -> None:
    global _current_llm_config
    _current_llm_config = config


def create_ollama_client() -> AsyncOpenAI:
    return create_openai_compatible_client("ollama")


def create_openai_compatible_client(provider_name: str | None = None) -> AsyncOpenAI:
    config = get_llm_config()
    provider_name = provider_name or config.default_provider

    provider = config.providers.get(provider_name)
    if provider is None:
        if config.providers:
            provider = next(iter(config.providers.values()))
        else:
            raise ValueError(
                f"No LLM provider configured. Available: {list(config.providers.keys())}"
            )

    return AsyncOpenAI(
        base_url=provider.base_url,
        api_key=provider.api_key or "no-key",
    )


def get_default_model(provider_name: str | None = None) -> str:
    config = get_llm_config()
    provider_name = provider_name or config.default_provider
    provider = config.providers.get(provider_name)
    if provider:
        return provider.default_model
    return agent_settings.ollama_model


def resolve_model_for_node(node_name: str, tenant_id: str | None = None) -> str:
    """Return the model name for a given agent node.

    Priority:
    1. Per-node env var (INNDXD_PLANNER_MODEL, etc.)
    2. Runtime node assignments from DB
    3. Default model from provider config
    """
    env_override: dict[str, str | None] = {
        "planner": agent_settings.planner_model,
        "collector": agent_settings.collector_model,
        "structurer": agent_settings.structurer_model,
    }
    overridden = env_override.get(node_name)
    if overridden:
        return overridden

    if tenant_id:
        try:
            from inndxd_api.routers.llm_providers import _node_assignments

            assignments = _node_assignments.get(tenant_id, {})
            model = assignments.get(node_name)  # type: ignore[assignment]
            if model:
                return str(model)
        except ImportError:
            pass

    return get_default_model()


def create_client_with_failover(tenant_id: str | None = None) -> AsyncOpenAI:
    config = get_llm_config()
    providers = list(config.providers.values())

    if not providers:
        raise ValueError("No LLM providers configured")

    for provider in providers:
        try:
            return AsyncOpenAI(
                base_url=provider.base_url,
                api_key=provider.api_key or "no-key",
            )
        except Exception:
            logger.warning("Provider %s unavailable, trying next", provider.name)
            continue

    raise ValueError("All LLM providers failed")
