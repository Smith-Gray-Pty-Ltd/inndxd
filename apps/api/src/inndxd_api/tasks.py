"""Celery task definitions for inndxd research execution."""

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

import asyncpg

from inndxd_api.celery_app import celery_app

logger = logging.getLogger(__name__)

_DSN = "postgresql://inndxd:inndxd@postgres:5432/inndxd"


async def _update_brief_status(brief_id: UUID, status: str) -> None:
    conn = await asyncpg.connect(_DSN)
    try:
        await conn.execute("UPDATE briefs SET status = $1 WHERE id = $2", status, str(brief_id))
    finally:
        await conn.close()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60, soft_time_limit=540, time_limit=600)
def run_research_task(
    self, brief_id_str: str, tenant_id_str: str, project_id_str: str, natural_language: str
):
    brief_id = UUID(brief_id_str)
    tenant_id = UUID(tenant_id_str)
    project_id = UUID(project_id_str)

    async def _run():
        try:
            await _update_brief_status(brief_id, "running")
            from inndxd_agents.swarm import run_research_swarm
            structured = await run_research_swarm(brief_id, tenant_id, project_id, natural_language)
            logger.info("Got %d structured items for brief %s", len(structured), brief_id)
            if structured:
                await _persist_items(structured)
            await _update_brief_status(brief_id, "completed")
        except Exception as exc:
            logger.error("Research task failed for brief %s: %s", brief_id, exc)
            await _update_brief_status(brief_id, "failed")
            raise self.retry(exc=exc) from exc

    asyncio.run(_run())


async def _persist_items(items: list[dict]) -> None:
    values = []
    for item in items:
        import json as _json
        values.append((
            str(item.get("project_id", "")),
            str(item.get("tenant_id", "")),
            str(item.get("brief_id", "")),
            item.get("source_url", ""),
            item.get("content_type", "web_page"),
            _json.dumps(item.get("raw_payload", {})),
            _json.dumps(item.get("structured_payload", {})),
        ))
    conn = await asyncpg.connect(_DSN)
    try:
        await conn.executemany(
            "INSERT INTO data_items "
            "(id, project_id, tenant_id, brief_id, "
            "source_url, content_type, raw_payload, structured_payload) "
            "VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6::jsonb, $7::jsonb)",
            values,
        )
        logger.info("Persisted %d data items", len(values))
    finally:
        await conn.close()


@celery_app.task
def cleanup_stuck_briefs():
    async def _cleanup():
        cutoff = datetime.now(UTC) - timedelta(hours=1)
        conn = await asyncpg.connect(_DSN)
        try:
            result = await conn.execute(
                "UPDATE briefs SET status = 'failed' WHERE status = 'running' AND created_at < $1",
                cutoff,
            )
            logger.info("Marked %s stuck briefs as failed", result.split()[-1] if result else 0)
        finally:
            await conn.close()

    asyncio.run(_cleanup())
