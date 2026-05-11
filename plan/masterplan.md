# Inndxd — Master Implementation Plan

> **Version:** 5.0 — Three-repo architecture, Stage 4 complete, Stage Cloud next
> **Last updated:** 2026-05-11

---

## Product Architecture

Inndxd is distributed across three repositories, two domains, and three deployment models:

| Domain | Purpose | Repo |
|---|---|---|
| `inndxd.ai` | The product — agents research, collect, structure, deliver data | `inndxd` (open-source) |
| `inndxd.com` | The business — signup, billing, admin, marketing | `inndxd-cloud` (proprietary) |

---

### Repo 1: `inndxd` (open-source, AGPL)

The core product. `git clone` + `docker compose up` = fully running.

```
inndxd/
├── packages/
│   ├── inndxd-core/              # DB models, domain, config, JWT, repos
│   ├── inndxd-agents/            # LangGraph swarm, 5 tools, LLM factory
│   └── inndxd-mcp/               # MCP server (stdio + SSE)
├── apps/
│   ├── api/                      # REST API — JSON, /metrics, WebSocket (port 8000)
│   └── web/                      # Dashboard UI — Jinja2 + Tailwind + HTMX (port 8080)
├── docker-compose.yml            # postgres, redis, ollama, api, web
└── README.md
```

**Deployment models:**
- Self-hosted: customer's own infrastructure
- Cloud shared (SaaS): `app.inndxd.ai` — we host it
- Managed VPS: `clientname.inndxd.ai` — dedicated instance
- Enterprise gov cloud: `inndxd.agency.gov.au` — deployed into customer's tenancy

---

### Repo 2: `inndxd-enterprise` (proprietary)

Gov/enterprise deployment artifacts. Never touches our infrastructure.

```
inndxd-enterprise/
├── infra/
│   ├── aws-govcloud/             # Terraform + k8s for IRAP/ISO deployments
│   ├── azure-government/         # Azure Government landing zone
│   └── gcp-assured/              # GCP Assured Workloads
├── compliance/
│   ├── iso27001/                 # Policy templates, evidence collection scripts
│   ├── irap/                     # Australian gov ISM control mappings
│   └── soc2/                     # Monitoring + alerting configs
└── apps/
    └── identity-providers/       # LDAP, SAML, Okta, Azure AD connectors
```

---

### Repo 3: `inndxd-cloud` (proprietary)

Runs the business at `inndxd.com`.

```
inndxd-cloud/
├── apps/
│   ├── website/                  # Marketing, docs, pricing, blog
│   ├── identity/                 # Signup: email, Google, GitHub OAuth
│   ├── billing/                  # Stripe: subscriptions, invoices, plan tiers
│   ├── admin/                    # Manage customers, VPS instances, cloud costs
│   └── gateway/                  # Routes traffic to customer instances on *.inndxd.ai
└── .github/workflows/            # CI/CD for customer provisioning
```

---

### How the three repos connect

```
┌─────────────────────────────────────────────────────────────┐
│                     inndxd.com (SaaS)                        │
│                                                              │
│  website/ ──► signup ──► identity/ ──► billing/             │
│                           │                                  │
│                           ▼                                  │
│                      admin/ ──► provisions ──► gateway/     │
│                                                      │      │
└──────────────────────────────────────────────────────┼──────┘
                                                       │
                              routes traffic to ───────┤
                                                       │
           ┌───────────────────────────────────────────┼──────┐
           │               inndxd.ai (product)         │      │
           │                                           ▼      │
           │  app.inndxd.ai  ──► api/ + web/ (shared)         │
           │  client.inndxd.ai  ──► api/ + web/ (VPS)         │
           │  inndxd.agency.gov.au ──► api/ + web/ (gov)      │
           │                                                  │
           └──────────────────────────────────────────────────┘
```

No code duplication. `inndxd-cloud` provisions and routes to `inndxd` instances. `inndxd-enterprise` deploys `inndxd` into customer tenancies via Terraform.

---

## Stage Completion Status

