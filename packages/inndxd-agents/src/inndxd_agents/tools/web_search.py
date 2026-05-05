from __future__ import annotations

from urllib.parse import parse_qs, quote_plus, urlparse

import httpx
from bs4 import BeautifulSoup
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


@tool(args_schema=WebSearchInput)
async def web_search_tool(query: str, max_results: int = 5) -> list[WebSearchResult]:
    """Search the web using DuckDuckGo HTML endpoint and extract content from results."""
    search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"

    links = []
    async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
        resp = await client.get(
            search_url,
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"},
        )
        soup = BeautifulSoup(resp.text, "html.parser")
        for result in soup.select(".result__a, .result__title .result__url"):
            raw_href = result.get("href", "") or ""
            if raw_href.startswith("//"):
                raw_href = "https:" + raw_href
            if "/l/?uddg=" in raw_href:
                parsed = urlparse(raw_href)
                raw_href = parse_qs(parsed.query).get("uddg", [raw_href])[0]
            if raw_href.startswith("http") and len(links) < max_results:
                links.append(raw_href)

    if not links:
        return []

    results = []
    try:
        async with AsyncWebCrawler() as crawler:
            config = CrawlerRunConfig(
                word_count_threshold=100,
                excluded_tags=["nav", "footer", "script", "style"],
                remove_overlay_elements=True,
                cache_mode="ENABLED",
            )
            crawl_results = await crawler.arun_many(urls=links, config=config)
            for cr in crawl_results:
                if cr.success:
                    results.append(
                        WebSearchResult(
                            url=cr.url,
                            title=cr.metadata.get("title") if cr.metadata else None,
                            text=(cr.markdown or "")[:8000],
                            status_code=cr.status_code,
                        )
                    )
    except Exception:
        pass

    if not results:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            for url in links:
                try:
                    resp = await client.get(
                        url,
                        headers={"User-Agent": "Mozilla/5.0 (compatible; InndxdBot/1.0)"},
                    )
                    soup = BeautifulSoup(resp.text, "html.parser")
                    text = soup.get_text(" ", strip=True)[:3000]
                    title_tag = soup.find("title")
                    results.append(
                        WebSearchResult(
                            url=url,
                            title=title_tag.text.strip() if title_tag else None,
                            text=text,
                            status_code=resp.status_code,
                        )
                    )
                except Exception:
                    pass

    return results
