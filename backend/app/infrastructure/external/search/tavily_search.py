from typing import Optional
import logging
from tavily import AsyncTavilyClient
from app.domain.models.tool_result import ToolResult
from app.domain.models.search import SearchResults, SearchResultItem
from app.domain.external.search import SearchEngine

logger = logging.getLogger(__name__)

DATE_RANGE_MAPPING = {
    "past_hour": "day",
    "past_day": "day",
    "past_week": "week",
    "past_month": "month",
    "past_year": "year",
}


class TavilySearchEngine(SearchEngine):
    """Tavily API based search engine implementation"""

    def __init__(self, api_key: str):
        self.client = AsyncTavilyClient(api_key=api_key)

    async def search(
        self,
        query: str,
        date_range: Optional[str] = None,
    ) -> ToolResult[SearchResults]:
        kwargs: dict = {
            "query": query,
            "max_results": 10,
            "search_depth": "basic",
        }

        if date_range and date_range != "all":
            tavily_range = DATE_RANGE_MAPPING.get(date_range)
            if tavily_range:
                kwargs["time_range"] = tavily_range

        try:
            response = await self.client.search(**kwargs)

            search_results = []
            for item in response.get("results", []):
                search_results.append(
                    SearchResultItem(
                        title=item.get("title", ""),
                        link=item.get("url", ""),
                        snippet=item.get("content", ""),
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
            logger.error(f"Tavily Search API call failed: {e}")
            error_results = SearchResults(
                query=query,
                date_range=date_range,
                total_results=0,
                results=[],
            )

            return ToolResult(
                success=False,
                message=f"Tavily Search API call failed: {e}",
                data=error_results,
            )
