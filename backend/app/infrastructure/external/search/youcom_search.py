from typing import Optional
import logging

import httpx

from app.domain.external.search import SearchEngine
from app.domain.models.search import SearchResultItem, SearchResults
from app.domain.models.tool_result import ToolResult

logger = logging.getLogger(__name__)

# Maps generic date_range values to You.com fileFilters (time-based search parameters)
_DATE_RANGE_MAP = {
    "past_hour": "h",
    "past_day": "d",
    "past_week": "w",
    "past_month": "m",
    "past_year": "y",
}


class YouComSearchEngine(SearchEngine):
    """Search engine implementation using the You.com Web Search API.

    You.com's Web Search API (https://api.you.com) returns ranked web results
    with snippets, backed by the You.com search index.
    Sign up at https://you.com to get an API key (free tier available).
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.you.com/v1/research"

    async def search(
        self,
        query: str,
        date_range: Optional[str] = None,
    ) -> ToolResult[SearchResults]:
        """Search web pages using the You.com Web Search API.

        Args:
            query: Search query
            date_range: Optional time range filter (past_hour/past_day/past_week/past_month/past_year/all)

        Returns:
            Search results
        """
        params: dict = {
            "query": query,
        }

        if date_range and date_range != "all":
            f = _DATE_RANGE_MAP.get(date_range)
            if f:
                params["fileFilters"] = f

        headers = {
            "X-API-Key": self.api_key,
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    self.base_url,
                    params=params,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()

            search_results: list[SearchResultItem] = []

            for item in data.get("hits", []):
                title = item.get("title", "")
                link = item.get("url", "")
                snippet = item.get("snippet", "")
                if title and link:
                    search_results.append(
                        SearchResultItem(title=title, link=link, snippet=snippet)
                    )

            results = SearchResults(
                query=query,
                date_range=date_range,
                total_results=len(search_results),
                results=search_results,
            )
            return ToolResult(success=True, data=results)

        except Exception as e:
            logger.error(f"You.com Search failed: {e}")
            error_results = SearchResults(
                query=query,
                date_range=date_range,
                total_results=0,
                results=[],
            )
            return ToolResult(
                success=False,
                message=f"You.com Search failed: {e}",
                data=error_results,
            )


if __name__ == "__main__":
    import asyncio
    import os

    async def test():
        key = os.environ.get("YOUCOM_API_KEY", "")
        engine = YouComSearchEngine(api_key=key)
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
