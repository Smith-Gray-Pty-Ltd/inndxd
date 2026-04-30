"""API fetch tool for REST and GraphQL endpoints."""

from __future__ import annotations

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field


class ApiFetchInput(BaseModel):
    url: str = Field(description="Full API endpoint URL")
    method: str = Field(default="GET", description="HTTP method: GET, POST, PUT, DELETE")
    headers: dict[str, str] | None = Field(default=None, description="HTTP headers")
    body: str | None = Field(default=None, description="Request body as JSON string")


class ApiFetchResult(BaseModel):
    url: str
    status_code: int
    response_text: str
    error: str | None = None


@tool(args_schema=ApiFetchInput)
async def api_fetch_tool(
    url: str,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    body: str | None = None,
) -> ApiFetchResult:
    """Fetch data from a REST or GraphQL API endpoint."""
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        try:
            response = await client.request(
                method=method.upper(),
                url=url,
                headers=headers or {},
                content=body,
            )
            return ApiFetchResult(
                url=url,
                status_code=response.status_code,
                response_text=response.text[:10000],
            )
        except Exception as e:
            return ApiFetchResult(
                url=url,
                status_code=0,
                response_text="",
                error=str(e),
            )
