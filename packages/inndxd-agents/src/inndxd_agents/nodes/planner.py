# packages/inndxd-agents/src/inndxd_agents/nodes/planner.py

import json
import logging
from typing import Any

from inndxd_agents.llm import create_ollama_client, resolve_model_for_node
from inndxd_agents.prompts.planner import PLANNER_SYSTEM, PLANNER_USER
from inndxd_agents.state import ResearchState as AgentState

logger = logging.getLogger(__name__)


async def planner_node(
    state: AgentState,
    llm_client: Any = None,
    model: str | None = None,
) -> dict:
    logger.debug("Entering planner_node for brief %s", state.get("brief_id"))
    if llm_client is None:
        llm_client = create_ollama_client()
    if model is None:
        model = resolve_model_for_node("planner")

    user_prompt = PLANNER_USER.format(natural_language=state["natural_language"])

    response = await llm_client.chat.completions.create(
        model=model,
        temperature=0.3,
        max_tokens=2048,
        messages=[
            {"role": "system", "content": PLANNER_SYSTEM},
            {"role": "user", "content": user_prompt},
        ],
    )

    content = response.choices[0].message.content or ""

    plan: str | None = None
    errors: list[str] = []

    try:
        cleaned = _extract_json(content)
        parsed = json.loads(cleaned)
        if not isinstance(parsed, dict):
            raise ValueError(f"Expected JSON object, got {type(parsed).__name__}")
        plan = json.dumps(parsed)
        logger.info("Planner produced valid plan with %d queries", len(parsed.get("queries", [])))
    except (json.JSONDecodeError, ValueError) as e:
        error_msg = f"Planner failed to produce valid JSON: {e}"
        logger.error(error_msg)
        errors.append(error_msg)
        plan = json.dumps({"queries": [], "target_domains": [], "data_schema": {}})

    logger.info("planner_node completed for brief %s", state.get("brief_id"))
    return {"plan": plan, "errors": errors, "planner_retries": state.get("planner_retries", 0) + 1}


def _extract_json(text: str) -> str:
    start = text.find("{")
    if start == -1:
        return text
    end = text.rfind("}")
    if end == -1:
        return text
    return text[start : end + 1]
