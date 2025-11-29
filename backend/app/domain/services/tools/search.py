from typing import Optional
from app.domain.external.search import SearchEngine
from app.domain.services.tools.base import BaseToolkit
from langchain.tools import tool
from app.domain.models.tool_result import ToolResult

class SearchToolkit(BaseToolkit):
    """Search tool class, providing search engine interaction functions"""

    name: str = "search"
    
    def __init__(self, search_engine: SearchEngine):
        """Initialize search tool class
        
        Args:
            search_engine: Search engine service
        """
        super().__init__()
        self.search_engine = search_engine
    
    @tool(parse_docstring=True)
    async def info_search_web(
        self,
        query: str,
        date_range: Optional[str] = None
    ) -> ToolResult:
        """Search web pages using search engine. Use for obtaining latest information or finding references.
        
        Args:
            query: Search query in Google search style, using 3-5 keywords.
            date_range: (Optional) Time range filter for search results.
        """
        return await self.search_engine.search(query, date_range) 