from typing import Optional
import logging

import httpx

from app.domain.external.search import SearchEngine
from app.domain.models.search import SearchResultItem, SearchResults
from app.domain.models.tool_result import ToolResult

logger = logging.getLogger(__name__)

# Maps generic date_range values to Serper tbs (time-based search) parameters
_DATE_RANGE_MAP = {
    "past_hour": "qdr:h",
    "past_day": "qdr:d",
    "past_week": "qdr:w",
    "past_month": "qdr:m",
    "past_year": "qdr:y",
}


class SerperSearchEngine(SearchEngine):
    """Search engine implementation using the Serper.dev Google Search API.

    Serper.dev provides reliable Google search results via a simple REST API.
    Sign up at https://serper.dev to get an API key (free tier available).
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://google.serper.dev/search"

    async def search(
        self,
        query: str,
        date_range: Optional[str] = None,
    ) -> ToolResult[SearchResults]:
        """Search web pages using Serper.dev Google Search API.

        Args:
            query: Search query
            date_range: Optional time range filter (past_hour/past_day/past_week/past_month/past_year/all)

        Returns:
            Search results
        """
        payload: dict = {
            "q": query,
            "num": 10,
        }

        if date_range and date_range != "all":
            tbs = _DATE_RANGE_MAP.get(date_range)
            if tbs:
                payload["tbs"] = tbs

        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    self.base_url,
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()

            search_results: list[SearchResultItem] = []

            for item in data.get("organic", []):
                title = item.get("title", "")
                link = item.get("link", "")
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
            logger.error(f"Serper Search failed: {e}")
            error_results = SearchResults(
                query=query,
                date_range=date_range,
                total_results=0,
                results=[],
            )
            return ToolResult(
                success=False,
                message=f"Serper Search failed: {e}",
                data=error_results,
            )


if __name__ == "__main__":
    import asyncio
    import os

    async def test():
        key = os.environ.get("SERPER_API_KEY", "")
        engine = SerperSearchEngine(api_key=key)
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
