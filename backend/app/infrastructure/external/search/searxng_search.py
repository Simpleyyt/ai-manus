"""SearXNG self-hosted search provider.

Free, open-source, no API key required. Recommended as the default free
search engine in the "Manus gratuito" guide:

    docker run -d -p 8080:8080 searxng/searxng

Enable JSON format in settings.yml: search.formats → ["html", "json"]

SearXNG aggregates results from multiple engines locally, avoiding per-user
quotas. This is the "corpo = container Docker local" piece of the replica.

Environment:
    SEARXNG_URL=http://localhost:8080  (or http://searxng:8080 in Docker Compose)
    SEARCH_PROVIDER=searxng
"""

import logging
from typing import Optional

import httpx

from app.domain.external.search import SearchEngine
from app.domain.models.search import SearchResultItem, SearchResults
from app.domain.models.tool_result import ToolResult

logger = logging.getLogger(__name__)


class SearXNGSearchEngine(SearchEngine):
    """SearXNG search engine via its JSON API."""

    def __init__(self, base_url: str = "http://localhost:8080", engines: str = ""):
        self.base_url = base_url.rstrip("/")
        self.engines = engines

    async def search(
        self,
        query: str,
        date_range: Optional[str] = None,
    ) -> ToolResult[SearchResults]:
        params: dict[str, str] = {
            "q": query,
            "format": "json",
            "categories": "general",
        }
        if self.engines:
            params["engines"] = self.engines

        # SearXNG supports time_range: day, week, month, year
        if date_range and date_range != "all":
            mapping = {
                "past_hour": "day",
                "past_day": "day",
                "past_week": "week",
                "past_month": "month",
                "past_year": "year",
            }
            if date_range in mapping:
                params["time_range"] = mapping[date_range]

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(f"{self.base_url}/search", params=params)
                resp.raise_for_status()
                data = resp.json()

            results = []
            for item in data.get("results", []):
                title = item.get("title", "")
                link = item.get("url", "")
                snippet = item.get("content", "") or item.get("snippet", "")
                if title and link:
                    results.append(
                        SearchResultItem(title=title, link=link, snippet=snippet)
                    )

            search_results = SearchResults(
                query=query,
                date_range=date_range,
                total_results=len(results),
                results=results,
            )
            return ToolResult(success=True, data=search_results)

        except Exception as e:
            logger.error(f"SearXNG search failed (url={self.base_url}): {e}")
            error_results = SearchResults(
                query=query,
                date_range=date_range,
                total_results=0,
                results=[],
            )
            return ToolResult(
                success=False,
                message=f"SearXNG search failed: {e}",
                data=error_results,
            )
