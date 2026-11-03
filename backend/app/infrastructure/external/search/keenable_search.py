from typing import Optional
import logging

import httpx

from app.domain.external.search import SearchEngine
from app.domain.models.search import SearchResultItem, SearchResults
from app.domain.models.tool_result import ToolResult

logger = logging.getLogger(__name__)

# Maps generic date_range values to Keenable relative published_after values.
# Keenable has no hour granularity, so past_hour uses the smallest window (1 day).
_DATE_RANGE_MAP = {
    "past_hour": "1d",
    "past_day": "1d",
    "past_week": "7d",
    "past_month": "1mo",
    "past_year": "1y",
}


class KeenableSearchEngine(SearchEngine):
    """Search engine implementation using the Keenable Search API.

    Keenable works without an API key through its public endpoint
    (rate-limited per IP). Set KEENABLE_API_KEY (from https://keenable.ai)
    to use the authenticated endpoint with higher limits.
    Docs: https://docs.keenable.ai/api-reference/search
    """

    BASE_URL = "https://api.keenable.ai/v1/search"
    APP_TITLE = "ai-manus"

    def __init__(
        self,
        api_key: Optional[str] = None,
        transport: Optional[httpx.AsyncBaseTransport] = None,
    ):
        self.api_key = api_key or ""
        self._transport = transport

    def _endpoint_and_headers(self) -> tuple[str, dict]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
            return self.BASE_URL, headers
        headers["X-Keenable-Title"] = self.APP_TITLE
        return f"{self.BASE_URL}/public", headers

    async def search(
        self,
        query: str,
        date_range: Optional[str] = None,
    ) -> ToolResult[SearchResults]:
        """Search web pages using the Keenable Search API.

        Args:
            query: Search query
            date_range: Optional time range filter (past_hour/past_day/past_week/past_month/past_year/all)

        Returns:
            Search results
        """
        payload: dict = {
            "query": query,
            "max_results": 10,
        }

        if date_range and date_range != "all":
            published_after = _DATE_RANGE_MAP.get(date_range)
            if published_after:
                payload["published_after"] = published_after

        url, headers = self._endpoint_and_headers()

        try:
            async with httpx.AsyncClient(timeout=30, transport=self._transport) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()

            items = data.get("results")
            if not isinstance(items, list):
                raise ValueError("Keenable response is missing a results list")

            search_results: list[SearchResultItem] = []
            for item in items:
                link = item.get("url") or ""
                if not link:
                    continue
                search_results.append(
                    SearchResultItem(
                        title=item.get("title") or link,
                        link=link,
                        snippet=item.get("snippet") or item.get("description") or "",
                    )
                )

            results = SearchResults(
                query=query,
                date_range=date_range,
                total_results=len(search_results),
                results=search_results,
            )
            return ToolResult(success=True, data=results)

        except Exception as e:
            logger.error(f"Keenable Search failed: {e}")
            error_results = SearchResults(
                query=query,
                date_range=date_range,
                total_results=0,
                results=[],
            )
            return ToolResult(
                success=False,
                message=f"Keenable Search failed: {e}",
                data=error_results,
            )


if __name__ == "__main__":
    import asyncio
    import os

    async def test():
        engine = KeenableSearchEngine(api_key=os.environ.get("KEENABLE_API_KEY", ""))
        result = await engine.search("Python programming")

        if result.success:
            print(f"Found {len(result.data.results)} results")
            for i, item in enumerate(result.data.results[:5]):
                print(f"{i + 1}. {item.title}")
                print(f"   {item.link}")
                print(f"   {item.snippet[:100]}")
                print()
        else:
            print(f"Search failed: {result.message}")

    asyncio.run(test())
