from typing import Optional, Protocol
from app.domain.models.tool_result import ToolResult

class Browser(Protocol):
    """Browser service gateway interface"""
    
    async def view_page(self) -> ToolResult:
        """View current page content"""
        ...
    
    async def navigate(self, url: str) -> ToolResult:
        """Navigate to specified URL"""
        ...
    
    async def restart(self, url: str) -> ToolResult:
        """Restart browser and navigate to specified URL"""
        ...
    
    async def click(
        self,
        index: Optional[int] = None,
        coordinate_x: Optional[float] = None,
        coordinate_y: Optional[float] = None
    ) -> ToolResult:
        """Click element"""
        ...
    
    async def input(
        self,
        text: str,
        press_enter: bool,
        index: Optional[int] = None,
        coordinate_x: Optional[float] = None,
        coordinate_y: Optional[float] = None
    ) -> ToolResult:
        """Input text"""
        ...
    
    async def move_mouse(
        self,
        coordinate_x: float,
        coordinate_y: float
    ) -> ToolResult:
        """Move mouse"""
        ...
    
    async def press_key(self, key: str) -> ToolResult:
        """Simulate key press"""
        ...
    
    async def select_option(
        self,
        index: int,
        option: int
    ) -> ToolResult:
        """Select dropdown option"""
        ...
    
    async def scroll_up(
        self,
        to_top: Optional[bool] = None
    ) -> ToolResult:
        """Scroll up"""
        ...
    
    async def scroll_down(
        self,
        to_bottom: Optional[bool] = None
    ) -> ToolResult:
        """Scroll down"""
        ...
    
    async def screenshot(
        self,
        full_page: Optional[bool] = False
    ) -> bytes:
        """Take a screenshot of the current page"""
        ...
    
    async def console_exec(self, javascript: str) -> ToolResult:
        """Execute JavaScript code"""
        ...
    
    async def console_view(self, max_lines: Optional[int] = None) -> ToolResult:
        """View console output"""
        ...
