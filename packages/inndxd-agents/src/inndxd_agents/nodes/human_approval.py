"""Human-in-the-loop approval node."""

import logging

from inndxd_agents.state import ResearchState as AgentState

logger = logging.getLogger(__name__)


async def human_approval_node(state: AgentState) -> dict:
    logger.info("Approval point reached for brief %s", state.get("brief_id"))
    logger.info("Plan: %s", state.get("plan"))
    logger.info("Collected %d items", len(state.get("collected_data", [])))
    return state
