"""Design system catalog — only active when INNDXD_DEV_MODE=true."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter()


def _render(request: Request, template: str, current: str) -> HTMLResponse:
    templates = request.app.state.templates
    return templates.TemplateResponse(
        f"design/{template}.html",
        {"request": request, "current": current},
    )


@router.get("/", response_class=HTMLResponse)
async def design_components(request: Request):
    return _render(request, "index", "components")


@router.get("/dashboard", response_class=HTMLResponse)
async def design_dashboard(request: Request):
    return _render(request, "dashboard", "dashboard")


@router.get("/datasets", response_class=HTMLResponse)
async def design_datasets(request: Request):
    return _render(request, "datasets", "datasets")


@router.get("/projects", response_class=HTMLResponse)
async def design_projects(request: Request):
    return _render(request, "projects", "projects")


@router.get("/briefs", response_class=HTMLResponse)
async def design_briefs(request: Request):
    return _render(request, "briefs", "briefs")


@router.get("/data-items", response_class=HTMLResponse)
async def design_data_items(request: Request):
    return _render(request, "data-items", "data-items")


@router.get("/admin", response_class=HTMLResponse)
async def design_admin(request: Request):
    return _render(request, "admin", "admin")
