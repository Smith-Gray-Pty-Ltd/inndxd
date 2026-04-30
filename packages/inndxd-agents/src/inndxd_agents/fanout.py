"""Multi-agent fan-out research graph."""

from __future__ import annotations

import asyncio
import json
import logging

logger = logging.getLogger(__name__)


async def fan_out_research(plan: str, state: dict, max_parallel: int = 3) -> list[dict]:
    plan_data = json.loads(plan)
    queries = plan_data.get("queries", [])

    from inndxd_agents.graph import build_research_graph

    async def _run_query(query: str):
        sub_state = {
            **state,
            "plan": json.dumps({"queries": [query], "target_domains": [], "data_schema": {}}),
        }
        graph = build_research_graph()
        result = await graph.ainvoke(sub_state)
        return result.get("structured_items", [])

    semaphore = asyncio.Semaphore(max_parallel)

    async def _bounded(q):
        async with semaphore:
            return await _run_query(q)

    all_results_groups = await asyncio.gather(
        *[_bounded(q) for q in queries], return_exceptions=True
    )

    merged: list[dict] = []
    for group in all_results_groups:
        if isinstance(group, Exception):
            logger.error("Fan-out query failed: %s", group)
            continue
        merged.extend(group)

    return merged
