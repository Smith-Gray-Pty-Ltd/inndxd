"""Celery task definitions for inndxd research execution."""

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from inndxd_core.db import async_session_factory
from inndxd_core.models.brief import Brief

from inndxd_api.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def run_research_task(
    self, brief_id_str: str, tenant_id_str: str, project_id_str: str, natural_language: str
):
    """Execute the research swarm as a Celery task."""
    import asyncio

    brief_id = UUID(brief_id_str)
    tenant_id = UUID(tenant_id_str)
    project_id = UUID(project_id_str)

    async def _run():
        try:
            await _update_brief_status(brief_id, "running")
            from inndxd_agents.swarm import run_research_swarm

            await run_research_swarm(brief_id, tenant_id, project_id, natural_language)
            await _update_brief_status(brief_id, "completed")
        except Exception as exc:
            logger.error("Research task failed for brief %s: %s", brief_id, exc)
            await _update_brief_status(brief_id, "failed")
            raise self.retry(exc=exc) from exc

    return asyncio.run(_run())


@celery_app.task
def cleanup_stuck_briefs():
    """Mark briefs that have been 'running' for more than 1 hour as failed."""
    import asyncio

    async def _cleanup():
        from sqlalchemy import update

        cutoff = datetime.now(UTC) - timedelta(hours=1)
        async with async_session_factory() as session:
            stmt = (
                update(Brief)
                .where(Brief.status == "running")
                .where(Brief.created_at < cutoff)
                .values(status="failed")
            )
            result = await session.execute(stmt)
            await session.commit()
            logger.info("Marked %d stuck briefs as failed", result.rowcount)

    asyncio.run(_cleanup())


async def _update_brief_status(brief_id: UUID, status: str) -> None:
    async with async_session_factory() as session:
        brief = await session.get(Brief, brief_id)
        if brief:
            brief.status = status
            await session.commit()
