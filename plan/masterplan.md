# Inndxd — Master Implementation Plan

> **Version: 3.0 — Updated after Stage 1, 2 & 3 completion **
> **Last updated: 2026-04-30

---

## Stage Completion Status

| Stage | Status | Lines of Code | Key Deliverables |
|---|---|---|---|
| **Stage 1** | ✅ Complete | ~1,100 | Core models, linear agent graph, FastAPI API, Docker infra, tenant isolation |
| **Stage 2** | ✅ Complete | ~2,800 | Enhanced graph, Celery workers, 5 tools, MCP server, pgvector, logging, Prometheus, export, WebSocket |
| **Stage 3** | ✅ Complete | ~2,400 | JWT auth, multi-provider LLM, API keys, OTel observability, fan-out/recursive/plugin graph upgrades |

---

## Current Architecture (Post Stage 2)

```
inndxd/
├── apps/
│   └── api/                              # FastAPI (v0.2.0)
│       ├── src/inndxd_api/
│       │   ├── main.py                   # App factory, all routers + /metrics
│       │   ├── config.py                 # Pydantic settings
│       │   ├── dependencies.py           # DB session + tenant RLS SET
│       │   ├── celery_app.py             # Celery + Redis + beat schedule
│       │   ├── tasks.py                  # run_research_task, cleanup_stuck_briefs
│       │   ├── metrics.py               # Prometheus counters + histogram
│       │   ├── routers/
│       │   │   ├── projects.py           # Full CRUD, tenant scoping
│       │   │   ├── briefs.py             # POST → Celery task + Prometheus
│       │   │   ├── data_items.py         # GET + export/json + export/csv
│       │   │   ├── runs.py               # GET + task-status (Celery state)
│       │   │   └── ws.py                 # WebSocket /ws/runs/{brief_id}
│       │   ├── schemas/                  # Pydantic request/response
│       │   └── middleware/
│       │       └── tenant.py             # TenantMiddleware + ContextVar
│       ├── tests/                        # pytest: projects, briefs, data_items, runs
│       └── Dockerfile
│
├── packages/
│   ├── inndxd-core/                      # Domain models + DB layer
│   │   └── src/inndxd_core/
│   │       ├── config.py                 # Database, Ollama, Redis, log level
│   │       ├── db.py                     # Async engine + session factory
│   │       ├── embedding.py              # Ollama nomic-embed-text
│   │       ├── logging_config.py         # JSON-structured logging
│   │       ├── models/                   # ORM: Project, Brief, DataItem (pgvector)
│   │       ├── domain/                   # Pydantic: Project, Brief, DataItem, LLMConfig
│   │       ├── repositories/             # Project, DataItem (semantic_search), Brief, Base
│   │       └── migrations/               # Alembic setup
│   │
│   ├── inndxd-agents/                    # LangGraph + 5 tools
│   │   └── src/inndxd_agents/
│   │       ├── config.py                 # Per-node model overrides
│   │       ├── graph.py                  # Conditional routing + approval variant
│   │       ├── llm.py                    # Multi-provider factory
│   │       ├── state.py                  # ResearchState + retry counters
│   │       ├── swarm.py                  # run_research_swarm() orchestrator
│   │       ├── nodes/                    # planner, collector, structurer, plan_validator, quality, human_approval
│   │       ├── tools/                    # web_search, twitter_search, api_fetch, browser, db_query + registry v2
│   │       └── prompts/                  # planner, collector, structurer templates
│   │
│   └── inndxd-mcp/                       # MCP server (v0.2.0)
│       └── src/inndxd_mcp/
│           ├── __init__.py
│           └── server.py                 # tools, resources, prompts, SSE transport
│
├── docker/
│   ├── postgres/init.sql                 # pgvector, UUID, RLS policies
│   └── ollama/entrypoint.sh             # Pull models on startup
│
├── docker-compose.yml                    # postgres, redis, ollama, api
├── pyproject.toml                        # Root workspace: 4 members
├── .env.example
├── .pre-commit-config.yaml
├── Justfile
├── plan/
│   ├── masterplan.md
│   └── stage2.md
└── README.md
```

---

## Package Dependency Graph

```
┌─────────────┐     ┌──────────────┐
│  inndxd-mcp │────▶│ inndxd-agents│
└──────┬──────┘     └──────┬───────┘
       │                   │
       ▼                   ▼
┌─────────────┐     ┌──────────────┐
│  inndxd-core│◀────│  apps/api    │
└─────────────┘     └──────────────┘
```

- `inndxd-core`: All DB models, domain types, repositories, config. No internal deps.
- `inndxd-agents`: LangGraph nodes, tools, LLM factory. Depends on `inndxd-core`.
- `apps/api`: FastAPI, Celery, Prometheus, WebSocket. Depends on `core` + `agents`.
- `inndxd-mcp`: MCP server exposing tools. Depends on `core` + `agents`.

---

## Tool Inventory

| Tool | File | Capabilities | Transport |
|---|---|---|---|
| `web_search_tool` | `tools/web_search.py` | web, search, general | Crawl4AI + DuckDuckGo |
| `twitter_search_tool` | `tools/twitter_search.py` | social, twitter, search | Crawl4AI + DuckDuckGo social |
| `api_fetch_tool` | `tools/api_fetch.py` | api, http, fetch | httpx |
| `browser_tool` | `tools/browser.py` | browser, web, scrape | Crawl4AI (table extraction) |
| `db_query_tool` | `tools/db_query.py` | database, internal, query | SQLAlchemy async |

All tools support `invoke_tool_with_timeout()` via registry v2.

---

## API Endpoints

| Method | Path | Phase | Description |
|---|---|---|---|
| `POST` | `/api/projects` | S1 | Create project |
| `GET` | `/api/projects` | S1 | List projects (tenant-scoped) |
| `GET` | `/api/projects/{id}` | S1 | Get project |
| `DELETE` | `/api/projects/{id}` | S1 | Delete project |
| `POST` | `/api/briefs` | S1 | Create brief → Celery task |
| `GET` | `/api/briefs` | S1 | List briefs |
| `GET` | `/api/data-items` | S1 | List data items |
| `GET` | `/api/data-items/{id}` | S1 | Get data item |
| `GET` | `/api/data-items/export/json` | S2 | Export as JSON |
| `GET` | `/api/data-items/export/csv` | S2 | Export as CSV |
| `GET` | `/api/runs/{brief_id}` | S1 | Run status |
| `GET` | `/api/runs/{brief_id}/task-status` | S2 | Celery task state |
| `GET` | `/metrics` | S2 | Prometheus metrics |
| `WS` | `/ws/runs/{brief_id}` | S2 | Agent progress streaming |

All endpoints require `X-Tenant-ID` header. RLS enforced via `SET app.current_tenant_id`.

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| uv workspaces | Native Python workspace support |
| `hatchling` build backend | `uv-core` unavailable in registry |
| `src/` layout | Clean separation from metadata |
| ResearchState extends MessagesState | Native LangGraph message accumulation |
| Conditional routing + retry limits | Prevents infinite loops |
| Celery + Redis | Production distributed task execution |
| Capability-based tool registry v2 | LLM-driven tool selection |
| JSON-structured logging | Machine-parseable observability |
| `@pytest.mark.db` skip marker | Local dev without Postgres |
| `SET app.current_tenant_id` | DB-level RLS per request |
| MCP dual transport (stdio + SSE) | Claude Desktop + web clients |
| Per-node model override env vars | Foundation for Stage 3 hot-swap |
