"""UI Brief management routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from inndxd_api.tasks import run_research_task
from inndxd_core.db import async_session_factory
from inndxd_core.models.brief import Brief
from inndxd_core.models.conversation import Conversation
from inndxd_core.models.data_item import DataItem
from inndxd_core.models.project import Project
from inndxd_core.models.project_context import ProjectContext
from sqlalchemy import select

from inndxd_web.auth import require_ui_user

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def list_briefs(request: Request):
    user = require_ui_user(request)
    templates = request.app.state.templates
    async with async_session_factory() as session:
        result = await session.execute(select(Brief).order_by(Brief.created_at.desc()))
        briefs = list(result.scalars().all())
    return templates.TemplateResponse(
        "briefs/list.html",
        {"request": request, "user": user, "briefs": briefs},
    )


@router.get("/create", response_class=HTMLResponse)
async def create_form(request: Request, project_id: str | None = None):
    user = require_ui_user(request)
    templates = request.app.state.templates
    async with async_session_factory() as session:
        result = await session.execute(select(Project).order_by(Project.created_at.desc()))
        projects = list(result.scalars().all())
    return templates.TemplateResponse(
        "briefs/create.html",
        {
            "request": request,
            "user": user,
            "projects": projects,
            "selected_project_id": project_id,
        },
    )


@router.post("/create")
async def create_brief(
    request: Request,
    project_id: str = Form(...),
    natural_language: str = Form(...),
):
    user = require_ui_user(request)
    templates = request.app.state.templates

    if not natural_language or len(natural_language.strip()) < 10:
        async with async_session_factory() as session:
            result = await session.execute(select(Project).order_by(Project.created_at.desc()))
            projects = list(result.scalars().all())
        return templates.TemplateResponse(
            "briefs/create.html",
            {
                "request": request,
                "user": user,
                "projects": projects,
                "error": "Natural language query must be at least 10 characters.",
                "natural_language": natural_language,
                "selected_project_id": project_id,
            },
            status_code=400,
        )

    if not project_id:
        async with async_session_factory() as session:
            result = await session.execute(select(Project).order_by(Project.created_at.desc()))
            projects = list(result.scalars().all())
        return templates.TemplateResponse(
            "briefs/create.html",
            {
                "request": request,
                "user": user,
                "projects": projects,
                "error": "Please select a project.",
                "natural_language": natural_language,
            },
            status_code=400,
        )

    tenant_id = user.get("tenant_id")
    if not tenant_id:
        tenant_id = "00000000-0000-0000-0000-000000000000"

    async with async_session_factory() as session:
        brief = Brief(
            tenant_id=UUID(tenant_id),
            project_id=UUID(project_id),
            natural_language=natural_language.strip(),
            status="pending",
        )
        session.add(brief)
        await session.commit()
        await session.refresh(brief)

        run_research_task.delay(
            str(brief.id), str(brief.tenant_id), project_id, natural_language.strip()
        )

    return RedirectResponse(url=f"/ui/briefs/{brief.id}", status_code=303)


@router.get("/{brief_id}", response_class=HTMLResponse)
async def brief_detail(request: Request, brief_id: UUID):
    user = require_ui_user(request)
    templates = request.app.state.templates
    async with async_session_factory() as session:
        brief = await session.get(Brief, brief_id)
        if not brief:
            return HTMLResponse("Brief not found", status_code=404)

        project = await session.get(Project, brief.project_id)

        result = await session.execute(
            select(DataItem)
            .where(DataItem.brief_id == brief_id)
            .order_by(DataItem.created_at.desc())
        )
        data_items = list(result.scalars().all())

    return templates.TemplateResponse(
        "briefs/detail.html",
        {
            "request": request,
            "user": user,
            "brief": brief,
            "project": project,
            "data_items": data_items,
            "status": brief.status,
        },
    )


@router.get("/{brief_id}/status-partial", response_class=HTMLResponse)
async def status_partial(request: Request, brief_id: UUID):
    templates = request.app.state.templates
    async with async_session_factory() as session:
        brief = await session.get(Brief, brief_id)
        if not brief:
            return HTMLResponse("Brief not found", status_code=404)
    return templates.TemplateResponse(
        "partials/_run_status.html",
        {"request": request, "status": brief.status, "brief_id": brief_id},
    )


@router.get("/{brief_id}/status-badge", response_class=HTMLResponse)
async def status_badge(request: Request, brief_id: UUID):
    templates = request.app.state.templates
    async with async_session_factory() as session:
        brief = await session.get(Brief, brief_id)
    return templates.TemplateResponse(
        "partials/_status_badge.html",
        {"request": request, "status": brief.status if brief else "unknown"},
    )


@router.get("/create/chat", response_class=HTMLResponse)
async def brief_chat_page(request: Request, project_id: str = Query(default="")):
    user = require_ui_user(request)
    templates = request.app.state.templates
    async with async_session_factory() as session:
        project = await session.get(Project, UUID(project_id))
        if not project:
            return HTMLResponse("Project not found", status_code=404)
    return templates.TemplateResponse(
        "briefs/chat.html",
        {"request": request, "user": user, "project": project},
    )


@router.post("/create/chat/configure")
async def brief_chat_configure(
    request: Request,
    project_id: str = Form(...),
):
    user = require_ui_user(request)

    tenant_id = user.get("tenant_id", "00000000-0000-0000-0000-000000000000")

    context_data = {}
    try:
        from inndxd_agents.chat_planner import extract_brief_config

        async with async_session_factory() as session:
            pc = await session.get(ProjectContext, UUID(project_id))
            if pc:
                context_data = pc.context_data

            result = await session.execute(
                select(Conversation)
                .where(Conversation.project_id == UUID(project_id))
                .where(Conversation.brief_id.is_(None))
                .order_by(Conversation.created_at.asc())
            )
            messages = [
                {"role": c.role, "content": c.content}
                for c in result.scalars()
            ]
        if messages:
            brief_config = await extract_brief_config(messages, context_data)
        else:
            brief_config = {}
    except Exception:
        brief_config = {}

    async with async_session_factory() as session:
        brief = Brief(
            tenant_id=UUID(tenant_id),
            project_id=UUID(project_id),
            natural_language=brief_config.get("data_schema", {}).get(
                "description", "Chat-defined brief"
            ),
            status="pending",
            config=brief_config,
        )
        session.add(brief)
        await session.commit()
        await session.refresh(brief)

    return HTMLResponse(f'<div id="brief-id" data-brief-id="{brief.id}">{brief.id}</div>')


@router.post("/create/chat/run")
async def brief_chat_run(
    request: Request,
    project_id: str = Form(...),
    brief_id: str = Form(default=""),
):
    user = require_ui_user(request)

    tenant_id = user.get("tenant_id", "00000000-0000-0000-0000-000000000000")

    context_data = {}
    try:
        from inndxd_agents.chat_planner import extract_brief_config

        async with async_session_factory() as session:
            pc = await session.get(ProjectContext, UUID(project_id))
            if pc:
                context_data = pc.context_data

            result = await session.execute(
                select(Conversation)
                .where(Conversation.project_id == UUID(project_id))
                .where(Conversation.brief_id.is_(None))
                .order_by(Conversation.created_at.asc())
            )
            messages = [
                {"role": c.role, "content": c.content}
                for c in result.scalars()
            ]
        if messages:
            brief_config = await extract_brief_config(messages, context_data)
        else:
            brief_config = {}
    except Exception:
        brief_config = {}

    async with async_session_factory() as session:
        brief = Brief(
            tenant_id=UUID(tenant_id),
            project_id=UUID(project_id),
            natural_language=brief_config.get(
                "data_schema", {}
            ).get("description", "Chat-defined brief"),
            status="pending",
            config=brief_config,
        )
        session.add(brief)
        await session.commit()
        await session.refresh(brief)

        run_research_task.delay(
            str(brief.id),
            str(brief.tenant_id),
            str(project_id),
            brief.natural_language,
        )

    return RedirectResponse(url=f"/ui/briefs/{brief.id}", status_code=303)
