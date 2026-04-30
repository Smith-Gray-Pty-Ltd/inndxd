"""Database query tool for accessing previously collected data."""

from __future__ import annotations

from uuid import UUID

from langchain_core.tools import tool
from pydantic import BaseModel, Field


class DbQueryInput(BaseModel):
    project_id: str = Field(description="Project UUID to query data for")
    query_type: str = Field(
        default="recent", description="Query type: 'recent', 'search', or 'stats'"
    )
    limit: int = Field(default=20, ge=1, le=100)


class DbQueryResult(BaseModel):
    total: int
    items: list[dict]
    query_type: str


@tool(args_schema=DbQueryInput)
async def db_query_tool(
    project_id: str, query_type: str = "recent", limit: int = 20
) -> DbQueryResult:
    """Query previously collected data items for a project."""
    from inndxd_core.db import async_session_factory
    from inndxd_core.models.data_item import DataItem
    from sqlalchemy import func, select

    try:
        pid = UUID(project_id)
    except ValueError:
        return DbQueryResult(total=0, items=[], query_type=query_type)

    async with async_session_factory() as session:
        if query_type == "stats":
            stmt = select(func.count()).select_from(DataItem).where(DataItem.project_id == pid)
            result = await session.execute(stmt)
            total = result.scalar() or 0
            stmt_types = (
                select(DataItem.content_type, func.count())
                .where(DataItem.project_id == pid)
                .group_by(DataItem.content_type)
            )
            type_results = await session.execute(stmt_types)
            items = [{"content_type": r[0], "count": r[1]} for r in type_results]
            return DbQueryResult(total=total, items=items, query_type=query_type)
        else:
            stmt = (
                select(DataItem)
                .where(DataItem.project_id == pid)
                .order_by(DataItem.created_at.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            rows = result.scalars().all()
            items = [
                {
                    "id": str(r.id),
                    "source_url": r.source_url,
                    "content_type": r.content_type,
                    "structured_payload": r.structured_payload,
                    "created_at": str(r.created_at),
                }
                for r in rows
            ]
            return DbQueryResult(total=len(items), items=items, query_type=query_type)
