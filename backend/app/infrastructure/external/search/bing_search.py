from typing import Optional
import logging
import httpx
from app.domain.models.tool_result import ToolResult
from app.domain.models.search import SearchResults, SearchResultItem
from app.domain.external.search import SearchEngine

logger = logging.getLogger(__name__)

class BingSearchEngine(SearchEngine):
    """Bing Web Search API v7 implementation"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.bing.microsoft.com/v7.0/search"

    async def search(
        self,
        query: str,
        date_range: Optional[str] = None,
    ) -> ToolResult[SearchResults]:
        """Search web pages using the Bing Web Search API v7

        Args:
            query: Search query, using 3-5 keywords
            date_range: (Optional) Time range filter for search results

        Returns:
            Search results
        """
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
        }

        params: dict = {
            "q": query,
            "count": "20",
            "mkt": "en-US",
            "textDecorations": "false",
            "textFormat": "Raw",
        }

        if date_range and date_range != "all":
            freshness_mapping = {
                "past_day": "Day",
                "past_week": "Week",
                "past_month": "Month",
            }
            freshness = freshness_mapping.get(date_range)
            if freshness:
                params["freshness"] = freshness

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    self.base_url, headers=headers, params=params
                )
                response.raise_for_status()
                data = response.json()

                search_results = []
                web_pages = data.get("webPages", {})
                for item in web_pages.get("value", []):
                    search_results.append(
                        SearchResultItem(
                            title=item.get("name", ""),
                            link=item.get("url", ""),
                            snippet=item.get("snippet", ""),
                        )
                    )

                total_results = int(
                    web_pages.get("totalEstimatedMatches", len(search_results))
                )

                results = SearchResults(
                    query=query,
                    date_range=date_range,
                    total_results=total_results,
                    results=search_results,
                )

                return ToolResult(success=True, data=results)

        except httpx.HTTPStatusError as e:
            logger.error(f"Bing Search API HTTP error: {e.response.status_code}")
            error_results = SearchResults(
                query=query,
                date_range=date_range,
                total_results=0,
                results=[],
            )
            return ToolResult(
                success=False,
                message=f"Bing Search API error (HTTP {e.response.status_code})",
                data=error_results,
            )
        except Exception as e:
            logger.error(f"Bing Search failed: {e}")
            error_results = SearchResults(
                query=query,
                date_range=date_range,
                total_results=0,
                results=[],
            )
            return ToolResult(
                success=False,
                message=f"Bing Search failed: {e}",
                data=error_results,
            )


if __name__ == "__main__":
    import asyncio
    import os

    async def test():
        api_key = os.environ.get("BING_SEARCH_API_KEY", "")
        if not api_key:
            print("Set BING_SEARCH_API_KEY environment variable to test")
            return
        search_engine = BingSearchEngine(api_key=api_key)
        result = await search_engine.search("Python programming")

        if result.success:
            print(f"Search successful! Found {len(result.data.results)} results")
            for i, item in enumerate(result.data.results[:3]):
                print(f"{i+1}. {item.title}")
                print(f"   {item.link}")
                print(f"   {item.snippet}")
                print()
        else:
            print(f"Search failed: {result.message}")

    asyncio.run(test())
