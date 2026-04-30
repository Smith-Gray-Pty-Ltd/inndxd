# inndxd

[![Stage 1 Complete](https://img.shields.io/badge/Stage-1%20Complete-brightgreen)](https://github.com/Smith-Gray-Pty-Ltd/inndxd)

Open-source agentic data platform. Define a project → autonomous agents research, collect, structure & deliver real-time data via API, MCP, WebSocket & skills.

## Features (Stage 1)

- ✅ **FastAPI REST API** - Tenant-scoped CRUD endpoints for projects, briefs, data-items, and runs
- ✅ **LangGraph Research Swarm** - Automated research pipeline: planner → collector → structurer
- ✅ **Docker Compose Infrastructure** - PostgreSQL with pgvector, Redis, and Ollama
- ✅ **Async SQLAlchemy** - Full async support for database operations
- ✅ **Tenant Isolation** - Multi-tenant support via X-Tenant-ID header
- ✅ **Integration Tests** - pytest-asyncio test suite with SQLite in-memory

## Architecture

A monorepo with three key packages:

```
┌─────────────────────────────────────────────────────────────┐
│                     apps/api (FastAPI)                      │
│  REST endpoints: projects, briefs, data-items, runs         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                 packages/inndxd-agents (LangGraph)          │
│  Swarm: planner → collector → structurer                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  packages/inndxd-core (Models)              │
│  SQLAlchemy models, repositories, domain schemas            │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- Docker & Docker Compose
- [just](https://github.com/casey/just) (optional task runner)

### Setup

```bash
# 1. Clone and sync dependencies
git clone https://github.com/Smith-Gray-Pty-Ltd/inndxd.git
cd inndxd
uv sync

# 2. Create .env file
cp .env.example .env
# Edit .env with your PostgreSQL connection string
# INNDXD_DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/inndxd

# 3. Start infrastructure (PostgreSQL with pgvector, Redis, Ollama)
docker compose up -d
```

### Create Project

```bash
TENANT_ID=$(uuidgen)
PROJECT_ID=$(curl -s -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: ${TENANT_ID}" \
  -d '{"name": "Property Investment", "description": "Find commercial properties"}' | jq -r '.id')

echo "Created project: ${PROJECT_ID}"
```

### Create Brief (Triggers Research Swarm)

```bash
curl -s -X POST http://localhost:8000/api/briefs \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: ${TENANT_ID}" \
  -d "{\"project_id\": \"${PROJECT_ID}\", \"natural_language\": \"Find top 5 commercial property platforms in Sydney\"}" | jq .

# Check brief status
curl -s http://localhost:8000/api/briefs \
  -H "X-Tenant-ID: ${TENANT_ID}" | jq .
```

### Check Data Items

```bash
curl -s http://localhost:8000/api/data-items \
  -H "X-Tenant-ID: ${TENANT_ID}" | jq .
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/projects` | Create a new project |
| GET | `/api/projects` | List projects for tenant |
| GET | `/api/projects/{id}` | Get project details |
| DELETE | `/api/projects/{id}` | Delete project |
| POST | `/api/briefs` | Create brief (triggers research swarm) |
| GET | `/api/briefs` | List briefs for tenant |
| GET | `/api/briefs/{id}` | Get brief details |
| GET | `/api/data-items` | List data items for tenant |
| GET | `/api/data-items/{id}` | Get data item details |
| GET | `/api/runs/{brief_id}` | Get run status for brief |

All endpoints require the `X-Tenant-ID` header (UUID format).

## Status

### Stage 1 ✅ Complete

- [x] Core models & repositories (`packages/inndxd-core/`)
- [x] LangGraph research swarm (`packages/inndxd-agents/`)
- [x] FastAPI REST API (`apps/api/`)
- [x] Docker Compose infrastructure
- [x] Tenant-scoped security
- [x] Integration tests

### Stage 2 🔄 In Progress

#### Phase 0: ✅ Complete
- [x] Fixed broken AgentState imports
- [x] Wired TenantMiddleware into FastAPI app
- [x] Alembic migration structure set up
- [x] Pre-commit hooks configured
- [x] Added test suite for routers, domain models, graph

#### Phase 0.5: ✅ Complete
- [x] Multi-provider LLM config models (`LLMProviderConfig`, `LLMConfig`)
- [x] Injectable LLM clients per agent node
- [x] Per-node model override env vars (`INNDXD_PLANNER_MODEL`, etc.)
- [x] `resolve_model_for_node()` utility
- [x] Roadmap entry for Stage 3

#### Phase 1: ✅ Complete
- [x] Conditional routing with retry limits
- [x] Quality gate evaluator (collect data sufficiency, structured output validity)
- [x] Plan validator node
- [x] Human-in-the-loop approval interrupt point
- [x] Graph state serialization helper
- [x] Inter-step entry/exit logging on all nodes

#### Phase 2: ✅ Complete
- [x] Celery app with Redis broker/backend
- [x] `run_research_task` Celery task (replaces BackgroundTasks)
- [x] `cleanup_stuck_briefs` periodic task (Celery beat, every 30 min)
- [x] Brief repository for async status updates
- [x] `GET /api/runs/{brief_id}/task-status` endpoint for Celery task state
- [x] `celery_worker` service in docker-compose.yml

#### Phase 3: ✅ Complete
- [x] Twitter/X search tool (`twitter_search_tool`)
- [x] API fetch tool (`api_fetch_tool`) — REST/GraphQL endpoints
- [x] Browser automation tool (`browser_tool`) — table extraction
- [x] Database query tool (`db_query_tool`) — stats and recent items
- [x] Tool registry v2 with capability-based routing (`get_tools_by_capability`)
- [x] `invoke_tool_with_timeout` wrapper for all tools
- [x] Collector node uses tool registry for dynamic tool selection
- [x] Crawl4AI cache enabled for repeated queries
- [x] Planner prompt updated with tool names and selection guidance

#### Phase 4: ✅ Complete
- [x] MCP SDK dependency added to `inndxd-mcp`
- [x] Full MCP server exposing all 5 agent tools (`list_tools`, `call_tool`)
- [x] Resource exposure: `inndxd://projects`, `inndxd://data-items/{project_id}`
- [x] Prompt templates: `research_brief` with topic and depth arguments
- [x] Dual transport: stdio (local AI tools) + SSE on port 8001 (web clients)
- [x] Server versioned at 0.2.0

#### Phase 5: ✅ Complete
- [x] pgvector embedding column on DataItem + semantic search (`cosine_distance`)
- [x] Embedding generation utility via Ollama API (`nomic-embed-text`)
- [x] DB-level RLS enforced via `SET app.current_tenant_id` per session
- [x] Structured JSON logging configuration (`configure_logging()`)
- [x] Prometheus metrics endpoint (`GET /metrics`) with counters and histogram
- [x] CSV and JSON export endpoints (`GET /api/data-items/export/csv|json`)
- [x] WebSocket endpoint (`ws://.../ws/runs/{brief_id}`) for streaming agent progress

### Stage 2 ✅ Complete — All 5 Phases Merged

#### Next: Stage 3 →
- [ ] Full multi-provider LLM system (API endpoints, DB-backed registry, hot-swap)
- [ ] JWT-based session authentication
- [ ] Web UI (to be planned)

## Development

```bash
# Run tests
just test

# Lint and format
just lint
just fmt

# Start dev server
uv run uvicorn inndxd_api.main:app --reload

# Docker tasks
just up      # Start services
just down    # Stop services
just logs    # Follow logs
```

## Roadmap

- **Stage 3 (Coming Soon):** Multi-Provider LLM Support — configure any OpenAI-compatible LLM provider (OpenAI, Anthropic, Groq, Ollama, DeepSeek API, etc.) and assign different models to each agent node. API endpoints for managing providers at runtime.

## License

MIT
