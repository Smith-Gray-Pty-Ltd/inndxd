# Inndxd — Stage 3 Implementation Plan

> **Prerequisite:** Stage 1 & 2 complete and merged to `main`.
> **Status:** All tasks are atomic — each touches at most one file. Suitable for small-model coding agents.

---

## Git Workflow Reference

- Fork from `main`: `git checkout -b stage3/phase<X>-<slug>`
- One commit per task: `phase<X>: <task-id> <imperative-verb> <what changed>`
- Before each commit: `~/.local/bin/uv run ruff check . && format --check && mypy . && pytest -v`
- Squash-merge PR back to `main` after all phase tasks pass
- Update `README.md` and `plan/stage3.md` tracking table after each phase merge

---

## Table of Contents

| Phase | Tasks | Description |
|---|---|---|
| [Phase 0](#phase-0-stage-2-cleanup) | 7 | Fix Stage 2 inconsistencies, TenantMiddleware wiring, config dedup |
| [Phase 1](#phase-1-jwt-authentication) | 14 | User model, registration, login, JWT middleware, role-based access |
| [Phase 2](#phase-2-multi-provider-llm-system) | 17 | DB-backed provider registry, management APIs, health checks, failover, per-node assignment |
| [Phase 3](#phase-3-api-key-management) | 8 | API key generation, rotation, revocation, rate limiting |
| [Phase 4](#phase-4-observability-upgrades) | 9 | OpenTelemetry tracing, audit log, enhanced Prometheus metrics |
| [Phase 5](#phase-5-agent-graph-upgrades) | 10 | Multi-agent orchestration, recursive research, custom plugins, benchmarking |

**Total: 65 tasks**

| Phase | Status |
|---|---|
| 0 — Stage 2 Cleanup | ⬜ Pending |
| 1 — JWT Authentication | ✅ Complete |
| 2 — Multi-Provider LLM | ✅ Complete |
| 3 — API Key Management | ✅ Complete |
| 4 — Observability | ⬜ Pending |
| 5 — Agent Graph Upgrades | ⬜ Pending |

---

## Phase 0: Stage 2 Cleanup

> **Goal:** Fix inconsistencies and wiring issues from Stage 2. No new features — pure quality and correctness.

---

### Task 0-1: Wire TenantMiddleware into FastAPI app

**File:** `apps/api/src/inndxd_api/main.py`
**Issue:** `TenantMiddleware` is imported but never registered on the app.

**Ensure the file contains:**
```python
from inndxd_api.middleware.tenant import TenantMiddleware
...
def create_app() -> FastAPI:
    app = FastAPI(...)
    app.add_middleware(TenantMiddleware)
    ...
```

If `create_app()` exists as a factory, register middleware inside it. If the app is top-level, call `app.add_middleware(TenantMiddleware)` after `app = FastAPI(...)`.

**Acceptance:** Every request passes through `TenantMiddleware`.

---

### Task 0-2: Deprecate duplicate config in apps/api

**File:** `apps/api/src/inndxd_api/config.py`
**Issue:** `apps/api/src/inndxd_api/config.py` is a stale duplicate of `inndxd_core/config.py`. Only `inndxd_core.config` should be the source of truth.

**Action:** Replace the entire file content with a re-export stub:

```python
"""Deprecated — use inndxd_core.config instead."""
from inndxd_core.config import Settings, settings  # noqa: F401
```

**Acceptance:** `from inndxd_api.config import settings` still works (backward compat), but the canonical config lives in `inndxd_core`.

---

### Task 0-3: Standardize main.py to use create_app factory

**File:** `apps/api/src/inndxd_api/main.py`
**Issue:** Some Stage 2 code expects `create_app()`, other code accesses `app` directly. Standardize on the factory pattern.

**Ensure the file has both:**
```python
def create_app() -> FastAPI:
    from inndxd_core.config import settings
    from inndxd_core.logging_config import configure_logging

    configure_logging(settings.log_level)

    app = FastAPI(
        title="Inndxd API",
        version="0.2.0",
        lifespan=lifespan,
    )
    app.add_middleware(TenantMiddleware)
    app.add_route("/metrics", get_metrics)
    app.include_router(projects_router, prefix="/api/projects", tags=["projects"])
    app.include_router(briefs_router, prefix="/api/briefs", tags=["briefs"])
    app.include_router(data_items_router, prefix="/api/data-items", tags=["data-items"])
    app.include_router(runs_router, prefix="/api/runs", tags=["runs"])
    app.include_router(ws_router, tags=["websocket"])
    return app


app = create_app()  # Top-level for uvicorn
```

**Acceptance:** Both `from inndxd_api.main import create_app` and `uvicorn inndxd_api.main:app` work.

---

### Task 0-4: Fix briefs.py to use Celery tasks (not inline background)

**File:** `apps/api/src/inndxd_api/routers/briefs.py`
**Issue:** Some filesystems have the older version that runs `run_research_swarm` inline. It should dispatch a Celery task.

**Ensure the `create_brief` endpoint does:**
```python
from inndxd_api.tasks import run_research_task

@router.post("/", response_model=BriefRead, status_code=status.HTTP_201_CREATED)
async def create_brief(
    body: BriefCreate,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    brief = Brief(
        tenant_id=tenant_id,
        project_id=body.project_id,
        natural_language=body.natural_language,
        status="pending",
    )
    db.add(brief)
    await db.commit()
    await db.refresh(brief)

    briefs_created.inc()
    run_research_task.delay(
        str(brief.id), str(tenant_id), str(body.project_id), body.natural_language
    )
    return brief
```

**Acceptance:** `POST /api/briefs` dispatches to Celery, not inline. No `async def run_research_task()` helper in this file.

---

### Task 0-5: Add missing `__init__.py` to all test directories

**Files:** `packages/inndxd-agents/tests/__init__.py`, `packages/inndxd-core/tests/__init__.py`
**Issue:** These were deleted in Phase 0 fixes but caused mypy collisions. Add them back if mypy needs them, or ensure mypy config excludes test dirs.

**Action:** Check `pyproject.toml` `[tool.mypy]` section. If `exclude` covers test dirs, these `__init__.py` files can remain absent. If not, add them as empty files.

**Acceptance:** `~/.local/bin/uv run mypy .` runs without duplicate module errors.

---

### Task 0-6: Add `inndxd-mcp` to root pyproject.toml source map

**File:** `pyproject.toml`
**Issue:** `inndxd-mcp` may be missing from `[tool.uv.sources]`.

**Ensure:**
```toml
[tool.uv.sources]
inndxd-core = { workspace = true }
inndxd-agents = { workspace = true }
inndxd-mcp = { workspace = true }
inndxd-api = { workspace = true }
```

**Acceptance:** `~/.local/bin/uv sync` installs all 4 workspace packages.

---

### Task 0-7: Bump masterplan.md and README versions to reflect Stage 2 completion

**Files:** `plan/masterplan.md`, `README.md`
**Action:** If not already done, ensure:

- `masterplan.md` titled "Master Implementation Plan" with Stage 1 & 2 both ✅
- README Stage 2 badge or line showing completion
- README status table shows all phases ✅
- README lists all API endpoints including Stage 2 additions (export, task-status, metrics, WebSocket)

**Acceptance:** Documentation accurately reflects the codebase at Stage 2 complete.

---

## Phase 1: JWT Authentication

> **Prerequisites:** Phase 0 complete.
> **Goal:** Replace `X-Tenant-ID` header with JWT-based session authentication. User registration, login, token validation middleware, role-based access.

---

### Task 1-1: Add auth dependencies (pyjwt, passlib, bcrypt) to API

**File:** `apps/api/pyproject.toml`
**Action:** Add auth packages.

**Add to dependencies:**
```toml
"pyjwt>=2.9,<3",
"passlib[bcrypt]>=1.7,<2",
```

**Acceptance:** `~/.local/bin/uv sync` installs pyjwt and passlib.

---

### Task 1-2: Create User ORM model

**File:** `packages/inndxd-core/src/inndxd_core/models/user.py` (CREATE)

```python
"""User model for authentication."""
from __future__ import annotations

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from inndxd_core.models.base import Base, TimestampMixin, UUIDMixin


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    default_tenant_id: Mapped[str] = mapped_column(String(36), nullable=True)
```

**Acceptance:** `from inndxd_core.models.user import User` succeeds.

---

### Task 1-3: Create User domain models

**File:** `packages/inndxd-core/src/inndxd_core/domain/user.py` (CREATE)

```python
"""User domain models."""
from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    is_active: bool
    is_admin: bool
    created_at: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
```

**Acceptance:** `from inndxd_core.domain.user import UserCreate, UserRead` works.

---

### Task 1-4: Add email-validator to core dependencies

**File:** `packages/inndxd-core/pyproject.toml`
**Action:** `pydantic[email-validator]` or `email-validator` directly.

**Add:** `"email-validator>=2.2,<3"` to core dependencies.

**Acceptance:** `from pydantic import EmailStr` works.

---

### Task 1-5: Create UserRepository

**File:** `packages/inndxd-core/src/inndxd_core/repositories/users.py` (CREATE)

```python
"""User repository."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from inndxd_core.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create(self, email: str, hashed_password: str) -> User:
        user = User(email=email, hashed_password=hashed_password)
        self.session.add(user)
        await self.session.flush()
        return user
```

**Acceptance:** `from inndxd_core.repositories.users import UserRepository` works.

---

### Task 1-6: Create auth utilities (password hashing, JWT encode/decode)

**File:** `apps/api/src/inndxd_api/auth.py` (CREATE)

```python
"""Authentication utilities: password hashing and JWT management."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext
from uuid import UUID

from inndxd_core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

JWT_SECRET = getattr(settings, "jwt_secret", "inndxd-dev-secret-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60 * 24  # 24 hours


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: UUID, tenant_id: UUID | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "exp": expire,
    }
    if tenant_id:
        payload["tenant_id"] = str(tenant_id)
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
```

**Acceptance:** `hash_password("test")` returns a bcrypt hash, `verify_password("test", hash)` returns True.

---

### Task 1-7: Create auth router (register + login)

**File:** `apps/api/src/inndxd_api/routers/auth.py` (CREATE)

```python
"""Authentication router: register and login."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from inndxd_api.auth import create_access_token, hash_password, verify_password
from inndxd_api.dependencies import get_db
from inndxd_core.domain.user import LoginRequest, TokenResponse, UserCreate, UserRead
from inndxd_core.repositories.users import UserRepository

router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(body: UserCreate, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    existing = await repo.get_by_email(body.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = await repo.create(body.email, hash_password(body.password))
    await db.commit()
    return user


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    user = await repo.get_by_email(body.email)
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")
    token = create_access_token(user.id, None)
    return TokenResponse(access_token=token)
```

**Acceptance:** `POST /api/auth/register` creates a user. `POST /api/auth/login` returns a JWT.

---

### Task 1-8: Register auth router in main.py

**File:** `apps/api/src/inndxd_api/main.py`
**Action:** Include the auth router.

**Add:**
```python
from inndxd_api.routers.auth import router as auth_router
...
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
```

**Acceptance:** `GET /api/auth/login` (POST) is reachable.

---

### Task 1-9: Create JWT auth dependency

**File:** `apps/api/src/inndxd_api/dependencies.py`
**Action:** Add a dependency that extracts and validates the JWT from the `Authorization` header.

**Add:**
```python
from fastapi import Depends, Header, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from inndxd_api.auth import decode_access_token

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(security),
    x_tenant_id: str | None = Header(None, alias="X-Tenant-ID"),
) -> dict:
    if credentials:
        payload = decode_access_token(credentials.credentials)
        return {"user_id": payload["sub"], "tenant_id": payload.get("tenant_id")}
    if x_tenant_id:
        try:
            UUID(x_tenant_id)
            return {"user_id": None, "tenant_id": x_tenant_id}
        except ValueError:
            pass
    return {"user_id": None, "tenant_id": None}
```

**Acceptance:** Routes using `Depends(get_current_user)` get user info from JWT or fall back to `X-Tenant-ID`.

---

### Task 1-10: Update get_tenant_id to prefer JWT over header

**File:** `apps/api/src/inndxd_api/dependencies.py`
**Action:** Make `get_tenant_id` derive the tenant from JWT when available.

**Modify:**
```python
def get_tenant_id(
    user: dict = Depends(get_current_user),
    x_tenant_id: str | None = Header(None, alias="X-Tenant-ID"),
) -> UUID | None:
    tid = user.get("tenant_id")
    if tid:
        return UUID(tid)
    if x_tenant_id:
        try:
            return UUID(x_tenant_id)
        except ValueError:
            pass
    return None
```

**Acceptance:** JWT takes priority for tenant identification. Header is fallback.

---

### Task 1-11: Add admin-required dependency

**File:** `apps/api/src/inndxd_api/dependencies.py`
**Action:** Add a dependency that validates admin role.

**Append:**
```python
async def require_admin(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    user_id = user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    from inndxd_core.models.user import User

    db_user = await db.get(User, UUID(user_id))
    if not db_user or not db_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin required")
    return user
```

**Acceptance:** Routes using `Depends(require_admin)` reject non-admin users with 403.

---

### Task 1-12: Add jwt_secret to core config

**File:** `packages/inndxd-core/src/inndxd_core/config.py`
**Action:** Add JWT configuration.

**Add:**
```python
jwt_secret: str = "inndxd-dev-secret-change-me"
jwt_algorithm: str = "HS256"
jwt_expire_minutes: int = 1440  # 24 hours
```

**Acceptance:** `from inndxd_core.config import settings; print(settings.jwt_secret)` works.

---

### Task 1-13: Add User SQLAlchemy model to models __init__.py

**File:** `packages/inndxd-core/src/inndxd_core/models/__init__.py`
**Action:** Re-export User.

**Add:**
```python
from inndxd_core.models.user import User
```

And add `"User"` to `__all__`.

**Acceptance:** `from inndxd_core.models import User` works.

---

### Task 1-14: Add user domain to domain __init__.py and repos to repositories __init__.py

**Files:**
- `packages/inndxd-core/src/inndxd_core/domain/__init__.py`
- `packages/inndxd-core/src/inndxd_core/repositories/__init__.py`

**Action:** Re-export User domain models and repository.

**Acceptance:** `from inndxd_core.domain import UserCreate` and `from inndxd_core.repositories import UserRepository` work.

---

## Phase 2: Multi-Provider LLM System

> **Prerequisites:** Phase 1 complete (needs JWT auth for admin-only provider management).
> **Goal:** DB-backed LLM provider registry with management APIs, health checks, failover, and per-node model assignment at runtime.

---

### Task 2-1: Create LLMProvider ORM model

**File:** `packages/inndxd-core/src/inndxd_core/models/llm_provider.py` (CREATE)

```python
"""LLM provider configuration model."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from inndxd_core.models.base import Base, TimestampMixin, UUIDMixin


class LLMProvider(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "llm_providers"

    tenant_id: Mapped[UUID] = mapped_column(PGUUID(), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    provider_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="openai_compatible"
    )
    base_url: Mapped[str] = mapped_column(Text, nullable=False)
    api_key: Mapped[str] = mapped_column(Text, nullable=False, default="")
    default_model: Mapped[str] = mapped_column(String(100), nullable=False)
    available_models: Mapped[str] = mapped_column(
        Text, nullable=False, default="[]"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    priority: Mapped[int] = mapped_column(default=0, nullable=False)
```

**Acceptance:** `from inndxd_core.models.llm_provider import LLMProvider` works.

---

### Task 2-2: Create LLMProvider domain models (Pydantic)

**File:** `packages/inndxd-core/src/inndxd_core/domain/llm_provider.py`
**Action:** Extend the existing domain file with CRUD schemas.

**Add:**
```python
from uuid import UUID
from datetime import datetime


class LLMProviderCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    provider_type: str = Field(default="openai_compatible")
    base_url: str
    api_key: str = ""
    default_model: str
    available_models: list[str] = Field(default_factory=list)
    is_active: bool = True
    priority: int = 0


class LLMProviderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    name: str
    provider_type: str
    base_url: str
    default_model: str
    available_models: list[str]
    is_active: bool
    priority: int
    created_at: datetime
    updated_at: datetime


class LLMProviderUpdate(BaseModel):
    name: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    default_model: str | None = None
    available_models: list[str] | None = None
    is_active: bool | None = None
    priority: int | None = None
```

**Acceptance:** `LLMProviderCreate(name="test", base_url="http://x", default_model="m")` validates.

---

### Task 2-3: Create LLMProviderRepository

**File:** `packages/inndxd-core/src/inndxd_core/repositories/llm_providers.py` (CREATE)

```python
"""LLM Provider repository."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from inndxd_core.models.llm_provider import LLMProvider


class LLMProviderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_by_tenant(self, tenant_id: UUID) -> list[LLMProvider]:
        result = await self.session.execute(
            select(LLMProvider)
            .where(LLMProvider.tenant_id == tenant_id)
            .order_by(LLMProvider.priority.desc())
        )
        return list(result.scalars().all())

    async def get_active_for_tenant(self, tenant_id: UUID) -> list[LLMProvider]:
        result = await self.session.execute(
            select(LLMProvider)
            .where(LLMProvider.tenant_id == tenant_id, LLMProvider.is_active == True)
            .order_by(LLMProvider.priority.desc())
        )
        return list(result.scalars().all())

    async def create(
        self, tenant_id: UUID, name: str, provider_type: str,
        base_url: str, api_key: str, default_model: str,
        available_models: list[str], priority: int,
    ) -> LLMProvider:
        provider = LLMProvider(
            tenant_id=tenant_id,
            name=name,
            provider_type=provider_type,
            base_url=base_url,
            api_key=api_key,
            default_model=default_model,
            available_models=json.dumps(available_models),
            priority=priority,
            is_active=True,
        )
        self.session.add(provider)
        await self.session.flush()
        return provider

    async def delete(self, provider: LLMProvider) -> None:
        await self.session.delete(provider)
        await self.session.flush()
```

**Acceptance:** `from inndxd_core.repositories.llm_providers import LLMProviderRepository` works.

---

### Task 2-4: Create LLM provider management router (admin only)

**File:** `apps/api/src/inndxd_api/routers/llm_providers.py` (CREATE)

```python
"""LLM Provider management router — admin only."""
from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from inndxd_api.dependencies import get_db, get_tenant_id, require_admin
from inndxd_core.domain.llm_provider import (
    LLMProviderCreate, LLMProviderRead, LLMProviderUpdate,
)
from inndxd_core.repositories.llm_providers import LLMProviderRepository

router = APIRouter()


@router.get("/", response_model=list[LLMProviderRead])
async def list_providers(
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    repo = LLMProviderRepository(db)
    return await repo.list_by_tenant(tenant_id)


@router.post("/", response_model=LLMProviderRead, status_code=status.HTTP_201_CREATED)
async def create_provider(
    body: LLMProviderCreate,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    repo = LLMProviderRepository(db)
    provider = await repo.create(
        tenant_id=tenant_id,
        name=body.name,
        provider_type=body.provider_type,
        base_url=body.base_url,
        api_key=body.api_key,
        default_model=body.default_model,
        available_models=body.available_models,
        priority=body.priority,
    )
    await db.commit()
    return provider


@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_provider(
    provider_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    from inndxd_core.models.llm_provider import LLMProvider as LLMProviderModel

    provider = await db.get(LLMProviderModel, provider_id)
    if not provider:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    repo = LLMProviderRepository(db)
    await repo.delete(provider)
    await db.commit()


@router.patch("/{provider_id}", response_model=LLMProviderRead)
async def update_provider(
    provider_id: UUID,
    body: LLMProviderUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    from inndxd_core.models.llm_provider import LLMProvider as LLMProviderModel

    provider = await db.get(LLMProviderModel, provider_id)
    if not provider:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    update_data = body.model_dump(exclude_unset=True)
    if "available_models" in update_data:
        update_data["available_models"] = json.dumps(update_data["available_models"])
    for key, value in update_data.items():
        setattr(provider, key, value)

    await db.commit()
    await db.refresh(provider)
    return provider
```

**Acceptance:** Admin can CRUD providers via `POST/GET/DELETE/PATCH /api/llm-providers`.

---

### Task 2-5: Register LLM providers router in main.py

**File:** `apps/api/src/inndxd_api/main.py`
**Action:** Add the LLM providers router.

**Acceptance:** `GET /api/llm-providers` returns [] (no providers yet).

---

### Task 2-6: Create provider health check utility

**File:** `apps/api/src/inndxd_api/provider_health.py` (CREATE)

```python
"""LLM provider health check utilities."""
from __future__ import annotations

import logging

import httpx
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


async def check_provider_health(base_url: str, api_key: str, model: str) -> bool:
    client = AsyncOpenAI(base_url=base_url, api_key=api_key or "no-key")
    try:
        models = await client.models.list()
        return any(m.id == model for m in models.data)
    except Exception:
        pass

    try:
        async with httpx.AsyncClient(timeout=10.0) as http:
            resp = await http.get(f"{base_url.rstrip('/')}/models")
            if resp.status_code == 200:
                data = resp.json()
                models_list = data.get("data", data.get("models", []))
                for m in models_list:
                    if m.get("id", m.get("name", "")) == model:
                        return True
        return False
    except Exception as exc:
        logger.debug("Health check failed for %s: %s", base_url, exc)
        return False
```

**Acceptance:** `check_provider_health("http://localhost:11434/v1", "ollama", "deepseek-r1:latest")` returns True/False.

---

### Task 2-7: Create provider health check endpoint

**File:** `apps/api/src/inndxd_api/routers/llm_providers.py` (append)

**Action:** Add a health check endpoint.

**Append:**
```python
@router.post("/{provider_id}/health")
async def health_check_provider(
    provider_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    from inndxd_core.models.llm_provider import LLMProvider as LLMProviderModel
    from inndxd_api.provider_health import check_provider_health

    provider = await db.get(LLMProviderModel, provider_id)
    if not provider:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    healthy = await check_provider_health(
        provider.base_url, provider.api_key, provider.default_model
    )
    return {"provider_id": str(provider_id), "healthy": healthy}
```

**Acceptance:** `POST /api/llm-providers/{id}/health` returns `{"healthy": true/false}`.

---

### Task 2-8: Create provider sync utility — load DB providers into runtime config

**File:** `apps/api/src/inndxd_api/provider_sync.py` (CREATE)

```python
"""Sync DB provider configs into the runtime LLM config."""
from __future__ import annotations

import json
import logging

from inndxd_agents.llm import set_llm_config
from inndxd_core.db import async_session_factory
from inndxd_core.domain.llm_provider import LLMConfig, LLMProviderConfig
from inndxd_core.models.llm_provider import LLMProvider
from sqlalchemy import select

logger = logging.getLogger(__name__)


async def sync_providers_for_tenant(tenant_id: str) -> LLMConfig:
    async with async_session_factory() as session:
        result = await session.execute(
            select(LLMProvider)
            .where(LLMProvider.tenant_id == tenant_id, LLMProvider.is_active == True)
            .order_by(LLMProvider.priority.desc())
        )
        rows = result.scalars().all()

    if not rows:
        return _build_default()

    providers = {}
    for row in rows:
        try:
            available = json.loads(row.available_models)
        except (json.JSONDecodeError, TypeError):
            available = [row.default_model]
        providers[row.name] = LLMProviderConfig(
            name=row.name,
            base_url=row.base_url,
            api_key=row.api_key,
            default_model=row.default_model,
            models=available,
        )

    config = LLMConfig(default_provider=rows[0].name, providers=providers)
    set_llm_config(config)
    logger.info("Synced %d providers for tenant %s", len(providers), tenant_id)
    return config
```

**Acceptance:** Calling `sync_providers_for_tenant(tenant_uuid)` loads DB providers into the runtime config.

---

### Task 2-9: Create per-node model assignment model

**File:** `packages/inndxd-core/src/inndxd_core/domain/llm_provider.py` (append)

**Append:**
```python
class NodeModelAssignment(BaseModel):
    planner_model: str | None = None
    collector_model: str | None = None
    structurer_model: str | None = None
```

**Acceptance:** `NodeModelAssignment(planner_model="gpt-4.5-chat")` validates.

---

### Task 2-10: Create node model assignment endpoint

**File:** `apps/api/src/inndxd_api/routers/llm_providers.py` (append)

**Append:**
```python
_node_assignments: dict[str, dict[str, str | None]] = {}


@router.get("/node-assignments")
async def get_node_assignments(_: dict = Depends(require_admin)):
    return _node_assignments


@router.put("/node-assignments")
async def set_node_assignments(
    body: NodeModelAssignment,
    tenant_id: UUID = Depends(get_tenant_id),
    _: dict = Depends(require_admin),
):
    tid = str(tenant_id)
    _node_assignments[tid] = {
        "planner": body.planner_model,
        "collector": body.collector_model,
        "structurer": body.structurer_model,
    }
    return {"status": "ok"}
```

**Acceptance:** `PUT /api/llm-providers/node-assignments` with model names, then `GET` returns them.

---

### Task 2-11: Update resolve_model_for_node to consult DB assignments

**File:** `packages/inndxd-agents/src/inndxd_agents/llm.py`
**Action:** Extend `resolve_model_for_node` to also check environment variables.

**Update the function:**
```python
def resolve_model_for_node(node_name: str, tenant_id: str | None = None) -> str:
    from inndxd_agents.config import settings as agent_settings

    env_override = {
        "planner": agent_settings.planner_model,
        "collector": agent_settings.collector_model,
        "structurer": agent_settings.structurer_model,
    }.get(node_name)
    if env_override:
        return env_override

    if tenant_id:
        try:
            from inndxd_api.routers.llm_providers import _node_assignments
            assignments = _node_assignments.get(tenant_id, {})
            model = assignments.get(node_name)
            if model:
                return model
        except ImportError:
            pass

    return get_default_model()
```

**Acceptance:** If per-node assignment is set for a tenant, `resolve_model_for_node` returns it.

---

### Task 2-12: Add auto-sync on app startup

**File:** `apps/api/src/inndxd_api/main.py`
**Action:** Call `sync_providers_for_tenant` during lifespan startup for a default tenant or on demand.

**In lifespan startup, after table creation:**
```python
try:
    from inndxd_api.provider_sync import sync_providers_for_tenant
    from inndxd_core.config import settings
    if settings.ollama_base_url:
        pass
except ImportError:
    pass
```

**Acceptance:** App starts with default Ollama config if no DB providers exist.

---

### Task 2-13: Add provider failover logic to LLM client creation

**File:** `packages/inndxd-agents/src/inndxd_agents/llm.py`
**Action:** If the primary provider is down, try the next in priority order.

**Add:**
```python
def create_client_with_failover(tenant_id: str | None = None) -> AsyncOpenAI:
    config = get_llm_config()
    providers = list(config.providers.values())

    if not providers:
        raise ValueError("No LLM providers configured")

    for provider in sorted(providers, key=lambda p: -config.providers.get(p.name, p).priority if hasattr(p, "priority") else 0):
        try:
            return create_openai_compatible_client(provider.name)
        except Exception:
            logger.warning("Provider %s unavailable, trying next", provider.name)
            continue

    raise ValueError("All LLM providers failed")
```

**Acceptance:** If primary provider is unavailable, the next in priority order is used.

---

### Task 2-14: Add health check to provider sync

**File:** `apps/api/src/inndxd_api/provider_sync.py`
**Action:** During sync, run a health check on each provider and log warnings for unhealthy ones.

**In `sync_providers_for_tenant`, after building the config:**
```python
from inndxd_api.provider_health import check_provider_health

for row in rows:
    healthy = await check_provider_health(row.base_url, row.api_key, row.default_model)
    if not healthy:
        logger.warning("Provider %s is unhealthy", row.name)
```

**Acceptance:** Health status is logged during provider sync.

---

### Task 2-15: Add provider sync endpoint (admin)

**File:** `apps/api/src/inndxd_api/routers/llm_providers.py` (append)

**Append:**
```python
@router.post("/sync")
async def sync_providers(
    tenant_id: UUID = Depends(get_tenant_id),
    _: dict = Depends(require_admin),
):
    from inndxd_api.provider_sync import sync_providers_for_tenant

    config = await sync_providers_for_tenant(str(tenant_id))
    return {
        "status": "synced",
        "providers": list(config.providers.keys()),
    }
```

**Acceptance:** `POST /api/llm-providers/sync` loads all active providers into runtime.

---

### Task 2-16: Add models/domain/repo re-exports for LLM provider

**Files:**
- `packages/inndxd-core/src/inndxd_core/models/__init__.py`
- `packages/inndxd-core/src/inndxd_core/domain/__init__.py`
- `packages/inndxd-core/src/inndxd_core/repositories/__init__.py`

**Action:** Add `LLMProvider` model, domain classes, and repository to respective `__init__.py` files.

**Acceptance:** All three importable via top-level package shortcuts.

---

### Task 2-17: Add provider import test

**File:** `packages/inndxd-core/tests/test_domain_models.py` (append)

**Append:**
```python
from inndxd_core.domain.llm_provider import LLMProviderConfig, LLMConfig, LLMProviderCreate


def test_llm_provider_config_creates():
    p = LLMProviderConfig(
        name="test",
        base_url="http://localhost:11434/v1",
        api_key="ollama",
        default_model="deepseek-r1:latest",
    )
    assert p.name == "test"


def test_llm_config_defaults():
    c = LLMConfig()
    assert c.default_provider == "ollama"
    assert c.providers == {}
```

**Acceptance:** `pytest` passes both new tests.

---

## Phase 3: API Key Management

> **Prerequisites:** Phase 1 complete (JWT auth).
> **Goal:** API key generation for programmatic access, key rotation, revocation, and rate limiting.

---

### Task 3-1: Add slowapi to API deps

**File:** `apps/api/pyproject.toml`
**Action:** Add rate limiting package.

**Add:** `"slowapi>=0.1,<1"`

**Acceptance:** `~/.local/bin/uv sync` installs slowapi.

---

### Task 3-2: Create APIKey ORM model

**File:** `packages/inndxd-core/src/inndxd_core/models/api_key.py` (CREATE)

```python
"""API Key model."""
from __future__ import annotations

import secrets
from uuid import UUID

from sqlalchemy import Boolean, String, DateTime
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from inndxd_core.models.base import Base, TimestampMixin, UUIDMixin
from inndxd_core.models.user import User


class APIKey(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "api_keys"

    user_id: Mapped[UUID] = mapped_column(PGUUID(), ForeignKey("users.id"), index=True, nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(12), index=True, nullable=False)
    key_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    @staticmethod
    def generate_key() -> tuple[str, str, str]:
        raw = "inndxd_" + secrets.token_urlsafe(32)
        prefix = raw[:12]
        return raw, prefix, hash_password(raw)

    @staticmethod
    def verify_key(raw: str, hashed: str) -> bool:
        return verify_password(raw, hashed)
```

**Note:** Add missing imports at top: `from inndxd_api.auth import hash_password, verify_password` won't work from core — use passlib directly.

**Acceptance:** `APIKey.generate_key()` returns a raw key string, prefix, and hash.

---

### Task 3-3: Create APIKey domain + repository

**Files:**
- `packages/inndxd-core/src/inndxd_core/domain/api_key.py` (CREATE)
- `packages/inndxd-core/src/inndxd_core/repositories/api_keys.py` (CREATE)

**Domain:**
```python
from __future__ import annotations
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class APIKeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)

class APIKeyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    key_prefix: str
    is_active: bool
    created_at: str
    last_used_at: str | None

class APIKeyCreated(BaseModel):
    id: UUID
    name: str
    raw_key: str
```

**Repository:**
```python
from __future__ import annotations
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from inndxd_core.models.api_key import APIKey

class APIKeyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_user(self, user_id: UUID) -> list[APIKey]:
        result = await self.session.execute(
            select(APIKey).where(APIKey.user_id == user_id)
        )
        return list(result.scalars().all())

    async def create(self, user_id: UUID, name: str) -> tuple[APIKey, str]:
        raw, prefix, key_hash = APIKey.generate_key()
        key = APIKey(user_id=user_id, key_prefix=prefix, key_hash=key_hash, name=name)
        self.session.add(key)
        await self.session.flush()
        return key, raw

    async def revoke(self, key: APIKey) -> None:
        key.is_active = False
        await self.session.flush()
```

**Acceptance:** Full create + list + revoke flow works.

---

### Task 3-4: Create API key management router

**File:** `apps/api/src/inndxd_api/routers/api_keys.py` (CREATE)

```python
"""API Key management."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from inndxd_api.dependencies import get_current_user, get_db
from inndxd_core.domain.api_key import APIKeyCreated, APIKeyRead
from inndxd_core.repositories.api_keys import APIKeyRepository

router = APIRouter()


@router.get("/", response_model=list[APIKeyRead])
async def list_keys(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    uid = UUID(user["user_id"])
    repo = APIKeyRepository(db)
    return await repo.list_for_user(uid)


@router.post("/", response_model=APIKeyCreated, status_code=status.HTTP_201_CREATED)
async def create_key(
    name: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    uid = UUID(user["user_id"])
    repo = APIKeyRepository(db)
    key, raw = await repo.create(uid, name)
    await db.commit()
    return APIKeyCreated(id=key.id, name=key.name, raw_key=raw)


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_key(
    key_id: UUID,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from inndxd_core.models.api_key import APIKey as APIKeyModel

    key = await db.get(APIKeyModel, key_id)
    if not key or str(key.user_id) != user["user_id"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    repo = APIKeyRepository(db)
    await repo.revoke(key)
    await db.commit()
```

**Acceptance:** `POST /api/api-keys` generates a key. `GET` lists keys. `DELETE` revokes.

---

### Task 3-5: Register API keys router

**File:** `apps/api/src/inndxd_api/main.py`
**Action:** Add API key router.

**Acceptance:** `GET /api/api-keys` is accessible (requires auth).

---

### Task 3-6: Create API key auth dependency

**File:** `apps/api/src/inndxd_api/dependencies.py`
**Action:** Allow authentication via `Authorization: Bearer inndxd_...` header (API key format).

**Add:**
```python
async def get_current_user_or_key(
    credentials: HTTPAuthorizationCredentials | None = Security(security),
    x_api_key: str | None = Header(None, alias="X-API-Key"),
) -> dict:
    raw_key = None
    if credentials and credentials.credentials.startswith("inndxd_"):
        raw_key = credentials.credentials
    elif x_api_key and x_api_key.startswith("inndxd_"):
        raw_key = x_api_key
    else:
        return await get_current_user(credentials, x_api_key)

    if raw_key:
        from inndxd_core.db import async_session_factory
        from inndxd_core.models.api_key import APIKey

        async with async_session_factory() as session:
            result = await session.execute(
                select(APIKey).where(
                    APIKey.key_prefix == raw_key[:12],
                    APIKey.is_active == True,
                )
            )
            key = result.scalar_one_or_none()
            if key and key.verify_key(raw_key, key.key_hash):
                key.last_used_at = datetime.now(timezone.utc)
                await session.commit()
                return {"user_id": str(key.user_id), "tenant_id": None, "api_key": True}

    return {"user_id": None, "tenant_id": None}
```

**Acceptance:** Requests with valid API key in header authenticate.

---

### Task 3-7: Add rate limiting middleware with slowapi

**File:** `apps/api/src/inndxd_api/rate_limit.py` (CREATE)

```python
"""Rate limiting configuration."""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
```

**Wire into main.py:**
```python
from inndxd_api.rate_limit import limiter
from slowapi.middleware import SlowAPIMiddleware

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
```

**Acceptance:** Repeated requests to endpoints get 429 responses.

---

### Task 3-8: Add re-exports for API key domain/repo/models

**Files:**
- `packages/inndxd-core/src/inndxd_core/models/__init__.py`
- `packages/inndxd-core/src/inndxd_core/domain/__init__.py`
- `packages/inndxd-core/src/inndxd_core/repositories/__init__.py`

**Action:** Register API key components.

**Acceptance:** Clean imports from top-level packages.

---

## Phase 4: Observability Upgrades

> **Prerequisites:** Phase 1 complete.
> **Goal:** OpenTelemetry distributed tracing, agent execution audit log, enhanced Prometheus metrics, request logging middleware.

---

### Task 4-1: Add OpenTelemetry deps to API

**File:** `apps/api/pyproject.toml`
**Action:** Add OTel packages.

```toml
"opentelemetry-api>=1.28,<2",
"opentelemetry-sdk>=1.28,<2",
"opentelemetry-instrumentation-fastapi>=0.49,<1",
"opentelemetry-exporter-otlp>=1.28,<2",
```

**Acceptance:** `~/.local/bin/uv sync` installs OTel.

---

### Task 4-2: Create OTel tracing setup

**File:** `apps/api/src/inndxd_api/tracing.py` (CREATE)

```python
"""OpenTelemetry tracing setup."""
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor


def setup_tracing(service_name: str = "inndxd-api", otlp_endpoint: str | None = None):
    provider = TracerProvider()
    if otlp_endpoint:
        exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)


def instrument_app(app):
    FastAPIInstrumentor.instrument_app(app)
```

**Wire in `main.py` `create_app()` after app creation:**
```python
from inndxd_api.tracing import setup_tracing, instrument_app
setup_tracing(otlp_endpoint=getattr(settings, "otlp_endpoint", None))
instrument_app(app)
```

**Acceptance:** `from inndxd_api.tracing import setup_tracing` works. Jaeger/Zipkin can collect traces with OTLP endpoint configured.

---

### Task 4-3: Create agent execution audit log model

**File:** `packages/inndxd-core/src/inndxd_core/models/audit_log.py` (CREATE)

```python
"""Agent execution audit log."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from inndxd_core.models.base import Base, TimestampMixin, UUIDMixin


class AuditLog(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "audit_log"

    tenant_id: Mapped[UUID] = mapped_column(PGUUID(), index=True, nullable=False)
    brief_id: Mapped[UUID] = mapped_column(PGUUID(), index=True, nullable=True)
    event_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    actor: Mapped[str] = mapped_column(String(100), nullable=False)
    details: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="success")
```

**Acceptance:** `from inndxd_core.models.audit_log import AuditLog` works.

---

### Task 4-4: Create AuditLog repository + domain

**Files:**
- `packages/inndxd-core/src/inndxd_core/repositories/audit_logs.py` (CREATE)
- `packages/inndxd-core/src/inndxd_core/domain/audit_log.py` (CREATE)

**Repository:**
```python
"""Audit log repository."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from inndxd_core.models.audit_log import AuditLog


class AuditLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def log(
        self, tenant_id: UUID, event_type: str, actor: str,
        details: dict, brief_id: UUID | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            tenant_id=tenant_id,
            brief_id=brief_id,
            event_type=event_type,
            actor=actor,
            details=details,
        )
        self.session.add(entry)
        await self.session.flush()
        return entry

    async def list_by_tenant(
        self, tenant_id: UUID, limit: int = 100,
    ) -> list[AuditLog]:
        result = await self.session.execute(
            select(AuditLog)
            .where(AuditLog.tenant_id == tenant_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
```

**Acceptance:** `AuditLogRepository().log(tenant_id, "brief_created", "system", {})` persists an entry.

---

### Task 4-5: Instrument swarm with audit logging

**File:** `packages/inndxd-agents/src/inndxd_agents/swarm.py`
**Action:** Add audit log entries at key points.

**In `run_research_swarm()`, after graph invoke:**
```python
try:
    from inndxd_core.repositories.audit_logs import AuditLogRepository
    async with async_session_factory() as session:
        audit = AuditLogRepository(session)
        await audit.log(
            tenant_id=tenant_id,
            brief_id=brief_id,
            event_type="research_completed",
            actor="system",
            details={
                "items_collected": len(structured_items),
                "errors": result.get("errors", []),
            },
        )
        await session.commit()
except ImportError:
    pass
```

**Acceptance:** Each completed research run creates an audit log entry.

---

### Task 4-6: Add audit log endpoints (admin)

**File:** `apps/api/src/inndxd_api/routers/audit_logs.py` (CREATE)

```python
"""Audit log viewer — admin only."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from inndxd_api.dependencies import get_db, get_tenant_id, require_admin
from inndxd_core.repositories.audit_logs import AuditLogRepository

router = APIRouter()


@router.get("/")
async def list_audit_logs(
    limit: int = Query(default=100, ge=1, le=1000),
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin),
):
    repo = AuditLogRepository(db)
    logs = await repo.list_by_tenant(tenant_id, limit=limit)
    return [
        {
            "id": str(log.id),
            "event_type": log.event_type,
            "actor": log.actor,
            "status": log.status,
            "details": log.details,
            "created_at": str(log.created_at),
        }
        for log in logs
    ]
```

**Acceptance:** `GET /api/audit-logs` returns recent audit entries.

---

### Task 4-7: Register audit log router in main.py

**File:** `apps/api/src/inndxd_api/main.py`
**Action:** Add audit log router.

**Acceptance:** `GET /api/audit-logs` is reachable (admin only).

---

### Task 4-8: Add request duration histogram to Prometheus

**File:** `apps/api/src/inndxd_api/metrics.py`
**Action:** Add a request duration histogram.

**Append:**
```python
request_duration = Histogram(
    "inndxd_request_duration_seconds",
    "HTTP request duration",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1, 2, 5],
)
```

**Add middleware in main.py to observe request duration:**
```python
from inndxd_api.metrics import request_duration
from time import perf_counter

@app.middleware("http")
async def metrics_middleware(request, call_next):
    start = perf_counter()
    response = await call_next(request)
    duration = perf_counter() - start
    request_duration.labels(
        method=request.method,
        endpoint=request.url.path,
    ).observe(duration)
    return response
```

**Acceptance:** `request_duration` histogram tracks all API call latencies.

---

### Task 4-9: Add model re-exports for audit log

**Files:**
- `packages/inndxd-core/src/inndxd_core/models/__init__.py`
- `packages/inndxd-core/src/inndxd_core/repositories/__init__.py`

**Action:** Register audit log model and repository.

**Acceptance:** Clean imports from package level.

---

## Phase 5: Agent Graph Upgrades

> **Prerequisites:** Phase 1 + Phase 2 complete.
> **Goal:** Multi-agent orchestration (fan-out research), recursive follow-up briefs, custom node plugin system, agent performance benchmarking.

---

### Task 5-1: Create multi-agent fan-out graph builder

**File:** `packages/inndxd-agents/src/inndxd_agents/fanout.py` (CREATE)

```python
"""Multi-agent fan-out research graph."""
from __future__ import annotations

import asyncio
import json
import logging

logger = logging.getLogger(__name__)


async def fan_out_research(plan: str, state: dict, max_parallel: int = 3) -> list[dict]:
    plan_data = json.loads(plan)
    queries = plan_data.get("queries", [])

    from inndxd_agents.graph import build_research_graph

    async def _run_query(query: str):
        sub_state = {**state, "plan": json.dumps({"queries": [query], "target_domains": [], "data_schema": {}})}
        graph = build_research_graph()
        result = await graph.ainvoke(sub_state)
        return result.get("structured_items", [])

    semaphore = asyncio.Semaphore(max_parallel)

    async def _bounded(q):
        async with semaphore:
            return await _run_query(q)

    all_results_groups = await asyncio.gather(*[_bounded(q) for q in queries], return_exceptions=True)

    merged: list[dict] = []
    for group in all_results_groups:
        if isinstance(group, Exception):
            logger.error("Fan-out query failed: %s", group)
            continue
        merged.extend(group)

    return merged
```

**Acceptance:** `fan_out_research(plan, state)` runs multiple queries in parallel with bounded concurrency.

---

### Task 5-2: Add fan-out endpoint

**File:** `apps/api/src/inndxd_api/routers/briefs.py`
**Action:** Add a fan-out brief endpoint.

**Append:**
```python
@router.post("/fanout", response_model=BriefRead, status_code=status.HTTP_201_CREATED)
async def create_fanout_brief(
    body: BriefCreate,
    max_parallel: int = 3,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    brief = Brief(
        tenant_id=tenant_id,
        project_id=body.project_id,
        natural_language=body.natural_language,
        status="pending",
    )
    db.add(brief)
    await db.commit()
    await db.refresh(brief)

    briefs_created.inc()
    run_fanout_task.delay(
        str(brief.id), str(tenant_id), str(body.project_id),
        body.natural_language, max_parallel,
    )
    return brief
```

**Add fan-out task to `tasks.py`:**
```python
@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def run_fanout_task(
    self, brief_id_str: str, tenant_id_str: str, project_id_str: str,
    natural_language: str, max_parallel: int = 3,
):
    import asyncio
    # ... similar to run_research_task but uses fan_out_research
```

**Acceptance:** `POST /api/briefs/fanout` runs multiple agents in parallel.

---

### Task 5-3: Create recursive research node

**File:** `packages/inndxd-agents/src/inndxd_agents/nodes/recursive.py` (CREATE)

```python
"""Recursive research node — generate follow-up queries from results."""
from __future__ import annotations

import json
import logging

from inndxd_agents.state import ResearchState as AgentState

logger = logging.getLogger(__name__)

RECURSIVE_SYSTEM = (
    "You are a recursive research agent. Given a set of research results, "
    "identify gaps and generate 2-3 follow-up search queries that would fill "
    "those gaps. Output ONLY a JSON array of query strings."
)


async def recursive_node(state: AgentState, depth: int = 0, max_depth: int = 2) -> dict:
    if depth >= max_depth:
        return {}

    structured = state.get("structured_items", [])
    if len(structured) < 3:
        return {}

    from inndxd_agents.llm import create_ollama_client, resolve_model_for_node

    client = create_ollama_client()
    model = resolve_model_for_node("planner")

    response = await client.chat.completions.create(
        model=model,
        temperature=0.5,
        max_tokens=512,
        messages=[
            {"role": "system", "content": RECURSIVE_SYSTEM},
            {"role": "user", "content": json.dumps(structured, indent=2)},
        ],
    )

    content = response.choices[0].message.content or ""
    try:
        cleaned = content[content.find("[") : content.rfind("]") + 1] if "[" in content else "[]"
        follow_ups = json.loads(cleaned)
        logger.info("Generated %d recursive follow-up queries", len(follow_ups))
        return {"follow_up_queries": follow_ups}
    except (json.JSONDecodeError, ValueError):
        return {}
```

**Acceptance:** `recursive_node(state)` generates follow-up query strings.

---

### Task 5-4: Add recursive option to research graph

**File:** `packages/inndxd-agents/src/inndxd_agents/graph.py`
**Action:** Add an optional recursive edge from `structurer` back to `planner` if follow-up queries exist.

**Add:**
```python
from inndxd_agents.nodes.recursive import recursive_node

def should_recurse(state: ResearchState) -> str:
    follow_ups = state.get("follow_up_queries", [])
    depth = state.get("recursive_depth", 0)
    if follow_ups and depth < 3:
        return "planner"
    return END
```

**Register in `build_research_graph()` if recursive=True parameter added.**

**Acceptance:** Graph can auto-generate and execute follow-up research.

---

### Task 5-5: Create custom node plugin interface

**File:** `packages/inndxd-agents/src/inndxd_agents/plugins.py` (CREATE)

```python
"""Custom node plugin interface."""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any


class AgentNodePlugin(ABC):
    name: str = "base_plugin"

    @abstractmethod
    async def execute(self, state: dict) -> dict:
        ...


_plugin_registry: dict[str, type[AgentNodePlugin]] = {}


def register_plugin(name: str, plugin_cls: type[AgentNodePlugin]) -> None:
    _plugin_registry[name] = plugin_cls


def get_plugin(name: str) -> type[AgentNodePlugin] | None:
    return _plugin_registry.get(name)


def list_plugins() -> list[str]:
    return list(_plugin_registry.keys())
```

**Acceptance:** Third-party packages can register custom agent nodes via `register_plugin()`.

---

### Task 5-6: Add plugin execution to graph builder

**File:** `packages/inndxd-agents/src/inndxd_agents/graph.py`
**Action:** Allow dynamic plugin injection.

**Add:**
```python
def build_research_graph_with_plugins(plugins: list[str] | None = None):
    graph = StateGraph(ResearchState)
    graph.add_node("planner", planner_node)
    graph.add_node("plan_validator", plan_validator_node)
    graph.add_node("collector", collector_node)
    graph.add_node("structurer", structurer_node)

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "plan_validator")
    ...

    if plugins:
        from inndxd_agents.plugins import get_plugin
        for plugin_name in plugins:
            plugin_cls = get_plugin(plugin_name)
            if plugin_cls:
                plugin = plugin_cls()
                graph.add_node(plugin_name, plugin.execute)
                graph.add_edge("structurer", plugin_name)
                graph.add_edge(plugin_name, END)

    return graph.compile()
```

**Acceptance:** Custom plugins injected at runtime appear in the graph.

---

### Task 5-7: Create agent benchmark runner

**File:** `packages/inndxd-agents/src/inndxd_agents/benchmark.py` (CREATE)

```python
"""Agent performance benchmarking utility."""
from __future__ import annotations

import asyncio
import logging
import time
from uuid import uuid4

logger = logging.getLogger(__name__)


async def benchmark_research(
    natural_language: str,
    runs: int = 3,
) -> dict:
    from inndxd_agents.graph import build_research_graph

    graph = build_research_graph()
    durations: list[float] = []
    items_counts: list[int] = []

    for i in range(runs):
        state = {
            "brief_id": str(uuid4()),
            "tenant_id": str(uuid4()),
            "project_id": str(uuid4()),
            "natural_language": natural_language,
            "messages": [],
            "plan": None,
            "collected_data": [],
            "structured_items": [],
            "errors": [],
            "collector_retries": 0,
            "structurer_retries": 0,
            "planner_retries": 0,
        }
        start = time.perf_counter()
        result = await graph.ainvoke(state)
        duration = time.perf_counter() - start
        durations.append(duration)
        items_counts.append(len(result.get("structured_items", [])))
        logger.info("Benchmark run %d/%d: %.2fs, %d items", i + 1, runs, duration, items_counts[-1])

    return {
        "runs": runs,
        "avg_duration_seconds": sum(durations) / len(durations) if durations else 0,
        "min_duration_seconds": min(durations) if durations else 0,
        "max_duration_seconds": max(durations) if durations else 0,
        "avg_items": sum(items_counts) / len(items_counts) if items_counts else 0,
    }
```

**Acceptance:** `benchmark_research("Test query", runs=2)` returns timing stats.

---

### Task 5-8: Add benchmark endpoint (admin)

**File:** `apps/api/src/inndxd_api/routers/benchmark.py` (CREATE)

```python
"""Benchmark endpoint — admin only."""
from fastapi import APIRouter, Depends
from inndxd_api.dependencies import require_admin
from inndxd_agents.benchmark import benchmark_research

router = APIRouter()


@router.post("/")
async def run_benchmark(query: str, runs: int = 3, _: dict = Depends(require_admin)):
    result = await benchmark_research(query, runs=runs)
    return result
```

**Acceptance:** `POST /api/benchmark` with query body returns timing stats.

---

### Task 5-9: Register benchmark router in main.py

**File:** `apps/api/src/inndxd_api/main.py`
**Action:** Include benchmark router.

**Acceptance:** `POST /api/benchmark` is reachable.

---

### Task 5-10: Add graph upgrade tests

**File:** `packages/inndxd-agents/tests/test_graph_builds.py`
**Action:** Add tests for new graph capabilities.

**Append:**
```python
from inndxd_agents.fanout import fan_out_research


def test_graph_builds_with_approval():
    from inndxd_agents.graph import build_research_graph_with_approval

    graph = build_research_graph_with_approval()
    assert graph is not None
    assert hasattr(graph, "ainvoke")


def test_serialize_state():
    from inndxd_agents.graph import serialize_state

    state = {
        "brief_id": "test-id",
        "tenant_id": "tenant-id",
        "project_id": "project-id",
        "natural_language": "test",
        "plan": '{"queries": []}',
        "collected_data": [],
        "structured_items": [],
        "errors": [],
        "collector_retries": 0,
        "structurer_retries": 0,
        "planner_retries": 0,
    }
    serialized = serialize_state(state)
    assert serialized["brief_id"] == "test-id"
    assert isinstance(serialized, dict)


def test_plugin_registry():
    from inndxd_agents.plugins import list_plugins

    assert isinstance(list_plugins(), list)
```

**Acceptance:** All 3 new tests pass.

---

## Execution Order (Recommended)

| Batch | Tasks | Depends On |
|---|---|---|
| Batch A | 0-1 through 0-7 | — |
| Batch B | 1-1, 1-2, 1-3, 1-4 | Batch A |
| Batch C | 1-5, 1-6, 1-7, 1-12 | Batch B |
| Batch D | 1-8, 1-9, 1-10, 1-11 | Batch C |
| Batch E | 1-13, 1-14 | Batch B |
| Batch F | 2-1, 2-2, 2-3, 2-6 | Batch D |
| Batch G | 2-4, 2-5, 2-7, 2-8 | Batch F |
| Batch H | 2-9 through 2-17 | Batch G |
| Batch I | 3-1, 3-2, 3-3 | Batch D |
| Batch J | 3-4 through 3-8 | Batch I |
| Batch K | 4-1, 4-2, 4-3, 4-4 | Batch D |
| Batch L | 4-5 through 4-9 | Batch K |
| Batch M | 5-1, 5-3, 5-5, 5-7 | Batch H |
| Batch N | 5-2, 5-4, 5-6, 5-8, 5-9, 5-10 | Batch M |

---

## Total Estimates

| Phase | Tasks | Est. Hours |
|---|---|---|
| 0 — Cleanup | 7 | 4 |
| 1 — JWT Auth | 14 | 10 |
| 2 — Multi-Provider LLM | 17 | 12 |
| 3 — API Key Management | 8 | 5 |
| 4 — Observability | 9 | 6 |
| 5 — Agent Graph Upgrades | 10 | 8 |

**Total: 65 tasks, ~45 hours**
