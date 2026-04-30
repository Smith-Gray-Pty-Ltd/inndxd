"""Recursive research node — generate follow-up queries from results."""

from __future__ import annotations

import json
import logging

from inndxd_agents.state import ResearchState

logger = logging.getLogger(__name__)

RECURSIVE_SYSTEM = (
    "You are a recursive research agent. Given a set of research results, "
    "identify gaps and generate 2-3 follow-up search queries that would fill "
    "those gaps. Output ONLY a JSON array of query strings."
)


async def recursive_node(state: ResearchState, depth: int = 0, max_depth: int = 2) -> dict:
    if depth >= max_depth:
        return {}

    structured = state.get("structured_items", [])
    if len(structured) < 3:
        return {}

    from inndxd_agents.llm import create_ollama_client, resolve_model_for_node

    client = create_ollama_client()
    model = resolve_model_for_node("planner")

    response = await client.chat.completions.create(
        model=model,
        temperature=0.5,
        max_tokens=512,
        messages=[
            {"role": "system", "content": RECURSIVE_SYSTEM},
            {"role": "user", "content": json.dumps(structured, indent=2)},
        ],
    )

    content = response.choices[0].message.content or ""
    try:
        cleaned = content[content.find("[") : content.rfind("]") + 1] if "[" in content else "[]"
        follow_ups = json.loads(cleaned)
        logger.info("Generated %d recursive follow-up queries", len(follow_ups))
        return {"follow_up_queries": follow_ups}
    except (json.JSONDecodeError, ValueError):
        return {}
