from contextlib import asynccontextmanager

from fastapi import FastAPI

from inndxd_api.routers import briefs_router, data_items_router, projects_router, runs_router
from inndxd_core.db import engine
from inndxd_core.models.base import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Inndxd API",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(projects_router, prefix="/api/projects", tags=["projects"])
    app.include_router(briefs_router, prefix="/api/briefs", tags=["briefs"])
    app.include_router(data_items_router, prefix="/api/data-items", tags=["data-items"])
    app.include_router(runs_router, prefix="/api/runs", tags=["runs"])
    return app


app = create_app()
