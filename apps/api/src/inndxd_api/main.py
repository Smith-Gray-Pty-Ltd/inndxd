from contextlib import asynccontextmanager

from fastapi import FastAPI
from inndxd_core.config import settings
from inndxd_core.db import engine
from inndxd_core.logging_config import configure_logging
from inndxd_core.models.base import Base

from inndxd_api.metrics import get_metrics
from inndxd_api.middleware.tenant import TenantMiddleware
from inndxd_api.routers import briefs_router, data_items_router, projects_router, runs_router
from inndxd_api.routers.auth import router as auth_router
from inndxd_api.routers.ws import router as ws_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(settings.log_level)
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
    app.add_middleware(TenantMiddleware)
    app.add_route("/metrics", get_metrics)
    app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
    app.include_router(projects_router, prefix="/api/projects", tags=["projects"])
    app.include_router(briefs_router, prefix="/api/briefs", tags=["briefs"])
    app.include_router(data_items_router, prefix="/api/data-items", tags=["data-items"])
    app.include_router(runs_router, prefix="/api/runs", tags=["runs"])
    app.include_router(ws_router, tags=["websocket"])
    return app


app = create_app()
