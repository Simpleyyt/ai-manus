from typing import Optional
import base64
import logging
import re
from urllib.parse import urlparse, parse_qs

from bs4 import BeautifulSoup
from curl_cffi.requests import AsyncSession

from app.domain.external.search import SearchEngine
from app.domain.models.search import SearchResultItem, SearchResults
from app.domain.models.tool_result import ToolResult

logger = logging.getLogger(__name__)


def _decode_bing_redirect(url: str) -> str:
    """Extract the real destination URL from a Bing /ck/a tracking redirect."""
    try:
        parsed = urlparse(url)
        u_values = parse_qs(parsed.query).get("u", [])
        if u_values and u_values[0].startswith("a1"):
            encoded = u_values[0][2:]
            padding = 4 - len(encoded) % 4
            if padding != 4:
                encoded += "=" * padding
            return base64.b64decode(encoded).decode("utf-8", errors="replace")
    except Exception:
        pass
    return url


class BingWebSearchEngine(SearchEngine):
    """Bing search engine implementation using web scraping with browser impersonation"""

    def __init__(self):
        self.base_url = "https://www.bing.com/search"

    async def search(
        self,
        query: str,
        date_range: Optional[str] = None,
    ) -> ToolResult[SearchResults]:
        """Search web pages by scraping Bing search results.

        Args:
            query: Search query, using 3-5 keywords
            date_range: (Optional) Time range filter for search results

        Returns:
            Search results
        """
        params: dict[str, str] = {
            "q": query,
            "count": "20",
        }

        if date_range and date_range != "all":
            freshness_filters = {
                "past_hour": 'ex1:"ez1"',
                "past_day": 'ex1:"ez2"',
                "past_week": 'ex1:"ez3"',
                "past_month": 'ex1:"ez4"',
                "past_year": 'ex1:"ez5"',
            }
            f = freshness_filters.get(date_range)
            if f:
                params["filters"] = f

        try:
            async with AsyncSession(impersonate="chrome") as session:
                response = await session.get(
                    self.base_url, params=params, timeout=30
                )
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")

                search_results: list[SearchResultItem] = []
                for item in soup.find_all("li", class_="b_algo"):
                    try:
                        title, link = "", ""

                        h2 = item.find("h2")
                        if h2:
                            a = h2.find("a")
                            if a:
                                title = a.get_text(strip=True)
                                link = a.get("href", "")

                        if not title:
                            continue

                        if "/ck/a?" in link:
                            link = _decode_bing_redirect(link)

                        snippet = ""
                        for tag in item.find_all(
                            ["p", "div"],
                            class_=re.compile(
                                r"b_lineclamp|b_descript|b_caption|b_paractl"
                            ),
                        ):
                            text = tag.get_text(strip=True)
                            if len(text) > 20:
                                snippet = text
                                break

                        if not snippet:
                            for p in item.find_all("p"):
                                text = p.get_text(strip=True)
                                if len(text) > 20:
                                    snippet = text
                                    break

                        if title and link:
                            search_results.append(
                                SearchResultItem(
                                    title=title,
                                    link=link,
                                    snippet=snippet,
                                )
                            )
                    except Exception as e:
                        logger.warning(f"Failed to parse Bing search result item: {e}")
                        continue

                total_results = 0
                for elem in soup.find_all(
                    ["span", "div"],
                    class_=re.compile(r"sb_count|b_focusTextMedium"),
                ):
                    m = re.search(r"([\d,]+)\s*results?", elem.get_text())
                    if m:
                        try:
                            total_results = int(m.group(1).replace(",", ""))
                            break
                        except ValueError:
                            continue

                results = SearchResults(
                    query=query,
                    date_range=date_range,
                    total_results=total_results or len(search_results),
                    results=search_results,
                )
                return ToolResult(success=True, data=results)

        except Exception as e:
            logger.error(f"Bing Web Search failed: {e}")
            error_results = SearchResults(
                query=query,
                date_range=date_range,
                total_results=0,
                results=[],
            )
            return ToolResult(
                success=False,
                message=f"Bing Web Search failed: {e}",
                data=error_results,
            )


if __name__ == "__main__":
    import asyncio

    async def test():
        engine = BingWebSearchEngine()
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
