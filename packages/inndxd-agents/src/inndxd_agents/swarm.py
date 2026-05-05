# packages/inndxd-agents/src/inndxd_agents/swarm.py

import logging
from uuid import UUID

from inndxd_agents.graph import build_research_graph

logger = logging.getLogger(__name__)


async def run_research_swarm(
    brief_id: UUID,
    tenant_id: UUID,
    project_id: UUID,
    natural_language: str,
) -> list[dict]:
    """Execute the research swarm with comprehensive error handling."""
    logger.info("Starting research swarm for brief %s", brief_id)
    logger.debug(
        "Parameters: brief_id=%s, tenant_id=%s, project_id=%s",
        brief_id,
        tenant_id,
        project_id,
    )

    try:
        graph = build_research_graph()
        logger.info("Research graph built successfully")
    except ImportError as exc:
        logger.error("Failed to import graph components: %s", exc, exc_info=True)
        return []
    except Exception as exc:
        logger.error("Failed to build research graph: %s", exc, exc_info=True)
        return []

    state = {
        "brief_id": str(brief_id),
        "tenant_id": str(tenant_id),
        "project_id": str(project_id),
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

    try:
        logger.info("Invoking research graph for brief %s", brief_id)
        result = await graph.ainvoke(state)
        logger.info("Research graph execution completed for brief %s", brief_id)
    except Exception as exc:
        logger.error("Graph execution failed for brief %s: %s", brief_id, exc, exc_info=True)
        return []

    structured_items = result.get("structured_items", [])

    if not structured_items and result.get("collected_data"):
        structured_items = result["collected_data"]
        for item in structured_items:
            item.setdefault("project_id", str(project_id))
            item.setdefault("tenant_id", str(tenant_id))
            item.setdefault("brief_id", str(brief_id))
            item.setdefault("source_url", item.get("url", ""))
            item.setdefault("content_type", "web_page")
            item.setdefault("raw_payload", {"text": item.get("text", "")})
            item.setdefault("structured_payload", item.copy())
        logger.info("Using raw collected data as fallback (%d items)", len(structured_items))

    return structured_items
