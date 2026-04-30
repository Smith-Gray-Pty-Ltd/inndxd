"""Validates the planner output before collection proceeds."""

import json
import logging

from inndxd_agents.state import ResearchState as AgentState

logger = logging.getLogger(__name__)

REQUIRED_PLAN_KEYS = {"queries", "target_domains", "data_schema"}


async def plan_validator_node(state: AgentState) -> dict:
    plan_raw = state.get("plan")
    if not plan_raw:
        return {"errors": state.get("errors", []) + ["Plan is empty"]}

    try:
        plan = json.loads(plan_raw)
    except json.JSONDecodeError:
        return {"errors": state.get("errors", []) + ["Plan is not valid JSON"]}

    errors: list[str] = []
    for key in REQUIRED_PLAN_KEYS:
        if key not in plan:
            errors.append(f"Plan missing required key: {key}")

    if "queries" in plan and (not isinstance(plan["queries"], list) or len(plan["queries"]) == 0):
        errors.append("Plan has no search queries")

    if errors:
        logger.warning("Plan validation failed: %s", errors)
        return {"errors": state.get("errors", []) + errors}

    logger.info("Plan validated successfully with %d queries", len(plan["queries"]))
    return state
