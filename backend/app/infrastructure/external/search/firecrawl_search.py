"""Firecrawl search + scrape provider (firecrawl.dev).

Firecrawl provides search and deep scraping with LLM-ready markdown.
In Manus replica, Firecrawl is used both as search engine and as browser
fallback for extracting structured data from pages (complementing browser_use).

Environment:
    FIRECRAWL_API_KEY=fc-...
    SEARCH_PROVIDER=firecrawl

Docs: https://docs.firecrawl.dev
"""

import logging
from typing import Optional

import httpx

from app.domain.external.search import SearchEngine
from app.domain.models.search import SearchResultItem, SearchResults
from app.domain.models.tool_result import ToolResult

logger = logging.getLogger(__name__)


class FirecrawlSearchEngine(SearchEngine):
    """Firecrawl search engine."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.firecrawl.dev/v1/search"

    async def search(
        self,
        query: str,
        date_range: Optional[str] = None,
    ) -> ToolResult[SearchResults]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        body: dict = {
            "query": query,
            "limit": 10,
            "scrapeOptions": {"formats": ["markdown"]},
        }

        if date_range and date_range != "all":
            # Firecrawl supports tbs param for time filtering
            mapping = {
                "past_hour": "qdr:h",
                "past_day": "qdr:d",
                "past_week": "qdr:w",
                "past_month": "qdr:m",
                "past_year": "qdr:y",
            }
            if date_range in mapping:
                body["tbs"] = mapping[date_range]

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(self.base_url, headers=headers, json=body)
                resp.raise_for_status()
                data = resp.json()

            results = []
            for item in data.get("data", []) + data.get("results", []):
                title = item.get("title", "")
                link = item.get("url", "")
                snippet = item.get("description", "") or item.get("markdown", "")[:500] or ""
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

        except httpx.HTTPStatusError as e:
            logger.error(f"Firecrawl HTTP error: {e.response.status_code} {e.response.text[:500]}")
            error_results = SearchResults(query=query, date_range=date_range, total_results=0, results=[])
            return ToolResult(success=False, message=f"Firecrawl error HTTP {e.response.status_code}", data=error_results)
        except Exception as e:
            logger.error(f"Firecrawl search failed: {e}")
            error_results = SearchResults(query=query, date_range=date_range, total_results=0, results=[])
            return ToolResult(success=False, message=f"Firecrawl failed: {e}", data=error_results)
