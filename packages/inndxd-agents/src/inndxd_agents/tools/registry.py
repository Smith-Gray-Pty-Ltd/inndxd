"""Tool registry v2 with capability-based tool selection."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field

from inndxd_agents.tools import (
    api_fetch_tool,
    browser_tool,
    db_query_tool,
    twitter_search_tool,
    web_search_tool,
)


@dataclass
class ToolEntry:
    tool: Callable
    name: str
    capabilities: list[str] = field(default_factory=list)


TOOL_REGISTRY: list[ToolEntry] = [
    ToolEntry(
        tool=web_search_tool,
        name="web_search",
        capabilities=["web", "search", "general"],
    ),
    ToolEntry(
        tool=twitter_search_tool,
        name="twitter_search",
        capabilities=["social", "twitter", "search"],
    ),
    ToolEntry(
        tool=api_fetch_tool,
        name="api_fetch",
        capabilities=["api", "http", "fetch"],
    ),
    ToolEntry(
        tool=browser_tool,
        name="browser",
        capabilities=["browser", "web", "scrape"],
    ),
    ToolEntry(
        tool=db_query_tool,
        name="db_query",
        capabilities=["database", "internal", "query"],
    ),
]


def get_tools_by_capability(*capabilities: str) -> list[Callable]:
    result: list[Callable] = []
    for entry in TOOL_REGISTRY:
        if all(c in entry.capabilities for c in capabilities):
            result.append(entry.tool)
    return result


def get_tools_by_name(*names: str) -> list[Callable]:
    result: list[Callable] = []
    for entry in TOOL_REGISTRY:
        if entry.name in names:
            result.append(entry.tool)
    return result


def get_all_tools() -> list[Callable]:
    return [entry.tool for entry in TOOL_REGISTRY]


async def invoke_tool_with_timeout(
    tool: Callable, input_dict: dict, timeout_seconds: float = 30.0
) -> dict:
    try:
        return await asyncio.wait_for(
            tool.ainvoke(input_dict),
            timeout=timeout_seconds,
        )
    except TimeoutError:
        return {"error": f"Tool {tool.name} timed out after {timeout_seconds}s"}
