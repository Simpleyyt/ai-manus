"""Generic custom HTTP search provider.

Allows integrating any third-party search API by configuring the endpoint,
authentication, and field-mapping via environment variables.

Supported request modes
-----------------------
- POST (default): sends a JSON body with the query field
- GET: sends the query as a URL query parameter

Authentication modes
--------------------
- Header-based (default): adds ``{SEARCH_API_KEY_HEADER}: {prefix} {key}`` to the
  request.  Set ``SEARCH_API_KEY_HEADER=X-API-KEY`` and leave the prefix empty for
  services like Serper.dev / Brave.
- Query-param: pass the key as a URL parameter by setting
  ``SEARCH_API_KEY_PARAM=api_key`` (used e.g. by SerpAPI).

Response field mapping
----------------------
The provider expects the API to return JSON.  Configure the field names to
locate the results array and the title/link/snippet inside each item.

Example – Serper.dev (POST)
    SEARCH_PROVIDER=custom
    SEARCH_API_URL=https://google.serper.dev/search
    SEARCH_API_KEY=<your-key>
    SEARCH_API_KEY_HEADER=X-API-KEY
    SEARCH_RESULT_FIELD=organic

Example – SerpAPI (GET)
    SEARCH_PROVIDER=custom
    SEARCH_API_URL=https://serpapi.com/search
    SEARCH_API_KEY=<your-key>
    SEARCH_API_KEY_PARAM=api_key
    SEARCH_API_METHOD=GET
    SEARCH_QUERY_FIELD=q
    SEARCH_RESULT_FIELD=organic_results

Example – Brave Search API (GET)
    SEARCH_PROVIDER=custom
    SEARCH_API_URL=https://api.search.brave.com/res/v1/web/search
    SEARCH_API_KEY=<your-key>
    SEARCH_API_KEY_HEADER=X-Subscription-Token
    SEARCH_API_KEY_HEADER_PREFIX=
    SEARCH_API_METHOD=GET
    SEARCH_QUERY_FIELD=q
    SEARCH_RESULT_FIELD=web.results
    SEARCH_SNIPPET_FIELD=description
"""

from typing import Optional, Any
import logging

import httpx

from app.domain.external.search import SearchEngine
from app.domain.models.search import SearchResultItem, SearchResults
from app.domain.models.tool_result import ToolResult

logger = logging.getLogger(__name__)


def _get_nested(data: dict, path: str) -> Any:
    """Retrieve a value from a nested dict using dot-separated path notation.

    Example: _get_nested({"web": {"results": [...]}}, "web.results") → [...]
    """
    parts = path.split(".")
    current: Any = data
    for part in parts:
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


class CustomSearchEngine(SearchEngine):
    """Generic search engine that calls a user-configured HTTP endpoint.

    All parameters are provided at construction time (sourced from env-vars via
    the factory function in __init__.py).

    Args:
        api_url: Full URL of the search endpoint.
        api_key: API key value.
        api_key_header: HTTP header name used to pass the key (e.g. ``X-API-KEY``
            or ``Authorization``).  Set to empty string to skip header auth.
        api_key_header_prefix: Optional prefix placed before the key value in the
            header (e.g. ``Bearer ``).  Include trailing space when needed.
        api_key_param: URL query-parameter name to send the key as (alternative to
            header auth).  Leave empty to use header auth.
        method: HTTP method – ``POST`` (default) or ``GET``.
        query_field: Field name for the search query in the request body / params.
        result_field: Dot-path to the results array in the JSON response.
        title_field: Field name for the result title.
        link_field: Field name for the result URL.
        snippet_field: Field name for the result snippet / description.
        extra_params: Additional fixed parameters to include in every request.
    """

    def __init__(
        self,
        api_url: str,
        api_key: str = "",
        api_key_header: str = "Authorization",
        api_key_header_prefix: str = "Bearer ",
        api_key_param: str = "",
        method: str = "POST",
        query_field: str = "q",
        result_field: str = "results",
        title_field: str = "title",
        link_field: str = "link",
        snippet_field: str = "snippet",
        extra_params: Optional[dict] = None,
    ):
        self.api_url = api_url
        self.api_key = api_key
        self.api_key_header = api_key_header
        self.api_key_header_prefix = api_key_header_prefix
        self.api_key_param = api_key_param
        self.method = method.upper()
        self.query_field = query_field
        self.result_field = result_field
        self.title_field = title_field
        self.link_field = link_field
        self.snippet_field = snippet_field
        self.extra_params = extra_params or {}

    def _build_headers(self) -> dict:
        headers: dict = {"Content-Type": "application/json"}
        if self.api_key and self.api_key_header:
            headers[self.api_key_header] = f"{self.api_key_header_prefix}{self.api_key}"
        return headers

    def _build_params(self, query: str) -> dict:
        params: dict = {self.query_field: query, **self.extra_params}
        if self.api_key and self.api_key_param:
            params[self.api_key_param] = self.api_key
        return params

    async def search(
        self,
        query: str,
        date_range: Optional[str] = None,
    ) -> ToolResult[SearchResults]:
        """Search using the configured custom API endpoint.

        Args:
            query: Search query
            date_range: Optional time range (ignored unless the API supports it
                via extra_params or a subclass overrides this method)

        Returns:
            Search results
        """
        headers = self._build_headers()
        params = self._build_params(query)

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                if self.method == "GET":
                    response = await client.get(
                        self.api_url, params=params, headers=headers
                    )
                else:
                    response = await client.post(
                        self.api_url, json=params, headers=headers
                    )
                response.raise_for_status()
                data = response.json()

            raw_results = _get_nested(data, self.result_field)
            if not isinstance(raw_results, list):
                logger.warning(
                    f"Custom search: expected list at field '{self.result_field}', "
                    f"got {type(raw_results).__name__}. Response keys: {list(data.keys()) if isinstance(data, dict) else 'N/A'}"
                )
                raw_results = []

            search_results: list[SearchResultItem] = []
            for item in raw_results:
                if not isinstance(item, dict):
                    continue
                title = str(item.get(self.title_field, "")).strip()
                link = str(item.get(self.link_field, "") or item.get("url", "")).strip()
                snippet = str(item.get(self.snippet_field, "")).strip()
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
            logger.error(f"Custom Search failed (url={self.api_url}): {e}")
            error_results = SearchResults(
                query=query,
                date_range=date_range,
                total_results=0,
                results=[],
            )
            return ToolResult(
                success=False,
                message=f"Custom Search failed: {e}",
                data=error_results,
            )


if __name__ == "__main__":
    import asyncio
    import os

    async def test():
        engine = CustomSearchEngine(
            api_url=os.environ.get("SEARCH_API_URL", ""),
            api_key=os.environ.get("SEARCH_API_KEY", ""),
            api_key_header=os.environ.get("SEARCH_API_KEY_HEADER", "Authorization"),
            api_key_header_prefix=os.environ.get("SEARCH_API_KEY_HEADER_PREFIX", "Bearer "),
            api_key_param=os.environ.get("SEARCH_API_KEY_PARAM", ""),
            method=os.environ.get("SEARCH_API_METHOD", "POST"),
            query_field=os.environ.get("SEARCH_QUERY_FIELD", "q"),
            result_field=os.environ.get("SEARCH_RESULT_FIELD", "results"),
            title_field=os.environ.get("SEARCH_TITLE_FIELD", "title"),
            link_field=os.environ.get("SEARCH_LINK_FIELD", "link"),
            snippet_field=os.environ.get("SEARCH_SNIPPET_FIELD", "snippet"),
        )
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
