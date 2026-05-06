"""Dashboard home route."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from inndxd_core.db import async_session_factory
from inndxd_core.models.brief import Brief
from inndxd_core.models.data_item import DataItem
from inndxd_core.models.project import Project
from sqlalchemy import func, select

from inndxd_web.auth import get_ui_user

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    templates = request.app.state.templates
    user = get_ui_user(request)
    if not user:
        return RedirectResponse(url="/ui/auth/login", status_code=303)

    async with async_session_factory() as session:
        total_projects = await session.scalar(select(func.count()).select_from(Project))
        total_briefs = await session.scalar(select(func.count()).select_from(Brief))
        total_data = await session.scalar(select(func.count()).select_from(DataItem))
        completed_briefs = await session.scalar(
            select(func.count()).select_from(Brief).where(Brief.status == "completed")
        )
        running_briefs = await session.scalar(
            select(func.count()).select_from(Brief).where(Brief.status == "running")
        )
        result = await session.execute(
            select(Brief, Project.name)
            .join(Project, Brief.project_id == Project.id, isouter=True)
            .order_by(Brief.created_at.desc())
            .limit(5)
        )
        recent = []
        for brief, proj_name in result:
            brief.project_name = proj_name
            recent.append(brief)

    return templates.TemplateResponse(
        "dashboard/index.html",
        {
            "request": request,
            "user": user,
            "version": "0.3.0",
            "stats": {
                "projects": total_projects or 0,
                "briefs": total_briefs or 0,
                "data_items": total_data or 0,
                "completed_briefs": completed_briefs or 0,
                "running_briefs": running_briefs or 0,
            },
            "recent_briefs": recent,
        },
    )
