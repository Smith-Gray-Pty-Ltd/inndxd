"""Design system catalog — only active when INNDXD_DEV_MODE=true."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def design_index(request: Request):
    templates = request.app.state.templates
    return templates.TemplateResponse(
        "design/index.html",
        {"request": request},
    )
