from typing import Optional

from pydantic import BaseModel, Field

from app.domain.external.browser import Browser
from app.domain.models.tool_result import ToolResult
from app.domain.services.tools.base import BaseToolkit, Tool


class BrowserViewTool(Tool):
    name = "browser_view"
    description = (
        "View content of the current browser page. Use for checking the latest "
        "state of previously opened pages."
    )

    class Args(BaseModel):
        pass

    async def run(self) -> ToolResult:
        return await self.toolkit.browser.view_page()


class BrowserNavigateTool(Tool):
    name = "browser_navigate"
    description = "Navigate browser to specified URL. Use when accessing new pages is needed."

    class Args(BaseModel):
        url: str = Field(description="Complete URL to visit. Must include protocol prefix.")

    async def run(self, url: str) -> ToolResult:
        return await self.toolkit.browser.navigate(url)


class BrowserRestartTool(Tool):
    name = "browser_restart"
    description = (
        "Restart browser and navigate to specified URL. Use when browser state needs to be reset."
    )

    class Args(BaseModel):
        url: str = Field(
            description="Complete URL to visit after restart. Must include protocol prefix."
        )

    async def run(self, url: str) -> ToolResult:
        return await self.toolkit.browser.restart(url)


class BrowserClickTool(Tool):
    name = "browser_click"
    description = "Click on elements in the current browser page. Use when clicking page elements is needed."

    class Args(BaseModel):
        index: Optional[int] = Field(
            default=None, description="(Optional) Index number of the element to click"
        )
        coordinate_x: Optional[float] = Field(
            default=None, description="(Optional) X coordinate of click position"
        )
        coordinate_y: Optional[float] = Field(
            default=None, description="(Optional) Y coordinate of click position"
        )

    async def run(
        self,
        index: Optional[int] = None,
        coordinate_x: Optional[float] = None,
        coordinate_y: Optional[float] = None,
    ) -> ToolResult:
        return await self.toolkit.browser.click(index, coordinate_x, coordinate_y)


class BrowserInputTool(Tool):
    name = "browser_input"
    description = (
        "Overwrite text in editable elements on the current browser page. "
        "Use when filling content in input fields."
    )

    class Args(BaseModel):
        text: str = Field(description="Complete text content to overwrite")
        press_enter: bool = Field(description="Whether to press Enter key after input")
        index: Optional[int] = Field(
            default=None, description="(Optional) Index number of the element to overwrite text"
        )
        coordinate_x: Optional[float] = Field(
            default=None, description="(Optional) X coordinate of the element to overwrite text"
        )
        coordinate_y: Optional[float] = Field(
            default=None, description="(Optional) Y coordinate of the element to overwrite text"
        )

    async def run(
        self,
        text: str,
        press_enter: bool,
        index: Optional[int] = None,
        coordinate_x: Optional[float] = None,
        coordinate_y: Optional[float] = None,
    ) -> ToolResult:
        return await self.toolkit.browser.input(
            text, press_enter, index, coordinate_x, coordinate_y
        )


class BrowserMoveMouseTool(Tool):
    name = "browser_move_mouse"
    description = (
        "Move cursor to specified position on the current browser page. "
        "Use when simulating user mouse movement."
    )

    class Args(BaseModel):
        coordinate_x: float = Field(description="X coordinate of target cursor position")
        coordinate_y: float = Field(description="Y coordinate of target cursor position")

    async def run(self, coordinate_x: float, coordinate_y: float) -> ToolResult:
        return await self.toolkit.browser.move_mouse(coordinate_x, coordinate_y)


class BrowserPressKeyTool(Tool):
    name = "browser_press_key"
    description = (
        "Simulate key press in the current browser page. Use when specific keyboard operations are needed."
    )

    class Args(BaseModel):
        key: str = Field(
            description=(
                "Key name to simulate (e.g., Enter, Tab, ArrowUp), "
                "supports key combinations (e.g., Control+Enter)."
            )
        )

    async def run(self, key: str) -> ToolResult:
        return await self.toolkit.browser.press_key(key)


class BrowserSelectOptionTool(Tool):
    name = "browser_select_option"
    description = (
        "Select specified option from dropdown list element in the current browser page. "
        "Use when selecting dropdown menu options."
    )

    class Args(BaseModel):
        index: int = Field(description="Index number of the dropdown list element")
        option: int = Field(description="Option number to select, starting from 0.")

    async def run(self, index: int, option: int) -> ToolResult:
        return await self.toolkit.browser.select_option(index, option)


class BrowserScrollUpTool(Tool):
    name = "browser_scroll_up"
    description = (
        "Scroll up the current browser page. Use when viewing content above or returning to page top."
    )

    class Args(BaseModel):
        to_top: Optional[bool] = Field(
            default=None,
            description="(Optional) Whether to scroll directly to page top instead of one viewport up.",
        )

    async def run(self, to_top: Optional[bool] = None) -> ToolResult:
        return await self.toolkit.browser.scroll_up(to_top)


class BrowserScrollDownTool(Tool):
    name = "browser_scroll_down"
    description = (
        "Scroll down the current browser page. Use when viewing content below or jumping to page bottom."
    )

    class Args(BaseModel):
        to_bottom: Optional[bool] = Field(
            default=None,
            description="(Optional) Whether to scroll directly to page bottom instead of one viewport down.",
        )

    async def run(self, to_bottom: Optional[bool] = None) -> ToolResult:
        return await self.toolkit.browser.scroll_down(to_bottom)


class BrowserConsoleExecTool(Tool):
    name = "browser_console_exec"
    description = (
        "Execute JavaScript code in browser console. Use when custom scripts need to be executed."
    )

    class Args(BaseModel):
        javascript: str = Field(
            description="JavaScript code to execute. Note that the runtime environment is browser console."
        )

    async def run(self, javascript: str) -> ToolResult:
        return await self.toolkit.browser.console_exec(javascript)


class BrowserConsoleViewTool(Tool):
    name = "browser_console_view"
    description = (
        "View browser console output. Use when checking JavaScript logs or debugging page errors."
    )

    class Args(BaseModel):
        max_lines: Optional[int] = Field(
            default=None, description="(Optional) Maximum number of log lines to return."
        )

    async def run(self, max_lines: Optional[int] = None) -> ToolResult:
        return await self.toolkit.browser.console_view(max_lines)


class BrowserToolkit(BaseToolkit):
    """Browser tool class, providing browser interaction functions"""

    name: str = "browser"
    instructions: str = """
- Use browser tools to open every URL provided by the user and URLs from search results
- Actively explore valuable links for deeper information
- Tools return the interactive element tree as `[index]<tag ... />` lines (indexes start at 1); use the index for subsequent interactions
- Elements marked `*[index]` are new since the previous state; indentation shows nesting
- Not all interactive elements are listed; use coordinates for unlisted elements
- Pages are auto-extracted to Markdown when possible; the extraction may include off-screen text but omits links/images and is not guaranteed complete
- If the extracted Markdown already covers what you need, don't scroll; otherwise scroll to view the full page
"""
    tool_types = [
        BrowserViewTool,
        BrowserNavigateTool,
        BrowserRestartTool,
        BrowserClickTool,
        BrowserInputTool,
        BrowserMoveMouseTool,
        BrowserPressKeyTool,
        BrowserSelectOptionTool,
        BrowserScrollUpTool,
        BrowserScrollDownTool,
        BrowserConsoleExecTool,
        BrowserConsoleViewTool,
    ]

    def __init__(self, browser: Browser):
        """Initialize browser tool class

        Args:
            browser: Browser service
        """
        self.browser = browser
        super().__init__()
