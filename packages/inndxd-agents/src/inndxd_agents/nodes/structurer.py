# packages/inndxd-agents/src/inndxd_agents/nodes/structurer.py

import json
import logging
from typing import Any

from inndxd_agents.llm import create_openai_compatible_client, resolve_model_for_node
from inndxd_agents.prompts.structurer import STRUCTURER_SYSTEM, STRUCTURER_USER
from inndxd_agents.state import ResearchState as AgentState

logger = logging.getLogger(__name__)


async def structurer_node(
    state: AgentState,
    llm_client: Any = None,
    model: str | None = None,
) -> dict:
    logger.debug("Entering structurer_node for brief %s", state.get("brief_id"))
    plan_raw = state.get("plan")
    collected_data = state.get("collected_data", [])

    if not plan_raw or not collected_data:
        return {
            "structured_items": [],
            "errors": ["Missing plan or collected data"],
            "structurer_retries": state.get("structurer_retries", 0) + 1,
        }

    try:
        plan = json.loads(plan_raw)
        data_schema = json.dumps(plan.get("data_schema", {}))
    except json.JSONDecodeError:
        return {
            "structured_items": [],
            "errors": ["Could not parse plan JSON"],
            "structurer_retries": state.get("structurer_retries", 0) + 1,
        }

    if llm_client is None:
        llm_client = create_openai_compatible_client()
    if model is None:
        model = resolve_model_for_node("structurer")

    trimmed = []
    for item in collected_data:
        trimmed.append(
            {k: (v[:500] if isinstance(v, str) and len(v) > 500 else v) for k, v in item.items()}
        )
    data_json = json.dumps(trimmed[:10], indent=2)
    logger.info(
        "Structurer processing %d trimmed items from %d collected",
        len(trimmed[:10]),
        len(collected_data),
    )

    user_prompt = STRUCTURER_USER.format(
        natural_language=state["natural_language"],
        data_schema=data_schema,
        collected_data=data_json,
    )

    response = await llm_client.chat.completions.create(
        model=model,
        temperature=0.2,
        max_tokens=4096,
        messages=[
            {"role": "system", "content": STRUCTURER_SYSTEM},
            {"role": "user", "content": user_prompt},
        ],
    )

    content = response.choices[0].message.content or ""
    logger.info("Structurer LLM response: %d chars (first 200: %s)", len(content), content[:200])
    structured_items: list[dict] = []
    errors: list[str] = []

    try:
        cleaned = _extract_json_array(content)
        parsed = json.loads(cleaned)
        if not isinstance(parsed, list):
            raise ValueError(f"Expected JSON array, got {type(parsed).__name__}")

        for item in parsed:
            item.setdefault("project_id", str(state["project_id"]))
            item.setdefault("tenant_id", str(state["tenant_id"]))
            item.setdefault("brief_id", str(state["brief_id"]))
            item.setdefault("source_url", item.get("source_url"))
            item.setdefault("content_type", item.get("content_type", "web_page"))
            item.setdefault("raw_payload", {})
            # structured_payload defaults to {} on model

        structured_items = parsed
        logger.info("Structurer produced %d structured items", len(structured_items))
    except (json.JSONDecodeError, ValueError) as e:
        error_msg = f"Structurer failed to parse output: {e}"
        logger.error(error_msg)
        errors.append(error_msg)

    if not structured_items and collected_data:
        structured_items = []
        for item in collected_data[:20]:
            structured_items.append(
                {
                    "source_url": item.get("url", ""),
                    "content_type": "web_page",
                    "structured_payload": {
                        "title": item.get("title", ""),
                        "snippet": (item.get("text", "") or "")[:500],
                        "url": item.get("url", ""),
                    },
                    "raw_payload": item,
                    "project_id": str(state["project_id"]),
                    "tenant_id": str(state["tenant_id"]),
                    "brief_id": str(state["brief_id"]),
                }
            )
        logger.info("Structurer fallback: using %d raw items", len(structured_items))

    logger.info("structurer_node completed for brief %s", state.get("brief_id"))
    return {
        "structured_items": structured_items,
        "errors": errors,
        "structurer_retries": state.get("structurer_retries", 0) + 1,
    }


def _extract_json_array(text: str) -> str:
    start = text.find("[")
    if start == -1:
        return text
    end = text.rfind("]")
    if end == -1:
        return text
    return text[start : end + 1]
