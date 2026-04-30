# Inndxd — Three-Repo Strategy

> **Agreed:** 2026-04-30
> **Domains:** `inndxd.ai` (product) · `inndxd.com` (business)

---

## Domain Mapping

| Domain | Purpose | Traffic |
|---|---|---|
| `inndxd.ai` | The product — agents research, collect, structure, deliver | Customer-facing |
| `inndxd.com` | The business — signup, billing, admin, marketing | Public + internal |

| Subdomain | Deployment | Tenant |
|---|---|---|
| `app.inndxd.ai` | Shared cloud (SaaS) | Multi-tenant |
| `clientname.inndxd.ai` | Managed VPS | Single-tenant |
| `inndxd.agency.gov.au` | Enterprise gov cloud | Single-tenant (their domain) |

---

## Repo 1: `inndxd` (open-source, AGPL)

```
inndxd/                                 # github.com/Smith-Gray-Pty-Ltd/inndxd
│
├── packages/
│   ├── inndxd-core/                    # Shared domain layer
│   │   ├── pyproject.toml
│   │   └── src/inndxd_core/
│   │       ├── __init__.py
│   │       ├── config.py               # DB, Ollama, Redis, JWT settings
│   │       ├── db.py                   # Async engine + session factory
│   │       ├── embedding.py            # Ollama nomic-embed-text
│   │       ├── logging_config.py       # JSON-structured logging
│   │       ├── auth.py                 # hash_password, verify_password, JWT
│   │       ├── models/                 # SQLAlchemy ORM
│   │       │   ├── __init__.py
│   │       │   ├── base.py             # Base, UUIDMixin, TimestampMixin
│   │       │   ├── project.py
│   │       │   ├── brief.py
│   │       │   ├── data_item.py        # + pgvector embedding column
│   │       │   ├── user.py             # email, hashed_password, is_admin
│   │       │   ├── llm_provider.py     # tenant-scoped provider config
│   │       │   ├── api_key.py          # key_prefix, key_hash, is_active
│   │       │   └── audit_log.py        # event_type, actor, details (JSONB)
│   │       ├── domain/                 # Pydantic schemas
│   │       │   ├── __init__.py
│   │       │   ├── project.py
│   │       │   ├── brief.py
│   │       │   ├── data_item.py
│   │       │   ├── user.py             # UserCreate, UserLogin, UserRead
│   │       │   ├── llm_provider.py     # LLMConfig, LLMProviderConfig
│   │       │   ├── llm_provider_crud.py
│   │       │   └── api_key.py
│   │       ├── repositories/           # Data access layer
│   │       │   ├── __init__.py
│   │       │   ├── base.py
│   │       │   ├── projects.py
│   │       │   ├── data_items.py       # + semantic_search()
│   │       │   ├── users.py
│   │       │   ├── llm_providers.py
│   │       │   ├── api_keys.py
│   │       │   └── audit_logs.py
│   │       └── migrations/             # Alembic
│   │
│   ├── inndxd-agents/                  # LangGraph swarm + tools
│   │   ├── pyproject.toml
│   │   └── src/inndxd_agents/
│   │       ├── __init__.py
│   │       ├── config.py               # Per-node model overrides
│   │       ├── graph.py                # StateGraph builder, conditions
│   │       ├── llm.py                  # Multi-provider factory + failover
│   │       ├── state.py                # ResearchState (extends MessagesState)
│   │       ├── swarm.py                # run_research_swarm() orchestrator
│   │       ├── fanout.py               # Parallel sub-graph (Semaphore)
│   │       ├── benchmark.py            # Multi-run performance benchmark
│   │       ├── plugins.py              # AgentNodePlugin ABC + registry
│   │       ├── nodes/
│   │       │   ├── __init__.py
│   │       │   ├── planner.py          # Query plan generation
│   │       │   ├── collector.py        # Tool execution with retry
│   │       │   ├── structurer.py       # Data extraction + schema map
│   │       │   ├── plan_validator.py   # Plan quality check
│   │       │   ├── quality.py          # Output sufficiency evaluator
│   │       │   ├── human_approval.py   # Interrupt for manual review
│   │       │   └── recursive.py        # LLM follow-up query generation
│   │       ├── tools/
│   │       │   ├── __init__.py
│   │       │   ├── registry.py         # v2 capability-based routing
│   │       │   ├── web_search.py       # Crawl4AI + DuckDuckGo
│   │       │   ├── twitter_search.py   # Social media discovery
│   │       │   ├── api_fetch.py        # REST/GraphQL fetcher
│   │       │   ├── browser.py          # Table extraction via Crawl4AI
│   │       │   └── db_query.py         # Internal SQLAlchemy query
│   │       ├── prompts/
│   │       └── tests/
│   │
│   └── inndxd-mcp/                     # MCP server
│       ├── pyproject.toml
│       └── src/inndxd_mcp/
│           ├── __init__.py
│           └── server.py               # tools, resources, prompts, stdio + SSE
│
├── apps/
│   ├── api/                            # REST API — JSON + /metrics + WebSocket
│   │   ├── pyproject.toml
│   │   ├── Dockerfile
│   │   ├── src/inndxd_api/
│   │   │   ├── __init__.py
│   │   │   ├── main.py                 # Port 8000 · 9 API routers
│   │   │   ├── config.py               # Re-export stub → inndxd_core
│   │   │   ├── dependencies.py         # get_db, get_tenant_id, get_brief
│   │   │   ├── celery_app.py           # Celery + Redis + beat
│   │   │   ├── tasks.py                # run_research_task, cleanup_stuck_briefs
│   │   │   ├── metrics.py              # Prometheus counters + histograms
│   │   │   ├── provider_health.py      # LLM provider /models health check
│   │   │   ├── provider_sync.py        # DB → runtime LLMConfig sync
│   │   │   ├── auth_deps.py            # get_current_user, require_admin
│   │   │   ├── tracing.py              # OpenTelemetry + FastAPI instrumentor
│   │   │   ├── routers/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py             # POST register, POST login
│   │   │   │   ├── api_keys.py         # CRUD + rotate API keys
│   │   │   │   ├── projects.py         # Full CRUD, tenant scoping
│   │   │   │   ├── briefs.py           # POST → Celery task + Prometheus
│   │   │   │   ├── data_items.py       # GET + export/json + export/csv
│   │   │   │   ├── runs.py             # GET + task-status (Celery state)
│   │   │   │   ├── llm_providers.py    # CRUD + health + node assignments + sync
│   │   │   │   ├── audit_logs.py       # Admin-only audit log viewer
│   │   │   │   ├── benchmark.py        # Admin-only agent benchmark
│   │   │   │   └── ws.py              # WebSocket /ws/runs/{brief_id}
│   │   │   ├── schemas/
│   │   │   └── middleware/
│   │   │       └── tenant.py           # TenantMiddleware + ContextVar
│   │   └── tests/
│   │
│   └── web/                            # Dashboard UI — Jinja2 + Tailwind + HTMX
│       ├── pyproject.toml
│       ├── src/inndxd_web/
│       │   ├── __init__.py
│       │   ├── main.py                 # Port 8080
│       │   ├── auth.py                 # JWT httpOnly cookie session
│       │   └── routers/
│       │       ├── __init__.py
│       │       ├── ui.py               # Dashboard home (with real DB stats)
│       │       ├── ui_auth.py          # Login/register/logout pages
│       │       ├── ui_projects.py      # Project CRUD pages       [Phase 2]
│       │       ├── ui_briefs.py        # Brief list/detail/create  [Phase 3]
│       │       ├── ui_data_items.py    # Data table + export       [Phase 4]
│       │       └── ui_admin.py         # Providers + keys + audit  [Phase 5]
│       ├── templates/
│       │   ├── base.html               # Sidebar + header layout
│       │   ├── auth/
│       │   │   ├── login.html
│       │   │   └── register.html
│       │   ├── dashboard/
│       │   │   └── index.html          # Stats + CTA
│       │   ├── projects/               # [Phase 2]
│       │   ├── briefs/                 # [Phase 3]
│       │   ├── data_items/             # [Phase 4]
│       │   ├── admin/                  # [Phase 5]
│       │   └── partials/
│       │       ├── _status_badge.html
│       │       └── _stats_cards.html
│       ├── static/css/input.css
│       └── tests/
│
├── docker/
│   ├── postgres/init.sql
│   └── ollama/entrypoint.sh
│
├── docker-compose.yml                  # postgres, redis, ollama, api (+ web)
├── pyproject.toml                      # Root workspace — 5 members
├── .env.example
├── .pre-commit-config.yaml
├── plan/
│   ├── masterplan.md
│   ├── repo-strategy.md                # ← this file
│   ├── stage2.md
│   ├── stage3.md
│   └── stage4.md
└── README.md
```

