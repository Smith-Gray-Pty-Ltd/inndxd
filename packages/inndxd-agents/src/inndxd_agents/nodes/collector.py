# packages/inndxd-agents/src/inndxd_agents/nodes/collector.py

import asyncio
import json
import logging

from inndxd_agents.state import ResearchState as AgentState
from inndxd_agents.tools.web_search import web_search_tool

logger = logging.getLogger(__name__)


async def collector_node(state: AgentState) -> dict:
    logger.debug("Entering collector_node for brief %s", state.get("brief_id"))

    plan_raw = state.get("plan")
    errors: list[str] = []

    if not plan_raw:
        logger.info("collector_node: no plan available for brief %s", state.get("brief_id"))
        return {
            "collected_data": [],
            "errors": ["No plan available for collection"],
            "collector_retries": state.get("collector_retries", 0) + 1,
        }

    try:
        plan = json.loads(plan_raw)
    except json.JSONDecodeError:
        logger.info("collector_node: bad plan JSON for brief %s", state.get("brief_id"))
        return {
            "collected_data": [],
            "errors": ["Could not parse plan JSON"],
            "collector_retries": state.get("collector_retries", 0) + 1,
        }

    queries: list[str] = plan.get("queries", [])

    if not queries:
        logger.info("collector_node: no queries in plan for brief %s", state.get("brief_id"))
        return {
            "collected_data": [],
            "errors": ["Plan contains no search queries"],
            "collector_retries": state.get("collector_retries", 0) + 1,
        }

    tasks = [_search_and_collect(q) for q in queries]
    results_per_query = await asyncio.gather(*tasks, return_exceptions=True)

    collected_data: list[dict] = []
    for i, result in enumerate(results_per_query):
        if isinstance(result, Exception):
            error_msg = f"Query '{queries[i]}' failed: {result}"
            logger.error(error_msg)
            errors.append(error_msg)
            continue
        collected_data.extend(result)

    logger.info(
        "collector_node: gathered %d results from %d queries for brief %s",
        len(collected_data),
        len(queries),
        state.get("brief_id"),
    )
    return {
        "collected_data": collected_data,
        "errors": errors,
        "collector_retries": state.get("collector_retries", 0) + 1,
    }


async def _search_and_collect(query: str) -> list[dict]:
    results = await web_search_tool.ainvoke({"query": query, "max_results": 5})

    collected: list[dict] = []
    for r in results:
        collected.append(
            {
                "url": r.url,
                "title": r.title,
                "text": r.text,
            }
        )

    return collected
