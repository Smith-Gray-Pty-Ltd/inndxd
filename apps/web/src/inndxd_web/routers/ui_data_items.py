"""UI Data Item management routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse
from inndxd_core.db import async_session_factory
from inndxd_core.models.brief import Brief
from inndxd_core.models.data_item import DataItem
from inndxd_core.models.project import Project
from sqlalchemy import asc, desc, select

from inndxd_web.auth import require_ui_user

router = APIRouter()

ALLOWED_SORT_COLS = {"content_type", "created_at"}


@router.get("/", response_class=HTMLResponse)
async def list_data_items(request: Request) -> HTMLResponse:
    user = require_ui_user(request)
    templates = request.app.state.templates
    tenant_id = user.get("tenant_id", "00000000-0000-0000-0000-000000000000")
    async with async_session_factory() as session:
        result = await session.execute(select(Project).order_by(Project.created_at.desc()))
        projects = list(result.scalars().all())
        result = await session.execute(
            select(Brief).where(Brief.tenant_id == tenant_id).order_by(Brief.created_at.desc())
        )
        all_briefs = list(result.scalars().all())
    return templates.TemplateResponse(
        "data_items/list.html",
        {
            "request": request,
            "user": user,
            "items": [],
            "projects": projects,
            "all_briefs": all_briefs,
            "current_project": "",
            "current_brief": "",
            "sort": "created_at",
            "order": "desc",
        },
    )


@router.get("/rows", response_class=HTMLResponse)
async def data_item_rows(
    request: Request,
    project_id: str = Query(default=""),
    brief_id: str = Query(default=""),
    sort: str = Query(default="created_at"),
    order: str = Query(default="desc"),
) -> HTMLResponse:
    user = require_ui_user(request)
    templates = request.app.state.templates

    tenant_id = user.get("tenant_id", "00000000-0000-0000-0000-000000000000")

    if sort not in ALLOWED_SORT_COLS:
        sort = "created_at"

    async with async_session_factory() as session:
        stmt = select(DataItem).where(DataItem.tenant_id == tenant_id)

        if project_id:
            stmt = stmt.where(DataItem.project_id == UUID(project_id))
        if brief_id:
            stmt = stmt.where(DataItem.brief_id == UUID(brief_id))

        col = getattr(DataItem, sort, DataItem.created_at)
        direction = desc(col) if order == "desc" else asc(col)
        stmt = stmt.order_by(direction).limit(500)

        result = await session.execute(stmt)
        items = list(result.scalars().all())

    return templates.TemplateResponse(
        "partials/_data_item_rows.html",
        {"request": request, "items": items},
    )
