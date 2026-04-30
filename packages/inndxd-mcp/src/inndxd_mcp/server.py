"""MCP server exposing inndxd agent tools, resources, and prompts."""
from __future__ import annotations

import asyncio
import json
import logging

from mcp.server import Server
from mcp.server.stdio import stdio_server

from inndxd_agents.tools.registry import TOOL_REGISTRY

logger = logging.getLogger(__name__)

server = Server("inndxd-mcp")


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


@server.list_tools()
async def list_tools() -> list[dict]:
    tools = []
    for entry in TOOL_REGISTRY:
        tools.append(
            {
                "name": entry.name,
                "description": getattr(entry.tool, "description", f"inndxd {entry.name} tool"),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query",
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Max results",
                            "default": 5,
                        },
                    },
                    "required": ["query"],
                },
            }
        )
    return tools


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[dict]:
    from inndxd_agents.tools.registry import get_tools_by_name

    tools = get_tools_by_name(name)
    if not tools:
        return [{"type": "text", "text": f"Tool not found: {name}"}]

    tool = tools[0]
    try:
        result = await tool.ainvoke(arguments)
        if hasattr(result, "__iter__") and not isinstance(result, dict):
            text_parts = [
                str(r) if isinstance(r, str) else getattr(r, "text", str(r))
                for r in result
            ]
            return [{"type": "text", "text": "\n\n---\n\n".join(text_parts)}]
        return [{"type": "text", "text": str(result)}]
    except Exception as exc:
        return [{"type": "text", "text": f"Error: {exc}"}]


@server.list_resources()
async def list_resources() -> list[dict]:
    return [
        {
            "uri": "inndxd://projects",
            "name": "Projects",
            "description": "All projects in the database",
            "mimeType": "application/json",
        },
        {
            "uri": "inndxd://data-items/{project_id}",
            "name": "Data Items",
            "description": "Collected data items for a project",
            "mimeType": "application/json",
        },
    ]


@server.read_resource()
async def read_resource(uri: str) -> str:
    from inndxd_core.db import async_session_factory
    from inndxd_core.models.data_item import DataItem
    from inndxd_core.models.project import Project
    from sqlalchemy import select

    if uri == "inndxd://projects":
        async with async_session_factory() as session:
            result = await session.execute(select(Project).limit(50))
            rows = result.scalars().all()
            return json.dumps(
                [
                    {
                        "id": str(r.id),
                        "name": r.name,
                        "description": r.description,
                        "created_at": str(r.created_at),
                    }
                    for r in rows
                ]
            )

    if uri.startswith("inndxd://data-items/"):
        project_id_str = uri.split("/")[-1]
        from uuid import UUID

        try:
            pid = UUID(project_id_str)
        except ValueError:
            return json.dumps({"error": "Invalid project ID"})
        async with async_session_factory() as session:
            result = await session.execute(
                select(DataItem).where(DataItem.project_id == pid).limit(100)
            )
            rows = result.scalars().all()
            return json.dumps(
                [
                    {
                        "id": str(r.id),
                        "source_url": r.source_url,
                        "content_type": r.content_type,
                        "structured_payload": r.structured_payload,
                        "created_at": str(r.created_at),
                    }
                    for r in rows
                ]
            )

    return json.dumps({"error": f"Unknown resource: {uri}"})


@server.list_prompts()
async def list_prompts() -> list[dict]:
    return [
        {
            "name": "research_brief",
            "description": "Generate a research brief for data collection",
            "arguments": [
                {"name": "topic", "description": "Research topic", "required": True},
                {
                    "name": "depth",
                    "description": "Research depth: shallow, medium, deep",
                    "required": False,
                },
            ],
        },
    ]


@server.get_prompt()
async def get_prompt(name: str, arguments: dict | None = None) -> dict:
    if name == "research_brief":
        topic = (arguments or {}).get("topic", "general research")
        depth = (arguments or {}).get("depth", "medium")

        depth_instructions = {
            "shallow": "Perform a quick surface-level search with 3-5 results.",
            "medium": "Perform a thorough search across multiple sources with 10-15 results.",
            "deep": "Perform an exhaustive deep-dive across web, social media, and APIs with 20+ results.",
        }

        return {
            "messages": [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": (
                            f"Research topic: {topic}\n\n"
                            f"Depth: {depth}\n"
                            f"{depth_instructions.get(depth, depth_instructions['medium'])}\n\n"
                            f"Please structure the results with:\n"
                            f"- Source URLs\n"
                            f"- Key findings\n"
                            f"- Dates/timestamps\n"
                            f"- Confidence level (high/medium/low)"
                        ),
                    },
                }
            ],
        }

    return {
        "messages": [
            {"role": "user", "content": {"type": "text", "text": "Prompt not found."}}
        ]
    }


async def run_sse(port: int = 8001):
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.routing import Mount, Route
    import uvicorn

    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        async with sse.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await server.run(
                streams[0], streams[1], server.create_initialization_options()
            )

    starlette_app = Starlette(
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )

    config = uvicorn.Config(starlette_app, port=port, host="0.0.0.0", log_level="info")
    server_instance = uvicorn.Server(config)
    await server_instance.serve()


if __name__ == "__main__":
    import sys

    if "--sse" in sys.argv:
        asyncio.run(run_sse())
    else:
        asyncio.run(main())
