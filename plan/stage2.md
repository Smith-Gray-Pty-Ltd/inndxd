# Inndxd — Stage 2 Implementation Plan

> **Status:** All tasks are atomic — each modifies at most one file or creates one new file. Suitable for a small model to execute one task at a time.
> **Prerequisite:** Stage 1 codebase as currently exists.

---

## Git Workflow: Branching, Commit & Merge Strategy

> **Rule:** Before starting ANY task, always run `git status` to check if work is already in progress. Do NOT create a new branch if one already exists for the current phase.

### Branch naming

| Phase | Branch | Base |
|---|---|---|
| 0 | `stage2/phase0-fixes` | `main` |
| 1 | `stage2/phase1-graph` | `stage2/phase0-fixes` |
| 2 | `stage2/phase2-celery` | `stage2/phase1-graph` |
| 3 | `stage2/phase3-tools` | `stage2/phase2-celery` |
| 4 | `stage2/phase4-mcp` | `stage2/phase3-tools` |
| 5 | `stage2/phase5-production` | `stage2/phase4-mcp` |

### Per-task workflow (for EVERY task in this plan)

1. **Checkout the phase branch:** `git checkout <phase-branch>`
2. **Do the task** — edit/create exactly one file.
3. **Stage + commit immediately after each task:**
   ```bash
   git add <file-path>
   git commit -m "<phase>: <task-id> <brief-description>"
   ```
   Example: `git commit -m "phase0: 0-1 fix broken AgentState import in planner"`
4. **Do NOT amend commits.** Each task gets its own commit. This makes `git bisect`, reverts, and review trivial.
5. **Run lint/tests before committing.** If they fail, fix the issue in the same commit.

### Commit message format

```
<phase-slug>: <task-id> <imperative-verb> <what changed>
```

| Tag | Meaning |
|---|---|
| `phase0:` | Stage 1 fixes |
| `phase1:` | Enhanced agent graph |
| `phase2:` | Celery workers |
| `phase3:` | New tools |
| `phase4:` | MCP server |
| `phase5:` | Production hardening |

### Merge strategy

- **After ALL tasks in a phase are complete,** open a PR from `<phase-branch>` into its base.
- Each PR MUST pass: `ruff check`, `ruff format --check`, `mypy`, and `pytest`.
- Merge using **squash merge** (one clean commit per phase into the base branch).
- Delete the phase branch after merge.

### Resuming after interruption

Always start by checking:
```
git branch --show-current   # Am I on a phase branch already?
git log --oneline -5        # What was the last completed task?
```

Pick up from the next uncompleted task number in the current phase.

---

## Opencode Tool Reference

> **IMPORTANT:** Opencode has specific dedicated tools for file operations. Using Bash for file operations will fail or produce wrong results. Always use the correct tool below.

### File reading & searching (NEVER use `cat`, `head`, `tail`, `find`, `grep` in Bash)

| Action | Use this tool | Example |
|---|---|---|
| Read a file | **Read** | `Read(filePath="/absolute/path/to/file.py")` |
| Read a directory listing | **Read** | `Read(filePath="/absolute/path/to/dir")` |
| Search for files by pattern | **Glob** | `Glob(pattern="**/*.py")` |
| Search file contents by regex | **Grep** | `Grep(pattern="class AgentState")` |

### File writing & editing (NEVER use `echo >`, `cat <<EOF`, `sed`, `awk` in Bash)

| Action | Use this tool | When to use |
|---|---|---|
| Create a new file | **Write** | File does not exist yet |
| Edit specific lines in existing file | **Edit** | File exists, changing specific parts |
| Overwrite entire existing file | **Write** | File exists, replacing everything |

### Running commands (use Bash ONLY for these)

| Action | Command example |
|---|---|
| Git operations | `git status`, `git add`, `git commit`, `git checkout` |
| Package management | `uv sync`, `uv run pip install ...` |
| Running tests/lint | `uv run pytest`, `uv run ruff check .`, `uv run mypy .` |
| Docker operations | `docker compose up -d`, `docker compose down` |
| Process/tool invocation | `python -m inndxd_mcp.server --sse` |

### Common mistakes to avoid

- ❌ `bash: cat file.py` — use **Read** instead
- ❌ `bash: grep -r "pattern" .` — use **Grep** instead
- ❌ `bash: echo "content" > file.py` — use **Write** instead
- ❌ `bash: find . -name "*.py"` — use **Glob** instead
- ❌ Using Bash to `cd` somewhere — use the `workdir` parameter on the Bash tool instead
- ❌ Running git commands inside shell scripts with newlines — chain with `&&` or make separate calls

### Verifying your work (after EVERY task)

Run these in Bash before committing:
```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy .
uv run pytest
```

If any fail, edit the file to fix the issue, then re-run before committing.

---

## Table of Contents

