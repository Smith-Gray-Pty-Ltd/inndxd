"""Inndxd Web Dashboard application."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates as _Jinja2Templates

from inndxd_web.routers.ui import router as ui_router
from inndxd_web.routers.ui_admin import router as ui_admin_router
from inndxd_web.routers.ui_auth import router as ui_auth_router
from inndxd_web.routers.ui_briefs import router as ui_briefs_router
from inndxd_web.routers.ui_chat import router as ui_chat_router
from inndxd_web.routers.ui_data_items import router as ui_data_items_router
from inndxd_web.routers.ui_projects import router as ui_projects_router

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"
STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "static"

_raw = _Jinja2Templates(directory=str(TEMPLATES_DIR))

class Jinja2Templates:
    def __init__(self, inner):
        self._inner = inner

    def TemplateResponse(  # noqa: N802
        self, name, context=None, status_code=200, headers=None, media_type=None):
        ctx = context or {}
        request = ctx.get("request")
        return self._inner.TemplateResponse(
            request=request,
            name=name,
            context=ctx,
            status_code=status_code,
            headers=headers,
            media_type=media_type,
        )

templates = Jinja2Templates(_raw)


def create_app() -> FastAPI:
    app = FastAPI(title="Inndxd Web", version="0.1.0")

    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    app.state.templates = templates

    app.include_router(ui_router, prefix="/ui", tags=["ui"])
    app.include_router(ui_auth_router, prefix="/ui/auth", tags=["ui-auth"])
    app.include_router(ui_admin_router, prefix="/ui/admin", tags=["ui-admin"])
    app.include_router(ui_briefs_router, prefix="/ui/briefs", tags=["ui-briefs"])
    app.include_router(ui_chat_router, prefix="/ui/chat", tags=["ui-chat"])
    app.include_router(ui_data_items_router, prefix="/ui/data-items", tags=["ui-data-items"])
    app.include_router(ui_projects_router, prefix="/ui/projects", tags=["ui-projects"])

    return app


app = create_app()
