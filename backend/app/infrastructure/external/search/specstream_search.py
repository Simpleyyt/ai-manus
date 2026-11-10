from datetime import date, timedelta
from typing import Optional
import logging

import httpx

from app.domain.external.search import SearchEngine
from app.domain.models.search import SearchResultItem, SearchResults
from app.domain.models.tool_result import ToolResult

logger = logging.getLogger(__name__)

# Maps generic date_range values to a number of days, sent as an after: operator in the query.
# The operator takes a day, so past_hour uses the smallest window (1 day).
_DATE_RANGE_DAYS = {
    "past_hour": 1,
    "past_day": 1,
    "past_week": 7,
    "past_month": 30,
    "past_year": 365,
}


class SpecStreamSearchEngine(SearchEngine):
    """Search engine implementation using the SpecStream Search API.

    Every result carries its source URL, a snippet and, when the page states one,
    its publish date. Get an API key at https://specstream.ai
    Docs: https://api.specstream.ai/openapi.json
    """

    BASE_URL = "https://api.specstream.ai/v1/web-search"

    def __init__(
        self,
        api_key: str,
        transport: Optional[httpx.AsyncBaseTransport] = None,
    ):
        self.api_key = api_key
        self._transport = transport

    async def search(
        self,
        query: str,
        date_range: Optional[str] = None,
    ) -> ToolResult[SearchResults]:
        """Search web pages using the SpecStream Search API.

        Args:
            query: Search query
            date_range: Optional time range filter (past_hour/past_day/past_week/past_month/past_year/all)

        Returns:
            Search results
        """
        q = query
        if date_range and date_range != "all":
            days = _DATE_RANGE_DAYS.get(date_range)
            if days:
                q = f"{query} after:{(date.today() - timedelta(days=days)).isoformat()}"

        params = {
            "q": q,
            "num": 10,
            "speed": "fast",
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=30, transport=self._transport) as client:
                response = await client.get(self.BASE_URL, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()

            sources = (data.get("data") or {}).get("sources")
            if not isinstance(sources, list):
                raise ValueError("SpecStream response is missing data.sources")

            search_results: list[SearchResultItem] = []
            for item in sources:
                link = item.get("url") or ""
                if not link:
                    continue
                search_results.append(
                    SearchResultItem(
                        title=item.get("title") or link,
                        link=link,
                        snippet=item.get("snippet") or "",
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
            logger.error(f"SpecStream Search failed: {e}")
            error_results = SearchResults(
                query=query,
                date_range=date_range,
                total_results=0,
                results=[],
            )
            return ToolResult(
                success=False,
                message=f"SpecStream Search failed: {e}",
                data=error_results,
            )


if __name__ == "__main__":
    import asyncio
    import os

    async def test():
        engine = SpecStreamSearchEngine(api_key=os.environ.get("SPECSTREAM_API_KEY", ""))
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