1. [Execution Notes (Phase 0 Retrospective)](#execution-notes-phase-0-retrospective)
2. [Phase 0: Stage 1 Fixes & Completion](#phase-0-stage-1-fixes--completion) — 16 tasks
3. [Phase 0.5: Multi-Provider LLM Groundwork](#phase-05-multi-provider-llm-groundwork) — 8 tasks
4. [Phase 1: Enhanced Agent Graph](#phase-1-enhanced-agent-graph) — 13 tasks
5. [Phase 2: Celery Distributed Workers](#phase-2-celery-distributed-workers) — 10 tasks
6. [Phase 3: New Tools](#phase-3-new-tools) — 11 tasks
7. [Phase 4: MCP Server (Full Implementation)](#phase-4-mcp-server-full-implementation) — 6 tasks
8. [Phase 5: DB RLS, Observability & API Enhancements](#phase-5-db-rls-observability--api-enhancements) — 11 tasks

**Total: 75 tasks** | **Depends on: Stage 1 completion**

| Phase | Status |
|---|---|
| 0 — Stage 1 Fixes | ✅ Complete (18 commits, merged to main) |
| 0.5 — LLM Groundwork | ✅ Complete (7 commits, merged to main) |
| 1 — Enhanced Graph | ✅ Complete (11 commits, merged to main) |
| 2 — Celery Workers | ✅ Complete (1 commit, merged to main) |
| 3 — New Tools | ✅ Complete (8 commits, merged to main) |
| 4 — MCP Server | ⬜ Pending |
| 5 — Production | ⬜ Pending |

--- (Phase 0 Retrospective)

> Findings from the coding agent that executed Phase 0 (tasks 0-1 through 0-16). Apply these lessons to all remaining phases.

### Build system

| Plan assumed | Reality |
|---|---|
| `uv-core` build backend | Not available in any package registry — changed to `hatchling` |
| `[build-system] requires = ["uv-core"]` | All packages now use `requires = ["hatchling"]`, `build-backend = "hatchling.build"` |
| Default package discovery | `hatchling` needs explicit `[tool.hatch.build.targets.wheel] packages = ["src/packagename"]` in each `pyproject.toml` |

### Workspace resolution

| Plan assumed | Reality |
|---|---|
| Workspace members auto-resolve | Root `pyproject.toml` needs `[tool.uv.sources]` with `package-name = { workspace = true }` for each member |
| `uv` available in PATH | On macOS, `uv` installs to `~/.local/bin/uv` — prefix all commands with the full path |
| `dev-dependencies` | Deprecated warning — use `[dependency-groups.dev]` instead, but leaving as-is for now to avoid churn |

### Test environment

| Plan assumed | Reality |
|---|---|
| SQLite as test DB | SQLite doesn't support `JSONB`, `PGUUID`, or Postgres `Vector` types — tests use mocking |
| `JsonValue` from `pydantic_core` | Not available — domain models use plain `dict` types |
| DB pooling for tests | `db.py` now conditionally skips pooling when `database_url` starts with `sqlite` |
| 3 pre-existing tests fail | `test_create_brief_and_check_status`, `test_list_data_items_empty`, `test_create_and_list_projects` need a real Postgres instance — skip with `-k "not test_create"` in CI-less environments |

### Per-node model overrides

| Plan assumed | Reality |
|---|---|
| Task 0-10 adds `ollama_model` to agent config | Done — `inndxd_agents/config.py` has `ollama_model` field |
| Task 0.5-5 adds per-node overrides | These are *additional* fields (`planner_model`, `collector_model`, `structurer_model`) that default to `None` — when unset, fall back to `ollama_model` |

### Commit history tip

The Phase 0 agent accidentally committed two duplicate commits (38ba2ad and e4df30e both say "0-16"). This doesn't break anything but is messy. For Phase 0.5+: check `git log --oneline -3` before committing to avoid duplicates.

---

> **Note:** Stage 3 will build the full multi-provider LLM system (API endpoints for managing providers, DB-backed registry, per-tenant config, runtime hot-swapping). Phase 0.5 is structural prep only — zero behavior change.
3. [Phase 1: Enhanced Agent Graph](#phase-1-enhanced-agent-graph) — 13 tasks
4. [Phase 2: Celery Distributed Workers](#phase-2-celery-distributed-workers) — 10 tasks
5. [Phase 3: New Tools](#phase-3-new-tools) — 11 tasks
6. [Phase 4: MCP Server (Full Implementation)](#phase-4-mcp-server-full-implementation) — 6 tasks
7. [Phase 5: DB RLS, Observability & API Enhancements](#phase-5-db-rls-observability--api-enhancements) — 11 tasks

**Total: 75 tasks** | **Depends on: Stage 1 completion**

> **Note:** Phase 0.5 lays groundwork for **Stage 3** (multi-provider LLM system where users plug in any LLM provider — Anthropic, OpenAI, Ollama, Groq, etc. — and map different models to different agent nodes). Phase 0.5 itself is backward-compatible: no behavior changes, only structural refactoring that makes future provider-switching trivial.

---

## Phase 0: Stage 1 Fixes & Completion

> **Execution order:** Tasks 1–5 are critical bug fixes and must be done first. Tasks 6–16 are missing Stage 1 components that can be done in any order.

---

### Task 0-1: Fix broken AgentState import in planner node

**File:** `packages/inndxd-agents/src/inndxd_agents/nodes/planner.py`
**Action:** Replace the broken import.

**Current (broken):**
```python
from inndxd_agents.state import AgentState  # AgentState does not exist in state.py
```

**Replace with:**
```python
from inndxd_agents.state import ResearchState as AgentState
```

**Acceptance:** `from inndxd_agents.nodes.planner import planner_node` succeeds.

---

### Task 0-2: Fix broken AgentState import in collector node

**File:** `packages/inndxd-agents/src/inndxd_agents/nodes/collector.py`
**Action:** Replace the broken import.

**Current (broken):**
```python
from inndxd_agents.state import AgentState
```

**Replace with:**
```python
from inndxd_agents.state import ResearchState as AgentState
```

**Acceptance:** `from inndxd_agents.nodes.collector import collector_node` succeeds.

---

### Task 0-3: Fix broken AgentState import in structurer node

**File:** `packages/inndxd-agents/src/inndxd_agents/nodes/structurer.py`
**Action:** Replace the broken import.

**Current (broken):**
```python
from inndxd_agents.state import AgentState
```

**Replace with:**
```python
from inndxd_agents.state import ResearchState as AgentState
```

**Acceptance:** `from inndxd_agents.nodes.structurer import structurer_node` succeeds.

---

### Task 0-4: Remove stale agent_state.py duplicate in core domain

**File:** `packages/inndxd-core/src/inndxd_core/domain/agent_state.py`
**Action:** Delete this file. The authoritative state definition is `inndxd_agents/state.py` (ResearchState). Having two definitions causes confusion.

**Acceptance:** File no longer exists. No imports break (no other file imports from here).

---

### Task 0-5: Clean junk text in data_item.py model

**File:** `packages/inndxd-core/src/inndxd_core/models/data_item.py`
**Action:** Delete the stray line at the end of the file.

**Current line 31:**
```
models/init
```

**Replace with:** (delete the line entirely — file ends at line 30)

**Acceptance:** File ends cleanly after the `DataItem` class definition.

---

### Task 0-6: Add missing `__init__.py` to inndxd_core package root

**File:** `packages/inndxd-core/src/inndxd_core/__init__.py` (CREATE)
**Action:** Create an empty `__init__.py` so the package is a proper Python package.

**Acceptance:** `import inndxd_core` succeeds without errors.

---

### Task 0-7: Add missing `__init__.py` to core domain subpackage

**File:** `packages/inndxd-core/src/inndxd_core/domain/__init__.py` (CREATE)
**Action:** Create an `__init__.py` that re-exports the domain models for convenience.

**Content:**
```python
from inndxd_core.domain.project import ProjectCreate, ProjectRead
from inndxd_core.domain.brief import BriefCreate, BriefRead
from inndxd_core.domain.data_item import DataItemCreate, DataItemRead

__all__ = [
    "ProjectCreate",
    "ProjectRead",
    "BriefCreate",
    "BriefRead",
    "DataItemCreate",
    "DataItemRead",
]
```

**Acceptance:** `from inndxd_core.domain import ProjectCreate` succeeds.

---

### Task 0-8: Wire TenantMiddleware into the FastAPI app

**File:** `apps/api/src/inndxd_api/main.py`
**Action:** Add the middleware to `create_app()`.

**Add import at top:**
```python
from inndxd_api.middleware.tenant import TenantMiddleware
```

**Add middleware in `create_app()` after `app = FastAPI(...)`:**
```python
app.add_middleware(TenantMiddleware)
```

**Acceptance:** The middleware runs on every request. `X-Tenant-ID` header sets the context var.

---

### Task 0-9: Remove duplicate ContextVar from dependencies.py

**File:** `apps/api/src/inndxd_api/dependencies.py`
**Action:** The `current_tenant_id` ContextVar is now owned by `middleware/tenant.py`. Remove the duplicate and import it instead.

**Remove:**
```python
current_tenant_id: ContextVar[UUID | None] = ContextVar("tenant_id", default=None)
```

**Add import:**
```python
from inndxd_api.middleware.tenant import current_tenant_id
```

**Acceptance:** Only one `current_tenant_id` ContextVar exists in the codebase. `grep -r "current_tenant_id"` shows it defined only in `middleware/tenant.py`.

---

### Task 0-10: Add ollama_model field to agent settings

**File:** `packages/inndxd-agents/src/inndxd_agents/config.py`
**Action:** Add the missing model configuration field.

**Add to `AgentSettings` class:**
```python
ollama_model: str = "deepseek-r1:latest"
```

**Acceptance:** `from inndxd_agents.config import settings; print(settings.ollama_model)` outputs `deepseek-r1:latest`.

---

### Task 0-11: Make planner node read model from config

**File:** `packages/inndxd-agents/src/inndxd_agents/nodes/planner.py`
**Action:** Replace hardcoded `DEFAULT_MODEL` with config value.

**Remove:**
```python
DEFAULT_MODEL = "deepseek-r1:latest"
```

**Add import (after existing imports):**
```python
from inndxd_agents.config import settings
```

**In `planner_node()` function, change:**
```python
model=DEFAULT_MODEL,
```
**to:**
```python
model=settings.ollama_model,
```

**Acceptance:** Changing `INNDXD_OLLAMA_MODEL` env var changes which model the planner uses.

---

### Task 0-12: Make structurer node read model from config

**File:** `packages/inndxd-agents/src/inndxd_agents/nodes/structurer.py`
**Action:** Replace hardcoded `DEFAULT_MODEL` with config value.

**Remove:**
```python
DEFAULT_MODEL = "deepseek-r1:latest"
```

**Add import (after existing imports):**
```python
from inndxd_agents.config import settings
```

**In `structurer_node()` function, change:**
```python
model=DEFAULT_MODEL,
```
**to:**
```python
model=settings.ollama_model,
```

**Acceptance:** Changing `INNDXD_OLLAMA_MODEL` env var changes which model the structurer uses.

---

### Task 0-13: Add INNDXD_REDIS_URL to .env.example

**File:** `.env.example`
**Action:** Append the missing line at the end of the file.

**Append:**
```
INNDXD_REDIS_URL=redis://localhost:6379/0
```

**Acceptance:** File has 6 lines. Redis URL is present.

---

### Task 0-14: Set up Alembic properly

**Files to create (3 files):**

**1. `packages/inndxd-core/src/inndxd_core/migrations/env.py`**

```python
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from inndxd_core.config import settings
from inndxd_core.models.base import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
config.set_main_option("sqlalchemy.url", settings.database_url)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

**2. `packages/inndxd-core/src/inndxd_core/migrations/script.py.mako`**

```mako
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

**3. `packages/inndxd-core/src/inndxd_core/migrations/versions/.gitkeep`**

Create an empty `.gitkeep` file in `packages/inndxd-core/src/inndxd_core/migrations/versions/` so the directory exists in git.

**Acceptance:** Running `uv run alembic -c packages/inndxd-core/src/inndxd_core/migrations/alembic.ini revision --autogenerate -m "init"` creates a migration file in `versions/`.

---

### Task 0-15: Add .pre-commit-config.yaml

**File:** `.pre-commit-config.yaml` (CREATE at repo root)

**Content:**
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.13.0
    hooks:
      - id: mypy
        additional_dependencies:
          - pydantic>=2.10
          - sqlalchemy>=2.0
          - types-redis
```

**Acceptance:** `uv run pre-commit run --all-files` runs ruff and mypy.

---

### Task 0-16: Add missing tests for runs router, domain models, and graph integration

**Files to create (3 files):**

**1. `apps/api/tests/test_runs.py`**

```python
import pytest
from uuid import uuid4
from httpx import ASGITransport, AsyncClient
from inndxd_api.main import create_app


@pytest.mark.asyncio
async def test_get_run_status_not_found():
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/api/runs/00000000-0000-0000-0000-000000000001",
            headers={"X-Tenant-ID": "00000000-0000-0000-0000-000000000001"},
        )
        assert response.status_code == 404
```

**2. `packages/inndxd-core/tests/test_domain_models.py`**

```python
import pytest
from uuid import uuid4
from inndxd_core.domain.project import ProjectCreate
from inndxd_core.domain.brief import BriefCreate
from inndxd_core.domain.data_item import DataItemCreate


def test_project_create_valid():
    p = ProjectCreate(
        name="Test",
        description=None,
        tenant_id=uuid4(),
    )
    assert p.name == "Test"


def test_project_create_name_too_short():
    with pytest.raises(Exception):
        ProjectCreate(name="", tenant_id=uuid4())


def test_brief_create_requires_min_length():
    tid = uuid4()
    pid = uuid4()
    with pytest.raises(Exception):
        BriefCreate(
            project_id=pid,
            tenant_id=tid,
            natural_language="short",
        )


def test_data_item_create_valid():
    tid = uuid4()
    pid = uuid4()
    bid = uuid4()
    item = DataItemCreate(
        project_id=pid,
        tenant_id=tid,
        brief_id=bid,
        source_url="https://example.com",
        content_type="article",
        raw_payload={"text": "hello"},
        structured_payload={"title": "hello"},
    )
    assert item.content_type == "article"
```

**3. `packages/inndxd-agents/tests/test_graph_builds.py`**

```python
import pytest
from inndxd_agents.graph import build_research_graph


def test_graph_builds_without_error():
    graph = build_research_graph()
    assert graph is not None
    assert hasattr(graph, "ainvoke")
```

**Acceptance:** `uv run pytest` runs all 3 new test files and they pass.

---

## Phase 0.5: Multi-Provider LLM Groundwork

> **Prerequisites:** Phase 0 complete (all 16 tasks).
> **Goal:** Refactor the LLM client layer to be injectable per-node and support multiple provider configs. This enables **Stage 3** (full multi-provider LLM system) without changing any behavior today. All existing tests and API calls continue to work unchanged.

---

### Task 0.5-1: Create LLM provider config domain model

**File:** `packages/inndxd-core/src/inndxd_core/domain/llm_provider.py` (CREATE)

**Action:** Create a Pydantic model that represents an LLM provider configuration. This is the data contract that Stage 3 will build on.

**Content:**
```python
"""LLM provider configuration domain model."""
from __future__ import annotations

from pydantic import BaseModel, Field


class LLMProviderConfig(BaseModel):
    name: str = Field(description="Unique provider identifier, e.g. 'ollama', 'openai', 'anthropic'")
    base_url: str = Field(description="API base URL for OpenAI-compatible endpoint")
    api_key: str = Field(default="", description="API key for the provider")
    default_model: str = Field(description="Default model name, e.g. 'deepseek-r1:latest' or 'gpt-4o'")
    models: list[str] = Field(
        default_factory=list,
        description="List of available model names on this provider",
    )


class LLMConfig(BaseModel):
    default_provider: str = Field(
        default="ollama",
        description="Default provider name to use when none specified per-node",
    )
    providers: dict[str, LLMProviderConfig] = Field(
        default_factory=dict,
        description="Map of provider name to provider config",
    )
```

**Acceptance:** `from inndxd_core.domain.llm_provider import LLMProviderConfig, LLMConfig` succeeds. Models can be serialized to/from JSON.

---

### Task 0.5-2: Create default LLM config factory from env vars (backward-compatible)

**File:** `packages/inndxd-agents/src/inndxd_agents/llm.py`
**Action:** Rewrite LLM factory to read from the new `LLMConfig` model, falling back to existing env vars. No behavior change.

**New full content:**
```python
"""LLM client factory supporting multiple providers."""
from __future__ import annotations

from openai import AsyncOpenAI

from inndxd_agents.config import settings
from inndxd_core.domain.llm_provider import LLMConfig, LLMProviderConfig


def _build_default_llm_config() -> LLMConfig:
    return LLMConfig(
        default_provider="ollama",
        providers={
            "ollama": LLMProviderConfig(
                name="ollama",
                base_url=settings.ollama_base_url,
                api_key="ollama",
                default_model=settings.ollama_model,
                models=[settings.ollama_model],
            ),
        },
    )


_current_llm_config: LLMConfig | None = None


def get_llm_config() -> LLMConfig:
    global _current_llm_config
    if _current_llm_config is None:
        _current_llm_config = _build_default_llm_config()
    return _current_llm_config


def set_llm_config(config: LLMConfig) -> None:
    global _current_llm_config
    _current_llm_config = config


def create_ollama_client() -> AsyncOpenAI:
    return create_openai_compatible_client("ollama")


def create_openai_compatible_client(provider_name: str | None = None) -> AsyncOpenAI:
    config = get_llm_config()
    provider_name = provider_name or config.default_provider

    provider = config.providers.get(provider_name)
    if provider is None:
        if config.providers:
            provider = next(iter(config.providers.values()))
        else:
            raise ValueError(f"No LLM provider configured. Available: {list(config.providers.keys())}")

    return AsyncOpenAI(
        base_url=provider.base_url,
        api_key=provider.api_key or "no-key",
    )


def get_default_model(provider_name: str | None = None) -> str:
    config = get_llm_config()
    provider_name = provider_name or config.default_provider
    provider = config.providers.get(provider_name)
    if provider:
        return provider.default_model
    return settings.ollama_model
```

**Acceptance:** `create_ollama_client()` still works identically. `get_default_model()` returns the configured default model. `set_llm_config(LLMConfig(...))` lets a caller override the config at runtime.

---

### Task 0.5-3: Make planner node accept injectable LLM client

**File:** `packages/inndxd-agents/src/inndxd_agents/nodes/planner.py`
**Action:** Refactor so the LLM client and model can be passed as parameters instead of created fresh each time. Defaults remain backward-compatible.

**Replace `planner_node` function with:**
```python
from typing import Any


async def planner_node(
    state: AgentState,
    llm_client: Any = None,
    model: str | None = None,
) -> dict:
    if llm_client is None:
        llm_client = create_ollama_client()
    if model is None:
        model = get_default_model()

    user_prompt = PLANNER_USER.format(natural_language=state["natural_language"])

    response = await llm_client.chat.completions.create(
        model=model,
        temperature=0.3,
        max_tokens=2048,
        messages=[
            {"role": "system", "content": PLANNER_SYSTEM},
            {"role": "user", "content": user_prompt},
        ],
    )

    content = response.choices[0].message.content or ""

    plan: str | None = None
    errors: list[str] = []

    try:
        cleaned = _extract_json(content)
        parsed = json.loads(cleaned)
        if not isinstance(parsed, dict):
            raise ValueError(f"Expected JSON object, got {type(parsed).__name__}")
        plan = json.dumps(parsed)
        logger.info("Planner produced valid plan with %d queries", len(parsed.get("queries", [])))
    except (json.JSONDecodeError, ValueError) as e:
        error_msg = f"Planner failed to produce valid JSON: {e}"
        logger.error(error_msg)
        errors.append(error_msg)
        plan = json.dumps({"queries": [], "target_domains": [], "data_schema": {}})

    return {"plan": plan, "errors": errors, "planner_retries": state.get("planner_retries", 0) + 1}
```

**Add imports at top (merge with existing):**
```python
from inndxd_agents.llm import create_ollama_client, get_default_model
```

**Remove the old import of `from inndxd_agents.config import settings` (no longer needed) and the `DEFAULT_MODEL` constant (already removed in task 0-11).**

**Acceptance:** Calling `planner_node(state)` (no arguments) behaves identically to before. Calling `planner_node(state, llm_client=my_client, model="gpt-4")` uses the injected client/model.

---

### Task 0.5-4: Make structurer node accept injectable LLM client

**File:** `packages/inndxd-agents/src/inndxd_agents/nodes/structurer.py`
**Action:** Same refactoring pattern as planner node. LLM client and model become optional parameters with backward-compatible defaults.

**Replace `structurer_node` function with:**
```python
from typing import Any


async def structurer_node(
    state: AgentState,
    llm_client: Any = None,
    model: str | None = None,
) -> dict:
    plan_raw = state.get("plan")
    collected_data = state.get("collected_data", [])

    if not plan_raw or not collected_data:
        return {"structured_items": [], "errors": ["Missing plan or collected data"], "structurer_retries": state.get("structurer_retries", 0) + 1}

    try:
        plan = json.loads(plan_raw)
        data_schema = json.dumps(plan.get("data_schema", {}))
    except json.JSONDecodeError:
        return {"structured_items": [], "errors": ["Could not parse plan JSON"], "structurer_retries": state.get("structurer_retries", 0) + 1}

    if llm_client is None:
        llm_client = create_ollama_client()
    if model is None:
        model = get_default_model()

    user_prompt = STRUCTURER_USER.format(
        natural_language=state["natural_language"],
        data_schema=data_schema,
        collected_data=json.dumps(collected_data, indent=2),
    )

    response = await llm_client.chat.completions.create(
        model=model,
        temperature=0.2,
        max_tokens=4096,
        messages=[
            {"role": "system", "content": STRUCTURER_SYSTEM},
            {"role": "user", "content": user_prompt},
        ],
    )

    content = response.choices[0].message.content or ""
    structured_items: list[dict] = []
    errors: list[str] = []

    try:
        cleaned = _extract_json_array(content)
        parsed = json.loads(cleaned)
        if not isinstance(parsed, list):
            raise ValueError(f"Expected JSON array, got {type(parsed).__name__}")

        for item in parsed:
            item.setdefault("project_id", str(state["project_id"]))
            item.setdefault("tenant_id", str(state["tenant_id"]))
            item.setdefault("brief_id", str(state["brief_id"]))
            item.setdefault("source_url", item.get("source_url"))
            item.setdefault("content_type", item.get("content_type", "web_page"))
            item.setdefault("raw_payload", {})
            item.setdefault("structured_payload", item)

        structured_items = parsed
        logger.info("Structurer produced %d structured items", len(structured_items))
    except (json.JSONDecodeError, ValueError) as e:
        error_msg = f"Structurer failed to parse output: {e}"
        logger.error(error_msg)
        errors.append(error_msg)

    return {"structured_items": structured_items, "errors": errors, "structurer_retries": state.get("structurer_retries", 0) + 1}
```

**Add import after existing imports:**
```python
from inndxd_agents.llm import create_ollama_client, get_default_model
```

**Acceptance:** `structurer_node(state)` works identically. `structurer_node(state, llm_client=anthropic_client, model="claude-sonnet-4-20250514")` works with injected client.

---

### Task 0.5-5: Add per-node model mapping to agent config

**File:** `packages/inndxd-agents/src/inndxd_agents/config.py`
**Action:** Add optional per-node model overrides. If unset, falls back to `ollama_model` (current behavior).

**Add fields to `AgentSettings`:**
```python
planner_model: str | None = None
collector_model: str | None = None
structurer_model: str | None = None
```

**Full config after edit:**
```python
class AgentSettings(BaseSettings):
    model_config = {"env_prefix": "INNDXD_", "env_file": ".env"}

    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_model: str = "deepseek-r1:latest"
    planner_model: str | None = None
    collector_model: str | None = None
    structurer_model: str | None = None
```

**Acceptance:** `INNDXD_PLANNER_MODEL=gpt-4o` resolves to `"gpt-4o"` via pydantic-settings. If unset, `None`.

---

### Task 0.5-6: Create node model resolver utility

**File:** `packages/inndxd-agents/src/inndxd_agents/llm.py` (append to end)

**Action:** Add a utility that resolves which model a given node should use, respecting per-node overrides.

**Append:**
```python
def resolve_model_for_node(node_name: str) -> str:
    """Return the model name for a given agent node.

    Priority:
    1. Per-node env var (INNDXD_PLANNER_MODEL, etc.)
    2. Default ollama_model setting
    """
    from inndxd_agents.config import settings as agent_settings

    node_model_map = {
        "planner": agent_settings.planner_model,
        "collector": agent_settings.collector_model,
        "structurer": agent_settings.structurer_model,
    }
    overridden = node_model_map.get(node_name)
    if overridden:
        return overridden
    return get_default_model()
```

**Acceptance:** `resolve_model_for_node("planner")` returns `settings.planner_model` if set, otherwise `settings.ollama_model`.

---

### Task 0.5-7: Update planner and structurer nodes to use `resolve_model_for_node`

**Files to edit (2 files):**
- `packages/inndxd-agents/src/inndxd_agents/nodes/planner.py`
- `packages/inndxd-agents/src/inndxd_agents/nodes/structurer.py`

**Action:** In each node, replace the `model` default logic to call `resolve_model_for_node()`.

**In both `planner_node()` and `structurer_node()`, change:**
```python
if model is None:
    model = get_default_model()
```
**to:**
```python
if model is None:
    model = resolve_model_for_node("planner")  # or "structurer" respectively
```

**In planner.py, the line becomes:**
```python
model = resolve_model_for_node("planner")
```

**In structurer.py, the line becomes:**
```python
model = resolve_model_for_node("structurer")
```

**Add import in both files:**
```python
from inndxd_agents.llm import resolve_model_for_node
```

**Acceptance:** Setting `INNDXD_PLANNER_MODEL=llama3.3:70b` makes only the planner use Llama 3.3. The structurer continues using the default model unless `INNDXD_STRUCTURER_MODEL` is also set.

---

### Task 0.5-8: Document multi-provider roadmap in README

**File:** `README.md`
**Action:** Append a brief "Coming in Stage 3" note so users know multi-provider LLM is on the roadmap.

**Append:**
```markdown
## Roadmap

- **Stage 3 (Coming Soon):** Multi-Provider LLM Support — configure any OpenAI-compatible LLM provider (OpenAI, Anthropic, Groq, Ollama, DeepSeek API, etc.) and assign different models to each agent node. API endpoints for managing providers at runtime.
```

**Acceptance:** README mentions multi-provider LLM as a Stage 3 feature.

---

## Phase 1: Enhanced Agent Graph

> **Prerequisites:** Phase 0 complete (at minimum, task 0-1 through 0-5).
> **Goal:** Conditional routing, quality gates, retry logic, human-in-the-loop, serializable state.

---

### Task 1-1: Create quality gate evaluator helper

**File:** `packages/inndxd-agents/src/inndxd_agents/nodes/quality.py` (CREATE)

**Action:** Create a pure function that evaluates whether collected data meets a minimum bar.

**Content:**
```python
"""Quality gate evaluation for agent outputs."""
import json


def evaluate_collected_data(collected_data: list[dict]) -> bool:
    """Return True if collected data is sufficient to proceed."""
    if not collected_data:
        return False
    total_text_length = sum(len(item.get("text", "")) for item in collected_data)
    return total_text_length >= 500


def evaluate_structured_items(structured_items: list[dict]) -> bool:
    """Return True if structured output is non-empty and well formed."""
    if not structured_items:
        return False
    for item in structured_items:
        if not isinstance(item, dict):
            return False
        if "structured_payload" not in item:
            return False
    return True
```

**Acceptance:** `from inndxd_agents.nodes.quality import evaluate_collected_data` succeeds.

---

### Task 1-2: Create plan validator node

**File:** `packages/inndxd-agents/src/inndxd_agents/nodes/plan_validator.py` (CREATE)

**Action:** Create a node that validates the planner output before collection begins. Returns a dict with `plan_valid` boolean and optional `validation_errors`.

**Content:**
```python
"""Validates the planner output before collection proceeds."""
import json
import logging

from inndxd_agents.state import ResearchState as AgentState

logger = logging.getLogger(__name__)

REQUIRED_PLAN_KEYS = {"queries", "target_domains", "data_schema"}


async def plan_validator_node(state: AgentState) -> dict:
    plan_raw = state.get("plan")
    if not plan_raw:
        return {"errors": state.get("errors", []) + ["Plan is empty"]}

    try:
        plan = json.loads(plan_raw)
    except json.JSONDecodeError:
        return {"errors": state.get("errors", []) + ["Plan is not valid JSON"]}

    errors: list[str] = []
    for key in REQUIRED_PLAN_KEYS:
        if key not in plan:
            errors.append(f"Plan missing required key: {key}")

    if "queries" in plan and (not isinstance(plan["queries"], list) or len(plan["queries"]) == 0):
        errors.append("Plan has no search queries")

    if errors:
        logger.warning("Plan validation failed: %s", errors)
        return {"errors": state.get("errors", []) + errors}

    logger.info("Plan validated successfully with %d queries", len(plan["queries"]))
    return state
```

**Acceptance:** Returns state unmodified if plan is valid. Adds errors if plan is malformed.

---

### Task 1-3: Add routing helper functions to graph.py

**File:** `packages/inndxd-agents/src/inndxd_agents/graph.py`
**Action:** Rewrite the file to support conditional edges and quality gates.

**New full content:**
```python
"""Research graph builder with conditional routing and quality gates."""
from langgraph.graph import END, START, StateGraph

from inndxd_agents.nodes.collector import collector_node
from inndxd_agents.nodes.plan_validator import plan_validator_node
from inndxd_agents.nodes.planner import planner_node
from inndxd_agents.nodes.quality import evaluate_collected_data, evaluate_structured_items
from inndxd_agents.nodes.structurer import structurer_node
from inndxd_agents.state import ResearchState


def should_proceed_after_validation(state: ResearchState) -> str:
    errors = state.get("errors", [])
    has_plan = bool(state.get("plan"))
    if not has_plan or errors:
        return "planner"
    return "collector"


def should_proceed_after_collection(state: ResearchState) -> str:
    collected = state.get("collected_data", [])
    if not evaluate_collected_data(collected):
        return "collector"
    return "structurer"


def should_retry_structure(state: ResearchState) -> str:
    structured = state.get("structured_items", [])
    if not evaluate_structured_items(structured):
        return "structurer"
    return END


def build_research_graph():
    graph = StateGraph(ResearchState)

    graph.add_node("planner", planner_node)
    graph.add_node("plan_validator", plan_validator_node)
    graph.add_node("collector", collector_node)
    graph.add_node("structurer", structurer_node)

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "plan_validator")

    graph.add_conditional_edges(
        "plan_validator",
        should_proceed_after_validation,
        {
            "collector": "collector",
            "planner": "planner",
        },
    )

    graph.add_conditional_edges(
        "collector",
        should_proceed_after_collection,
        {
            "structurer": "structurer",
            "collector": "collector",
        },
    )

    graph.add_conditional_edges(
        "structurer",
        should_retry_structure,
        {
            "structurer": "structurer",
            END: END,
        },
    )

    return graph.compile()
```

**Acceptance:** Graph builds. Graph topology is: `START → planner → plan_validator → [collector or planner] → [structurer or collector] → [structurer or END]`.

---

### Task 1-4: Add max retry counter to state

**File:** `packages/inndxd-agents/src/inndxd_agents/state.py`
**Action:** Add retry counters to prevent infinite loops.

**Add new fields inside `ResearchState`:**
```python
collector_retries: int
structurer_retries: int
planner_retries: int
```

**Full state after edit:**
```python
import operator
from typing import Annotated

from langgraph.graph import MessagesState


class ResearchState(MessagesState):
    brief_id: str
    tenant_id: str
    project_id: str
    natural_language: str
    plan: str | None
    collected_data: Annotated[list, operator.add]
    structured_items: Annotated[list, operator.add]
    errors: Annotated[list[str], operator.add]
    collector_retries: int
    structurer_retries: int
    planner_retries: int
```

**Acceptance:** State TypedDict has the three new integer fields.

---

### Task 1-5: Update routing helpers to use retry counters

**File:** `packages/inndxd-agents/src/inndxd_agents/graph.py`
**Action:** Update the routing functions to respect retry limits.

**Replace the three routing functions with:**
```python
MAX_COLLECTOR_RETRIES = 3
MAX_STRUCTURER_RETRIES = 2
MAX_PLANNER_RETRIES = 2


def should_proceed_after_validation(state: ResearchState) -> str:
    errors = state.get("errors", [])
    has_plan = bool(state.get("plan"))
    retries = state.get("planner_retries", 0)
    if not has_plan or (errors and retries < MAX_PLANNER_RETRIES):
        return "planner"
    return "collector"


def should_proceed_after_collection(state: ResearchState) -> str:
    collected = state.get("collected_data", [])
    retries = state.get("collector_retries", 0)
    if not evaluate_collected_data(collected) and retries < MAX_COLLECTOR_RETRIES:
        return "collector"
    return "structurer"


def should_retry_structure(state: ResearchState) -> str:
    structured = state.get("structured_items", [])
    retries = state.get("structurer_retries", 0)
    if not evaluate_structured_items(structured) and retries < MAX_STRUCTURER_RETRIES:
        return "structurer"
    return END
```

**Acceptance:** Graph will not loop more than the max retry count for any phase.

---

### Task 1-6: Increment retry counters in nodes

**File:** `packages/inndxd-agents/src/inndxd_agents/nodes/planner.py`
**Action:** Increment `planner_retries` each time the node runs.

**In `planner_node`, add to the return dict:**
```python
"planner_retries": state.get("planner_retries", 0) + 1,
```

So the return statement becomes:
```python
return {"plan": plan, "errors": errors, "planner_retries": state.get("planner_retries", 0) + 1}
```

**Acceptance:** Each planner invocation increments the retry counter.

---

### Task 1-7: Increment retry counters in collector node

**File:** `packages/inndxd-agents/src/inndxd_agents/nodes/collector.py`
**Action:** Increment `collector_retries` each time the node runs.

**In `collector_node`, update return statements to include:**
```python
"collector_retries": state.get("collector_retries", 0) + 1,
```

**Change all three return statements:**
```python
# Return 1 (no plan):
return {"collected_data": [], "errors": ["No plan available for collection"], "collector_retries": state.get("collector_retries", 0) + 1}

# Return 2 (bad JSON):
return {"collected_data": [], "errors": ["Could not parse plan JSON"], "collector_retries": state.get("collector_retries", 0) + 1}

# Return 3 (no queries):
return {"collected_data": [], "errors": ["Plan contains no search queries"], "collector_retries": state.get("collector_retries", 0) + 1}

# Return 4 (success):
return {"collected_data": collected_data, "errors": errors, "collector_retries": state.get("collector_retries", 0) + 1}
```

**Acceptance:** Each collector invocation increments the retry counter.

---

### Task 1-8: Increment retry counters in structurer node

**File:** `packages/inndxd-agents/src/inndxd_agents/nodes/structurer.py`
**Action:** Increment `structurer_retries` each time the node runs.

**In `structurer_node`, update all return statements:**
```python
# Return 1 (missing plan/data):
return {"structured_items": [], "errors": ["Missing plan or collected data"], "structurer_retries": state.get("structurer_retries", 0) + 1}

# Return 2 (bad JSON):
return {"structured_items": [], "errors": ["Could not parse plan JSON"], "structurer_retries": state.get("structurer_retries", 0) + 1}

# Return 3 (success):
return {"structured_items": structured_items, "errors": errors, "structurer_retries": state.get("structurer_retries", 0) + 1}
```

**Acceptance:** Each structurer invocation increments the retry counter.

---

### Task 1-9: Update swarm to initialize retry counters

**File:** `packages/inndxd-agents/src/inndxd_agents/swarm.py`
**Action:** Add retry counter initial values to the state dict passed to `graph.ainvoke()`.

**In `run_research_swarm()`, add to the state dict:**
```python
"collector_retries": 0,
"structurer_retries": 0,
"planner_retries": 0,
```

So the state dict becomes:
```python
state = {
    "brief_id": str(brief_id),
    "tenant_id": str(tenant_id),
    "project_id": str(project_id),
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
```

**Acceptance:** `run_research_swarm()` passes state with retry counters set to 0.

---

### Task 1-10: Add human-in-the-loop node (stub)

**File:** `packages/inndxd-agents/src/inndxd_agents/nodes/human_approval.py` (CREATE)

**Action:** Create a node that returns state unmodified. This serves as a LangGraph interrupt point where an external system can pause execution.

**Content:**
```python
"""Human-in-the-loop approval node."""
import logging

from inndxd_agents.state import ResearchState as AgentState

logger = logging.getLogger(__name__)


async def human_approval_node(state: AgentState) -> dict:
    """Node that serves as an interrupt point for human review.
    
    When this node is reached, the graph raises a GraphInterrupt
    if compiled with interrupt_before=["human_approval"].
    """
    logger.info("Approval point reached for brief %s", state.get("brief_id"))
    logger.info("Plan: %s", state.get("plan"))
    logger.info("Collected %d items", len(state.get("collected_data", [])))
    return state
```

**Acceptance:** Node can be imported and added to the graph.

---

### Task 1-11: Update graph builder to optionally include human approval

**File:** `packages/inndxd-agents/src/inndxd_agents/graph.py`
**Action:** Add human approval as an optional interrupt point between collector and structurer.

**Add import:**
```python
from inndxd_agents.nodes.human_approval import human_approval_node
```

**Add a new function `build_research_graph_with_approval()`:**
```python
def build_research_graph_with_approval():
    graph = StateGraph(ResearchState)

    graph.add_node("planner", planner_node)
    graph.add_node("plan_validator", plan_validator_node)
    graph.add_node("collector", collector_node)
    graph.add_node("human_approval", human_approval_node)
    graph.add_node("structurer", structurer_node)

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "plan_validator")

    graph.add_conditional_edges(
        "plan_validator",
        should_proceed_after_validation,
        {"collector": "collector", "planner": "planner"},
    )

    graph.add_conditional_edges(
        "collector",
        should_proceed_after_collection,
        {"human_approval": "human_approval", "collector": "collector"},
    )

    graph.add_edge("human_approval", "structurer")

    graph.add_conditional_edges(
        "structurer",
        should_retry_structure,
        {"structurer": "structurer", END: END},
    )

    return graph.compile(interrupt_before=["human_approval"])
```

**Acceptance:** `build_research_graph_with_approval()` compiles a graph that pauses at the human approval node.

---

### Task 1-12: Add graph state serialization helper

**File:** `packages/inndxd-agents/src/inndxd_agents/graph.py` (append to end)

**Action:** Add a function to serialize graph state to a JSON-safe dict for checkpointing.

**Append to end of file:**
```python
def serialize_state(state: ResearchState) -> dict:
    """Convert graph state to a JSON-serializable dict for checkpointing."""
    return {
        "brief_id": state.get("brief_id"),
        "tenant_id": state.get("tenant_id"),
        "project_id": state.get("project_id"),
        "natural_language": state.get("natural_language"),
        "plan": state.get("plan"),
        "collected_data": state.get("collected_data", []),
        "structured_items": state.get("structured_items", []),
        "errors": state.get("errors", []),
        "collector_retries": state.get("collector_retries", 0),
        "structurer_retries": state.get("structurer_retries", 0),
        "planner_retries": state.get("planner_retries", 0),
    }
```

**Acceptance:** `serialize_state()` returns a plain dict with all state fields and no non-serializable objects.

---

### Task 1-13: Add inter-step logging to all nodes

**Files to edit (3 files):**
- `packages/inndxd-agents/src/inndxd_agents/nodes/planner.py`
- `packages/inndxd-agents/src/inndxd_agents/nodes/collector.py`
- `packages/inndxd-agents/src/inndxd_agents/nodes/structurer.py`

**Action:** Ensure each node logs:
- **Entry:** `logger.debug("Entering planner_node for brief %s", state.get("brief_id"))`
- **Exit success:** `logger.info("planner_node completed for brief %s", state.get("brief_id"))`
- **Exit failure:** Already present. Verify coverage.

For each file, add an entry log at the start of the node function and an exit log before each return statement (only where not already present).

**Acceptance:** Running with `INNDXD_LOG_LEVEL=DEBUG` shows entry/exit messages for all three nodes.

---

## Phase 2: Celery Distributed Workers

> **Prerequisites:** Phase 0 complete. Redis service is already in docker-compose.yml.
> **Goal:** Replace `BackgroundTasks` with Celery for distributed, reliable agent execution.

---

### Task 2-1: Add celery and redis-py to API dependencies

**File:** `apps/api/pyproject.toml`
**Action:** Add celery and redis packages.

**Add to dependencies list:**
```toml
"celery>=5.4,<6",
"redis>=5.2,<6",
```

**Acceptance:** `uv sync` installs celery and redis.

---

### Task 2-2: Create Celery app config

**File:** `apps/api/src/inndxd_api/celery_app.py` (CREATE)

**Action:** Create the Celery application instance with Redis broker.

**Content:**
```python
"""Celery app configuration for distributed task execution."""
from celery import Celery

from inndxd_core.config import settings

celery_app = Celery(
    "inndxd_tasks",
    broker=settings.redis_url if hasattr(settings, "redis_url") else "redis://localhost:6379/0",
    backend=settings.redis_url if hasattr(settings, "redis_url") else "redis://localhost:6379/0",
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)
```

**Acceptance:** `from inndxd_api.celery_app import celery_app` succeeds. App has Redis broker configured.

---

### Task 2-3: Add redis_url to core config

**File:** `packages/inndxd-core/src/inndxd_core/config.py`
**Action:** Add the missing `redis_url` field.

**Add to `Settings` class:**
```python
redis_url: str = "redis://localhost:6379/0"
```

**Acceptance:** `from inndxd_core.config import settings; print(settings.redis_url)` works.

---

### Task 2-4: Create research task definition

**File:** `apps/api/src/inndxd_api/tasks.py` (CREATE)

**Action:** Define the Celery task that runs the research swarm.

**Content:**
```python
"""Celery task definitions for inndxd research execution."""
import logging
from uuid import UUID

from inndxd_api.celery_app import celery_app
from inndxd_core.db import async_session_factory
from inndxd_core.models.brief import Brief

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def run_research_task(self, brief_id_str: str, tenant_id_str: str, project_id_str: str, natural_language: str):
    """Execute the research swarm as a Celery task."""
    import asyncio

    brief_id = UUID(brief_id_str)
    tenant_id = UUID(tenant_id_str)
    project_id = UUID(project_id_str)

    async def _run():
        try:
            from inndxd_agents.swarm import run_research_swarm
            result = await run_research_swarm(brief_id, tenant_id, project_id, natural_language)

            async with async_session_factory() as session:
                brief = await session.get(Brief, brief_id)
                if brief:
                    brief.status = "completed"
                    await session.commit()
        except Exception as exc:
            logger.error("Research task failed for brief %s: %s", brief_id, exc)
            async with async_session_factory() as session:
                brief = await session.get(Brief, brief_id)
                if brief:
                    brief.status = "failed"
                    await session.commit()
            raise self.retry(exc=exc)

    return asyncio.run(_run())
```

**Acceptance:** Task can be called with `run_research_task.delay(str(brief_id), str(tenant_id), str(project_id), natural_language)`.

---

### Task 2-5: Create Brief repository

**File:** `packages/inndxd-core/src/inndxd_core/repositories/briefs.py` (CREATE)

**Action:** Create a repository for Brief operations needed by Celery tasks.

**Content:**
```python
"""Brief repository for data access."""
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from inndxd_core.models.brief import Brief


class BriefRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, brief_id: UUID) -> Brief | None:
        return await self.session.get(Brief, brief_id)

    async def update_status(self, brief_id: UUID, status: str) -> None:
        stmt = (
            update(Brief)
            .where(Brief.id == brief_id)
            .values(status=status)
        )
        await self.session.execute(stmt)
        await self.session.commit()
```

**Acceptance:** `from inndxd_core.repositories.briefs import BriefRepository` succeeds.

---

### Task 2-6: Update briefs router to use Celery tasks

**File:** `apps/api/src/inndxd_api/routers/briefs.py`
**Action:** Replace `BackgroundTasks` with Celery task dispatch.

**Add import:**
```python
from inndxd_api.tasks import run_research_task
```

**Replace the `background_tasks.add_task(...)` call with:**
```python
run_research_task.delay(str(brief.id), str(tenant_id), str(body.project_id), body.natural_language)
```

**Remove `BackgroundTasks` from the router entirely:**
- Remove `BackgroundTasks` from imports
- Remove `background_tasks` parameter from `create_brief`

**Remove the local `_run_research_task()` and `_get_async_session()` functions** (lines 90–124) — they're no longer needed.

**Acceptance:** `POST /api/briefs` dispatches a Celery task instead of creating a background task. No import errors.

---

### Task 2-7: Add Celery worker to docker-compose.yml

**File:** `docker-compose.yml`
**Action:** Add a celery worker service.

**Add new service:**
```yaml
  celery_worker:
    build:
      context: .
      dockerfile: apps/api/Dockerfile
    command: ["uv", "run", "celery", "-A", "inndxd_api.celery_app", "worker", "--loglevel=info", "--concurrency=4"]
    environment:
      INNDXD_DATABASE_URL: postgresql+asyncpg://inndxd:inndxd@postgres:5432/inndxd
      INNDXD_OLLAMA_BASE_URL: http://ollama:11434/v1
      INNDXD_REDIS_URL: redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      ollama:
        condition: service_started
    volumes:
      - .:/app
```

**Acceptance:** `docker compose up celery_worker` starts a Celery worker.

---

### Task 2-8: Add task status/result API endpoint to runs router

**File:** `apps/api/src/inndxd_api/routers/runs.py`
**Action:** Enhance the runs router to query Celery task status.

**Read the current file first, then add:**
```python
from inndxd_api.tasks import run_research_task
from celery.result import AsyncResult
```

**Add a new endpoint:**
```python
@router.get("/{brief_id}/task-status")
async def get_task_status(brief_id: UUID):
    """Get Celery task status for a brief."""
    from inndxd_api.celery_app import celery_app
    result = AsyncResult(str(brief_id), app=celery_app)
    return {
        "brief_id": str(brief_id),
        "task_id": result.id,
        "status": result.status,
        "result": str(result.result) if result.ready() else None,
    }
```

**Acceptance:** `GET /api/runs/{brief_id}/task-status` returns Celery task state.

---

### Task 2-9: Add Celery beat schedule for periodic cleanup

**File:** `apps/api/src/inndxd_api/celery_app.py`
**Action:** Append a task cleanup beat schedule.

**Append to file:**
```python
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    "cleanup-stuck-tasks": {
        "task": "inndxd_api.tasks.cleanup_stuck_briefs",
        "schedule": crontab(minute="*/30"),
    },
}
celery_app.conf.timezone = "UTC"
```

**Acceptance:** Celery beat config is present on the app.

---

### Task 2-10: Create cleanup task for stuck briefs

**File:** `apps/api/src/inndxd_api/tasks.py` (append to end)

**Action:** Add a periodic cleanup task that marks long-running briefs as failed.

**Append:**
```python
@celery_app.task
def cleanup_stuck_briefs():
    """Mark briefs that have been 'running' for more than 1 hour as failed."""
    import asyncio
    from datetime import datetime, timedelta, timezone

    async def _cleanup():
        from sqlalchemy import update
        from inndxd_core.db import async_session_factory
        from inndxd_core.models.brief import Brief

        cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
        async with async_session_factory() as session:
            stmt = (
                update(Brief)
                .where(Brief.status == "running")
                .where(Brief.created_at < cutoff)
                .values(status="failed")
            )
            result = await session.execute(stmt)
            await session.commit()
            logger.info("Marked %d stuck briefs as failed", result.rowcount)

    asyncio.run(_cleanup())
```

**Acceptance:** Can be called directly and marks stale briefs as failed.

---

## Phase 3: New Tools

> **Prerequisites:** Phase 0 complete.
> **Goal:** Expand the tool ecosystem with 4 new tools + a capability-based registry v2.

---

### Task 3-1: Create Twitter/X search tool

**File:** `packages/inndxd-agents/src/inndxd_agents/tools/twitter_search.py` (CREATE)

**Action:** Create a tool that searches Twitter/X using a configurable API endpoint or DuckDuckGo social search fallback.

**Content:**
```python
"""Twitter/X search tool using DuckDuckGo social search."""
from __future__ import annotations

import asyncio
import re
from urllib.parse import quote_plus

import httpx
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from langchain_core.tools import tool
from pydantic import BaseModel, Field


class TwitterSearchInput(BaseModel):
    query: str = Field(description="Search query string for Twitter/X")
    max_results: int = Field(default=10, ge=1, le=30)


class TweetResult(BaseModel):
    url: str
    author: str | None
    text: str
    timestamp: str | None


@tool(args_schema=TwitterSearchInput)
async def twitter_search_tool(query: str, max_results: int = 10) -> list[TweetResult]:
    """Search Twitter/X for recent posts matching a query.

    Uses DuckDuckGo social search to find tweets.
    """
    encoded = quote_plus(f"{query} site:twitter.com OR site:x.com")
    search_url = f"https://html.duckduckgo.com/html/?q={encoded}"

    results: list[TweetResult] = []
    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig(
            word_count_threshold=100,
            excluded_tags=["nav", "footer", "script", "style"],
            remove_overlay_elements=True,
        )
        page = await crawler.arun(url=search_url, config=config)
        if page.success and page.markdown:
            links = re.findall(r'\[([^\]]*)\]\((https?://(?:twitter\.com|x\.com)/[^\s\)]+)\)', page.markdown)
            for title, url in links[:max_results]:
                results.append(TweetResult(
                    url=url,
                    author=None,
                    text=title[:500],
                    timestamp=None,
                ))
    return results
```

**Acceptance:** `from inndxd_agents.tools.twitter_search import twitter_search_tool` succeeds. Tool has `@tool` decorator and LangChain-compatible interface.

---

### Task 3-2: Create API fetch tool

**File:** `packages/inndxd-agents/src/inndxd_agents/tools/api_fetch.py` (CREATE)

**Action:** Create a tool that fetches data from arbitrary REST/GraphQL APIs.

**Content:**
```python
"""API fetch tool for REST and GraphQL endpoints."""
from __future__ import annotations

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field


class ApiFetchInput(BaseModel):
    url: str = Field(description="Full API endpoint URL")
    method: str = Field(default="GET", description="HTTP method: GET, POST, PUT, DELETE")
    headers: dict[str, str] | None = Field(default=None, description="HTTP headers")
    body: str | None = Field(default=None, description="Request body as JSON string")


class ApiFetchResult(BaseModel):
    url: str
    status_code: int
    response_text: str
    error: str | None = None


@tool(args_schema=ApiFetchInput)
async def api_fetch_tool(
    url: str,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    body: str | None = None,
) -> ApiFetchResult:
    """Fetch data from a REST or GraphQL API endpoint."""
    import json

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        try:
            response = await client.request(
                method=method.upper(),
                url=url,
                headers=headers or {},
                content=body,
            )
            return ApiFetchResult(
                url=url,
                status_code=response.status_code,
                response_text=response.text[:10000],
            )
        except Exception as e:
            return ApiFetchResult(
                url=url,
                status_code=0,
                response_text="",
                error=str(e),
            )
```

**Acceptance:** `from inndxd_agents.tools.api_fetch import api_fetch_tool` succeeds.

---

### Task 3-3: Create browser automation tool

**File:** `packages/inndxd-agents/src/inndxd_agents/tools/browser.py` (CREATE)

**Action:** Create a browser automation tool using Playwright or a stub that falls back to Crawl4AI.

**Content:**
```python
"""Browser automation tool using Crawl4AI."""
from __future__ import annotations

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from langchain_core.tools import tool
from pydantic import BaseModel, Field


class BrowserInput(BaseModel):
    url: str = Field(description="URL to load and extract content from")
    wait_for: str | None = Field(default=None, description="CSS selector to wait for before extraction")
    extract_tables: bool = Field(default=False, description="Whether to extract HTML tables")


class BrowserResult(BaseModel):
    url: str
    title: str | None
    markdown: str
    tables: list[dict] | None = None
    status_code: int


@tool(args_schema=BrowserInput)
async def browser_tool(
    url: str,
    wait_for: str | None = None,
    extract_tables: bool = False,
) -> BrowserResult:
    """Load a web page and extract its content, optionally extracting tables."""
    config = CrawlerRunConfig(
        word_count_threshold=100,
        excluded_tags=["nav", "footer", "script", "style"],
        remove_overlay_elements=True,
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, config=config)

    if not result.success:
        return BrowserResult(
            url=url,
            title=None,
            markdown="",
            status_code=result.status_code,
        )

    tables = None
    if extract_tables and result.markdown:
        tables = _extract_markdown_tables(result.markdown)

    return BrowserResult(
        url=url,
        title=result.metadata.get("title") if result.metadata else None,
        markdown=(result.markdown or "")[:10000],
        tables=tables,
        status_code=result.status_code,
    )


def _extract_markdown_tables(markdown: str) -> list[dict]:
    import re
    tables: list[dict] = []
    table_pattern = re.compile(r'\|[^\n]+\|\n\|[-| ]+\|\n((?:\|[^\n]+\|\n?)+)', re.MULTILINE)
    for match in table_pattern.finditer(markdown):
        tables.append({"raw": match.group(0)})
    return tables
```

**Acceptance:** `from inndxd_agents.tools.browser import browser_tool` succeeds.

---

### Task 3-4: Create database query tool

**File:** `packages/inndxd-agents/src/inndxd_agents/tools/db_query.py` (CREATE)

**Action:** Create a tool that queries the inndxd database for previously collected data.

**Content:**
```python
"""Database query tool for accessing previously collected data."""
from __future__ import annotations

import json
from uuid import UUID

from langchain_core.tools import tool
from pydantic import BaseModel, Field


class DbQueryInput(BaseModel):
    project_id: str = Field(description="Project UUID to query data for")
    query_type: str = Field(default="recent", description="Query type: 'recent', 'search', or 'stats'")
    limit: int = Field(default=20, ge=1, le=100)


class DbQueryResult(BaseModel):
    total: int
    items: list[dict]
    query_type: str


@tool(args_schema=DbQueryInput)
async def db_query_tool(project_id: str, query_type: str = "recent", limit: int = 20) -> DbQueryResult:
    """Query previously collected data items for a project."""
    from inndxd_core.db import async_session_factory
    from inndxd_core.models.data_item import DataItem
    from sqlalchemy import select, func

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
```

**Acceptance:** `from inndxd_agents.tools.db_query import db_query_tool` succeeds.

---

### Task 3-5: Create new tools `__init__.py` to re-export all tools

**File:** `packages/inndxd-agents/src/inndxd_agents/tools/__init__.py`
**Action:** Update to re-export all tools from a single place.

**Replace current content with:**
```python
from inndxd_agents.tools.web_search import web_search_tool
from inndxd_agents.tools.twitter_search import twitter_search_tool
from inndxd_agents.tools.api_fetch import api_fetch_tool
from inndxd_agents.tools.browser import browser_tool
from inndxd_agents.tools.db_query import db_query_tool

__all__ = [
    "web_search_tool",
    "twitter_search_tool",
    "api_fetch_tool",
    "browser_tool",
    "db_query_tool",
]
```

**Acceptance:** `from inndxd_agents.tools import web_search_tool, twitter_search_tool` works.

---

### Task 3-6: Create tool registry v2 with capability-based routing

**File:** `packages/inndxd-agents/src/inndxd_agents/tools/registry.py`
**Action:** Rewrite to support capability tags and tool selection by capability.

**Replace full content with:**
```python
"""Tool registry v2 with capability-based tool selection."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from inndxd_agents.tools import (
    api_fetch_tool,
    browser_tool,
    db_query_tool,
    twitter_search_tool,
    web_search_tool,
)


@dataclass
class ToolEntry:
    tool: Callable
    name: str
    capabilities: list[str] = field(default_factory=list)


TOOL_REGISTRY: list[ToolEntry] = [
    ToolEntry(
        tool=web_search_tool,
        name="web_search",
        capabilities=["web", "search", "general"],
    ),
    ToolEntry(
        tool=twitter_search_tool,
        name="twitter_search",
        capabilities=["social", "twitter", "search"],
    ),
    ToolEntry(
        tool=api_fetch_tool,
        name="api_fetch",
        capabilities=["api", "http", "fetch"],
    ),
    ToolEntry(
        tool=browser_tool,
        name="browser",
        capabilities=["browser", "web", "scrape"],
    ),
    ToolEntry(
        tool=db_query_tool,
        name="db_query",
        capabilities=["database", "internal", "query"],
    ),
]


def get_tools_by_capability(*capabilities: str) -> list[Callable]:
    """Return tools that have ALL of the requested capabilities."""
    result: list[Callable] = []
    for entry in TOOL_REGISTRY:
        if all(c in entry.capabilities for c in capabilities):
            result.append(entry.tool)
    return result


def get_tools_by_name(*names: str) -> list[Callable]:
    """Return tools by their registered names."""
    result: list[Callable] = []
    for entry in TOOL_REGISTRY:
        if entry.name in names:
            result.append(entry.tool)
    return result


def get_all_tools() -> list[Callable]:
    """Return all registered tools."""
    return [entry.tool for entry in TOOL_REGISTRY]
```

**Acceptance:** `get_tools_by_capability("search")` returns `[web_search_tool, twitter_search_tool]`. `get_all_tools()` returns 5 tools.

---

### Task 3-7: Update collector node to use tool registry

**File:** `packages/inndxd-agents/src/inndxd_agents/nodes/collector.py`
**Action:** Use the tool registry to select search tools dynamically based on plan targets.

**Add import:**
```python
from inndxd_agents.tools.registry import get_tools_by_capability
```

**In `_search_and_collect()`, replace the single `web_search_tool` call with a tool-agnostic approach:**
```python
async def _search_and_collect(query: str) -> list[dict]:
    search_tools = get_tools_by_capability("search", "web")
    if not search_tools:
        return []

    primary_tool = search_tools[0]
    try:
        results = await primary_tool.ainvoke({"query": query, "max_results": 5})
    except Exception:
        return []

    collected: list[dict] = []
    for r in results:
        collected.append({
            "url": r.url if hasattr(r, "url") else "",
            "title": r.title if hasattr(r, "title") else None,
            "text": r.text if hasattr(r, "text") else str(r),
        })
    return collected
```

**Acceptance:** Collector uses whatever search tools are registered, not just `web_search_tool`.

---

### Task 3-8: Add tools to agent graph as bound tools (optional LLM tool calling)

**File:** `packages/inndxd-agents/src/inndxd_agents/nodes/collector.py`
**Action:** No schema change — the collector already iterates the plan's queries. This task is a placeholder for future LLM-driven tool selection. Verify no changes needed.

**Acceptance:** Collector continues to work as before with the new tool registry.

---

### Task 3-9: Add crawl4ai cache configuration

**File:** `packages/inndxd-agents/src/inndxd_agents/tools/web_search.py`
**Action:** Replace `cache_mode="BYPASS"` with `cache_mode="ENABLED"` for better performance on repeated queries.

**Change:**
```python
cache_mode="BYPASS",
```
**to:**
```python
cache_mode="ENABLED",
```

**Acceptance:** Repeated queries use cached results.

---

### Task 3-10: Add tool timeout wrapper

**File:** `packages/inndxd-agents/src/inndxd_agents/tools/registry.py` (append to end)

**Action:** Add a utility that wraps any tool with a timeout.

**Append:**
```python
import asyncio


async def invoke_tool_with_timeout(tool: Callable, input_dict: dict, timeout_seconds: float = 30.0) -> dict:
    """Invoke a tool with a timeout. Returns error dict on timeout."""
    try:
        return await asyncio.wait_for(
            tool.ainvoke(input_dict),
            timeout=timeout_seconds,
        )
    except asyncio.TimeoutError:
        return {"error": f"Tool {tool.name} timed out after {timeout_seconds}s"}
```

**Acceptance:** `invoke_tool_with_timeout(web_search_tool, {"query": "test"}, 5.0)` works.

---

### Task 3-11: Add tool names to prompt templates for planner awareness

**File:** `packages/inndxd-agents/src/inndxd_agents/prompts/planner.py`
**Action:** Make the planner prompt aware of available tool capabilities.

**Add tools reference to `PLANNER_SYSTEM`:**
```python
AVAILABLE_TOOLS = """
- web_search: General web search via DuckDuckGo, returns extracted markdown from result pages.
- twitter_search: Social media search for tweets/posts on Twitter/X.
- api_fetch: Direct HTTP fetch from REST API endpoints (GET, POST, etc).
- browser: Full browser rendering and content extraction from specific URLs.
- db_query: Query previously collected internal data for this project.

When building your plan, specify which tool type each query requires using the "tool" field.
For example: {"queries": [{"query": "...", "tool": "web_search", "max_results": 5}], ...}
"""
```

**Insert `AVAILABLE_TOOLS` into `PLANNER_SYSTEM` before the closing instruction.**

**Acceptance:** Planner prompt mentions available tools.

---

## Phase 4: MCP Server (Full Implementation)

> **Prerequisites:** Phase 0 complete. Phase 3 tools must exist to expose via MCP.
> **Goal:** Full MCP protocol implementation — tools, resources, prompts, SSE transport.

---

### Task 4-1: Add MCP SDK dependency

**File:** `packages/inndxd-mcp/pyproject.toml`
**Action:** Add `mcp` SDK dependency.

**Replace `dependencies = []` with:**
```toml
dependencies = [
    "mcp>=1.0,<2",
    "inndxd-core",
    "inndxd-agents",
]
```

**Acceptance:** `uv sync` installs the MCP SDK.

---

### Task 4-2: Implement MCP server with tool exposure

**File:** `packages/inndxd-mcp/src/inndxd_mcp/server.py` (CREATE)

**Action:** Create the full MCP server that exposes all agent tools.

**Content:**
```python
"""MCP server exposing inndxd agent tools as MCP tools."""
from __future__ import annotations

import asyncio
import logging

from mcp.server import Server
from mcp.server.stdio import stdio_server

from inndxd_agents.tools.registry import get_all_tools, TOOL_REGISTRY

logger = logging.getLogger(__name__)

server = Server("inndxd-mcp")


async def main():
    """Run the MCP server via stdio transport."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


@server.list_tools()
async def list_tools() -> list[dict]:
    """List all available inndxd tools."""
    tools = []
    for entry in TOOL_REGISTRY:
        tools.append({
            "name": entry.name,
            "description": getattr(entry.tool, "description", f"inndxd {entry.name} tool"),
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "max_results": {"type": "integer", "description": "Max results", "default": 5},
                },
                "required": ["query"],
            },
        })
    return tools


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[dict]:
    """Execute a named inndxd tool."""
    from inndxd_agents.tools.registry import get_tools_by_name

    tools = get_tools_by_name(name)
    if not tools:
        return [{"error": f"Tool not found: {name}"}]

    tool = tools[0]
    try:
        result = await tool.ainvoke(arguments)
        if hasattr(result, "__iter__") and not isinstance(result, dict):
            text_parts = [
                str(r) if isinstance(r, str) else getattr(r, "text", str(r))
                for r in result
            ]
            return [{"type": "text", "text": "\n\n---\n\n".join(text_parts)}]
        return [{"type": "text", "text": str(result)}]
    except Exception as exc:
        return [{"type": "text", "text": f"Error: {exc}"}]
```

**Acceptance:** Running `python -m inndxd_mcp.server` starts the MCP server on stdio.

---

### Task 4-3: Add MCP resource exposure (projects, briefs, data_items)

**File:** `packages/inndxd-mcp/src/inndxd_mcp/server.py` (append to file)

**Action:** Add resource endpoints for browsing the database contents.

**Append to file:**
```python
@server.list_resources()
async def list_resources() -> list[dict]:
    """List available data resources."""
    return [
        {
            "uri": "inndxd://projects",
            "name": "Projects",
            "description": "All projects in the database",
        },
        {
            "uri": "inndxd://data-items/{project_id}",
            "name": "Data Items",
            "description": "Collected data items for a project",
            "mimeType": "application/json",
        },
    ]


@server.read_resource()
async def read_resource(uri: str) -> str:
    """Read data from a resource URI."""
    import json

    from inndxd_core.db import async_session_factory
    from inndxd_core.models.project import Project
    from inndxd_core.models.data_item import DataItem
    from sqlalchemy import select

    if uri == "inndxd://projects":
        async with async_session_factory() as session:
            result = await session.execute(select(Project).limit(50))
            rows = result.scalars().all()
            return json.dumps([
                {"id": str(r.id), "name": r.name, "description": r.description, "created_at": str(r.created_at)}
                for r in rows
            ])

    if uri.startswith("inndxd://data-items/"):
        project_id_str = uri.split("/")[-1]
        from uuid import UUID
        try:
            pid = UUID(project_id_str)
        except ValueError:
            return json.dumps({"error": "Invalid project ID"})
        async with async_session_factory() as session:
            result = await session.execute(
                select(DataItem).where(DataItem.project_id == pid).limit(100)
            )
            rows = result.scalars().all()
            return json.dumps([
                {"id": str(r.id), "source_url": r.source_url, "content_type": r.content_type,
                 "structured_payload": r.structured_payload, "created_at": str(r.created_at)}
                for r in rows
            ])

    return json.dumps({"error": f"Unknown resource: {uri}"})
```

**Acceptance:** MCP clients can list and read inndxd resources.

---

### Task 4-4: Add MCP prompts

**File:** `packages/inndxd-mcp/src/inndxd_mcp/server.py` (append to file)

**Action:** Add prompt templates for common inndxd workflows.

**Append to file:**
```python
@server.list_prompts()
async def list_prompts() -> list[dict]:
    """List available MCP prompts."""
    return [
        {
            "name": "research_brief",
            "description": "Generate a research brief for data collection",
            "arguments": [
                {"name": "topic", "description": "Research topic", "required": True},
                {"name": "depth", "description": "Research depth: shallow, medium, deep", "required": False},
            ],
        },
    ]


@server.get_prompt()
async def get_prompt(name: str, arguments: dict | None = None) -> dict:
    """Get a prompt by name with arguments."""
    if name == "research_brief":
        topic = (arguments or {}).get("topic", "general research")
        depth = (arguments or {}).get("depth", "medium")

        depth_instructions = {
            "shallow": "Perform a quick surface-level search with 3-5 results.",
            "medium": "Perform a thorough search across multiple sources with 10-15 results.",
            "deep": "Perform an exhaustive deep-dive across web, social media, and APIs with 20+ results.",
        }

        return {
            "messages": [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": (
                            f"Research topic: {topic}\n\n"
                            f"Depth: {depth}\n"
                            f"{depth_instructions.get(depth, depth_instructions['medium'])}\n\n"
                            f"Please structure the results with:\n"
                            f"- Source URLs\n"
                            f"- Key findings\n"
                            f"- Dates/timestamps\n"
                            f"- Confidence level (high/medium/low)"
                        ),
                    },
                }
            ],
        }

    return {"messages": [{"role": "user", "content": {"type": "text", "text": "Prompt not found."}}]}
```

**Acceptance:** MCP clients can list and retrieve inndxd prompts.

---

### Task 4-5: Add SSE transport option to MCP server

**File:** `packages/inndxd-mcp/src/inndxd_mcp/server.py` (append to file)

**Action:** Add an SSE transport entrypoint for web-based MCP clients.

**Append to file:**
```python
async def run_sse(port: int = 8001):
    """Run the MCP server with SSE transport on a given port."""
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.routing import Mount, Route
    import uvicorn

    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        async with sse.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await server.run(
                streams[0], streams[1], server.create_initialization_options()
            )

    starlette_app = Starlette(
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )

    config = uvicorn.Config(starlette_app, port=port, host="0.0.0.0", log_level="info")
    server_instance = uvicorn.Server(config)
    await server_instance.serve()
```

**Add to `if __name__ == "__main__"`:**
```python
if __name__ == "__main__":
    import sys
    if "--sse" in sys.argv:
        asyncio.run(run_sse())
    else:
        asyncio.run(main())
```

**Acceptance:** `python -m inndxd_mcp.server --sse` starts SSE transport on port 8001.

---

### Task 4-6: Add MCP server instructions file

**File:** `packages/inndxd-mcp/src/inndxd_mcp/__init__.py`
**Action:** Update the stub comment with version info re-export.

**Replace current content with:**
```python
"""Inndxd MCP Server — exposes agent tools and data as MCP resources."""
__version__ = "0.2.0"
```

**Acceptance:** `import inndxd_mcp; print(inndxd_mcp.__version__)` outputs `0.2.0`.

---

## Phase 5: DB RLS, Observability & API Enhancements

> **Prerequisites:** Phase 0, Phase 1, Phase 2 complete.
> **Goal:** Production readiness — pgvector search, RLS enforcement, structured logging, OpenTelemetry, Prometheus, export endpoints, WebSocket streaming.

---

### Task 5-1: Add pgvector embedding column to DataItem model

**File:** `packages/inndxd-core/src/inndxd_core/models/data_item.py`
**Action:** Add a vector column for embeddings.

**Add inside `DataItem` class, after existing columns:**
```python
embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)
```

**Add import for Vector:**
```python
from pgvector.sqlalchemy import Vector
```

**Acceptance:** DataItem table has an embedding column after Alembic migration.

---

### Task 5-2: Add semantic search to DataItemRepository

**File:** `packages/inndxd-core/src/inndxd_core/repositories/data_items.py`
**Action:** Add a method for vector similarity search.

**Add method to `DataItemRepository`:**
```python
async def semantic_search(
    self,
    query_embedding: list[float],
    limit: int = 10,
) -> list[DataItem]:
    """Find semantically similar data items using vector similarity."""
    from sqlalchemy import select

    stmt = (
        select(DataItem)
        .where(DataItem.embedding.is_not(None))
        .order_by(DataItem.embedding.cosine_distance(query_embedding))
        .limit(limit)
    )
    result = await self.session.execute(stmt)
    return list(result.scalars().all())
```

**Acceptance:** `repo.semantic_search([0.1, 0.2, ...])` returns similar items.

---

### Task 5-3: Add embedding generation utility

**File:** `packages/inndxd-core/src/inndxd_core/embedding.py` (CREATE)

**Action:** Create a utility to generate embeddings via Ollama.

**Content:**
```python
"""Embedding generation via Ollama API."""
from __future__ import annotations

import httpx


async def generate_embedding(text: str, base_url: str = "http://localhost:11434") -> list[float] | None:
    """Generate a vector embedding for a text string using Ollama."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{base_url}/api/embeddings",
                json={"model": "nomic-embed-text", "prompt": text},
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("embedding")
    except Exception:
        pass
    return None
```

**Acceptance:** `await generate_embedding("test text")` returns a 768-dimension embedding or None.

---

### Task 5-4: Enforce DB-level RLS via application SET

**File:** `apps/api/src/inndxd_api/dependencies.py`
**Action:** Add a DB session scoping that sets `app.current_tenant_id`.

**In `get_db()` function, add before `yield session`:**
```python
await session.execute(
    text("SELECT set_config('app.current_tenant_id', :tid, false)"),
    {"tid": str(current_tenant_id.get())},
)
```

**Add import:**
```python
from sqlalchemy import text
```

**Acceptance:** Every DB query in a request sets `app.current_tenant_id`. The RLS policies in `docker/postgres/init.sql` will then automatically filter rows.

---

### Task 5-5: Add structured logging config

**File:** `packages/inndxd-core/src/inndxd_core/logging_config.py` (CREATE)

**Action:** Create a centralized logging setup with JSON formatting.

**Content:**
```python
"""Centralized structured logging configuration."""
import logging
import json
import sys
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = str(record.exc_info[1])
        return json.dumps(log_entry, default=str)


def configure_logging(level: str = "INFO") -> None:
    """Set up structured JSON logging to stdout."""
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root.handlers.clear()
    root.addHandler(handler)
```

**Acceptance:** `configure_logging("DEBUG")` makes all logs JSON-formatted to stdout.

---

### Task 5-6: Wire structured logging into API startup

**File:** `apps/api/src/inndxd_api/main.py`
**Action:** Call `configure_logging()` at startup.

**Add import:**
```python
from inndxd_core.logging_config import configure_logging
```

**Add at top of `lifespan()` function (before table creation):**
```python
from inndxd_core.config import settings
configure_logging(settings.log_level)
```

**Acceptance:** API logs are JSON formatted.

---

### Task 5-7: Add Prometheus metrics endpoint

**File:** `apps/api/src/inndxd_api/metrics.py` (CREATE)

**Action:** Create a Prometheus metrics module.

**Content:**
```python
"""Prometheus metrics for the inndxd API."""
from prometheus_client import Counter, Histogram, generate_latest, REGISTRY
from fastapi import Response

briefs_created = Counter(
    "inndxd_briefs_created_total",
    "Total number of briefs created",
)

agent_run_duration = Histogram(
    "inndxd_agent_run_duration_seconds",
    "Duration of agent graph execution",
    buckets=[1, 5, 10, 30, 60, 120, 300, 600],
)

data_items_collected = Counter(
    "inndxd_data_items_collected_total",
    "Total number of data items collected",
)


def get_metrics() -> Response:
    return Response(
        content=generate_latest(REGISTRY),
        media_type="text/plain",
    )
```

**Add prometheus_client to API dependencies in `apps/api/pyproject.toml`.**

**Acceptance:** `GET /metrics` returns Prometheus-formatted metrics.

---

### Task 5-8: Add /metrics route to FastAPI app

**File:** `apps/api/src/inndxd_api/main.py`
**Action:** Add the metrics endpoint.

**Add import:**
```python
from inndxd_api.metrics import get_metrics
```

**In `create_app()`, add:**
```python
app.add_route("/metrics", get_metrics)
```

**Acceptance:** `GET /metrics` returns Prometheus text format.

---

### Task 5-9: Instrument brief creation with Prometheus

**File:** `apps/api/src/inndxd_api/routers/briefs.py`
**Action:** Increment the Prometheus counter on brief creation.

**In `create_brief()`, after brief creation, add:**
```python
from inndxd_api.metrics import briefs_created
briefs_created.inc()
```

**Acceptance:** Creating a brief increments the Prometheus counter.

---

### Task 5-10: Add export endpoints (CSV/JSON)

**File:** `apps/api/src/inndxd_api/routers/data_items.py`
**Action:** Add export endpoints that return data in CSV or JSON format.

**Read the current file first, then add:**

```python
@router.get("/export/json")
async def export_json(
    project_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Export all data items for a project as a JSON file."""
    from fastapi.responses import StreamingResponse
    import io, json

    stmt = select(DataItem).where(
        DataItem.project_id == project_id,
        DataItem.tenant_id == tenant_id,
    )
    result = await db.execute(stmt)
    items = result.scalars().all()

    data = [
        {
            "id": str(item.id),
            "source_url": item.source_url,
            "content_type": item.content_type,
            "structured_payload": item.structured_payload,
            "created_at": str(item.created_at),
        }
        for item in items
    ]

    return StreamingResponse(
        io.StringIO(json.dumps(data, indent=2)),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=project-{project_id}.json"},
    )


@router.get("/export/csv")
async def export_csv(
    project_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Export all data items for a project as CSV."""
    from fastapi.responses import StreamingResponse
    import io, csv

    stmt = select(DataItem).where(
        DataItem.project_id == project_id,
        DataItem.tenant_id == tenant_id,
    )
    result = await db.execute(stmt)
    items = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "source_url", "content_type", "structured_payload", "created_at"])

    for item in items:
        writer.writerow([
            str(item.id),
            item.source_url or "",
            item.content_type,
            item.structured_payload,
            str(item.created_at),
        ])

    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=project-{project_id}.csv"},
    )
```

**Required imports (add at top of file):**
```python
from sqlalchemy import select
from inndxd_core.models.data_item import DataItem
```

**Acceptance:** `GET /api/data-items/export/json?project_id=...` returns a JSON download. `GET /api/data-items/export/csv?project_id=...` returns a CSV download.

---

### Task 5-11: Add WebSocket endpoint for streaming agent progress

**File:** `apps/api/src/inndxd_api/routers/ws.py` (CREATE)

**Action:** Create a WebSocket endpoint that streams agent execution progress.

**Content:**
```python
"""WebSocket endpoint for streaming agent progress."""
from __future__ import annotations

import asyncio
import json
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


@router.websocket("/ws/runs/{brief_id}")
async def run_progress_websocket(websocket: WebSocket, brief_id: str):
    """Stream agent run progress over WebSocket."""
    await websocket.accept()

    try:
        bid = UUID(brief_id)
    except ValueError:
        await websocket.send_json({"type": "error", "message": "Invalid brief ID"})
        await websocket.close()
        return

    try:
        await websocket.send_json({"type": "connected", "brief_id": str(bid)})
        await websocket.send_json({"type": "status", "status": "connecting"})

        await asyncio.sleep(0.5)
        await websocket.send_json({"type": "status", "status": "planning"})

        await asyncio.sleep(0.5)
        await websocket.send_json({"type": "status", "status": "collecting"})

        await asyncio.sleep(0.5)
        await websocket.send_json({"type": "status", "status": "structuring"})

        await asyncio.sleep(0.5)
        await websocket.send_json({"type": "status", "status": "completed"})

        from inndxd_core.db import async_session_factory
        from inndxd_core.models.brief import Brief

        async with async_session_factory() as session:
            brief = await session.get(Brief, bid)
            if brief:
                await websocket.send_json({
                    "type": "result_summary",
                    "brief_id": str(brief.id),
                    "status": brief.status,
                })

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        await websocket.send_json({"type": "error", "message": str(exc)})
    finally:
        await websocket.close()
```

**Register in `main.py`:**
```python
# Add to create_app():
from inndxd_api.routers.ws import router as ws_router
app.include_router(ws_router, tags=["websocket"])
```

**Acceptance:** A WebSocket client connecting to `ws://localhost:8000/ws/runs/{brief_id}` receives progress messages.

---

## Execution Order (Recommended)

| Batch | Tasks | Parallel? |
|---|---|---|
| **Batch A** | 0-1, 0-2, 0-3, 0-5 | Yes — 4 files, independent |
| **Batch B** | 0-4, 0-6, 0-7, 0-13 | Yes — 3 creates + 1 delete + 1 edit |
| **Batch C** | 0-8, 0-9, 0-10, 0-11, 0-12 | Sequential — dependencies on each other |
| **Batch D** | 0-14, 0-15 | Yes — 2 independent setups |
| **Batch E** | 0-16 | Tests — run last to validate Phase 0 |
| **Batch F** | 1-1, 1-2, 1-7, 1-8, 1-9, 1-10, 1-12 | Yes — independent new files/edits |
| **Batch G** | 1-3, 1-4, 1-5, 1-6, 1-11, 1-13 | Sequential — graph refactor |
| **Batch H** | 2-1, 2-3, 2-5 | Yes — dependency additions |
| **Batch I** | 2-2, 2-4, 2-6, 2-7, 2-8, 2-9, 2-10 | Sequential — Celery wiring |
| **Batch J** | 3-1, 3-2, 3-3, 3-4 | Yes — 4 new tool files |
| **Batch K** | 3-5, 3-6, 3-7, 3-8, 3-9, 3-10, 3-11 | Sequential — registry + integration |
| **Batch L** | 4-1, 4-2, 4-3, 4-4, 4-5, 4-6 | Sequential — MCP server |
| **Batch M** | 5-1, 5-2, 5-3, 5-5, 5-7, 5-10, 5-11 | Yes — independent new components |
| **Batch N** | 5-4, 5-6, 5-8, 5-9 | Sequential — wiring |

**Total estimated effort:** ~45 hours for Stage 2 (67 tasks × ~40 min avg).

---

## Key Stage 2 Design Decisions

| Decision | Rationale |
|---|---|
| Conditional routing with retry limits (not infinite loops) | Agent graph can recover from bad plans or insufficient collection without hanging |
| Celery over BackgroundTasks | Production workloads need reliable distributed execution, retry semantics, and monitoring |
| Tool registry v2 with capabilities | Enables LLM to choose the right tool for a search target without hardcoding |
| MCP server via stdio + SSE | Dual transport supports both local AI tools (Claude Desktop) and web-based MCP clients |
| pgvector for semantic search | Enable "find similar" queries across accumulated data |
| Prometheus + JSON logging | Production observability without heavyweight agents |
| CSV/JSON export | Allow users to take data out of inndxd into their own tools |

---

## Appendix: Stage 2 Graph Topology (after Phase 1)

```
                        ┌──────────┐
                        │  START   │
                        └────┬─────┘
                             │
                        ┌────▼─────┐
                        │ planner  │◄──────────────┐
                        └────┬─────┘               │
                             │                     │ (if plan invalid + retries < max)
                        ┌────▼─────────┐           │
                        │plan_validator├───────────┘
                        └────┬─────────┘
                             │ (if plan valid)
                        ┌────▼─────┐
                        │ collector│◄──────────────┐
                        └────┬─────┘               │
                             │                     │ (if data insufficient + retries < max)
                        ┌────▼─────────┐           │
                    ┌───┤ quality_gate ├───────────┘
                    │   └──────────────┘
                    │ (if data sufficient)
               ┌────▼─────┐
               │structurer │◄──────────────┐
               └────┬─────┘               │
                    │                     │ (if output invalid + retries < max)
               ┌────▼─────────┐           │
               │  validate    ├───────────┘
               │  output      │
               └────┬─────────┘
                    │ (if output valid)
               ┌────▼─────┐
               │   END    │
               └──────────┘
```
