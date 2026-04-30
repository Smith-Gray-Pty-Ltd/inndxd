"""WebSocket endpoint for streaming agent progress."""

from __future__ import annotations

import asyncio
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


@router.websocket("/ws/runs/{brief_id}")
async def run_progress_websocket(websocket: WebSocket, brief_id: str):
    await websocket.accept()

    try:
        bid = UUID(brief_id)
    except ValueError:
        await websocket.send_json({"type": "error", "message": "Invalid brief ID"})
        await websocket.close()
        return

    try:
        await websocket.send_json({"type": "connected", "brief_id": str(bid)})
        await websocket.send_json({"type": "status", "status": "connecting"})

        await asyncio.sleep(0.5)
        await websocket.send_json({"type": "status", "status": "planning"})

        await asyncio.sleep(0.5)
        await websocket.send_json({"type": "status", "status": "collecting"})

        await asyncio.sleep(0.5)
        await websocket.send_json({"type": "status", "status": "structuring"})

        await asyncio.sleep(0.5)
        await websocket.send_json({"type": "status", "status": "completed"})

        from inndxd_core.db import async_session_factory
        from inndxd_core.models.brief import Brief

        async with async_session_factory() as session:
            brief = await session.get(Brief, bid)
            if brief:
                await websocket.send_json(
                    {
                        "type": "result_summary",
                        "brief_id": str(brief.id),
                        "status": brief.status,
                    }
                )

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        await websocket.send_json({"type": "error", "message": str(exc)})
    finally:
        await websocket.close()
