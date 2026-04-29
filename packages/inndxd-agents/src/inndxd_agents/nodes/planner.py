# packages/inndxd-agents/src/inndxd_agents/nodes/planner.py

import json
import logging

from inndxd_agents.llm import create_ollama_client
from inndxd_agents.prompts.planner import PLANNER_SYSTEM, PLANNER_USER
from inndxd_agents.state import ResearchState as AgentState

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "deepseek-r1:latest"


async def planner_node(state: AgentState) -> dict:
    client = create_ollama_client()
    user_prompt = PLANNER_USER.format(natural_language=state["natural_language"])

    response = await client.chat.completions.create(
        model=DEFAULT_MODEL,
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

    return {"plan": plan, "errors": errors}


def _extract_json(text: str) -> str:
    start = text.find("{")
    if start == -1:
        return text
    end = text.rfind("}")
    if end == -1:
        return text
    return text[start : end + 1]
