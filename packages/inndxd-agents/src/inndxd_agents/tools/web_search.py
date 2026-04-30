from __future__ import annotations

import re

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from langchain_core.tools import tool
from pydantic import BaseModel, Field


class WebSearchInput(BaseModel):
    query: str = Field(description="Search query string")
    max_results: int = Field(default=5, ge=1, le=20)


class WebSearchResult(BaseModel):
    url: str
    title: str | None
    text: str
    status_code: int


def _build_search_urls(query: str, n: int) -> list[str]:
    from urllib.parse import quote_plus

    encoded = quote_plus(query)
    return [f"https://html.duckduckgo.com/html/?q={encoded}"]


@tool(args_schema=WebSearchInput)
async def web_search_tool(query: str, max_results: int = 5) -> list[WebSearchResult]:
    """Search the web using DuckDuckGo and extract clean markdown content from results.

    Args:
        query: The search query string.
        max_results: Maximum number of result pages to crawl (1-20).

    Returns:
        A list of search results with URL, title, extracted text, and status code.
    """
    search_url = _build_search_urls(query, max_results)[0]
    results: list[WebSearchResult] = []

    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig(
            word_count_threshold=200,
            excluded_tags=["nav", "footer", "script", "style"],
            remove_overlay_elements=True,
            cache_mode="ENABLED",
        )
        page_result = await crawler.arun(url=search_url, config=config)

        if page_result.success:
            raw_text = page_result.markdown or ""
            result_links = _extract_result_links(raw_text)
            page_urls = result_links[:max_results]

            if not page_urls:
                return results

            crawl_results = await crawler.arun_many(
                urls=page_urls,
                config=config,
            )

            for cr in crawl_results:
                if cr.success:
                    results.append(
                        WebSearchResult(
                            url=cr.url,
                            title=cr.metadata.get("title") if cr.metadata else None,
                            text=(cr.markdown or "")[:5000],
                            status_code=cr.status_code,
                        )
                    )

    return results


def _extract_result_links(markdown: str) -> list[str]:
    urls: list[str] = []
    for match in re.finditer(r"\[([^\]]*)\]\((https?://[^\s\)]+)\)", markdown):
        url = match.group(2)
        if not _is_internal_duckduckgo(url):
            urls.append(url)
    return urls


def _is_internal_duckduckgo(url: str) -> bool:
    skip_domains = {"duckduckgo.com", "duck.co"}
    return any(domain in url for domain in skip_domains)
