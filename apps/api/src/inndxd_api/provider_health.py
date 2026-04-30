"""LLM provider health check utilities."""
from __future__ import annotations

import logging

import httpx
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


async def check_provider_health(base_url: str, api_key: str, model: str) -> bool:
    client = AsyncOpenAI(base_url=base_url, api_key=api_key or "no-key")
    try:
        models = await client.models.list()
        return any(m.id == model for m in models.data)
    except Exception:
        pass
    try:
        async with httpx.AsyncClient(timeout=10.0) as http:
            resp = await http.get(f"{base_url.rstrip('/')}/models")
            if resp.status_code == 200:
                data = resp.json()
                models_list = data.get("data", data.get("models", []))
                for m in models_list:
                    if m.get("id", m.get("name", "")) == model:
                        return True
        return False
    except Exception as exc:
        logger.debug("Health check failed for %s: %s", base_url, exc)
        return False
