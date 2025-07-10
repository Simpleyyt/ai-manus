from typing import Optional
import logging
import httpx
import json
import re
from urllib.parse import urlparse
from app.domain.models.tool_result import ToolResult
from app.domain.external.search import SearchEngine

logger = logging.getLogger(__name__)

class QuarkSearch(SearchEngine):
    """Bing web search engine implementation using web scraping"""
    
    # 需要过滤的域名列表
    FILTERED_DOMAINS = {
        # 'zhihu.com',         # 知乎需要登录
        # 'zhuanlan.zhihu.com',# 知乎专栏
        # 'juejin.cn',         # 掘金需要登录
        # 'jianshu.com',       # 简书需要登录
        # 'csdn.net',          # CSDN需要登录
        # 'blog.csdn.net',     # CSDN博客
        # 'weibo.com',         # 微博需要登录
        # 'douban.com',        # 豆瓣需要登录
        # 'segmentfault.com',  # 思否需要登录
    }
    
    def __init__(self):
        self.base_url = "http://192.168.1.204:9018/search"

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
        
    async def search(
        self, 
        query: str, 
        date_range: Optional[str] = None,
        max_results: int = 5,
        snippet_length: int = 200
    ) -> ToolResult:

        params = {
            "query": query
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.base_url, json=params)
                response.raise_for_status()
                result = json.loads(response.text)
                search_output = result.get("result")

                result_count = 0
                search_results = []
                # content["mainText"]
                for content in search_output:
                    title = content["htmlTitle"].replace("<em>", "").replace("</em>", "")
                    link = content["link"]
                    snippet = content["htmlSnippet"].replace("<em>", "").replace("</em>", "")
                    search_results.append({
                        "title": title,
                        "link": link,
                        "snippet": snippet,
                    })
                    result_count += 1

                total_results = "0"
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
        search_engine = QuarkSearch()
        # 测试编程相关查询
        # print("\n=== Programming Query Test ===")
        # result = await search_engine.search("Python requests 教程", max_results=3)
        # print(result)
        
        # 测试普通查询
        print("\n=== General Query Test ===")
        result = await search_engine.search("中国历史", max_results=3)
        print(result)
        
    asyncio.run(test()) 