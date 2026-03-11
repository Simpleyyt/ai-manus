from typing import Optional
import logging

import httpx

from app.domain.external.search import SearchEngine
from app.domain.models.search import SearchResultItem, SearchResults
from app.domain.models.tool_result import ToolResult

logger = logging.getLogger(__name__)


class BaiduSearchEngine(SearchEngine):
    """Baidu Qianfan AI Search API implementation (requires API key)"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = (
            "https://qianfan.baidubce.com/v2/ai_search/web_search"
        )

    async def search(
        self,
        query: str,
        date_range: Optional[str] = None,
    ) -> ToolResult[SearchResults]:
        """Search web pages using the Baidu Qianfan AI Search API.

        Args:
            query: Search query (max 72 characters)
            date_range: (Optional) Time range filter for search results

        Returns:
            Search results
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        body: dict = {
            "messages": [{"role": "user", "content": query[:72]}],
            "search_source": "baidu_search_v2",
            "edition": "standard",
            "resource_type_filter": [{"type": "web", "top_k": 20}],
        }

        if date_range and date_range != "all":
            recency_mapping = {
                "past_week": "week",
                "past_month": "month",
                "past_year": "year",
            }
            recency = recency_mapping.get(date_range)
            if recency:
                body["search_filter"] = {
                    "search_recency_filter": recency,
                }
            elif date_range == "past_day":
                body["search_filter"] = {
                    "range": {
                        "pageTime": {"gte": "now-1d/d"},
                    },
                }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.base_url, headers=headers, json=body
                )
                response.raise_for_status()
                data = response.json()

                search_results: list[SearchResultItem] = []

                for item in data.get("search_results", []):
                    title = item.get("title", "")
                    link = item.get("url", "")
                    snippet = item.get("content", "") or item.get(
                        "snippet", ""
                    )
                    if title and link:
                        search_results.append(
                            SearchResultItem(
                                title=title,
                                link=link,
                                snippet=snippet,
                            )
                        )

                results = SearchResults(
                    query=query,
                    date_range=date_range,
                    total_results=len(search_results),
                    results=search_results,
                )
                return ToolResult(success=True, data=results)

        except httpx.HTTPStatusError as e:
            logger.error(
                f"Baidu Search API HTTP error: {e.response.status_code}"
            )
            error_results = SearchResults(
                query=query,
                date_range=date_range,
                total_results=0,
                results=[],
            )
            return ToolResult(
                success=False,
                message=f"Baidu Search API error (HTTP {e.response.status_code})",
                data=error_results,
            )
        except Exception as e:
            logger.error(f"Baidu Search failed: {e}")
            error_results = SearchResults(
                query=query,
                date_range=date_range,
                total_results=0,
                results=[],
            )
            return ToolResult(
                success=False,
                message=f"Baidu Search failed: {e}",
                data=error_results,
            )


if __name__ == "__main__":
    import asyncio
    import os

    async def test():
        api_key = os.environ.get("BAIDU_SEARCH_API_KEY", "")
        if not api_key:
            print("Set BAIDU_SEARCH_API_KEY environment variable to test")
            return
        search_engine = BaiduSearchEngine(api_key=api_key)
        result = await search_engine.search("Python 编程")

        if result.success:
            print(
                f"Search successful! Found {len(result.data.results)} results"
            )
            for i, item in enumerate(result.data.results[:5]):
                print(f"{i + 1}. {item.title}")
                print(f"   {item.link}")
                print(f"   {item.snippet[:100]}")
                print()
        else:
            print(f"Search failed: {result.message}")

    asyncio.run(test())
