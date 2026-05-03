"""Admin UI routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from inndxd_core.db import async_session_factory
from inndxd_core.models.api_key import APIKey
from inndxd_core.models.audit_log import AuditLog
from inndxd_core.models.llm_provider import LLMProvider
from inndxd_core.models.user import User
from inndxd_core.repositories.llm_providers import LLMProviderRepository
from sqlalchemy import select

from inndxd_web.auth import require_ui_user

router = APIRouter()


async def _require_admin(request: Request) -> dict | HTMLResponse:
    user = require_ui_user(request)
    async with async_session_factory() as session:
        db_user = await session.get(User, UUID(user["sub"]))
        if not db_user or not db_user.is_admin:
            return HTMLResponse(
                '<html><body style="font-family:sans-serif;display:flex;align-items:center;'
                'justify-content:center;height:100vh;background:#f3f4f6">'
                '<div style="text-align:center">'
                '<h1 style="font-size:4rem;color:#dc2626;margin:0">403</h1>'
                '<p style="color:#6b7280">Admin access required</p>'
                '<a href="/ui" style="color:#2563eb">Back to Dashboard</a>'
                "</div></body></html>",
                status_code=403,
            )
    user["admin"] = True
    return user


@router.get("/providers", response_class=HTMLResponse)
async def list_providers(request: Request) -> HTMLResponse:
    admin_user = await _require_admin(request)
    if isinstance(admin_user, HTMLResponse):
        return admin_user
    templates = request.app.state.templates
    async with async_session_factory() as session:
        result = await session.execute(select(LLMProvider).order_by(LLMProvider.priority.desc()))
        providers = list(result.scalars().all())
    return templates.TemplateResponse(
        "admin/providers/list.html",
        {
            "request": request,
            "user": admin_user,
            "admin": True,
            "providers": providers,
        },
    )


@router.get("/providers/create", response_class=HTMLResponse)
async def create_provider_form(request: Request) -> HTMLResponse:
    admin_user = await _require_admin(request)
    if isinstance(admin_user, HTMLResponse):
        return admin_user
    templates = request.app.state.templates
    return templates.TemplateResponse(
        "admin/providers/create.html",
        {"request": request, "user": admin_user, "admin": True},
    )


@router.post("/providers/create")
async def create_provider(
    request: Request,
    name: str = Form(...),
    provider_type: str = Form(...),
    base_url: str = Form(...),
    api_key: str = Form(default=""),
    default_model: str = Form(...),
    available_models: str = Form(default=""),
    priority: int = Form(default=0),
) -> RedirectResponse | HTMLResponse:
    admin_user = await _require_admin(request)
    if isinstance(admin_user, HTMLResponse):
        return admin_user
    templates = request.app.state.templates
    if not name.strip() or not base_url.strip() or not default_model.strip():
        return templates.TemplateResponse(
            "admin/providers/create.html",
            {
                "request": request,
                "user": admin_user,
                "admin": True,
                "error": "Name, Base URL, and Default Model are required.",
            },
            status_code=400,
        )
    models_list = [m.strip() for m in available_models.split(",") if m.strip()]
    async with async_session_factory() as session:
        repo = LLMProviderRepository(session)
        await repo.create(
            tenant_id=UUID("00000000-0000-0000-0000-000000000000"),
            name=name.strip(),
            provider_type=provider_type,
            base_url=base_url.strip(),
            api_key=api_key,
            default_model=default_model.strip(),
            available_models=models_list,
            priority=priority,
        )
        await session.commit()
    return RedirectResponse(url="/ui/admin/providers", status_code=303)


@router.delete("/providers/{provider_id}")
async def delete_provider(request: Request, provider_id: UUID) -> HTMLResponse:
    admin_user = await _require_admin(request)
    if isinstance(admin_user, HTMLResponse):
        return admin_user
    async with async_session_factory() as session:
        provider = await session.get(LLMProvider, provider_id)
        if provider:
            await session.delete(provider)
            await session.commit()
    return HTMLResponse(status_code=200)


@router.get("/providers/{provider_id}/health", response_class=HTMLResponse)
async def provider_health_badge(request: Request, provider_id: UUID) -> HTMLResponse:
    async with async_session_factory() as session:
        provider = await session.get(LLMProvider, provider_id)
        if not provider:
            return HTMLResponse("Not found", status_code=404)

    import time

    import httpx

    start = time.monotonic()
    healthy = False
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(
                f"{provider.base_url}/models",
                headers={"Authorization": f"Bearer {provider.api_key}"} if provider.api_key else {},
            )
            healthy = resp.status_code == 200
    except Exception:
        healthy = False
    latency = int((time.monotonic() - start) * 1000)

    badge = "bg-green-100 text-green-800" if healthy else "bg-red-100 text-red-800"
    label = f"Healthy ({latency}ms)" if healthy else "Unhealthy"
    return HTMLResponse(
        f'<span class="inline-flex items-center px-2 py-0.5 '
        f'rounded text-xs font-medium {badge}">{label}</span>'
    )


@router.get("/api-keys", response_class=HTMLResponse)
async def list_api_keys(request: Request) -> HTMLResponse:
    admin_user = await _require_admin(request)
    if isinstance(admin_user, HTMLResponse):
        return admin_user
    templates = request.app.state.templates
    async with async_session_factory() as session:
        result = await session.execute(select(APIKey).order_by(APIKey.created_at.desc()))
        keys = list(result.scalars().all())
    return templates.TemplateResponse(
        "admin/api_keys/list.html",
        {
            "request": request,
            "user": admin_user,
            "admin": True,
            "api_keys": keys,
        },
    )


@router.post("/api-keys/{key_id}/revoke")
async def revoke_api_key(request: Request, key_id: UUID) -> HTMLResponse:
    admin_user = await _require_admin(request)
    if isinstance(admin_user, HTMLResponse):
        return admin_user
    async with async_session_factory() as session:
        key = await session.get(APIKey, key_id)
        if key:
            key.is_active = False
            await session.commit()
    return HTMLResponse(status_code=200)


@router.post("/api-keys/create", response_class=HTMLResponse)
async def create_api_key(
    request: Request,
    name: str = Form(...),
) -> HTMLResponse:
    admin_user = await _require_admin(request)
    if isinstance(admin_user, HTMLResponse):
        return admin_user
    templates = request.app.state.templates
    async with async_session_factory() as session:
        from inndxd_core.repositories.api_keys import APIKeyRepository

        repo = APIKeyRepository(session)
        key, raw = await repo.create(UUID(admin_user["sub"]), name.strip())
        await session.commit()
    return templates.TemplateResponse(
        "partials/_key_created_modal.html",
        {
            "request": request,
            "key_name": key.name,
            "key_prefix": key.key_prefix,
            "raw_key": raw,
            "key_id": key.id,
        },
    )


@router.get("/audit-logs", response_class=HTMLResponse)
async def list_audit_logs(
    request: Request,
    event_type: str = Query(default=""),
) -> HTMLResponse:
    admin_user = await _require_admin(request)
    if isinstance(admin_user, HTMLResponse):
        return admin_user
    templates = request.app.state.templates
    async with async_session_factory() as session:
        stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(200)
        if event_type:
            stmt = stmt.where(AuditLog.event_type == event_type)
        result = await session.execute(stmt)
        logs = list(result.scalars().all())

        event_types_result = await session.execute(select(AuditLog.event_type).distinct())
        event_types = sorted(set(r[0] for r in event_types_result.all()))

    return templates.TemplateResponse(
        "admin/audit_logs/list.html",
        {
            "request": request,
            "user": admin_user,
            "admin": True,
            "logs": logs,
            "event_types": event_types,
            "current_event_type": event_type,
        },
    )
