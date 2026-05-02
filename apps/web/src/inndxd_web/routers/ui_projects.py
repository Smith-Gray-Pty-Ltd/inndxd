"""UI Project management routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from inndxd_core.db import async_session_factory
from inndxd_core.models.brief import Brief
from inndxd_core.models.project import Project
from sqlalchemy import select

from inndxd_web.auth import require_ui_user

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def list_projects(request: Request) -> HTMLResponse:
    user = require_ui_user(request)
    templates = request.app.state.templates
    async with async_session_factory() as session:
        result = await session.execute(select(Project).order_by(Project.created_at.desc()))
        projects = list(result.scalars().all())
    return templates.TemplateResponse(
        "projects/list.html",
        {"request": request, "user": user, "projects": projects},
    )


@router.get("/create", response_class=HTMLResponse)
async def create_form(request: Request) -> HTMLResponse:
    user = require_ui_user(request)
    templates = request.app.state.templates
    return templates.TemplateResponse(
        "projects/create.html",
        {"request": request, "user": user},
    )


@router.post("/create")
async def create_project(
    request: Request,
    name: str = Form(...),
    description: str = Form(default=""),
) -> RedirectResponse:
    user = require_ui_user(request)
    templates = request.app.state.templates
    if not name.strip():
        return templates.TemplateResponse(
            "projects/create.html",
            {"request": request, "user": user, "error": "Name is required"},
            status_code=400,
        )
    tenant_id = user.get("tenant_id")
    if not tenant_id:
        tenant_id = "00000000-0000-0000-0000-000000000000"
    async with async_session_factory() as session:
        project = Project(
            tenant_id=UUID(tenant_id),
            name=name.strip(),
            description=description.strip() or None,
        )
        session.add(project)
        await session.commit()
    return RedirectResponse(url="/ui/projects", status_code=303)


@router.get("/{project_id}/edit", response_class=HTMLResponse)
async def edit_form(request: Request, project_id: UUID) -> HTMLResponse:
    user = require_ui_user(request)
    templates = request.app.state.templates
    async with async_session_factory() as session:
        project = await session.get(Project, project_id)
        if not project:
            return HTMLResponse("Project not found", status_code=404)
    return templates.TemplateResponse(
        "projects/edit.html",
        {"request": request, "user": user, "project": project},
    )


@router.post("/{project_id}/edit")
async def update_project(
    request: Request,
    project_id: UUID,
    name: str = Form(...),
    description: str = Form(default=""),
) -> RedirectResponse:
    require_ui_user(request)
    async with async_session_factory() as session:
        project = await session.get(Project, project_id)
        if not project:
            return RedirectResponse(url="/ui/projects", status_code=303)
        project.name = name.strip()
        project.description = description.strip() or None
        await session.commit()
    return RedirectResponse(url="/ui/projects", status_code=303)


@router.delete("/{project_id}")
async def delete_project(request: Request, project_id: UUID) -> HTMLResponse:
    require_ui_user(request)
    async with async_session_factory() as session:
        project = await session.get(Project, project_id)
        if project:
            await session.delete(project)
            await session.commit()
    return HTMLResponse(status_code=200)


@router.get("/{project_id}", response_class=HTMLResponse)
async def project_detail(request: Request, project_id: UUID) -> HTMLResponse:
    user = require_ui_user(request)
    templates = request.app.state.templates
    async with async_session_factory() as session:
        project = await session.get(Project, project_id)
        if not project:
            return HTMLResponse("Project not found", status_code=404)
        result = await session.execute(
            select(Brief).where(Brief.project_id == project_id).order_by(Brief.created_at.desc())
        )
        briefs = list(result.scalars().all())
    return templates.TemplateResponse(
        "projects/detail.html",
        {"request": request, "user": user, "project": project, "briefs": briefs},
    )