### Depends on

Nothing external. Self-contained. `git clone` + `docker compose up` = fully running.

### Ports

| Service | Port | Protocol |
|---|---|---|
| `apps/api` | 8000 | JSON, /metrics, WebSocket |
| `apps/web` | 8080 | HTML (Jinja2) |

---

## Repo 2: `inndxd-enterprise` (proprietary)

```
inndxd-enterprise/                      # github.com/Smith-Gray-Pty-Ltd/inndxd-enterprise
│
├── infra/
│   ├── aws-govcloud/                   # Terraform + k8s for IRAP/ISO
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   ├── modules/
│   │   │   ├── vpc/
│   │   │   ├── eks/
│   │   │   ├── rds/
│   │   │   └── security-groups/
│   │   └── environments/
│   │       ├── dev/
│   │       ├── staging/
│   │       └── prod/
│   ├── azure-government/
│   │   └── (same structure)
│   └── gcp-assured/
│       └── (same structure)
│
├── compliance/
│   ├── iso27001/
│   │   ├── policies/                   # Access control, encryption, logging
│   │   ├── evidence/                   # Scripts to auto-collect compliance data
│   │   └── controls.md                 # ISO 27001:2022 Annex A control map
│   ├── irap/
│   │   ├── ism-controls.md             # Australian ISM control mapping
│   │   └── assessment/                 # IRAP assessment evidence templates
│   └── soc2/
│       ├── trust-criteria.md
│       └── monitoring/                 # Alerting configs for availability
│
├── apps/
│   └── identity-providers/             # LDAP, SAML, Okta, Azure AD connectors
│       ├── pyproject.toml
│       └── src/
│           ├── ldap.py                  # Active Directory connector
│           ├── saml.py                  # SAML 2.0 IdP initiation
│           ├── oidc.py                  # Generic OIDC (Okta, Auth0, Azure AD)
│           └── mapping.py              # LDAP group → inndxd role mapping
│
├── docker-compose.enterprise.yml       # Adds IdP to inndxd stack
├── pyproject.toml
└── README.md
```

