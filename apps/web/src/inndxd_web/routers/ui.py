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


async def _count(model) -> int:
    async with async_session_factory() as session:
        result = await session.execute(select(func.count()).select_from(model))
        return result.scalar() or 0


@router.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request) -> HTMLResponse:
    templates = request.app.state.templates
    user = get_ui_user(request)
    if not user:
        return RedirectResponse(url="/ui/auth/login", status_code=303)

    return templates.TemplateResponse(
        "dashboard/index.html",
        {
            "request": request,
            "user": user,
            "version": "0.3.0",
            "stats": {
                "projects": await _count(Project),
                "briefs": await _count(Brief),
                "data_items": await _count(DataItem),
            },
        },
    )
