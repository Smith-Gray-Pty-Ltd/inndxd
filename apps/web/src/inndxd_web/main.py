"""Inndxd Web Dashboard application."""
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from inndxd_web.routers.ui import router as ui_router
from inndxd_web.routers.ui_auth import router as ui_auth_router
from inndxd_web.routers.ui_projects import router as ui_projects_router

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"
STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "static"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def create_app() -> FastAPI:
    app = FastAPI(title="Inndxd Web", version="0.1.0")

    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    app.state.templates = templates

    app.include_router(ui_router, prefix="/ui", tags=["ui"])
    app.include_router(ui_auth_router, prefix="/ui/auth", tags=["ui-auth"])
    app.include_router(ui_projects_router, prefix="/ui/projects", tags=["ui-projects"])

    return app


app = create_app()