### Depends on

`inndxd` (open-source) — consumes it as a package dependency. The enterprise stack **wraps** the open-source product.

### What this repo does NOT contain

- No product code (shared via `inndxd` open-source packages)
- No business logic (customer management is in `inndxd-cloud`)
- No UI customization (just infrastructure + compliance + identity)

---

## Repo 3: `inndxd-cloud` (proprietary)

```
inndxd-cloud/                           # github.com/Smith-Gray-Pty-Ltd/inndxd-cloud
│
├── apps/
│   ├── gateway/                        # Routes traffic to customer instances
│   │   ├── pyproject.toml
│   │   └── src/
│   │       ├── main.py                 # Reverse proxy for *.inndxd.ai
│   │       ├── router.py               # Lookup tenant → instance IP/port
│   │       └── provision.py            # Spin up/down VPS instances via API
│   │
│   ├── website/                        # Public marketing site — inndxd.com
│   │   ├── pyproject.toml
│   │   ├── src/
│   │   │   └── main.py                 # FastAPI serving static + Jinja2
│   │   └── templates/
│   │       ├── base.html               # Public layout (no auth, no sidebar)
│   │       ├── index.html              # Landing page / hero
│   │       ├── pricing.html            # SaaS + VPS + Enterprise tiers
│   │       ├── docs/                   # Documentation pages
│   │       └── blog/                   # Blog, case studies
│   │
│   ├── identity/                       # Signup + social auth
│   │   ├── pyproject.toml
│   │   └── src/
│   │       ├── main.py                 # /signup, /login, /forgot-password
│   │       ├── providers/
│   │       │   ├── local.py            # Email/password (uses inndxd-core auth)
│   │       │   ├── google.py           # OAuth 2.0
│   │       │   └── github.py           # OAuth 2.0
│   │       └── models.py               # Customer (name, company, plan_id)
│   │
│   ├── billing/                        # Stripe subscriptions
│   │   ├── pyproject.toml
│   │   └── src/
│   │       ├── main.py                 # /billing, /subscribe, /invoices
│   │       ├── stripe.py               # Webhook handler, checkout sessions
│   │       ├── plans.py                # Plan tier definitions
│   │       └── models.py               # Subscription, Invoice, Payment
│   │
│   └── admin/                          # Internal admin panel — only us
│       ├── pyproject.toml
│       └── src/
│           ├── main.py                 # /admin dashboard
│           ├── customers.py            # Customer lookup, plan mgmt, impersonate
│           ├── instances.py            # VPS health, costs, provisioning
│           └── analytics.py            # Usage stats, revenue, churn
│
├── .github/workflows/
│   ├── deploy-website.yml              # Deploy website to Vercel/Cloudflare
│   ├── deploy-gateway.yml              # Deploy gateway to k8s
│   └── provision-customer.yml          # GitHub Actions to spin up new tenant
│
├── docker-compose.yml                  # gateway + website + identity + billing + admin
├── pyproject.toml                      # Root workspace
├── .env.example
└── README.md
```

