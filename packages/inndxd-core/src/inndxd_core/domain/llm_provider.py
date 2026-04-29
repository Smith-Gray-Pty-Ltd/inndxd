"""LLM provider configuration domain model."""
from __future__ import annotations

from pydantic import BaseModel, Field


class LLMProviderConfig(BaseModel):
    name: str = Field(description="Unique provider identifier, e.g. 'ollama', 'openai', 'anthropic'")
    base_url: str = Field(description="API base URL for OpenAI-compatible endpoint")
    api_key: str = Field(default="", description="API key for the provider")
    default_model: str = Field(description="Default model name, e.g. 'deepseek-r1:latest' or 'gpt-4o'")
    models: list[str] = Field(
        default_factory=list,
        description="List of available model names on this provider",
    )


class LLMConfig(BaseModel):
    default_provider: str = Field(
        default="ollama",
        description="Default provider name to use when none specified per-node",
    )
    providers: dict[str, LLMProviderConfig] = Field(
        default_factory=dict,
        description="Map of provider name to provider config",
    )
