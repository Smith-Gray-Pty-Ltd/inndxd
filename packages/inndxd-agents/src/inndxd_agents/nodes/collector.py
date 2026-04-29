# packages/inndxd-agents/src/inndxd_agents/nodes/collector.py

import asyncio
import json
import logging

from inndxd_agents.state import ResearchState as AgentState
from inndxd_agents.tools.web_search import web_search_tool

logger = logging.getLogger(__name__)


async def collector_node(state: AgentState) -> dict:
    plan_raw = state.get("plan")
    errors: list[str] = []

    if not plan_raw:
        return {"collected_data": [], "errors": ["No plan available for collection"]}

    try:
        plan = json.loads(plan_raw)
    except json.JSONDecodeError:
        return {"collected_data": [], "errors": ["Could not parse plan JSON"]}

    queries: list[str] = plan.get("queries", [])

    if not queries:
        return {"collected_data": [], "errors": ["Plan contains no search queries"]}

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

    logger.info("Collector gathered %d results from %d queries", len(collected_data), len(queries))
    return {"collected_data": collected_data, "errors": errors}


async def _search_and_collect(query: str) -> list[dict]:
    results = await web_search_tool.ainvoke({"query": query, "max_results": 5})

    collected: list[dict] = []
    for r in results:
        collected.append({
            "url": r.url,
            "title": r.title,
            "text": r.text,
        })

    return collected