### Depends on

`inndxd` (open-source) — installs `inndxd-core` as a package (for auth utils, models). Does NOT run `apps/api` or `apps/web` — those run on customer instances.

### What this repo does NOT contain

- No agent orchestration (that's in the `inndxd` instances on customer infra)
- No research data (zero customer data touches this repo)
- No MCP server

---

## How the Three Repos Connect

```
  ┌──────────────────────────────────────────────────────────────┐
  │                     inndxd-cloud                             │
  │                                                              │
  │  website/ ──► identity/ ──► billing/ ──► admin/             │
  │     │              │             │            │              │
  │     │         creates          charges     monitors         │
  │     │         Customer         Stripe      everything       │
  │     ▼              │             │            │              │
  │  Signup flow   JWT issued    Plan active   Dashboard        │
  │                     │             │            │              │
  │                     ▼             ▼            ▼              │
  │               gateway/ ──► provisions ──► routes traffic    │
  └──────────────────────┬──────────────────────────────────────┘
                         │
        routes traffic to │
                         │
  ┌──────────────────────┼──────────────────────────────────────┐
  │               inndxd (customer instances)                   │
  │                                                              │
  │  app.inndxd.ai          → api/ + web/ (shared SaaS)         │
  │  clientname.inndxd.ai   → api/ + web/ (dedicated VPS)       │
  │  inndxd.agency.gov.au   → api/ + web/ (gov cloud)           │
  │                                                              │
  │  Each instance runs the same open-source code.              │
  │  Different deployment model, same product.                  │
  └──────────────────────────────────────────────────────────────┘
                         │
        deployed via      │
                         │
  ┌──────────────────────┼──────────────────────────────────────┐
  │               inndxd-enterprise                             │
  │                                                              │
  │  infra/aws-govcloud/ → deploys inndxd into AWS GovCloud    │
  │  infra/azure-government/ → deploys into Azure Gov           │
  │  compliance/iso27001/ → evidence for auditor                │
  │  compliance/irap/ → ISM control mapping                    │
  │  apps/identity-providers/ → LDAP, SAML, Okta connectors    │
  └──────────────────────────────────────────────────────────────┘
```

---

## Cross-Repo Dependencies

| Consumer | Depends On | How |
|---|---|---|
| `inndxd-enterprise` | `inndxd` | Installs `inndxd-core` + `inndxd-agents` + `inndxd-mcp` as packages via PyPI |
| `inndxd-cloud/identity` | `inndxd` | Installs `inndxd-core` for `auth.py` (hash_password, JWT) |
| `inndxd-cloud/gateway` | `inndxd` | Routes to `inndxd` instances; no code dependency |
| `inndxd-cloud/billing` | `inndxd-cloud/identity` | Reads `Customer` model; no inndxd dependency |

---

## Git Strategy

| Repo | Branch Strategy | CI/CD |
|---|---|---|
| `inndxd` | `main` + `stage4/phase<X>-<slug>` → squash-merge PR | Build + publish PyPI packages |
| `inndxd-enterprise` | `main` + feature branches | Terraform plan → apply per env |
| `inndxd-cloud` | `main` + feature branches | Deploy to k8s per service |

### OpenCode sessions

One session per repo, one terminal per session. The repos are designed so you rarely need cross-repo context:

```
Terminal 1: opencode in inndxd/           # Product development
Terminal 2: opencode in inndxd-cloud/     # Business ops
Terminal 3: opencode in inndxd-enterprise/ # Enterprise deployments
```

When you DO need both (e.g., tracing a bug from `inndxd-cloud/gateway` → `inndxd` instance): open two terminal tabs. The model won't share context between sessions, but the repos don't share context either — the gateway talks to the API via HTTP, not import.