| Stage | Status | Lines of Code | Key Deliverables |
|---|---|---|---|
| **Stage 1** | ✅ Complete | ~1,100 | Core models, linear agent graph, FastAPI API, Docker infra, tenant isolation |
| **Stage 2** | ✅ Complete | ~2,800 | Enhanced graph, Celery workers, 5 tools, MCP server, pgvector, logging, Prometheus, export, WebSocket |
| **Stage 3** | ✅ Complete | ~2,400 | JWT auth, multi-provider LLM, API keys, OTel observability, fan-out/recursive/plugin graph upgrades |
| **Stage 4** | ✅ Complete | ~3,500 | Web dashboard: DaisyUI + HTMX, 7 routers, 24 templates, AI chat, design catalog, admin panels |
| **Stage Cloud** | 🔄 Next | — | Business ops: website, identity, billing, admin, gateway → `inndxd-cloud` repo |

---

## Current Architecture (Post Stage 4)

```
inndxd/
├── apps/
│   └── api/                              # FastAPI (v0.3.0)
│       ├── src/inndxd_api/
│       │   ├── main.py                   # App factory: 9 API routers + /metrics
│       │   ├── config.py                 # Re-export stub → inndxd_core.config
│       │   ├── dependencies.py           # DB session + tenant RLS SET
│       │   ├── celery_app.py             # Celery + Redis + beat schedule
│       │   ├── tasks.py                  # run_research_task, cleanup_stuck_briefs
│       │   ├── metrics.py               # Prometheus counters + histograms
│       │   ├── provider_health.py        # LLM provider /models health check
│       │   ├── provider_sync.py          # DB → runtime LLMConfig sync
│       │   ├── auth_deps.py              # get_current_user, require_admin
│       │   ├── tracing.py                # OpenTelemetry + FastAPI instrumentor
│       │   ├── routers/
│       │   │   ├── auth.py               # POST register, login
│       │   │   ├── api_keys.py           # CRUD + rotate API keys
│       │   │   ├── projects.py           # Full CRUD, tenant scoping
│       │   │   ├── briefs.py             # POST → Celery task + Prometheus
│       │   │   ├── data_items.py         # GET + export/json + export/csv
│       │   │   ├── runs.py               # GET + task-status (Celery state)
│       │   │   ├── llm_providers.py      # Provider CRUD, health, node assignments, sync
│       │   │   ├── audit_logs.py         # Admin-only audit log viewer
│       │   │   ├── benchmark.py          # Admin-only agent benchmark
│       │   │   └── ws.py                 # WebSocket /ws/runs/{brief_id}
│       │   ├── schemas/                  # Pydantic request/response
│       │   └── middleware/
│       │       └── tenant.py             # TenantMiddleware + ContextVar
│       ├── tests/                        # pytest: projects, briefs, data_items, runs
│       └── Dockerfile
│
│   └── web/                              # Dashboard UI (v0.4.0)
│       ├── src/inndxd_web/
│       │   ├── main.py                 # App factory, 7 routers, dev-mode design catalog
│       │   ├── auth.py                 # JWT httpOnly cookie session
│       │   └── routers/
│       │       ├── ui.py               # Dashboard home (live DB stats)
│       │       ├── ui_auth.py          # Login, register, logout
│       │       ├── ui_projects.py      # Project CRUD + setup chat
│       │       ├── ui_briefs.py        # Brief lifecycle + chat + refine/version
│       │       ├── ui_chat.py          # SSE streaming chat agent
│       │       ├── ui_data_items.py    # Sortable/filterable data table + export
│       │       ├── ui_admin.py         # LLM providers, API keys, audit logs
│       │       └── _design.py          # DaisyUI design catalog (dev mode)
│       ├── templates/                    # 24 Jinja2 templates
│       │   ├── base.html               # DaisyUI drawer layout, collapsible sidebar
│       │   ├── auth/                   # login, register
│       │   ├── dashboard/              # Stats cards, quick actions
│       │   ├── projects/               # list, create, edit, detail, setup_chat
│       │   ├── briefs/                 # list, create, detail, chat
│       │   ├── data_items/             # Sortable table
│       │   ├── admin/                  # providers, api_keys, audit_logs
│       │   ├── design/                 # Component catalog
│       │   └── partials/               # 12 reusable HTMX partials
│       ├── static/css/
│       │   ├── input.css               # Tailwind directives
│       │   └── bundle.css              # Tailwind v4 + DaisyUI v5 compiled
│       └── tests/
│
├── packages/
│   ├── inndxd-core/                      # Domain models + DB layer
│   │   └── src/inndxd_core/
│   │       ├── config.py                 # DB, Ollama, Redis, log level, JWT
│   │       ├── db.py                     # Async engine + session factory
│   │       ├── embedding.py              # Ollama nomic-embed-text
│   │       ├── logging_config.py         # JSON-structured logging
│   │       ├── auth.py                   # hash_password, verify_password, JWT encode/decode
│   │       ├── models/                   # ORM: Project, Brief, DataItem, User, LLMProvider, APIKey, AuditLog
│   │       ├── domain/                   # Pydantic: all schemas + LLMConfig/LLMProviderConfig
│   │       ├── repositories/             # Project, DataItem, Brief, User, LLMProvider, APIKey, AuditLog, Base
│   │       └── migrations/               # Alembic setup
│   │
│   ├── inndxd-agents/                    # LangGraph + 5 tools
│   │   └── src/inndxd_agents/
│   │       ├── config.py                 # Per-node model overrides
│   │       ├── graph.py                  # Build graph, conditions, serialization
│   │       ├── llm.py                    # Multi-provider factory + failover
│   │       ├── state.py                  # ResearchState + retry counters
│   │       ├── swarm.py                  # run_research_swarm() orchestrator
│   │       ├── fanout.py                 # Parallel sub-graph execution with Semaphore
│   │       ├── benchmark.py              # Multi-run performance benchmark
│   │       ├── plugins.py                # AgentNodePlugin ABC + global registry
│   │       ├── nodes/
│   │       │   ├── planner.py            # Query plan generation
│   │       │   ├── collector.py          # Tool execution with retry
│   │       │   ├── structurer.py         # Data extraction + schema mapping
│   │       │   ├── plan_validator.py     # Plan quality check
│   │       │   ├── quality.py            # Output sufficiency evaluator
│   │       │   ├── human_approval.py     # Interrupt for manual review
│   │       │   └── recursive.py          # LLM-driven follow-up query generation
│   │       ├── tools/
│   │       │   ├── web_search.py         # Crawl4AI + DuckDuckGo
│   │       │   ├── twitter_search.py     # Social media discovery
│   │       │   ├── api_fetch.py          # REST/GraphQL fetcher
│   │       │   ├── browser.py            # Crawl4AI table extraction
│   │       │   └── db_query.py           # Internal SQLAlchemy query
│   │       └── prompts/                  # Planner, collector, structurer system prompts
│   │
│   └── inndxd-mcp/                       # MCP server (v0.2.0)
│       └── src/inndxd_mcp/
│           ├── __init__.py
│           └── server.py                 # Tools, resources, prompts, stdio + SSE
│
├── docker/
│   ├── postgres/init.sql                 # pgvector, UUID, RLS policies
│   └── ollama/entrypoint.sh              # Pull models on startup
│
├── docker-compose.yml                    # postgres, redis, ollama, api
├── pyproject.toml                        # Root workspace: 4 members
├── .env.example
├── plan/
│   └── masterplan.md
├── .env.example
└── README.md
```

