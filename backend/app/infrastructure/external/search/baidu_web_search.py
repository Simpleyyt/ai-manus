from typing import Optional
import logging
import re
import time

from bs4 import BeautifulSoup
from curl_cffi.requests import AsyncSession

from app.domain.external.search import SearchEngine
from app.domain.models.search import SearchResultItem, SearchResults
from app.domain.models.tool_result import ToolResult

logger = logging.getLogger(__name__)


class BaiduWebSearchEngine(SearchEngine):
    """Baidu search engine implementation using web scraping with browser impersonation"""

    def __init__(self):
        self.base_url = "https://www.baidu.com/s"

    async def search(
        self,
        query: str,
        date_range: Optional[str] = None,
    ) -> ToolResult[SearchResults]:
        """Search web pages by scraping Baidu search results.

        Args:
            query: Search query, using 3-5 keywords
            date_range: (Optional) Time range filter for search results

        Returns:
            Search results
        """
        params: dict[str, str] = {
            "wd": query,
            "rn": "20",
            "ie": "utf-8",
        }

        if date_range and date_range != "all":
            now = int(time.time())
            offsets = {
                "past_hour": 3600,
                "past_day": 86400,
                "past_week": 604800,
                "past_month": 2592000,
                "past_year": 31536000,
            }
            offset = offsets.get(date_range)
            if offset:
                start = now - offset
                params["gpc"] = f"stf={start},{now}|stftype=2"

        try:
            async with AsyncSession(impersonate="chrome") as session:
                response = await session.get(
                    self.base_url, params=params, timeout=30
                )
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")

                search_results: list[SearchResultItem] = []

                content_left = soup.find("div", id="content_left")
                if not content_left:
                    content_left = soup

                result_divs = content_left.find_all(
                    "div", class_=re.compile(r"\bresult\b")
                )
                if not result_divs:
                    result_divs = content_left.find_all("div", class_="c-container")

                for div in result_divs:
                    try:
                        title, link = "", ""

                        h3 = div.find("h3")
                        if h3:
                            a = h3.find("a")
                            if a:
                                title = a.get_text(strip=True)
                                link = a.get("href", "")

                        if not title:
                            continue

                        mu = div.get("mu", "")
                        if mu and mu.startswith("http"):
                            link = mu

                        if link and "baidu.com/link" in link:
                            data_log = div.get("data-log", "")
                            if data_log:
                                url_match = re.search(
                                    r'"mu":"(https?://[^"]+)"', data_log
                                )
                                if url_match:
                                    link = url_match.group(1)

                        snippet = ""

                        for tag in div.find_all(
                            ["div", "span"],
                            class_=re.compile(
                                r"c-abstract|content-right|c-span-last"
                            ),
                        ):
                            text = tag.get_text(strip=True)
                            if len(text) > 20:
                                snippet = text
                                break

                        if not snippet:
                            for tag in div.find_all(["span", "div", "p"]):
                                cls = " ".join(tag.get("class", []))
                                if any(
                                    kw in cls
                                    for kw in ["abstract", "content", "desc"]
                                ):
                                    text = tag.get_text(strip=True)
                                    if len(text) > 20:
                                        snippet = text
                                        break

                        if not snippet:
                            all_text = div.get_text(separator=" ", strip=True)
                            if title in all_text:
                                all_text = all_text.replace(title, "", 1).strip()
                            if len(all_text) > 30:
                                snippet = all_text[:300]

                        if title and link:
                            search_results.append(
                                SearchResultItem(
                                    title=title,
                                    link=link,
                                    snippet=snippet,
                                )
                            )
                    except Exception as e:
                        logger.warning(
                            f"Failed to parse Baidu search result item: {e}"
                        )
                        continue

                total_results = 0
                for elem in soup.find_all(
                    ["span", "div"],
                    class_=re.compile(r"nums|hint_PIwjx"),
                ):
                    m = re.search(r"约([\d,]+)个", elem.get_text())
                    if m:
                        try:
                            total_results = int(m.group(1).replace(",", ""))
                            break
                        except ValueError:
                            continue

                if not total_results:
                    nums_text = soup.find(
                        string=re.compile(r"百度为您找到相关结果约")
                    )
                    if nums_text:
                        m = re.search(r"约([\d,]+)个", str(nums_text))
                        if m:
                            try:
                                total_results = int(
                                    m.group(1).replace(",", "")
                                )
                            except ValueError:
                                pass

                results = SearchResults(
                    query=query,
                    date_range=date_range,
                    total_results=total_results or len(search_results),
                    results=search_results,
                )
                return ToolResult(success=True, data=results)

        except Exception as e:
            logger.error(f"Baidu Web Search failed: {e}")
            error_results = SearchResults(
                query=query,
                date_range=date_range,
                total_results=0,
                results=[],
            )
            return ToolResult(
                success=False,
                message=f"Baidu Web Search failed: {e}",
                data=error_results,
            )


if __name__ == "__main__":
    import asyncio

    async def test():
        engine = BaiduWebSearchEngine()
        result = await engine.search("Python 编程")

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
