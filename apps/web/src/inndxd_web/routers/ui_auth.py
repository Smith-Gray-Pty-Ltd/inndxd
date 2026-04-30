"""UI authentication routes."""
from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from inndxd_core.auth import hash_password, verify_password
from inndxd_core.db import async_session_factory
from inndxd_core.repositories.users import UserRepository

from inndxd_web.auth import clear_auth_cookie, set_auth_cookie

router = APIRouter()


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    templates = request.app.state.templates
    return templates.TemplateResponse("auth/login.html", {
        "request": request, "user": None,
    })


@router.post("/login")
async def login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
) -> HTMLResponse | RedirectResponse:
    templates = request.app.state.templates
    async with async_session_factory() as session:
        repo = UserRepository(session)
        user = await repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            return templates.TemplateResponse("auth/login.html", {
                "request": request, "user": None, "error": "Invalid email or password",
            }, status_code=401)
        if not user.is_active:
            return templates.TemplateResponse("auth/login.html", {
                "request": request, "user": None, "error": "Account is disabled",
            }, status_code=403)
        response = RedirectResponse(url="/ui", status_code=303)
        set_auth_cookie(response, str(user.id), str(user.tenant_id) if user.tenant_id else None)
        return response


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request) -> HTMLResponse:
    templates = request.app.state.templates
    return templates.TemplateResponse("auth/register.html", {
        "request": request, "user": None,
    })


@router.post("/register")
async def register_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
) -> HTMLResponse | RedirectResponse:
    templates = request.app.state.templates
    async with async_session_factory() as session:
        repo = UserRepository(session)
        existing = await repo.get_by_email(email)
        if existing:
            return templates.TemplateResponse("auth/register.html", {
                "request": request, "user": None, "error": "Email already registered",
            }, status_code=409)
        if len(password) < 8:
            return templates.TemplateResponse("auth/register.html", {
                "request": request, "user": None, "error": "Password must be at least 8 characters",
            }, status_code=400)
        hashed = hash_password(password)
        user = await repo.create(email, hashed)
        await session.commit()
    response = RedirectResponse(url="/ui", status_code=303)
    set_auth_cookie(response, str(user.id), None)
    return response


@router.get("/logout")
async def logout() -> RedirectResponse:
    response = RedirectResponse(url="/ui/auth/login", status_code=303)
    clear_auth_cookie(response)
    return response
