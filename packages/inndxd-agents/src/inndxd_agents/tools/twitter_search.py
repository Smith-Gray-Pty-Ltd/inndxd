"""Twitter/X search tool using DuckDuckGo social search."""

from __future__ import annotations

import re
from urllib.parse import quote_plus

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from langchain_core.tools import tool
from pydantic import BaseModel, Field


class TwitterSearchInput(BaseModel):
    query: str = Field(description="Search query string for Twitter/X")
    max_results: int = Field(default=10, ge=1, le=30)


class TweetResult(BaseModel):
    url: str
    author: str | None
    text: str
    timestamp: str | None


@tool(args_schema=TwitterSearchInput)
async def twitter_search_tool(query: str, max_results: int = 10) -> list[TweetResult]:
    """Search Twitter/X for recent posts matching a query.

    Uses DuckDuckGo social search to find tweets.
    """
    encoded = quote_plus(f"{query} site:twitter.com OR site:x.com")
    search_url = f"https://html.duckduckgo.com/html/?q={encoded}"

    results: list[TweetResult] = []
    async with AsyncWebCrawler() as crawler:
        config = CrawlerRunConfig(
            word_count_threshold=100,
            excluded_tags=["nav", "footer", "script", "style"],
            remove_overlay_elements=True,
        )
        page = await crawler.arun(url=search_url, config=config)
        if page.success and page.markdown:
            links = re.findall(
                r"\[([^\]]*)\]\((https?://(?:twitter\.com|x\.com)/[^\s\)]+)\)",
                page.markdown,
            )
            for title, url in links[:max_results]:
                results.append(
                    TweetResult(
                        url=url,
                        author=None,
                        text=title[:500],
                        timestamp=None,
                    )
                )
    return results
