"""Embedding generation via Ollama API."""
from __future__ import annotations

import httpx


async def generate_embedding(
    text: str, base_url: str = "http://localhost:11434"
) -> list[float] | None:
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{base_url}/api/embeddings",
                json={"model": "nomic-embed-text", "prompt": text},
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("embedding")
    except Exception:
        pass
    return None
