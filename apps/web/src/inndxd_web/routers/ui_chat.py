"""UI Chat routes — SSE streaming, message history, send."""

from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from inndxd_agents.chat_planner import chat_with_planner
from inndxd_core.db import async_session_factory
from inndxd_core.models.conversation import Conversation
from sqlalchemy import select

from inndxd_web.auth import require_ui_user

router = APIRouter()


@router.post("/send")
async def chat_send(
    request: Request,
    message: str = Form(...),
    project_id: str = Form(default=""),
    brief_id: str = Form(default=""),
):
    require_ui_user(request)
    templates = request.app.state.templates

    if not message.strip():
        return HTMLResponse("", status_code=200)

    project_uuid = UUID(project_id) if project_id else None
    brief_uuid = UUID(brief_id) if brief_id else None

    user_msg = {
        "role": "user",
        "content": message.strip(),
    }

    async with async_session_factory() as session:
        conv = Conversation(
            tenant_id=UUID("00000000-0000-0000-0000-000000000000"),
            project_id=project_uuid,
            brief_id=brief_uuid,
            role="user",
            content=user_msg["content"],
        )
        session.add(conv)
        await session.commit()

    return templates.TemplateResponse(
        "partials/_chat_message.html",
        {
            "request": request,
            "role": "user",
            "content": user_msg["content"],
        },
    )


@router.get("/stream")
async def chat_stream(
    request: Request,
    project_id: str = Query(default=""),
    brief_id: str = Query(default=""),
    mode: str = Query(default="brief_setup"),
):
    require_ui_user(request)

    project_uuid = UUID(project_id) if project_id else None
    brief_uuid = UUID(brief_id) if brief_id else None

    history: list[dict[str, str]] = []
    async with async_session_factory() as session:
        stmt = select(Conversation)
        if brief_uuid:
            stmt = stmt.where(Conversation.brief_id == brief_uuid)
        elif project_uuid:
            stmt = stmt.where(Conversation.project_id == project_uuid)
        else:
            return StreamingResponse(
                _sse_error("project_id or brief_id required"),
                media_type="text/event-stream",
            )
        stmt = stmt.order_by(Conversation.created_at.asc()).limit(50)
        result = await session.execute(stmt)
        for conv in result.scalars():
            history.append({"role": conv.role, "content": conv.content})

    context: dict | None = None
    if project_uuid:
        from inndxd_core.models.project_context import ProjectContext

        async with async_session_factory() as session:
            pc = await session.get(ProjectContext, project_uuid)
            if pc:
                context = pc.context_data

    async def generate():
        full_response = ""
        try:
            async for token in chat_with_planner(history, context=context, mode=mode):
                full_response += token
                yield f"data: {json.dumps({'token': token})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

        if full_response.strip() and (project_uuid or brief_uuid):
            async with async_session_factory() as session:
                conv = Conversation(
                    tenant_id=UUID("00000000-0000-0000-0000-000000000000"),
                    project_id=project_uuid,
                    brief_id=brief_uuid,
                    role="assistant",
                    content=full_response,
                )
                session.add(conv)
                await session.commit()

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/history", response_class=HTMLResponse)
async def chat_history(
    request: Request,
    project_id: str = Query(default=""),
    brief_id: str = Query(default=""),
):
    require_ui_user(request)
    templates = request.app.state.templates

    project_uuid = UUID(project_id) if project_id else None
    brief_uuid = UUID(brief_id) if brief_id else None

    messages: list[dict] = []
    async with async_session_factory() as session:
        stmt = select(Conversation)
        if brief_uuid:
            stmt = stmt.where(Conversation.brief_id == brief_uuid)
        elif project_uuid:
            stmt = stmt.where(Conversation.project_id == project_uuid)
        else:
            return HTMLResponse(
                '<div class="text-center text-base-content/50 py-4">'
                "Select a project or brief to continue.</div>"
            )

        stmt = stmt.order_by(Conversation.created_at.asc()).limit(50)
        result = await session.execute(stmt)
        for conv in result.scalars():
            messages.append({
                "role": conv.role,
                "content": conv.content,
                "timestamp": conv.created_at.strftime("%H:%M"),
                "avatar": None,
            })

    return templates.TemplateResponse(
        "partials/_chat_history.html",
        {
            "request": request,
            "messages": messages,
        },
    )


async def _sse_error(message: str):
    yield f"data: {json.dumps({'error': message})}\n\n"
