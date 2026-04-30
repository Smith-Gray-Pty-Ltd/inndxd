from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import FastAPI
from inndxd_core.config import settings
from inndxd_core.db import engine
from inndxd_core.logging_config import configure_logging
from inndxd_core.models.base import Base

from inndxd_api.metrics import get_metrics, request_duration
from inndxd_api.middleware.tenant import TenantMiddleware
from inndxd_api.routers import briefs_router, data_items_router, projects_router, runs_router
from inndxd_api.routers.api_keys import router as api_keys_router
from inndxd_api.routers.audit_logs import router as audit_logs_router
from inndxd_api.routers.auth import router as auth_router
from inndxd_api.routers.benchmark import router as benchmark_router
from inndxd_api.routers.llm_providers import router as llm_providers_router
from inndxd_api.routers.ws import router as ws_router
from inndxd_api.tracing import instrument_app, setup_tracing


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(settings.log_level)
    setup_tracing(otlp_endpoint=getattr(settings, "otlp_endpoint", None))
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Inndxd API",
        version="0.2.0",
        lifespan=lifespan,
    )

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

    app.add_middleware(TenantMiddleware)
    app.add_route("/metrics", get_metrics)
    app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
    app.include_router(api_keys_router, prefix="/api/api-keys", tags=["api-keys"])
    app.include_router(llm_providers_router, prefix="/api/llm-providers", tags=["llm-providers"])
    app.include_router(audit_logs_router, prefix="/api/audit-logs", tags=["audit"])
    app.include_router(projects_router, prefix="/api/projects", tags=["projects"])
    app.include_router(briefs_router, prefix="/api/briefs", tags=["briefs"])
    app.include_router(data_items_router, prefix="/api/data-items", tags=["data-items"])
    app.include_router(runs_router, prefix="/api/runs", tags=["runs"])
    app.include_router(benchmark_router, prefix="/api/benchmark", tags=["benchmark"])
    app.include_router(ws_router, tags=["websocket"])
    instrument_app(app)
    return app


app = create_app()
