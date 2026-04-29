# packages/inndxd-agents/src/inndxd_agents/swarm.py

import logging
from uuid import UUID

from inndxd_agents.graph import build_research_graph
from inndxd_core.db import async_session_factory
from inndxd_core.repositories.data_items import DataItemRepository

logger = logging.getLogger(__name__)


async def run_research_swarm(
    brief_id: UUID,
    tenant_id: UUID,
    project_id: UUID,
    natural_language: str,
) -> list[dict]:
    logger.info("Starting research swarm for brief %s", brief_id)
    graph = build_research_graph()
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
    }
    result = await graph.ainvoke(state)
    logger.info("Research swarm completed for brief %s", brief_id)

    structured_items = result["structured_items"]
    if structured_items:
        async with async_session_factory() as session:
            repo = DataItemRepository(session)
            await repo.bulk_insert(structured_items)
            await session.commit()
        logger.info("Persisted %d structured items for brief %s", len(structured_items), brief_id)

    return structured_items
