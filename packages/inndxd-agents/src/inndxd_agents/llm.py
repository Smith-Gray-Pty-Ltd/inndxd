from __future__ import annotations

from openai import AsyncOpenAI

from inndxd_agents.config import settings


def create_ollama_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        base_url=settings.ollama_base_url,
        api_key="ollama",
    )