```
                          ____  _   _ _   _ ____  ____  __  __
                         |_  _|| \ | | \ | |  _ \|  _ \ \ \/ /
                           ||  |  \| |  \| | | | | | | | \  / 
                           ||  | |\  | |\  | |_| | |_| | /  \ 
                          |___||_| \_|_| \_|____/|____/ /_/\_\
```

# inndxd

**AI agents that research, collect, and structure data — on autopilot.**

[![AGPLv3](https://img.shields.io/badge/license-AGPLv3-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)](https://python.org)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen)](https://docker.com)

Define a project in plain English. Autonomous agents plan the research, search the web and APIs, extract structured data, and deliver it through a REST API, WebSocket, or MCP server — all running inside your own infrastructure with zero data leaving your control.

---

### Autonomous &emsp; Open-Source &emsp; Production-Ready

**Multi-agent swarm** that plans, searches, validates, and structures. Five research tools with capability-based routing. Fan-out for parallel execution. Recursive follow-ups when data is incomplete.

**AGPLv3.** Self-host or cloud. Your data stays yours. No vendor lock-in. Full API, MCP, WebSocket — integrate with anything.

**JWT auth, API keys, rate limiting.** OpenTelemetry tracing, Prometheus metrics, JSON-structured logging. PostgreSQL + pgvector for semantic search. Celery + Redis for reliable distributed execution.

---

## Quick Start

```bash
git clone https://github.com/Smith-Gray-Pty-Ltd/inndxd.git
cd inndxd
cp .env.example .env
docker compose up -d
~/.local/bin/uv sync
```

### Register, build, monitor — four API calls

```bash
# 1. Register and get your JWT
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "demo@inndxd.ai", "password": "securepass123"}' | jq -r '.access_token')

# 2. Create a project
PID=$(curl -s -X POST http://localhost:8000/api/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Market Research", "description": "Q2 competitive analysis"}' | jq -r '.id')

# 3. Create a brief — the agents start working immediately
curl -s -X POST http://localhost:8000/api/briefs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"project_id\": \"$PID\", \"natural_language\": \"Top 5 SaaS analytics tools in 2026 with pricing\"}" | jq .

# 4. Check your structured results
curl -s http://localhost:8000/api/data-items \
  -H "Authorization: Bearer $TOKEN" | jq .
```

**Web dashboard** at [localhost:8080/ui](http://localhost:8080/ui) — login, manage projects, create briefs, view live results with HTMX-powered status updates.

---

## Architecture

```
                         ┌──────────────┐
                         │  inndxd-mcp  │ ← tools, resources, prompts, SSE
                         └──────┬───────┘
                                │
                                ▼
┌──────────────┐         ┌──────────────┐
│ inndxd-core  │◀────────│inndxd-agents │ ← LangGraph swarm, 5 tools, fan-out
│ models, JWT  │         └──────┬───────┘
└──────┬───────┘                │
       │                        │
       ▼                        ▼
┌──────────────┐         ┌──────────────┐
│  apps/api    │         │  apps/web    │
│  Port 8000   │         │  Port 8080   │
│  REST + WS   │         │  Dashboard   │
└──────┬───────┘         └──────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  PostgreSQL + pgvector  |  Redis  |  Ollama  │
└─────────────────────────────────────────┘
```

### How a Research Brief Works

```
START → planner → plan_validator → collector → quality_gate
                                                      │
                                              ┌───────┘
                                              ▼
                                         structurer → END
```

The planner reads your brief and builds a query plan. The collector executes searches using the right tools for each target (web search, API fetch, browser scrape, database query, Twitter/X search). A quality gate checks if enough data was gathered — if not, it loops back for more. The structurer extracts clean, typed data and persists it to PostgreSQL.

[Full source tree →](https://github.com/Smith-Gray-Pty-Ltd/inndxd-project/blob/main/inndxd/architecture/source-tree.md)

---

## Roadmap

| Stage | Status | What |
|---|---|---|
| **1** — Foundation | ✅ Complete | Core models, agent graph, FastAPI API, Docker infra |
| **2** — Production | ✅ Complete | Celery workers, 5 research tools, MCP server, Prometheus, export, WebSocket |
| **3** — Security & Observability | ✅ Complete | JWT auth, multi-provider LLM, API keys, OpenTelemetry, audit logs |
| **4** — Web Dashboard | 🔄 In Progress | Jinja2 + Tailwind + HTMX — Phase 0-2 done, Phase 3 (Briefs) next |
| **Cloud** | ⬜ Planned | Signup, billing, admin, gateway — [plan →](https://github.com/Smith-Gray-Pty-Ltd/inndxd-project/blob/main/inndxd-cloud/planning/stage-cloud.md) |

Detailed plans live in the [project docs repo](https://github.com/Smith-Gray-Pty-Ltd/inndxd-project).

---

## Features

### Multi-Provider LLM

DB-backed provider registry. Register any OpenAI-compatible endpoint — OpenAI, Anthropic, Groq, Ollama, DeepSeek, local models. Assign different models to different agent nodes. Health checks keep unhealthy providers out of rotation. Failover falls through providers in priority order.

### Research Toolbelt

Five tools with capability-based routing. **Web search** via Crawl4AI + DuckDuckGo. **Twitter/X search**. **API fetch** for any REST or GraphQL endpoint. **Browser scrape** with table extraction. **Internal DB query** for previously collected data. All tools support timeouts, retry, and caching.

### Web Dashboard

Server-rendered with HTMX — zero custom JavaScript. Login, register, project management, brief creation, live status updates via polling. Sortable data tables with CSV/JSON export. Admin panels for LLM providers, API keys, and audit logs. Feels like a SPA, ships nothing but HTML.

### Developer API

28 REST endpoints. Full CRUD for projects, briefs, and data items. Export to JSON or CSV. JWT auth with API key support and rate limiting. WebSocket streaming for agent progress. MCP server with stdio + SSE transport — works with Claude Desktop and web clients. Prometheus metrics at `/metrics`.

### Observability Suite

OpenTelemetry distributed tracing across the agent graph. JSON-structured logging. Prometheus counters for brief creation, data items collected, and request duration histograms. Audit log for every agent execution — who ran what, when, with what results.

---

## License

AGPL-3.0-only — see [LICENSE](LICENSE).

Built by [Smith & Gray](https://github.com/Smith-Gray-Pty-Ltd).
