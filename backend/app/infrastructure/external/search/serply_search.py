from typing import Optional
import logging

import httpx

from app.domain.external.search import SearchEngine
from app.domain.models.search import SearchResultItem, SearchResults
from app.domain.models.tool_result import ToolResult

logger = logging.getLogger(__name__)

# Maps generic date_range values to Google tbs (time-based search) parameters,
# which Serply passes through to the underlying Google query.
_DATE_RANGE_MAP = {
    "past_hour": "qdr:h",
    "past_day": "qdr:d",
    "past_week": "qdr:w",
    "past_month": "qdr:m",
    "past_year": "qdr:y",
}


class SerplySearchEngine(SearchEngine):
    """Search engine implementation using the Serply Google Search API.

    Serply (https://serply.io) returns structured Google search results via a
    simple REST API. Sign up at https://serply.io to get an API key; the API
    reference is at https://serply.io/docs.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.serply.io/v1/search"

    async def search(
        self,
        query: str,
        date_range: Optional[str] = None,
    ) -> ToolResult[SearchResults]:
        """Search web pages using the Serply Google Search API.

        Args:
            query: Search query
            date_range: Optional time range filter (past_hour/past_day/past_week/past_month/past_year/all)

        Returns:
            Search results
        """
        params: dict = {
            "q": query,
            "num": 10,
        }

        if date_range and date_range != "all":
            tbs = _DATE_RANGE_MAP.get(date_range)
            if tbs:
                params["tbs"] = tbs

        headers = {
            "X-Api-Key": self.api_key,
            "Accept": "application/json",
            "User-Agent": "ai-manus (+https://github.com/Simpleyyt/ai-manus)",
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

            for item in data.get("results", []):
                title = item.get("title", "")
                link = item.get("link", "")
                snippet = item.get("description", "")
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
            logger.error(f"Serply Search failed: {e}")
            error_results = SearchResults(
                query=query,
                date_range=date_range,
                total_results=0,
                results=[],
            )
            return ToolResult(
                success=False,
                message=f"Serply Search failed: {e}",
                data=error_results,
            )


if __name__ == "__main__":
    import asyncio
    import os

    async def test():
        key = os.environ.get("SERPLY_API_KEY", "")
        engine = SerplySearchEngine(api_key=key)
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
