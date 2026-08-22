from typing import Optional

from pydantic import BaseModel, Field

from app.domain.external.search import SearchEngine
from app.domain.models.tool_result import ToolResult
from app.domain.services.tools.base import BaseToolkit, Tool


class InfoSearchWebTool(Tool):
    name = "info_search_web"
    description = (
        "Search web pages using search engine. Use for obtaining latest "
        "information or finding references."
    )

    class Args(BaseModel):
        query: str = Field(description="Search query in Google search style, using 3-5 keywords.")
        date_range: Optional[str] = Field(
            default=None,
            description="(Optional) Time range filter for search results.",
        )

    async def run(self, query: str, date_range: Optional[str] = None) -> ToolResult:
        return await self.toolkit.search_engine.search(query, date_range)


class SearchToolkit(BaseToolkit):
    """Search tool class, providing search engine interaction functions"""

    name: str = "search"
    instructions: str = """
- Prefer the dedicated search tool over browsing to a search engine results page
- Snippets are not valid sources; open the original pages via browser before citing
- Visit multiple result URLs for comprehensive information or cross-validation
- Search step by step: query attributes of a single entity separately, handle entities one by one
- Authoritative web information takes priority over internal model knowledge
"""
    tool_types = [InfoSearchWebTool]

    def __init__(self, search_engine: SearchEngine):
        """Initialize search tool class

        Args:
            search_engine: Search engine service
        """
        self.search_engine = search_engine
        super().__init__()