> **Stage plans (stage2–4, stage-cloud):** [inndxd-project](https://github.com/Smith-Gray-Pty-Ltd/inndxd-project) — private planning repo.

---

## Package Dependency Graph

```
                    ┌──────────────┐
                    │  inndxd-mcp  │
                    └──────┬───────┘
                           │
                           ▼
┌──────────────┐    ┌──────────────┐
│ inndxd-core  │◀───│inndxd-agents │
└──────┬───────┘    └──────────────┘
       │                     │
       ▼                     ▼
┌──────────────┐
│  apps/api    │
└──────────────┘
```

- `inndxd-core`: All DB models, domain types, repositories, config, JWT auth. No internal deps.
- `inndxd-agents`: LangGraph nodes, tools, LLM factory, fan-out, recursive, plugins. Depends on `inndxd-core`.
- `apps/api`: REST API, Celery, Prometheus, WebSocket, OTel. Depends on `core` + `agents`.
- `inndxd-mcp`: MCP server exposing tools. Depends on `core` + `agents`.
- `apps/web`: Dashboard UI — DaisyUI + HTMX, 7 routers, 24 templates, AI chat, design catalog. Depends on `core`. Separate process on port 8080.

---

## Tool Inventory

| Tool | Capabilities | Transport |
|---|---|---|
| `web_search_tool` | web, search, general | Crawl4AI + DuckDuckGo |
| `twitter_search_tool` | social, twitter, search | Crawl4AI + DuckDuckGo social |
| `api_fetch_tool` | api, http, fetch | httpx |
| `browser_tool` | browser, web, scrape | Crawl4AI (table extraction) |
| `db_query_tool` | database, internal, query | SQLAlchemy async |

All support `invoke_tool_with_timeout()`. Capability-based routing via registry v2.

---

## API Endpoints

| Method | Path | Stage | Description |
|---|---|---|---|
| `POST` | `/api/auth/register` | S3 | Register user |
| `POST` | `/api/auth/login` | S3 | Login → JWT |
| `POST` | `/api/projects` | S1 | Create project |
| `GET` | `/api/projects` | S1 | List projects |
| `GET` | `/api/projects/{id}` | S1 | Get project |
| `DELETE` | `/api/projects/{id}` | S1 | Delete project |
| `POST` | `/api/briefs` | S1 | Create brief → Celery task |
| `GET` | `/api/briefs` | S1 | List briefs |
| `GET` | `/api/data-items` | S1 | List data items |
| `GET` | `/api/data-items/{id}` | S1 | Get data item |
| `GET` | `/api/data-items/export/json` | S2 | Export JSON |
| `GET` | `/api/data-items/export/csv` | S2 | Export CSV |
| `GET` | `/api/runs/{brief_id}` | S1 | Run status |
| `GET` | `/api/runs/{brief_id}/task-status` | S2 | Celery task state |
| `GET` | `/api/llm-providers` | S3 | List providers (admin) |
| `POST` | `/api/llm-providers` | S3 | Register provider (admin) |
| `PATCH` | `/api/llm-providers/{id}` | S3 | Update provider (admin) |
| `DELETE` | `/api/llm-providers/{id}` | S3 | Delete provider (admin) |
| `POST` | `/api/llm-providers/sync` | S3 | Sync to runtime (admin) |
| `POST` | `/api/llm-providers/{id}/health` | S3 | Health check (admin) |
| `GET` | `/api/api-keys` | S3 | List API keys |
| `POST` | `/api/api-keys` | S3 | Generate key |
| `DELETE` | `/api/api-keys/{id}` | S3 | Revoke key |
| `POST` | `/api/api-keys/{id}/rotate` | S3 | Rotate key |
| `GET` | `/api/audit-logs` | S3 | View audit log (admin) |
| `POST` | `/api/benchmark` | S3 | Run benchmark (admin) |
| `GET` | `/metrics` | S2 | Prometheus metrics |
| `WS` | `/ws/runs/{brief_id}` | S2 | Agent progress streaming |

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| Three-repo split (`inndxd`, `inndxd-enterprise`, `inndxd-cloud`) | Open-source core, proprietary infra, business ops — clean domain boundaries |
| `inndxd.ai` = product, `inndxd.com` = business | Separates usage from commercial layer; `.com` signals enterprise permanence |
| Auth in `inndxd-core` | JWT is universal — all apps validate the same token regardless of auth provider |
| Identity providers in enterprise/cloud repos | LDAP/SAML/OIDC are deployment concerns, not product concerns |
| `apps/web/` as separate FastAPI process | UI scales independently from API; different security surface |
| HTMX + Jinja2 for dashboard | Server-side rendering, zero custom JS, live polling, works with existing FastAPI |
| uv workspaces | Native Python workspace support, shared lockfile |
| `src/` layout | Clean separation from metadata |
| `hatchling` build backend | Compatible with uv workspaces |
| `@pytest.mark.db` | Local dev without Postgres |
| JSON-structured logging | Machine-parseable observability |
| MCP dual transport (stdio + SSE) | Claude Desktop + web clients |
