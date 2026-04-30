"""UI session management via JWT httpOnly cookie."""
from __future__ import annotations

from fastapi import HTTPException, Request, Response, status
from inndxd_core.auth import create_access_token, decode_access_token

UI_COOKIE_NAME = "inndxd_session"


def set_auth_cookie(response: Response, user_id: str, tenant_id: str | None) -> None:
    token = create_access_token(user_id, tenant_id)
    response.set_cookie(
        key=UI_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=86400,
    )


def clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(UI_COOKIE_NAME)


def get_ui_user(request: Request) -> dict | None:
    token = request.cookies.get(UI_COOKIE_NAME)
    if not token:
        return None
    try:
        return decode_access_token(token)
    except Exception:
        return None


def require_ui_user(request: Request) -> dict:
    user = get_ui_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/ui/auth/login"},
        )
    return user
