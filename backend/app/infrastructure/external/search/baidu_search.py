from typing import Optional
import logging
import httpx
import re
from urllib.parse import quote
from bs4 import BeautifulSoup
from app.domain.models.tool_result import ToolResult
from app.domain.external.search import SearchEngine

logger = logging.getLogger(__name__)

class BaiduSearchEngine(SearchEngine):
    """Baidu web search engine implementation using web scraping"""
    
    def __init__(self):
        """Initialize Baidu search engine"""
        self.base_url = "https://www.baidu.com/s"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
        }
        # Initialize cookies with the provided cookie string
        self.cookies = httpx.Cookies()
        
    async def search(
        self, 
        query: str, 
        date_range: Optional[str] = None
    ) -> ToolResult:
        """Search web pages using Baidu web search
        
        Args:
            query: Search query, using 3-5 keywords
            date_range: (Optional) Time range filter for search results
            
        Returns:
            Search results
        """
        params = {
            "wd": query,
            #"pn": "0",  # Page number (0 for first page)
            #"rn": "10",  # Number of results per page
        }
        
        # Add time range filter
        if date_range and date_range != "all":
            # Convert date_range to time range parameters supported by Baidu
            date_mapping = {
                "past_day": "1",
                "past_week": "2", 
                "past_month": "3",
                "past_year": "4"
            }
            if date_range in date_mapping:
                params["gpc"] = f"stf={date_mapping[date_range]}"
        
        try:
            async with httpx.AsyncClient(headers=self.headers, cookies=self.cookies, timeout=30.0) as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                
                # Update cookies with response cookies in memory
                self.cookies.update(response.cookies)
                
                # Parse HTML content
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract search results
                search_results = []
                
                # Try different selectors for Baidu search results
                result_divs = soup.find_all('div', class_='result') or \
                             soup.find_all('div', class_='result-op') or \
                             soup.find_all('div', class_='c-container') or \
                             soup.find_all('div', attrs={'mu': True}) or \
                             soup.find_all('div', attrs={'data-log': True})
                
                for div in result_divs:
                    try:
                        # Extract title - try multiple approaches
                        title = ""
                        link = ""
                        
                        # Method 1: Standard h3 > a structure
                        title_tag = div.find('h3')
                        if title_tag:
                            title_a = title_tag.find('a')
                            if title_a:
                                title = title_a.get_text(strip=True)
                                link = title_a.get('href', '')
                        
                        # Method 2: Try direct a tag with title-like classes
                        if not title:
                            title_links = div.find_all('a', class_=re.compile(r'title|link'))
                            for a in title_links:
                                if a.get_text(strip=True):
                                    title = a.get_text(strip=True)
                                    link = a.get('href', '')
                                    break
                        
                        # Method 3: Try any a tag with substantial text
                        if not title:
                            all_links = div.find_all('a')
                            for a in all_links:
                                text = a.get_text(strip=True)
                                if len(text) > 10 and not text.startswith('http'):
                                    title = text
                                    link = a.get('href', '')
                                    break
                        
                        if not title:
                            continue
                        
                        # Extract snippet - try multiple approaches
                        snippet = ""
                        
                        # Method 1: Look for abstract/content classes
                        snippet_divs = div.find_all(['div', 'span'], class_=re.compile(r'abstract|content|desc'))
                        if snippet_divs:
                            snippet = snippet_divs[0].get_text(strip=True)
                        
                        # Method 2: Look for common text containers
                        if not snippet:
                            text_containers = div.find_all(['div', 'span', 'p'], class_=re.compile(r'c-span|c-abstract'))
                            for container in text_containers:
                                text = container.get_text(strip=True)
                                if len(text) > 20:
                                    snippet = text
                                    break
                        
                        # Method 3: Get any substantial text from the div
                        if not snippet:
                            all_text = div.get_text(strip=True)
                            # Extract first sentence-like text
                            sentences = re.split(r'[。！？\n]', all_text)
                            for sentence in sentences:
                                if len(sentence.strip()) > 20:
                                    snippet = sentence.strip()
                                    break
                        
                        # Clean up the link if it's a Baidu redirect
                        if link.startswith('/link?url='):
                            url_match = re.search(r'url=([^&]+)', link)
                            if url_match:
                                link = url_match.group(1)
                        elif link.startswith('/'):
                            link = 'https://www.baidu.com' + link
                        
                        if title and link:
                            search_results.append({
                                "title": title,
                                "link": link,
                                "snippet": snippet,
                            })
                    except Exception as e:
                        logger.warning(f"Failed to parse search result: {e}")
                        continue
                
                # Extract total results count
                total_results = "0"
                results_nums = soup.find_all(string=re.compile(r'百度为您找到相关结果约'))
                if results_nums:
                    match = re.search(r'约([\d,]+)个结果', results_nums[0])
                    if match:
                        total_results = match.group(1).replace(',', '')
                
                # Build return result
                results = {
                    "query": query,
                    "date_range": date_range,
                    "search_info": {
                        "searchTime": "N/A",
                        "formattedTotalResults": total_results,
                        "totalResults": total_results
                    },
                    "results": search_results,
                    "total_results": total_results
                }
                
                return ToolResult(success=True, data=results)
                
        except Exception as e:
            logger.error(f"Baidu Search failed: {e}")
            return ToolResult(
                success=False,
                message=f"Baidu Search failed: {e}",
                data={
                    "query": query,
                    "date_range": date_range,
                    "results": []
                }
            )


# Simple test
if __name__ == "__main__":
    import asyncio
    
    async def test():
        search_engine = BaiduSearchEngine()
        result = await search_engine.search("Python 编程")
        
        if result.success:
            print(f"Search successful! Found {len(result.data['results'])} results")
            for i, item in enumerate(result.data['results'][:3]):
                print(f"{i+1}. {item['title']}")
                print(f"   {item['link']}")
                print()
        else:
            print(f"Search failed: {result.message}")
    
    asyncio.run(test())