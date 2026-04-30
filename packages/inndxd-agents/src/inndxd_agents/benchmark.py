"""Agent performance benchmarking utility."""

from __future__ import annotations

import logging
import time
from uuid import uuid4

logger = logging.getLogger(__name__)


async def benchmark_research(natural_language: str, runs: int = 3) -> dict:
    from inndxd_agents.graph import build_research_graph

    graph = build_research_graph()
    durations: list[float] = []
    items_counts: list[int] = []

    for i in range(runs):
        state = {
            "brief_id": str(uuid4()),
            "tenant_id": str(uuid4()),
            "project_id": str(uuid4()),
            "natural_language": natural_language,
            "messages": [],
            "plan": None,
            "collected_data": [],
            "structured_items": [],
            "errors": [],
            "collector_retries": 0,
            "structurer_retries": 0,
            "planner_retries": 0,
        }
        start = time.perf_counter()
        result = await graph.ainvoke(state)
        dur = time.perf_counter() - start
        durations.append(dur)
        items_counts.append(len(result.get("structured_items", [])))
        logger.info(
            "Benchmark run %d/%d: %.2fs, %d items",
            i + 1,
            runs,
            dur,
            items_counts[-1],
        )

    return {
        "runs": runs,
        "avg_duration_seconds": sum(durations) / len(durations) if durations else 0,
        "min_duration_seconds": min(durations) if durations else 0,
        "max_duration_seconds": max(durations) if durations else 0,
        "avg_items": sum(items_counts) / len(items_counts) if items_counts else 0,
    }
