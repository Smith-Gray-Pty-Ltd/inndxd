# packages/inndxd-agents/src/inndxd_agents/nodes/structurer.py

import json
import logging

from inndxd_agents.config import settings
from inndxd_agents.llm import create_ollama_client
from inndxd_agents.prompts.structurer import STRUCTURER_SYSTEM, STRUCTURER_USER
from inndxd_agents.state import ResearchState as AgentState

logger = logging.getLogger(__name__)


async def structurer_node(state: AgentState) -> dict:
    plan_raw = state.get("plan")
    collected_data = state.get("collected_data", [])

    if not plan_raw or not collected_data:
        return {"structured_items": [], "errors": ["Missing plan or collected data"]}

    try:
        plan = json.loads(plan_raw)
        data_schema = json.dumps(plan.get("data_schema", {}))
    except json.JSONDecodeError:
        return {"structured_items": [], "errors": ["Could not parse plan JSON"]}

    client = create_ollama_client()

    user_prompt = STRUCTURER_USER.format(
        natural_language=state["natural_language"],
        data_schema=data_schema,
        collected_data=json.dumps(collected_data, indent=2),
    )

    response = await client.chat.completions.create(
        model=settings.ollama_model,
        temperature=0.2,
        max_tokens=4096,
        messages=[
            {"role": "system", "content": STRUCTURER_SYSTEM},
            {"role": "user", "content": user_prompt},
        ],
    )

    content = response.choices[0].message.content or ""
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
            item.setdefault("structured_payload", item)

        structured_items = parsed
        logger.info("Structurer produced %d structured items", len(structured_items))
    except (json.JSONDecodeError, ValueError) as e:
        error_msg = f"Structurer failed to parse output: {e}"
        logger.error(error_msg)
        errors.append(error_msg)

    return {"structured_items": structured_items, "errors": errors}


def _extract_json_array(text: str) -> str:
    start = text.find("[")
    if start == -1:
        return text
    end = text.rfind("]")
    if end == -1:
        return text
    return text[start : end + 1]
