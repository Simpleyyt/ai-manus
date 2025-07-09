from typing import Optional
import logging
import httpx
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from app.domain.models.tool_result import ToolResult
from app.domain.external.search import SearchEngine

logger = logging.getLogger(__name__)

class BingSearchEngine(SearchEngine):
    """Bing web search engine implementation using web scraping"""
    
    # 需要过滤的域名列表
    FILTERED_DOMAINS = {
        'zhihu.com',         # 知乎需要登录
        'zhuanlan.zhihu.com',# 知乎专栏
        'juejin.cn',         # 掘金需要登录
        'jianshu.com',       # 简书需要登录
        'csdn.net',          # CSDN需要登录
        'blog.csdn.net',     # CSDN博客
        'weibo.com',         # 微博需要登录
        'douban.com',        # 豆瓣需要登录
        'segmentfault.com',  # 思否需要登录
    }
    
    def __init__(self):
        """Initialize Bing search engine"""
        self.base_url = "https://cn.bing.com/search"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        self.cookies = httpx.Cookies()

    def _clean_text(self, text: str) -> str:
        """Clean text by removing problematic characters and normalizing whitespace"""
        if not text:
            return ""
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        # 保留 Markdown 相关字符，同时移除其他特殊字符
        text = re.sub(r'[^\w\s\-.,?!()[\]{}\'\"#*`~>+=/@|]+', '', text)
        # 移除控制字符，但保留换行和制表符
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
        # 规范化 Markdown 语法
        text = re.sub(r'(\*{2,})', '**', text)  # 规范化加粗
        text = re.sub(r'(_{2,})', '__', text)   # 规范化下划线
        text = re.sub(r'(`{3,})', '```', text)  # 规范化代码块
        return text.strip()
        
    def _trim_text(self, text: str, max_length: int = 200) -> str:
        """Trim text to maximum length while preserving word boundaries"""
        if not text or len(text) <= max_length:
            return text
        return text[:max_length].rsplit(' ', 1)[0] + '...'
        
    def _is_allowed_domain(self, url: str) -> bool:
        """Check if the domain is allowed (not in filtered list)"""
        try:
            domain = urlparse(url).netloc.lower()
            # 移除www.前缀再判断
            if domain.startswith('www.'):
                domain = domain[4:]
            return not any(filtered_domain in domain for filtered_domain in self.FILTERED_DOMAINS)
        except:
            return False
            
    def _modify_query(self, query: str) -> str:
        """Modify query to exclude unwanted sites and prioritize good sources"""
        # 使用Bing搜索语法排除特定网站
        excluded_sites = ' '.join(f'-site:{domain}' for domain in self.FILTERED_DOMAINS)
        # 添加一些优质网站的偏好
        preferred_sites = 'site:python.org OR site:docs.python.org OR site:github.com OR site:stackoverflow.com OR site:microsoft.com OR site:developer.mozilla.org'
        # 如果查询中包含编程相关词汇，添加优质技术网站偏好
        programming_keywords = {'python', 'java', 'javascript', 'code', 'programming', 'api', 'framework', '编程', '开发', '代码'}
        query_words = set(query.lower().split())
        if any(keyword in query_words for keyword in programming_keywords):
            return f"({query}) ({preferred_sites}) {excluded_sites}"
        return f"{query} {excluded_sites}"
        
    async def search(
        self, 
        query: str, 
        date_range: Optional[str] = None,
        max_results: int = 5,
        snippet_length: int = 200
    ) -> ToolResult:
        """Search web pages using Bing web search"""
        # 修改查询以排除不需要的网站
        modified_query = self._modify_query(query)
        
        params = {
            "q": modified_query,
            "count": str(max_results * 2),  # 请求更多结果以补偿被过滤的结果
        }
        
        # Add time range filter
        if date_range and date_range != "all":
            date_mapping = {
                "past_day": "24h",
                "past_week": "7d",
                "past_month": "30d",
                "past_year": "365d"
            }
            if date_range in date_mapping:
                params["filters"] = f"ex1:\"ez{date_mapping[date_range]}\""
        
        try:
            async with httpx.AsyncClient(headers=self.headers, cookies=self.cookies, timeout=30.0, follow_redirects=True) as client:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                
                self.cookies.update(response.cookies)
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                search_results = []
                result_count = 0
                
                result_divs = soup.find_all('li', class_='b_algo') or \
                             soup.find_all('div', class_='b_algo')
                
                for div in result_divs:
                    if result_count >= max_results:
                        break
                        
                    try:
                        title = ""
                        link = ""
                        
                        title_h2 = div.find('h2')
                        if title_h2:
                            title_a = title_h2.find('a')
                            if title_a:
                                title = self._clean_text(title_a.get_text(strip=True))
                                title = self._trim_text(title, max_length=100)
                                link = title_a.get('href', '')
                        
                        if not title or not link:
                            continue
                            
                        # # 检查域名是否允许
                        # if not self._is_allowed_domain(link):
                        #     continue
                            
                        snippet = ""
                        
                        snippet_p = div.find('p')
                        if snippet_p:
                            snippet = self._clean_text(snippet_p.get_text(strip=True))
                            snippet = self._trim_text(snippet, max_length=snippet_length)
                        
                        if not snippet:
                            desc_div = div.find('div', class_=re.compile(r'b_caption|b_snippet'))
                            if desc_div:
                                snippet = self._clean_text(desc_div.get_text(strip=True))
                                snippet = self._trim_text(snippet, max_length=snippet_length)
                        
                        search_results.append({
                            "title": title,
                            "link": link,
                            "snippet": snippet,
                        })
                        result_count += 1
                        
                    except Exception as e:
                        logger.warning(f"Failed to parse search result: {e}")
                        continue
                
                total_results = "0"
                count_div = soup.find('span', class_='sb_count')
                if count_div:
                    count_text = count_div.get_text(strip=True)
                    match = re.search(r'([\d,]+)', count_text)
                    if match:
                        total_results = match.group(1).replace(',', '')
                
                results = {
                    "query": query,
                    "date_range": date_range,
                    "search_info": {
                        "searchTime": "N/A",
                        "formattedTotalResults": total_results,
                        "totalResults": total_results,
                        "returnedResults": len(search_results)
                    },
                    "results": search_results,
                    "total_results": total_results
                }
                
                return ToolResult(success=True, data=results)
                
        except Exception as e:
            logger.error(f"Bing Search failed: {e}")
            return ToolResult(
                success=False,
                message=f"Bing Search failed: {e}",
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
        search_engine = BingSearchEngine()
        # 测试编程相关查询
        print("\n=== Programming Query Test ===")
        result = await search_engine.search("Python requests 教程", max_results=3)
        print(result)
        
        # 测试普通查询
        print("\n=== General Query Test ===")
        result = await search_engine.search("中国历史", max_results=3)
        print(result)
        
    asyncio.run(test()) 