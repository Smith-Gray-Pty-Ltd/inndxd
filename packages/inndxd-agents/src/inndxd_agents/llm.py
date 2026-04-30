"""LLM client factory supporting multiple providers."""

from __future__ import annotations

from inndxd_core.domain.llm_provider import LLMConfig, LLMProviderConfig
from openai import AsyncOpenAI

from inndxd_agents.config import settings


def _build_default_llm_config() -> LLMConfig:
    return LLMConfig(
        default_provider="ollama",
        providers={
            "ollama": LLMProviderConfig(
                name="ollama",
                base_url=settings.ollama_base_url,
                api_key="ollama",
                default_model=settings.ollama_model,
                models=[settings.ollama_model],
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
    return settings.ollama_model


def resolve_model_for_node(node_name: str) -> str:
    """Return the model name for a given agent node.

    Priority:
    1. Per-node env var (INNDXD_PLANNER_MODEL, etc.)
    2. Default ollama_model setting
    """
    from inndxd_agents.config import settings as agent_settings

    node_model_map = {
        "planner": agent_settings.planner_model,
        "collector": agent_settings.collector_model,
        "structurer": agent_settings.structurer_model,
    }
    overridden = node_model_map.get(node_name)
    if overridden:
        return overridden
    return get_default_model()
