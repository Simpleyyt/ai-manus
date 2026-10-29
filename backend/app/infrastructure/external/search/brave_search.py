"""Brave Search API provider (api.search.brave.com).

Brave Search free tier ended Feb 2026 ($5 monthly credits). Provided as
SEARCH_PROVIDER=brave for users with paid key, mirroring Manus research stack.

Also achievable via SEARCH_PROVIDER=custom with:
    SEARCH_API_URL=https://api.search.brave.com/res/v1/web/search
    SEARCH_API_KEY=your-brave-key
    SEARCH_API_KEY_HEADER=X-Subscription-Token
    SEARCH_API_KEY_HEADER_PREFIX=
    SEARCH_API_METHOD=GET
    SEARCH_RESULT_FIELD=web.results
    SEARCH_SNIPPET_FIELD=description

We provide a native provider for convenience and better error handling.

Environment:
    BRAVE_SEARCH_API_KEY=BSA...
    SEARCH_PROVIDER=brave
"""

import logging
from typing import Optional

import httpx

from app.domain.external.search import SearchEngine
from app.domain.models.search import SearchResultItem, SearchResults
from app.domain.models.tool_result import ToolResult

logger = logging.getLogger(__name__)


class BraveSearchEngine(SearchEngine):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.search.brave.com/res/v1/web/search"

    async def search(
        self,
        query: str,
        date_range: Optional[str] = None,
    ) -> ToolResult[SearchResults]:
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": self.api_key,
        }
        params: dict[str, str] = {"q": query, "count": "10"}
        if date_range and date_range != "all":
            mapping = {
                "past_hour": "pd",
                "past_day": "pd",
                "past_week": "pw",
                "past_month": "pm",
                "past_year": "py",
            }
            # Brave uses freshness param: pd,pw,pm,py
            if date_range in mapping:
                params["freshness"] = mapping[date_range]

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(self.base_url, headers=headers, params=params)
                resp.raise_for_status()
                data = resp.json()

            raw = data.get("web", {}).get("results", []) if isinstance(data.get("web"), dict) else data.get("results", [])
            results = []
            for item in raw:
                title = item.get("title", "")
                link = item.get("url", "")
                snippet = item.get("description", "") or item.get("snippet", "")
                if title and link:
                    results.append(SearchResultItem(title=title, link=link, snippet=snippet))

            search_results = SearchResults(
                query=query, date_range=date_range, total_results=len(results), results=results
            )
            return ToolResult(success=True, data=search_results)

        except Exception as e:
            logger.error(f"Brave search failed: {e}")
            error_results = SearchResults(query=query, date_range=date_range, total_results=0, results=[])
            return ToolResult(success=False, message=f"Brave search failed: {e}", data=error_results)
