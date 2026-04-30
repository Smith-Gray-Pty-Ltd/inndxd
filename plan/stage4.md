# Inndxd — Stage 4 Implementation Plan (Web UI)

> **Prerequisite:** Stages 1, 2, & 3 complete and merged to `main`.
> **Tech Stack:** FastAPI + Jinja2 + Tailwind CSS (CDN) + HTMX
> **Goal:** A server-rendered, interactive dashboard that feels like a SPA but ships zero custom JavaScript.

---

## Git Workflow

- Fork from `main`: `git checkout -b stage4/phase<X>-<slug>`
- One commit per task: `phase<X>: <task-id> <verb> <what changed>`
- Before each commit: `~/.local/bin/uv run ruff check . && ruff format --check . && mypy . && pytest -v`
- Squash-merge PR back to `main` after all phase tasks pass
- Update `README.md`, `plan/masterplan.md`, and `plan/stage4.md` tracking table after each phase merge

---

## Table of Contents

| Phase | Tasks | Description |
|---|---|---|
| [Phase 0](#phase-0-foundation) | 8 | Static assets, base template, layout, Jinja2 config, Tailwind setup |
| [Phase 1](#phase-1-authentication-pages) | 8 | Login/register pages, session auth, logout, protected routes |
| [Phase 2](#phase-2-dashboard--projects) | 10 | Dashboard home with stats, project CRUD pages |
| [Phase 3](#phase-3-briefs-management) | 11 | Brief create/list/detail, live status via HTMX polling, result viewer |
| [Phase 4](#phase-4-data-items--export) | 8 | Sortable/filterable data table, CSV/JSON export links |
| [Phase 5](#phase-5-admin-panels) | 10 | LLM provider management, API key management, audit log viewer |

**Total: 55 tasks**

| Phase | Status |
|---|---|
| 0 — Foundation | ⬜ Pending |
| 1 — Auth Pages | ⬜ Pending |
| 2 — Dashboard & Projects | ⬜ Pending |
| 3 — Briefs Management | ⬜ Pending |
| 4 — Data Items & Export | ⬜ Pending |
| 5 — Admin Panels | ⬜ Pending |

---

## Architecture

```
apps/api/
├── templates/                    # Jinja2 templates
│   ├── base.html                 # Root layout: sidebar + header + content slot
│   ├── auth/
│   │   ├── login.html
│   │   └── register.html
│   ├── dashboard/
│   │   └── index.html
│   ├── projects/
│   │   ├── list.html
│   │   ├── create.html
│   │   ├── edit.html
│   │   └── detail.html
│   ├── briefs/
│   │   ├── list.html
│   │   ├── create.html
│   │   └── detail.html
│   ├── data_items/
│   │   └── list.html
│   ├── admin/
│   │   ├── providers/
│   │   │   ├── list.html
│   │   │   └── create.html
│   │   ├── api_keys/
│   │   │   └── list.html
│   │   └── audit_logs/
│   │       └── list.html
│   └── partials/
│       ├── _status_badge.html    # Reusable colored badge
│       ├── _brief_rows.html      # HTMX-swapped table rows
│       ├── _run_status.html      # HTMX-polled status card
│       ├── _stats_cards.html     # Dashboard stat tiles
│       └── _modal.html           # Generic modal wrapper
├── static/                       # Static assets
│   └── css/
│       └── input.css             # Tailwind directives (if using CLI)
└── src/inndxd_api/
    └── routers/
        ├── ui.py                 # Dashboard home + layout routes
        ├── ui_auth.py            # Login/register/logout pages
        ├── ui_projects.py        # Project CRUD pages
        ├── ui_briefs.py          # Brief create/list/detail + live status partials
        ├── ui_data_items.py      # Data items table + export
        └── ui_admin.py           # Providers + API keys + audit logs
```

**New dependencies:**
- `jinja2>=3.1,<4` (already available via FastAPI standard)
- `python-multipart>=0.0.18,<1` (form data parsing)

**All state lives on the server.** HTMX requests return Jinja2 partials. No custom JS except Tailwind's utility classes and HTMX attributes (hx-get, hx-post, hx-target, hx-trigger, hx-swap).

---

## Phase 0: Foundation

> **Goal:** Bare minimum — base template renders. Tailwind CSS loads. Static files served. No auth, no data. Just a shell.

### Task 0-1: Add `jinja2` + `python-multipart` to API deps

**File:** `apps/api/pyproject.toml`
**Action:** Add to dependencies list:
```toml
"jinja2>=3.1,<4",
"python-multipart>=0.0.18,<1",
```

**Acceptance:** `~/.local/bin/uv sync` installs both. `import jinja2` succeeds.

### Task 0-2: Create templates/ directory and base.html layout

**Directory:** `apps/api/templates/` (CREATE)

**File:** `apps/api/templates/base.html` (CREATE)

```html
<!DOCTYPE html>
<html lang="en" class="h-full bg-gray-50">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Inndxd{% endblock %}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    {% block head %}{% endblock %}
</head>
<body class="h-full">
    <div class="flex h-full">
        <!-- Sidebar -->
        <aside class="w-64 bg-gray-900 text-white flex flex-col">
            <div class="p-4 text-xl font-bold border-b border-gray-700">
                Inndxd
            </div>
            <nav class="flex-1 p-4 space-y-1">
                {% block sidebar %}
                <a href="/ui" class="block px-3 py-2 rounded hover:bg-gray-700">Dashboard</a>
                <a href="/ui/projects" class="block px-3 py-2 rounded hover:bg-gray-700">Projects</a>
                <a href="/ui/briefs" class="block px-3 py-2 rounded hover:bg-gray-700">Briefs</a>
                <a href="/ui/data-items" class="block px-3 py-2 rounded hover:bg-gray-700">Data Items</a>
                {% if admin %}
                <div class="pt-4 mt-4 border-t border-gray-700">
                    <p class="px-3 text-xs uppercase text-gray-400">Admin</p>
                    <a href="/ui/admin/providers" class="block px-3 py-2 rounded hover:bg-gray-700">LLM Providers</a>
                    <a href="/ui/admin/api-keys" class="block px-3 py-2 rounded hover:bg-gray-700">API Keys</a>
                    <a href="/ui/admin/audit-logs" class="block px-3 py-2 rounded hover:bg-gray-700">Audit Log</a>
                </div>
                {% endif %}
                {% endblock %}
            </nav>
            <div class="p-4 border-t border-gray-700 text-sm text-gray-400">
                {% block user_info %}v{{ version }}{% endblock %}
            </div>
        </aside>

        <!-- Main content -->
        <main class="flex-1 overflow-auto">
            {% block header %}
            <header class="bg-white shadow-sm px-8 py-4 flex justify-between items-center">
                <h1 class="text-2xl font-semibold text-gray-900">{% block page_title %}Dashboard{% endblock %}</h1>
                <div class="flex items-center space-x-4">
                    {% if user %}
                    <span class="text-sm text-gray-500">{{ user.email }}</span>
                    <a href="/ui/auth/logout" class="text-sm text-red-600 hover:underline">Logout</a>
                    {% endif %}
                </div>
            </header>
            {% endblock %}

            <div class="p-8">
                {% block content %}{% endblock %}
            </div>
        </main>
    </div>
</body>
</html>
```

**Acceptance:** Template exists at `apps/api/templates/base.html` and is syntactically valid Jinja2 + HTML.

### Task 0-3: Configure Jinja2Templates in main.py

**File:** `apps/api/src/inndxd_api/main.py`

**Action:** Add Jinja2 templates to the create_app factory:

```python
from pathlib import Path

from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"
STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "static"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
```

Add in `create_app()`:
```python
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
```

Make `templates` and `app` accessible to UI routers. Store `templates` on `app.state.templates`.

**Acceptance:** `from inndxd_api.main import templates` works.

### Task 0-4: Create static/ directory with Tailwind input.css

**Directory:** `apps/api/static/css/` (CREATE)

**File:** `apps/api/static/css/input.css` (CREATE)

```css
/* @import "tailwindcss"; */
/* Uncomment above when using Tailwind CLI. CDN version uses inline script. */
```

**Acceptance:** `apps/api/static/css/input.css` exists. Directory structure `apps/api/static/` is mountable.

### Task 0-5: Create router/ui.py with dashboard home route

**File:** `apps/api/src/inndxd_api/routers/ui.py` (CREATE)

```python
"""UI Dashboard routes."""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request) -> HTMLResponse:
    templates = request.app.state.templates
    return templates.TemplateResponse("dashboard/index.html", {
        "request": request,
        "version": "0.3.0",
        "stats": {
            "projects": 0,
            "briefs": 0,
            "data_items": 0,
        },
    })
```

**Acceptance:** `GET /ui` renders dashboard/index.html.

### Task 0-6: Create dashboard/index.html (placeholder)

**File:** `apps/api/templates/dashboard/index.html` (CREATE)

```html
{% extends "base.html" %}
{% block title %}Dashboard — Inndxd{% endblock %}
{% block page_title %}Dashboard{% endblock %}
{% block content %}
<div class="grid grid-cols-3 gap-6">
    <div class="bg-white rounded-lg shadow p-6">
        <p class="text-sm text-gray-500">Projects</p>
        <p class="text-3xl font-bold text-blue-600">{{ stats.projects }}</p>
    </div>
    <div class="bg-white rounded-lg shadow p-6">
        <p class="text-sm text-gray-500">Briefs</p>
        <p class="text-3xl font-bold text-green-600">{{ stats.briefs }}</p>
    </div>
    <div class="bg-white rounded-lg shadow p-6">
        <p class="text-sm text-gray-500">Data Items</p>
        <p class="text-3xl font-bold text-purple-600">{{ stats.data_items }}</p>
    </div>
</div>
{% endblock %}
```

**Acceptance:** `GET /ui` renders 3 stat cards.

### Task 0-7: Register ui router in main.py

**File:** `apps/api/src/inndxd_api/main.py`

**Action:** Import and include:
```python
from inndxd_api.routers.ui import router as ui_router
...
app.include_router(ui_router, prefix="/ui", tags=["ui"])
```

**Acceptance:** `GET /ui` returns HTML (200). Sidebar nav links visible. Dashboard stats show 0/0/0.

### Task 0-8: Create partials/_status_badge.html

**File:** `apps/api/templates/partials/_status_badge.html` (CREATE)

```html
{% if status == 'pending' %}
<span class="px-2 py-1 text-xs font-medium rounded-full bg-yellow-100 text-yellow-800">Pending</span>
{% elif status == 'running' %}
<span class="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">Running</span>
{% elif status == 'completed' %}
<span class="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">Completed</span>
{% elif status == 'failed' %}
<span class="px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-800">Failed</span>
{% else %}
<span class="px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-800">{{ status }}</span>
{% endif %}
```

**Acceptance:** Include with `{% include 'partials/_status_badge.html' %}` renders correct Tailwind badge.

---

## Phase 1: Authentication Pages

> **Goal:** Login and register pages that POST to existing `/api/auth/*` endpoints. Session stored via JWT in httpOnly cookie. Logout clears cookie. Protected routes redirect to login.

### Task 1-1: Create auth/login.html page

**File:** `apps/api/templates/auth/login.html` (CREATE)

```html
{% extends "base.html" %}
{% block title %}Login — Inndxd{% endblock %}
{% block page_title %}Login{% endblock %}
{% block sidebar %}{% endblock %}
{% block header %}{% endblock %}
{% block content %}
<div class="max-w-md mx-auto mt-20">
    <h1 class="text-3xl font-bold text-center mb-8">Inndxd</h1>
    <div class="bg-white rounded-lg shadow p-8">
        {% if error %}
        <div class="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded">{{ error }}</div>
        {% endif %}
        <form method="POST" action="/ui/auth/login" class="space-y-4">
            <div>
                <label class="block text-sm font-medium text-gray-700">Email</label>
                <input type="email" name="email" required
                       class="mt-1 block w-full rounded border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500 p-2 border">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700">Password</label>
                <input type="password" name="password" required
                       class="mt-1 block w-full rounded border-gray-300 shadow-sm focus:ring-blue-500 focus:border-blue-500 p-2 border">
            </div>
            <button type="submit"
                    class="w-full py-2 px-4 bg-blue-600 text-white rounded hover:bg-blue-700 font-medium">
                Sign In
            </button>
        </form>
        <p class="mt-4 text-center text-sm text-gray-500">
            No account? <a href="/ui/auth/register" class="text-blue-600 hover:underline">Register</a>
        </p>
    </div>
</div>
{% endblock %}
```

**Acceptance:** `GET /ui/auth/login` renders a login form. No sidebar.

### Task 1-2: Create auth/register.html page

**File:** `apps/api/templates/auth/register.html` (CREATE)

Same structure as login but with email + password + confirm password fields. POST to `/ui/auth/register`. Link at bottom: "Already have an account? Sign in."

**Acceptance:** `GET /ui/auth/register` renders a registration form.

### Task 1-3: Create UI auth session manager utility

**File:** `apps/api/src/inndxd_api/ui_session.py` (CREATE)

```python
"""UI session management via JWT httpOnly cookie."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse

from inndxd_ui.auth_utils import UI_COOKIE_NAME, decode_ui_token, create_ui_token


def set_auth_cookie(response: Response, user_id: str, tenant_id: str | None) -> None:
    token = create_ui_token(user_id, tenant_id)
    response.set_cookie(
        key=UI_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=False,  # True in prod
        samesite="lax",
        max_age=86400,
    )


def clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(UI_COOKIE_NAME)


def get_ui_user(request: Request) -> dict | None:
    token = request.cookies.get(UI_COOKIE_NAME)
    if not token:
        return None
    try:
        return decode_ui_token(token)
    except Exception:
        return None


def require_ui_user(request: Request) -> dict:
    user = get_ui_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/ui/auth/login"},
        )
    return user
```

Add the cookie name constant and token functions to a shared `inndxd_ui/auth_utils.py`:
```python
UI_COOKIE_NAME = "inndxd_session"
```

And in the same file:
```python
def create_ui_token(user_id: str, tenant_id: str | None) -> str:
    from inndxd_core.config import settings
    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def decode_ui_token(token: str) -> dict:
    from inndxd_core.config import settings
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
```

Wait — keep all of this in one file. Let me simplify.

**Acceptance:** `from inndxd_api.ui_session import set_auth_cookie, get_ui_user, require_ui_user` works.

### Task 1-4: Create router/ui_auth.py with login/register/logout routes

**File:** `apps/api/src/inndxd_api/routers/ui_auth.py` (CREATE)

```python
"""UI authentication routes."""
from typing import Any

from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from inndxd_api.dependencies import get_db
from inndxd_api.ui_session import clear_auth_cookie, set_auth_cookie
from inndxd_core.auth import hash_password, verify_password
from inndxd_core.repositories.users import UserRepository

router = APIRouter()


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    templates = request.app.state.templates
    return templates.TemplateResponse("auth/login.html", {"request": request})


@router.post("/login")
async def login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
) -> Response:
    templates = request.app.state.templates
    repo = UserRepository(db)
    user = await repo.get_by_email(email)
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse("auth/login.html", {
            "request": request, "error": "Invalid email or password"
        }, status_code=401)
    response = RedirectResponse(url="/ui", status_code=303)
    set_auth_cookie(response, str(user.id), str(user.tenant_id) if user.tenant_id else None)
    return response


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request) -> HTMLResponse:
    templates = request.app.state.templates
    return templates.TemplateResponse("auth/register.html", {"request": request})


@router.post("/register")
async def register_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
) -> Response:
    templates = request.app.state.templates
    repo = UserRepository(db)
    existing = await repo.get_by_email(email)
    if existing:
        return templates.TemplateResponse("auth/register.html", {
            "request": request, "error": "Email already registered"
        }, status_code=409)
    hashed = hash_password(password)
    user = await repo.create(email, hashed)
    await db.commit()
    response = RedirectResponse(url="/ui", status_code=303)
    set_auth_cookie(response, str(user.id), None)
    return response


@router.get("/logout")
async def logout() -> RedirectResponse:
    response = RedirectResponse(url="/ui/auth/login", status_code=303)
    clear_auth_cookie(response)
    return response
```

**Acceptance:** Full auth flow: GET login form → POST credentials → set cookie → redirect to /ui. GET /ui/auth/logout clears cookie.

### Task 1-5: Register ui_auth router in main.py

**File:** `apps/api/src/inndxd_api/main.py`

**Action:**
```python
from inndxd_api.routers.ui_auth import router as ui_auth_router
...
app.include_router(ui_auth_router, prefix="/ui/auth", tags=["ui-auth"])
```

**Acceptance:** `GET /ui/auth/login` renders form. Routes reachable.

### Task 1-6: Update base.html navigation for auth state

**File:** `apps/api/templates/base.html`

**Action:** In the header block, check if `user` context var is set. If not, show "Sign In" link. The `user` context is None when not logged in. Auth pages already disable sidebar/header via empty blocks — ensure non-auth pages show full sidebar.

**Ensure sidebar and header blocks are conditional on user.** If user is None (login/register pages), they override those blocks to empty. If user is present (protected pages), sidebar + header render normally.

**Acceptance:** Login page shows no sidebar. Dashboard shows sidebar.

### Task 1-7: Add user context middleware to all UI routes

**File:** `apps/api/src/inndxd_api/routers/ui.py`

**Action:** Add a middleware or dependency that populates `user` in every template context.

```python
from inndxd_api.ui_session import get_ui_user

@router.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request) -> HTMLResponse:
    templates = request.app.state.templates
    user = get_ui_user(request)
    if not user:
        return RedirectResponse(url="/ui/auth/login", status_code=303)
    return templates.TemplateResponse("dashboard/index.html", {
        "request": request,
        "user": user,
        "version": "0.3.0",
        "stats": {"projects": 0, "briefs": 0, "data_items": 0},
    })
```

**Acceptance:** All UI routes pass `user` to template context. `base.html` uses `{{ user.email }}` in header.

### Task 1-8: Add auth protection to remaining UI routers

**File:** All future UI routers (ui_projects.py, ui_briefs.py, etc.)

**Action:** Each router function calls `get_ui_user(request)` or `require_ui_user(request)`. If None, redirect to `/ui/auth/login`.

Create a pattern comment at top of each UI router file:
```python
# All routes in this file require authentication.
# Call get_ui_user(request) at the top of each route. Redirect if None.
```

**Acceptance:** Every UI router file has the auth guard call at the top of each route function.

---

## Phase 2: Dashboard & Projects

> **Goal:** Dashboard shows real stats from DB. Projects page: list view with create/edit/delete. HTMX delete with confirmation. Form validation with server-side errors rendered inline.

### Task 2-1: Update dashboard home to query real stats

**File:** `apps/api/src/inndxd_api/routers/ui.py`

**Action:** In `dashboard_home()`, query real counts:

```python
from inndxd_core.db import async_session_factory
from sqlalchemy import func, select
from inndxd_core.models.project import Project
from inndxd_core.models.brief import Brief
from inndxd_core.models.data_item import DataItem

async with async_session_factory() as session:
    projects = (await session.execute(select(func.count()).select_from(Project))).scalar() or 0
    briefs = (await session.execute(select(func.count()).select_from(Brief))).scalar() or 0
    items = (await session.execute(select(func.count()).select_from(DataItem))).scalar() or 0
```

**Acceptance:** Dashboard shows real counts from the database.

### Task 2-2: Create projects/list.html — table with action buttons

**File:** `apps/api/templates/projects/list.html` (CREATE)

```html
{% extends "base.html" %}
{% block title %}Projects — Inndxd{% endblock %}
{% block page_title %}Projects{% endblock %}
{% block content %}
<div class="mb-6 flex justify-between">
    <p class="text-gray-500">{{ projects|length }} project(s)</p>
    <a href="/ui/projects/create" class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">Create Project</a>
</div>

<div class="bg-white rounded-lg shadow overflow-hidden">
    <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
            <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
                <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
        </thead>
        <tbody class="divide-y divide-gray-200">
            {% for project in projects %}
            <tr class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap font-medium">{{ project.name }}</td>
                <td class="px-6 py-4 text-gray-500 truncate max-w-xs">{{ project.description or "—" }}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ project.created_at.strftime('%Y-%m-%d') }}</td>
                <td class="px-6 py-4 text-right space-x-2">
                    <a href="/ui/projects/{{ project.id }}" class="text-blue-600 hover:underline text-sm">View</a>
                    <a href="/ui/projects/{{ project.id }}/edit" class="text-gray-600 hover:underline text-sm">Edit</a>
                    <button hx-delete="/ui/projects/{{ project.id }}"
                            hx-confirm="Delete this project?"
                            hx-target="closest tr"
                            hx-swap="outerHTML swap:1s"
                            class="text-red-600 hover:underline text-sm">Delete</button>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endblock %}
```

**Acceptance:** Lists projects. HTMX delete removes row from DOM. Create button links to create page.

### Task 2-3: Create router/ui_projects.py — list route

**File:** `apps/api/src/inndxd_api/routers/ui_projects.py` (CREATE)

```python
"""UI Project management routes."""
from typing import Any

from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select

from inndxd_api.ui_session import require_ui_user
from inndxd_core.db import async_session_factory
from inndxd_core.models.project import Project

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def list_projects(request: Request) -> HTMLResponse:
    user = require_ui_user(request)
    templates = request.app.state.templates
    async with async_session_factory() as session:
        result = await session.execute(select(Project).order_by(Project.created_at.desc()))
        projects = list(result.scalars().all())
    return templates.TemplateResponse("projects/list.html", {
        "request": request, "user": user, "projects": projects,
    })
```

**Acceptance:** `GET /ui/projects` lists all projects.

### Task 2-4: Add GET create-projects form route

**File:** `apps/api/src/inndxd_api/routers/ui_projects.py`

**Add:**
```python
@router.get("/create", response_class=HTMLResponse)
async def create_form(request: Request) -> HTMLResponse:
    user = require_ui_user(request)
    templates = request.app.state.templates
    return templates.TemplateResponse("projects/create.html", {
        "request": request, "user": user,
    })
```

**Acceptance:** `GET /ui/projects/create` shows a form with Name + Description fields.

### Task 2-5: Create projects/create.html

**File:** `apps/api/templates/projects/create.html` (CREATE)

```html
{% extends "base.html" %}
{% block title %}Create Project — Inndxd{% endblock %}
{% block page_title %}Create Project{% endblock %}
{% block content %}
<div class="max-w-2xl bg-white rounded-lg shadow p-8">
    {% if error %}
    <div class="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded">{{ error }}</div>
    {% endif %}
    <form method="POST" action="/ui/projects/create" class="space-y-4">
        <div>
            <label class="block text-sm font-medium text-gray-700">Name *</label>
            <input type="text" name="name" required
                   class="mt-1 block w-full border rounded p-2 focus:ring-blue-500 focus:border-blue-500">
        </div>
        <div>
            <label class="block text-sm font-medium text-gray-700">Description</label>
            <textarea name="description" rows="3"
                      class="mt-1 block w-full border rounded p-2 focus:ring-blue-500 focus:border-blue-500"></textarea>
        </div>
        <div class="flex space-x-4">
            <button type="submit" class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">Create</button>
            <a href="/ui/projects" class="px-4 py-2 border rounded text-gray-600 hover:bg-gray-50">Cancel</a>
        </div>
    </form>
</div>
{% endblock %}
```

**Acceptance:** Form renders. Name required. Description optional.

### Task 2-6: Add POST create route (insert into DB)

**File:** `apps/api/src/inndxd_api/routers/ui_projects.py`

**Add:**
```python
from fastapi import Form

@router.post("/create")
async def create_project(
    request: Request,
    name: str = Form(...),
    description: str = Form(default=""),
) -> RedirectResponse:
    user = require_ui_user(request)
    if not name.strip():
        templates = request.app.state.templates
        return templates.TemplateResponse("projects/create.html", {
            "request": request, "user": user, "error": "Name is required"
        }, status_code=400)
    async with async_session_factory() as session:
        import uuid
        project = Project(
            id=uuid.uuid4(),
            tenant_id=uuid.UUID(user.get("tenant_id", "00000000-0000-0000-0000-000000000000")),
            name=name.strip(),
            description=description.strip() or None,
        )
        session.add(project)
        await session.commit()
    return RedirectResponse(url="/ui/projects", status_code=303)
```

**Acceptance:** Submitting the form creates a project and redirects to the list.

### Task 2-7: Add GET edit form route

**File:** `apps/api/src/inndxd_api/routers/ui_projects.py`

**Add:**
```python
from uuid import UUID
from fastapi import Path

@router.get("/{project_id}/edit", response_class=HTMLResponse)
async def edit_form(request: Request, project_id: UUID) -> HTMLResponse:
    user = require_ui_user(request)
    templates = request.app.state.templates
    async with async_session_factory() as session:
        project = await session.get(Project, project_id)
        if not project:
            return HTMLResponse("Project not found", status_code=404)
    return templates.TemplateResponse("projects/edit.html", {
        "request": request, "user": user, "project": project,
    })
```

**Acceptance:** `GET /ui/projects/{id}/edit` shows pre-filled form.

### Task 2-8: Create projects/edit.html

**File:** `apps/api/templates/projects/edit.html` (CREATE)

Same structure as create.html but pre-fills `value="{{ project.name }}"` and `{{ project.description }}`. POST action to `/ui/projects/{{ project.id }}/edit`.

**Acceptance:** Edit form pre-fills existing values.

### Task 2-9: Add POST/PUT edit + DELETE routes

**File:** `apps/api/src/inndxd_api/routers/ui_projects.py`

**Add POST edit:**
```python
@router.post("/{project_id}/edit")
async def update_project(request: Request, project_id: UUID, name: str = Form(...), description: str = Form(default="")) -> RedirectResponse:
    user = require_ui_user(request)
    async with async_session_factory() as session:
        project = await session.get(Project, project_id)
        if not project:
            return HTMLResponse("Not found", 404)
        project.name = name.strip()
        project.description = description.strip() or None
        await session.commit()
    return RedirectResponse(url="/ui/projects", status_code=303)
```

**Add DELETE (HTMX):**
```python
@router.delete("/{project_id}")
async def delete_project(request: Request, project_id: UUID) -> Response:
    user = require_ui_user(request)
    async with async_session_factory() as session:
        project = await session.get(Project, project_id)
        if project:
            await session.delete(project)
            await session.commit()
    return Response(status_code=200)  # HTMX will remove the row
```

**Acceptance:** Edit updates project. HTMX delete removes row from table and deletes from DB.

### Task 2-10: Create project detail page (projects/detail.html)

**File:** `apps/api/templates/projects/detail.html` (CREATE)

Shows project name, description, created date. Below it: a table of briefs belonging to this project with status badges. Link to create a new brief pre-selecting this project.

**Route:** `GET /ui/projects/{project_id}`

**Acceptance:** Project detail page shows briefs table with status badges (using `partials/_status_badge.html`).

---

## Phase 3: Briefs Management

> **Goal:** Create brief form (natural language textarea). Brief list with status badges, live polling. Brief detail shows full research results with structured items. Run status updates every 2 seconds via HTMX polling on `partials/_run_status.html`.

### Task 3-1: Create briefs/list.html with status badges + live polling

**File:** `apps/api/templates/briefs/list.html` (CREATE)

Table: Natural Language (truncated), Status badge, Project, Created date, Actions.

Each row's status cell wrapped in:
```html
<div hx-get="/ui/briefs/{{ brief.id }}/status-badge"
     hx-trigger="every 2s"
     hx-swap="innerHTML">
    {% include 'partials/_status_badge.html' %}
</div>
```

**Acceptance:** Brief list page shows all briefs with live-updated status badges.

### Task 3-2: Create partials/_run_status.html for brief detail live updates

**File:** `apps/api/templates/partials/_run_status.html` (CREATE)

```html
<div id="brief-status" class="bg-white rounded-lg shadow p-6 mb-6">
    <div class="flex items-center space-x-4">
        <h3 class="text-lg font-medium">Status</h3>
        {% include 'partials/_status_badge.html' %}
    </div>
    {% if status == 'running' %}
    <div class="mt-4">
        <div class="animate-pulse bg-blue-100 rounded h-2 w-full"></div>
        <p class="text-sm text-gray-500 mt-2">Research in progress...</p>
    </div>
    {% endif %}
</div>
```

On the brief detail page, wrap the status section:
```html
<div hx-get="/ui/briefs/{{ brief.id }}/status-partial"
     hx-trigger="every 2s"
     hx-swap="innerHTML">
    {% include 'partials/_run_status.html' %}
</div>
```

**Acceptance:** Brief detail page polls status every 2s. Status badge updates. When completed, polling stops (server returns `hx-trigger="none"`).

### Task 3-3: Create router/ui_briefs.py — list + detail + create routes

**File:** `apps/api/src/inndxd_api/routers/ui_briefs.py` (CREATE)

Routes:
- `GET /` — list all briefs
- `GET /create?project_id=<id>` — create form
- `POST /create` — create brief (triggers Celery task)
- `GET /{brief_id}` — detail page
- `GET /{brief_id}/status-partial` — HTMX partial for status badge
- `GET /{brief_id}/status-badge` — HTMX badge-only partial for list updates

**Acceptance:** Full brief lifecycle: create → list with live badge → detail with live status + results.

### Task 3-4: Create briefs/create.html

**File:** `apps/api/templates/briefs/create.html` (CREATE)

Form with:
- Project dropdown (pre-selected if `project_id` query param)
- Natural language textarea (required, min 10 chars)
- Submit + Cancel buttons

**Acceptance:** Form renders. Submitting creates brief and dispatches to Celery via existing `run_research_task.delay()`.

### Task 3-5: Wire brief creation to Celery task in UI router

**File:** `apps/api/src/inndxd_api/routers/ui_briefs.py`

**POST /create route:**
```python
from inndxd_api.tasks import run_research_task
from inndxd_core.models.brief import Brief

brief = Brief(
    tenant_id=UUID(user["tenant_id"]) if user.get("tenant_id") else uuid4(),
    project_id=UUID(project_id),
    natural_language=nl,
    status="pending",
)
session.add(brief)
await session.commit()
await session.refresh(brief)
run_research_task.delay(str(brief.id), str(brief.tenant_id), str(project_id), nl)
```

**Acceptance:** Creating a brief from the UI dispatches the existing Celery task.

### Task 3-6: Create briefs/detail.html — full results view

**File:** `apps/api/templates/briefs/detail.html` (CREATE)

Shows:
- Brief metadata (natural language, project, created date)
- Live status section (HTMX polling `_run_status.html` partial)
- Data items table: key → value → source → score
- If completed, show structured_items rendered as cards or table
- Export links: JSON / CSV for this brief's data items

**Acceptance:** Completed brief shows all collected data items in a clean table. Running brief shows loading indicator.

### Task 3-7: Add status-partial endpoint

**File:** `apps/api/src/inndxd_api/routers/ui_briefs.py`

**Add:**
```python
@router.get("/{brief_id}/status-partial", response_class=HTMLResponse)
async def status_partial(request: Request, brief_id: UUID) -> HTMLResponse:
    templates = request.app.state.templates
    async with async_session_factory() as session:
        brief = await session.get(Brief, brief_id)
        if not brief:
            return HTMLResponse("Brief not found", status_code=404)
    return templates.TemplateResponse("partials/_run_status.html", {
        "request": request, "status": brief.status, "brief_id": brief_id,
    })
```

If status is completed or failed, the partial sets `hx-trigger="none"` to stop polling:
```html
{% if status in ('completed', 'failed') %}
<div hx-swap-oob="true" id="brief-status"
     hx-trigger="none">
{% else %}
<div id="brief-status" hx-trigger="every 2s">
{% endif %}
```

**Acceptance:** Polling stops when brief reaches terminal state.

### Task 3-8: Add status-badge endpoint for list updates

**File:** `apps/api/src/inndxd_api/routers/ui_briefs.py`

**Add:**
```python
@router.get("/{brief_id}/status-badge", response_class=HTMLResponse)
async def status_badge(request: Request, brief_id: UUID) -> HTMLResponse:
    templates = request.app.state.templates
    async with async_session_factory() as session:
        brief = await session.get(Brief, brief_id)
    return templates.TemplateResponse("partials/_status_badge.html", {
        "request": request, "status": brief.status if brief else "unknown",
    })
```

**Acceptance:** Brief list rows show live-updated status badges.

### Task 3-9: Register ui_briefs router in main.py

**File:** `apps/api/src/inndxd_api/main.py`

```python
from inndxd_api.routers.ui_briefs import router as ui_briefs_router
...
app.include_router(ui_briefs_router, prefix="/ui/briefs", tags=["ui-briefs"])
```

**Acceptance:** `GET /ui/briefs` renders brief list. All brief routes functional.

### Task 3-10: Add redirect-to-login when creating brief unauthenticated

**File:** `apps/api/src/inndxd_api/routers/ui_briefs.py`

**Action:** Replace `tenant_id` source — currently using user's tenant_id from session. If no user, redirect to login. Ensure `require_ui_user(request)` is called at top of every route.

**Acceptance:** Unauthenticated access to `/ui/briefs` redirects to login.

### Task 3-11: Add brief list to project detail page

**File:** `apps/api/templates/projects/detail.html`

**Action:** Embed a section showing briefs for this project. Use same pattern as briefs/list.html but filtered by project_id. Include live status badges via HTMX polling.

**Acceptance:** Project detail page lists its briefs with live-updated status badges.

---

## Phase 4: Data Items & Export

> **Goal:** Sortable, filterable data items table. Click column headers to sort. Filter by project, brief, or status. CSV/JSON export buttons that generate files from the current filtered view.

### Task 4-1: Create data_items/list.html — sortable table with HTMX

**File:** `apps/api/templates/data_items/list.html` (CREATE)

```html
{% extends "base.html" %}
{% block title %}Data Items — Inndxd{% endblock %}
{% block page_title %}Data Items{% endblock %}
{% block content %}
<!-- Filters -->
<div id="filters" class="mb-6 flex space-x-4">
    <select name="project_id" hx-get="/ui/data-items/rows" hx-target="#table-body"
            class="border rounded p-2">
        <option value="">All Projects</option>
        {% for p in projects %}
        <option value="{{ p.id }}" {% if p.id == current_project %}selected{% endif %}>{{ p.name }}</option>
        {% endfor %}
    </select>
    <select name="brief_id" hx-get="/ui/data-items/rows" hx-target="#table-body"
            class="border rounded p-2">
        <option value="">All Briefs</option>
        {% for b in briefs %}
        <option value="{{ b.id }}" {% if b.id == current_brief %}selected{% endif %}>{{ b.natural_language[:50] }}...</option>
        {% endfor %}
    </select>
</div>

<!-- Export -->
<div class="mb-4 flex space-x-4">
    <a href="/api/data-items/export/json" class="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700">JSON Export</a>
    <a href="/api/data-items/export/csv" class="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700">CSV Export</a>
</div>

<!-- Table -->
<div class="bg-white rounded-lg shadow overflow-hidden">
    <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
            <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer"
                    hx-get="/ui/data-items/rows?sort=key&order={% if sort == 'key' and order == 'asc' %}desc{% else %}asc{% endif %}"
                    hx-target="#table-body">Key {% if sort == 'key' %}{{ '▲' if order == 'asc' else '▼' }}{% endif %}</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Value</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Source</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer"
                    hx-get="/ui/data-items/rows?sort=created_at&order={% if sort == 'created_at' and order == 'asc' %}desc{% else %}asc{% endif %}"
                    hx-target="#table-body">Date {% if sort == 'created_at' %}{{ '▲' if order == 'asc' else '▼' }}{% endif %}</th>
            </tr>
        </thead>
        <tbody id="table-body" class="divide-y divide-gray-200">
            {% include 'partials/_data_item_rows.html' %}
        </tbody>
    </table>
</div>
{% endblock %}
```

**Acceptance:** Table renders. Clicking column header sorts the table. Filters update table rows via HTMX.

### Task 4-2: Create partials/_data_item_rows.html

**File:** `apps/api/templates/partials/_data_item_rows.html` (CREATE)

```html
{% for item in items %}
<tr class="hover:bg-gray-50">
    <td class="px-6 py-4 font-medium text-sm">{{ item.key }}</td>
    <td class="px-6 py-4 text-sm text-gray-600 max-w-md truncate">{{ item.value }}</td>
    <td class="px-6 py-4 text-sm text-gray-500">{{ item.source or "—" }}</td>
    <td class="px-6 py-4 text-sm text-gray-500">{{ item.created_at.strftime('%Y-%m-%d %H:%M') }}</td>
</tr>
{% else %}
<tr><td colspan="4" class="px-6 py-8 text-center text-gray-500">No data items found.</td></tr>
{% endfor %}
```

**Acceptance:** Partial renders table rows. Empty state shows message.

### Task 4-3: Create router/ui_data_items.py — list + rows + export

**File:** `apps/api/src/inndxd_api/routers/ui_data_items.py` (CREATE)

Routes:
- `GET /` — full page with filters + table
- `GET /rows?project_id=&brief_id=&sort=&order=` — HTMX partial returning just `<tbody>` content

**Acceptance:** Full page renders. Row updates work via HTMX.

### Task 4-4: Add sort + filter logic to data items query

**File:** `apps/api/src/inndxd_api/routers/ui_data_items.py`

**In GET /rows:**
```python
from sqlalchemy import asc, desc

stmt = select(DataItem)
if project_id:
    stmt = stmt.where(DataItem.project_id == UUID(project_id))
if brief_id:
    stmt = stmt.where(DataItem.brief_id == UUID(brief_id))

col = getattr(DataItem, sort, DataItem.created_at)
direction = desc(col) if order == "desc" else asc(col)
stmt = stmt.order_by(direction).limit(500)

result = await session.execute(stmt)
items = list(result.scalars().all())
```

**Acceptance:** Sorting + filtering works. URL parameters preserved.

### Task 4-5: Register ui_data_items router in main.py

**File:** `apps/api/src/inndxd_api/main.py`

```python
from inndxd_api.routers.ui_data_items import router as ui_data_items_router
...
app.include_router(ui_data_items_router, prefix="/ui/data-items", tags=["ui-data-items"])
```

**Acceptance:** `GET /ui/data-items` renders data items page.

### Task 4-6: Ensure export links carry current filter params

**File:** `apps/api/templates/data_items/list.html`

**Action:** Update JSON/CSV export links to include current `project_id` and `brief_id` query parameters:

```html
<a href="/api/data-items/export/json?project_id={{ current_project }}&brief_id={{ current_brief }}"
   class="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700">JSON Export</a>
```

**Acceptance:** Export links carry current filter state.

### Task 4-7: Add tenant scoping to data items UI queries

**File:** `apps/api/src/inndxd_api/routers/ui_data_items.py`

**Action:** Add `where(DataItem.tenant_id == user_tenant_id)` to all queries. Derive tenant from user session.

**Acceptance:** Users only see their own tenant's data.

### Task 4-8: Add empty state UX for all list pages

**Files:**
- `apps/api/templates/projects/list.html`
- `apps/api/templates/briefs/list.html`
- `apps/api/templates/data_items/list.html`

**Action:** When list is empty, show a friendly message with a CTA:
```html
{% if not items %}
<div class="bg-white rounded-lg shadow p-12 text-center">
    <p class="text-gray-500 text-lg mb-4">No data yet.</p>
    <a href="/ui/briefs/create" class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">Create your first brief</a>
</div>
{% else %}
...table...
{% endif %}
```

**Acceptance:** Empty states show CTAs. No blank pages.

---

## Phase 5: Admin Panels

> **Goal:** Admin-only pages for managing LLM providers, API keys, and viewing audit logs. Accessible only when `user.is_admin == True`. Non-admin sees 403.

### Task 5-1: Create router/ui_admin.py with admin guard

**File:** `apps/api/src/inndxd_api/routers/ui_admin.py` (CREATE)

```python
"""Admin UI routes."""
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from inndxd_api.ui_session import require_ui_user

router = APIRouter()


async def _require_admin(request: Request) -> dict:
    user = require_ui_user(request)
    from inndxd_core.db import async_session_factory
    from inndxd_core.models.user import User
    from uuid import UUID

    async with async_session_factory() as session:
        db_user = await session.get(User, UUID(user["sub"]))
        if not db_user or not db_user.is_admin:
            from fastapi.responses import HTMLResponse
            return None  # Will trigger 403 in route
    return user
```

**Acceptance:** Admin guard function usable by all admin routes.

### Task 5-2: Create LLM providers admin list page

**File:** `apps/api/templates/admin/providers/list.html` (CREATE)

Table: Name, Provider Type, Base URL, Default Model, Active (toggle), Priority, Health Status, Actions.

Health status cell polls `/api/llm-providers/{id}/health` via HTMX.

Toggle active button sends PATCH to `/api/llm-providers/{id}`.

**Route:** `GET /ui/admin/providers`

**Acceptance:** Admin sees provider table with health checks and toggle.

### Task 5-3: Create LLM provider create form page

**File:** `apps/api/templates/admin/providers/create.html` (CREATE)

Form fields: Name, Provider Type (dropdown: openai_compatible, anthropic, ollama), Base URL, API Key, Default Model, Available Models (comma-separated), Priority (number).

**Route:** `GET /ui/admin/providers/create` + `POST /ui/admin/providers/create`

**Acceptance:** Admin can add new providers via the UI.

### Task 5-4: Add LLM provider management routes to ui_admin.py

**File:** `apps/api/src/inndxd_api/routers/ui_admin.py`

Routes:
- `GET /providers` — list page
- `GET /providers/create` — form
- `POST /providers/create` — insert via `LLMProviderRepository`
- `DELETE /providers/{provider_id}` — HTMX delete

**Acceptance:** Full CRUD for providers via admin UI.

### Task 5-5: Create API keys admin management page

**File:** `apps/api/templates/admin/api_keys/list.html` (CREATE)

Table: Key Prefix, Name, Active, Created, Last Used, Actions (Revoke, Rotate).

Rotate button POSTs to `/api/api-keys/{id}/rotate` via HTMX and shows new key in a one-time modal.

**Route:** `GET /ui/admin/api-keys`

**Acceptance:** Admin sees all API keys. Can revoke and rotate.

### Task 5-6: Add API key management routes to ui_admin.py

**File:** `apps/api/src/inndxd_api/routers/ui_admin.py`

Routes:
- `GET /api-keys` — list page
- `POST /api-keys/{key_id}/revoke` — HTMX post to revoke
- `POST /api-keys/{key_id}/rotate` — HTMX post to rotate, return modal with new key

**Acceptance:** Admin can manage API keys from the UI.

### Task 5-7: Create audit log viewer page

**File:** `apps/api/templates/admin/audit_logs/list.html` (CREATE)

Table: Timestamp, Event Type, Actor, Status, Details (expandable).

Filter by event type (dropdown) or date range.

**Route:** `GET /ui/admin/audit-logs`

**Acceptance:** Admin can view and filter audit log entries.

### Task 5-8: Add audit log routes to ui_admin.py

**File:** `apps/api/src/inndxd_api/routers/ui_admin.py`

Routes:
- `GET /audit-logs` — list page with optional `event_type` filter
- `GET /audit-logs/rows?event_type=&limit=` — HTMX partial for filtered table rows

**Acceptance:** Audit log viewable. Filters work via HTMX.

### Task 5-9: Register ui_admin router in main.py with prefix

**File:** `apps/api/src/inndxd_api/main.py`

```python
from inndxd_api.routers.ui_admin import router as ui_admin_router
...
app.include_router(ui_admin_router, prefix="/ui/admin", tags=["ui-admin"])
```

**Acceptance:** Admin pages reachable at `/ui/admin/providers`, `/ui/admin/api-keys`, `/ui/admin/audit-logs`.

### Task 5-10: Add admin guard to base.html sidebar

**File:** `apps/api/templates/base.html`

**Action:** Pass `admin` boolean in template context from all routes. Sidebar `{% if admin %}` block shows admin nav links. In `_require_admin()` helper, set `admin=True` in returned dict.

**Acceptance:** Only admins see admin nav links in sidebar.

---

## Execution Order

| Batch | Tasks | Depends On |
|---|---|---|
| A | 0-1 through 0-8 | — |
| B | 1-1, 1-2, 1-3 | A |
| C | 1-4 through 1-8 | B |
| D | 2-1 through 2-10 | C |
| E | 3-1 through 3-11 | D |
| F | 4-1 through 4-8 | D |
| G | 5-1 through 5-10 | C (auth) + D (projects for admin context) |

---

## Total Estimates

| Phase | Tasks | Est. Hours |
|---|---|---|
| 0 — Foundation | 8 | 5 |
| 1 — Auth Pages | 8 | 5 |
| 2 — Dashboard & Projects | 10 | 7 |
| 3 — Briefs Management | 11 | 8 |
| 4 — Data Items & Export | 8 | 5 |
| 5 — Admin Panels | 10 | 7 |

**Total: 55 tasks, ~37 hours**
