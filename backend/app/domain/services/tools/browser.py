from typing import Optional
from app.domain.external.browser import Browser
from app.domain.services.tools.base import tool, BaseTool
from app.domain.models.tool_result import ToolResult

class BrowserTool(BaseTool):
    """Browser tool class, providing browser interaction functions"""

    name: str = "browser"
    
    def __init__(self, browser: Browser):
        """Initialize browser tool class
        
        Args:
            browser: Browser service
        """
        super().__init__()
        self.browser = browser
    
    @tool(
        name="browser_view",
        description="View content of the current browser page. Use for checking the latest state of previously opened pages.",
        parameters={},
        required=[]
    )
    async def browser_view(self) -> ToolResult:
        """View current browser page content
        
        Returns:
            Browser page content
        """
        return await self.browser.view_page()
    
    @tool(
        name="browser_navigate",
        description="Navigate browser to specified URL. Use when accessing new pages is needed.",
        parameters={
            "url": {
                "type": "string",
                "description": "Complete URL to visit. Must include protocol prefix."
            }
        },
        required=["url"]
    )
    async def browser_navigate(self, url: str) -> ToolResult:
        """Navigate browser to specified URL
        
        Args:
            url: Complete URL address, must include protocol prefix
            
        Returns:
            Navigation result
        """
        return await self.browser.navigate(url)
    
    @tool(
        name="browser_restart",
        description="Restart browser and navigate to specified URL. Use when browser state needs to be reset.",
        parameters={
            "url": {
                "type": "string",
                "description": "Complete URL to visit after restart. Must include protocol prefix."
            }
        },
        required=["url"]
    )
    async def browser_restart(self, url: str) -> ToolResult:
        """Restart browser and navigate to specified URL
        
        Args:
            url: Complete URL address to visit after restart, must include protocol prefix
            
        Returns:
            Restart result
        """
        return await self.browser.restart(url)
    
    @tool(
        name="browser_click",
        description="Click on elements in the current browser page. Use when clicking page elements is needed.",
        parameters={
            "index": {
                "type": "integer",
                "description": "(Optional) Index number of the element to click"
            },
            "coordinate_x": {
                "type": "number",
                "description": "(Optional) X coordinate of click position"
            },
            "coordinate_y": {
                "type": "number",
                "description": "(Optional) Y coordinate of click position"
            }
        },
        required=[]
    )
    async def browser_click(
        self,
        index: Optional[int] = None,
        coordinate_x: Optional[float] = None,
        coordinate_y: Optional[float] = None
    ) -> ToolResult:
        """Click on elements in the current browser page
        
        Args:
            index: (Optional) Index number of the element to click
            coordinate_x: (Optional) X coordinate of click position
            coordinate_y: (Optional) Y coordinate of click position
            
        Returns:
            Click result
        """
        return await self.browser.click(index, coordinate_x, coordinate_y)
    
    @tool(
        name="browser_input",
        description="Overwrite text in editable elements on the current browser page. Use when filling content in input fields.",
        parameters={
            "index": {
                "type": "integer",
                "description": "(Optional) Index number of the element to overwrite text"
            },
            "coordinate_x": {
                "type": "number",
                "description": "(Optional) X coordinate of the element to overwrite text"
            },
            "coordinate_y": {
                "type": "number",
                "description": "(Optional) Y coordinate of the element to overwrite text"
            },
            "text": {
                "type": "string",
                "description": "Complete text content to overwrite"
            },
            "press_enter": {
                "type": "boolean",
                "description": "Whether to press Enter key after input"
            }
        },
        required=["text", "press_enter"]
    )
    async def browser_input(
        self,
        text: str,
        press_enter: bool,
        index: Optional[int] = None,
        coordinate_x: Optional[float] = None,
        coordinate_y: Optional[float] = None
    ) -> ToolResult:
        """Overwrite text in editable elements on the current browser page
        
        Args:
            text: Complete text content to overwrite
            press_enter: Whether to press Enter key after input
            index: (Optional) Index number of the element to overwrite text
            coordinate_x: (Optional) X coordinate of the element to overwrite text
            coordinate_y: (Optional) Y coordinate of the element to overwrite text
            
        Returns:
            Input result
        """
        return await self.browser.input(text, press_enter, index, coordinate_x, coordinate_y)
    
    @tool(
        name="browser_move_mouse",
        description="Move cursor to specified position on the current browser page. Use when simulating user mouse movement.",
        parameters={
            "coordinate_x": {
                "type": "number",
                "description": "X coordinate of target cursor position"
            },
            "coordinate_y": {
                "type": "number",
                "description": "Y coordinate of target cursor position"
            }
        },
        required=["coordinate_x", "coordinate_y"]
    )
    async def browser_move_mouse(
        self,
        coordinate_x: float,
        coordinate_y: float
    ) -> ToolResult:
        """Move mouse cursor to specified position on the current browser page
        
        Args:
            coordinate_x: X coordinate of target cursor position
            coordinate_y: Y coordinate of target cursor position
            
        Returns:
            Move result
        """
        return await self.browser.move_mouse(coordinate_x, coordinate_y)
    
    @tool(
        name="browser_press_key",
        description="Simulate key press in the current browser page. Use when specific keyboard operations are needed.",
        parameters={
            "key": {
                "type": "string",
                "description": "Key name to simulate (e.g., Enter, Tab, ArrowUp), supports key combinations (e.g., Control+Enter)."
            }
        },
        required=["key"]
    )
    async def browser_press_key(
        self,
        key: str
    ) -> ToolResult:
        """Simulate key press in the current browser page
        
        Args:
            key: Key name to simulate (e.g., Enter, Tab, ArrowUp), supports key combinations (e.g., Control+Enter)
            
        Returns:
            Key press result
        """
        return await self.browser.press_key(key)
    
    @tool(
        name="browser_select_option",
        description="Select specified option from dropdown list element in the current browser page. Use when selecting dropdown menu options.",
        parameters={
            "index": {
                "type": "integer",
                "description": "Index number of the dropdown list element"
            },
            "option": {
                "type": "integer",
                "description": "Option number to select, starting from 0."
            }
        },
        required=["index", "option"]
    )
    async def browser_select_option(
        self,
        index: int,
        option: int
    ) -> ToolResult:
        """Select specified option from dropdown list element in the current browser page
        
        Args:
            index: Index number of the dropdown list element
            option: Option number to select, starting from 0
            
        Returns:
            Selection result
        """
        return await self.browser.select_option(index, option)
    
    @tool(
        name="browser_scroll_up",
        description="Scroll up the current browser page. Use when viewing content above or returning to page top.",
        parameters={
            "to_top": {
                "type": "boolean",
                "description": "(Optional) Whether to scroll directly to page top instead of one viewport up."
            }
        },
        required=[]
    )
    async def browser_scroll_up(
        self,
        to_top: Optional[bool] = None
    ) -> ToolResult:
        """Scroll up the current browser page
        
        Args:
            to_top: (Optional) Whether to scroll directly to page top instead of one viewport up
            
        Returns:
            Scroll result
        """
        return await self.browser.scroll_up(to_top)
    
    @tool(
        name="browser_scroll_down",
        description="Scroll down the current browser page. Use when viewing content below or jumping to page bottom.",
        parameters={
            "to_bottom": {
                "type": "boolean",
                "description": "(Optional) Whether to scroll directly to page bottom instead of one viewport down."
            }
        },
        required=[]
    )
    async def browser_scroll_down(
        self,
        to_bottom: Optional[bool] = None
    ) -> ToolResult:
        """Scroll down the current browser page
        
        Args:
            to_bottom: (Optional) Whether to scroll directly to page bottom instead of one viewport down
            
        Returns:
            Scroll result
        """
        return await self.browser.scroll_down(to_bottom)
    
    @tool(
        name="browser_console_exec",
        description="Execute JavaScript code in browser console. Use when custom scripts need to be executed.",
        parameters={
            "javascript": {
                "type": "string",
                "description": "JavaScript code to execute. Note that the runtime environment is browser console."
            }
        },
        required=["javascript"]
    )
    async def browser_console_exec(
        self,
        javascript: str
    ) -> ToolResult:
        """Execute JavaScript code in browser console
        
        Args:
            javascript: JavaScript code to execute, note that the runtime environment is browser console
            
        Returns:
            Execution result
        """
        return await self.browser.console_exec(javascript)
    
    @tool(
        name="browser_console_view",
        description="View browser console output. Use when checking JavaScript logs or debugging page errors.",
        parameters={
            "max_lines": {
                "type": "integer",
                "description": "(Optional) Maximum number of log lines to return."
            }
        },
        required=[]
    )
    async def browser_console_view(
        self,
        max_lines: Optional[int] = None
    ) -> ToolResult:
        """View browser console output
        
        Args:
            max_lines: (Optional) Maximum number of log lines to return
            
        Returns:
            Console output
        """
        return await self.browser.console_view(max_lines)
    
    @tool(
        name="browser_smart_scroll",
        description="Smart scrolling for long pages and infinite scroll content. Automatically detects when new content loads.",
        parameters={
            "direction": {
                "type": "string",
                "description": "(Optional) Scroll direction: 'down' or 'up'. Default is 'down'.",
                "enum": ["down", "up"]
            },
            "max_scrolls": {
                "type": "integer",
                "description": "(Optional) Maximum number of scrolls to perform. Default is 10."
            }
        },
        required=[]
    )
    async def browser_smart_scroll(
        self,
        direction: str = "down",
        max_scrolls: Optional[int] = 10
    ) -> ToolResult:
        """Smart scrolling that handles infinite scroll pages intelligently
        
        Args:
            direction: Scroll direction ('down' or 'up')
            max_scrolls: Maximum number of scroll attempts
            
        Returns:
            Scroll statistics including content loaded
        """
        return await self.browser.smart_scroll(direction, max_scrolls, check_for_new_content=True)
    
    @tool(
        name="browser_navigate_robust",
        description="Navigate to URL with automatic error handling, popup closing, and retry logic. Use this instead of browser_navigate for problematic sites.",
        parameters={
            "url": {
                "type": "string",
                "description": "Complete URL to visit. Must include protocol prefix."
            },
            "handle_popups": {
                "type": "boolean",
                "description": "(Optional) Auto-close cookie banners and popups. Default is True."
            }
        },
        required=["url"]
    )
    async def browser_navigate_robust(
        self,
        url: str,
        handle_popups: Optional[bool] = True
    ) -> ToolResult:
        """Navigate to URL with enhanced error handling and automatic popup closing
        
        Args:
            url: Complete URL address, must include protocol prefix
            handle_popups: Whether to automatically close popups and cookie banners
            
        Returns:
            Navigation result with interactive elements
        """
        return await self.browser.navigate_with_error_handling(url, max_retries=3, handle_popups=handle_popups) 