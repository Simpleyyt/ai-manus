from typing import Optional, List, Set
from app.domain.external.search import SearchEngine
from app.domain.services.tools.base import tool, BaseTool
from app.domain.models.tool_result import ToolResult
from app.infrastructure.external.search.bing_search import BingSearchEngine
from app.infrastructure.external.search.baidu_search import BaiduSearchEngine
import logging
import time

logger = logging.getLogger(__name__)

class SearchTool(BaseTool):
    """Search tool class, providing search engine interaction functions"""

    name: str = "search"
    
    def __init__(self, search_engine: Optional[SearchEngine] = None):
        """Initialize search tool class
        
        Args:
            search_engine: Primary search engine service (optional)
        """
        super().__init__()
        self.search_engines = []
        self.searched_queries: Set[str] = set()  # Track searched queries
        self.last_search_time = 0  # Track last search time
        
        # Add the primary search engine if provided
        if search_engine:
            self.search_engines.append(search_engine)
            
        # Add backup search engines
        if not isinstance(search_engine, BingSearchEngine):
            self.search_engines.append(BingSearchEngine())
        if not isinstance(search_engine, BaiduSearchEngine):
            self.search_engines.append(BaiduSearchEngine())
            
        self.current_engine_index = 0
        logger.info(f"Initialized SearchTool with {len(self.search_engines)} search engines")
    
    async def _try_search(self, query: str, date_range: Optional[str] = None) -> ToolResult:
        """Try searching with current engine, switch to next on failure"""
        # Check if query was already searched
        if query in self.searched_queries:
            return ToolResult(
                success=False,
                message=f"已经搜索过该查询: {query}",
                data={"is_duplicate": True}
            )
            
        # Add delay between searches
        current_time = time.time()
        if current_time - self.last_search_time < 3:  # 3 seconds minimum delay
            await time.sleep(3 - (current_time - self.last_search_time))
        
        max_retries = len(self.search_engines)
        retries = 0
        
        while retries < max_retries:
            current_engine = self.search_engines[self.current_engine_index]
            engine_name = current_engine.__class__.__name__
            
            try:
                logger.info(f"Attempting search with {engine_name}")
                result = await current_engine.search(query, date_range)
                if result.success:
                    # Record successful search
                    self.searched_queries.add(query)
                    self.last_search_time = time.time()
                    return result
                logger.warning(f"Search failed with {engine_name}: {result.message}")
            except Exception as e:
                logger.error(f"Error using {engine_name}: {str(e)}")
            
            # Switch to next engine
            self.current_engine_index = (self.current_engine_index + 1) % len(self.search_engines)
            retries += 1
            
            if retries < max_retries:
                logger.info(f"Switching to next search engine")
                await time.sleep(2)  # Add delay before trying next engine
        
        # Record failed search to prevent retrying
        self.searched_queries.add(query)
        return ToolResult(
            success=False,
            message="所有搜索引擎都失败了，请稍后重试或更换搜索关键词",
            data={"all_engines_failed": True}
        )
    
    @tool(
        name="info_search_web",
        description="Search web pages using search engine. Use for obtaining latest information or finding references.",
        parameters={
            "query": {
                "type": "string",
                "description": "Search query in Google search style, using 3-5 keywords."
            },
            "date_range": {
                "type": "string",
                "enum": ["all", "past_hour", "past_day", "past_week", "past_month", "past_year"],
                "description": "(Optional) Time range filter for search results."
            }
        },
        required=["query"]
    )
    async def info_search_web(
        self,
        query: str,
        date_range: Optional[str] = None
    ) -> ToolResult:
        """Search web pages using available search engines
        
        Args:
            query: Search query
            date_range: Optional time range filter
            
        Returns:
            Search results from the first successful engine
        """
        return await self._try_search(query, date_range) 