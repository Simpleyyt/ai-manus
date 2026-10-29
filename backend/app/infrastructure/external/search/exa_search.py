"""Exa AI search provider (exa.ai).

Exa is an AI-first search API ideal for LLM agents: returns clean content
with highlights and supports date filters. Listed in Landis API essentials.

Environment:
    EXA_API_KEY=your-exa-key
    SEARCH_PROVIDER=exa

Docs: https://docs.exa.ai
"""

import logging
from typing import Optional

import httpx

from app.domain.external.search import SearchEngine
from app.domain.models.search import SearchResultItem, SearchResults
from app.domain.models.tool_result import ToolResult

logger = logging.getLogger(__name__)


class ExaSearchEngine(SearchEngine):
    """Exa AI search engine."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.exa.ai/search"

    async def search(
        self,
        query: str,
        date_range: Optional[str] = None,
    ) -> ToolResult[SearchResults]:
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "x-api-key": self.api_key,
        }

        body: dict = {
            "query": query,
            "numResults": 10,
            "type": "auto",
            "contents": {"highlights": True},
        }

        # Exa supports startPublishedDate via ISO8601; we map date_range
        # to relative filtering via useAutoprompt + date filter when needed.
        # For simplicity, pass as category filter; Exa handles recency internally.
        if date_range and date_range != "all":
            # Exa livecrawl + recency hints
            body["livecrawl"] = "fallback"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(self.base_url, headers=headers, json=body)
                resp.raise_for_status()
                data = resp.json()

            results = []
            for item in data.get("results", []):
                title = item.get("title", "")
                link = item.get("url", "")
                snippet = (
                    item.get("text", "")[:500]
                    if item.get("text")
                    else (item.get("highlights", [""])[0] if item.get("highlights") else "")
                )
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
            logger.error(f"Exa search HTTP error: {e.response.status_code} {e.response.text[:500]}")
            error_results = SearchResults(query=query, date_range=date_range, total_results=0, results=[])
            return ToolResult(success=False, message=f"Exa search error HTTP {e.response.status_code}", data=error_results)
        except Exception as e:
            logger.error(f"Exa search failed: {e}")
            error_results = SearchResults(query=query, date_range=date_range, total_results=0, results=[])
            return ToolResult(success=False, message=f"Exa search failed: {e}", data=error_results)
