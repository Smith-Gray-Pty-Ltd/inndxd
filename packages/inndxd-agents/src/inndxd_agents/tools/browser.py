"""Browser automation tool using Crawl4AI."""

from __future__ import annotations

import re

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from langchain_core.tools import tool
from pydantic import BaseModel, Field


class BrowserInput(BaseModel):
    url: str = Field(description="URL to load and extract content from")
    wait_for: str | None = Field(
        default=None, description="CSS selector to wait for before extraction"
    )
    extract_tables: bool = Field(default=False, description="Whether to extract HTML tables")


class BrowserResult(BaseModel):
    url: str
    title: str | None
    markdown: str
    tables: list[dict] | None = None
    status_code: int


@tool(args_schema=BrowserInput)
async def browser_tool(
    url: str,
    wait_for: str | None = None,
    extract_tables: bool = False,
) -> BrowserResult:
    """Load a web page and extract its content, optionally extracting tables."""
    config = CrawlerRunConfig(
        word_count_threshold=100,
        excluded_tags=["nav", "footer", "script", "style"],
        remove_overlay_elements=True,
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, config=config)

    if not result.success:
        return BrowserResult(
            url=url,
            title=None,
            markdown="",
            status_code=result.status_code,
        )

    tables = None
    if extract_tables and result.markdown:
        tables = _extract_markdown_tables(result.markdown)

    return BrowserResult(
        url=url,
        title=result.metadata.get("title") if result.metadata else None,
        markdown=(result.markdown or "")[:10000],
        tables=tables,
        status_code=result.status_code,
    )


def _extract_markdown_tables(markdown: str) -> list[dict]:
    tables: list[dict] = []
    table_pattern = re.compile(r"\|[^\n]+\|\n\|[-| ]+\|\n((?:\|[^\n]+\|\n?)+)", re.MULTILINE)
    for match in table_pattern.finditer(markdown):
        tables.append({"raw": match.group(0)})
    return tables
