"""Browser implementation built on the browser_use library, following its
official Tools patterns (browser_use/tools/service.py):

- Every action is dispatched as an event on the session event bus
  (ClickElementEvent, TypeTextEvent, ScrollEvent, SendKeysEvent, ...) so the
  library's watchdogs handle waiting, scrolling into view, new-tab switching
  and error validation — no hand-rolled CDP action code.
- Page state comes from ``session.get_browser_state_summary()`` and the DOM
  tree is serialized with the official ``dom_state.llm_representation()``
  (``[index]<tag ... />`` format), the same representation the browser-use
  agent itself consumes.
- Page content is extracted to Markdown with the official
  ``extract_clean_markdown()`` helper (no LLM call involved).
- Console output is captured via CDP ``Runtime.consoleAPICalled`` /
  ``Runtime.exceptionThrown`` events, the same way DevTools does.
"""

from typing import Any, List, Optional
import asyncio
import json
import logging
from collections import deque

from browser_use.browser.events import (
    ClickCoordinateEvent,
    ClickElementEvent,
    GetDropdownOptionsEvent,
    NavigateToUrlEvent,
    ScrollEvent,
    SelectDropdownOptionEvent,
    SendKeysEvent,
    SwitchTabEvent,
    TypeTextEvent,
)
from browser_use.browser.session import BrowserSession, CDPSession
from browser_use.browser.views import BrowserStateSummary
from browser_use.dom.markdown_extractor import extract_clean_markdown

from app.domain.models.tool_result import ToolResult

logger = logging.getLogger(__name__)

# The agent truncates whole tool results at ~16000 chars (BaseAgent
# max_tool_result_chars), so cap the two big fields below that budget.
MAX_ELEMENT_TREE_CHARS = 6000
MAX_MARKDOWN_CHARS = 8000
MAX_CONSOLE_LOG_ENTRIES = 500
DEFAULT_VIEWPORT_HEIGHT = 1000


class BrowserUseBrowser:
    """Browser implementation using the browser_use library (BrowserSession + CDP).

    Connects to an existing Chrome instance via CDP URL and implements the
    domain ``Browser`` protocol.
    """

    def __init__(self, cdp_url: str):
        self.cdp_url = cdp_url
        self._session: Optional[BrowserSession] = None
        self._console_logs: deque[str] = deque(maxlen=MAX_CONSOLE_LOG_ENTRIES)
        self._console_clients: set[int] = set()
        self._console_enabled_sessions: set[str] = set()

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    async def _ensure_session(self) -> BrowserSession:
        """Return a started BrowserSession, initialising it if necessary."""
        if self._session is not None:
            return self._session

        max_retries = 5
        retry_delay = 1.0
        last_error: Exception = RuntimeError("Unknown error")

        for attempt in range(max_retries):
            try:
                session = BrowserSession(
                    cdp_url=self.cdp_url,
                    minimum_wait_page_load_time=0.5,
                    wait_for_network_idle_page_load_time=2.0,
                    highlight_elements=False,
                )
                await session.start()
                self._session = session
                await self._ensure_console_capture()
                return session
            except Exception as exc:
                last_error = exc
                await self.cleanup()
                if attempt == max_retries - 1:
                    logger.error(
                        "Failed to initialise BrowserSession after %d attempts: %s",
                        max_retries,
                        exc,
                    )
                    raise
                retry_delay = min(retry_delay * 2, 10.0)
                logger.warning(
                    "BrowserSession init failed (attempt %d/%d), retrying in %.1fs: %s",
                    attempt + 1,
                    max_retries,
                    retry_delay,
                    exc,
                )
                await asyncio.sleep(retry_delay)

        raise last_error

    async def cleanup(self) -> None:
        """Stop the browser session and release resources."""
        if self._session is not None:
            try:
                await self._session.stop()
            except Exception as exc:
                logger.error("Error stopping BrowserSession: %s", exc)
            finally:
                self._session = None
                self._console_clients.clear()
                self._console_enabled_sessions.clear()

    # ------------------------------------------------------------------
    # Event dispatch helper (official browser-use tools pattern)
    # ------------------------------------------------------------------

    async def _dispatch(self, event: Any) -> Any:
        """Dispatch an event on the session event bus and await its result.

        This mirrors the pattern used by browser_use/tools/service.py::

            event = browser_session.event_bus.dispatch(SomeEvent(...))
            await event
            result = await event.event_result(raise_if_any=True, raise_if_none=False)
        """
        session = await self._ensure_session()
        handle = session.event_bus.dispatch(event)
        await handle
        return await handle.event_result(raise_if_any=True, raise_if_none=False)

    # ------------------------------------------------------------------
    # Console log capture (CDP Runtime events, like DevTools)
    # ------------------------------------------------------------------

    @staticmethod
    def _format_remote_object(obj: dict) -> str:
        """Render a CDP RemoteObject roughly the way DevTools console would."""
        if "value" in obj:
            value = obj["value"]
            return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, default=str)
        return obj.get("description") or obj.get("unserializableValue") or obj.get("type", "")

    async def _ensure_console_capture(self) -> None:
        """Register CDP console/exception listeners for the focused tab."""
        if self._session is None:
            return
        try:
            cdp_session: CDPSession = await self._session.get_or_create_cdp_session()

            client_key = id(cdp_session.cdp_client)
            if client_key not in self._console_clients:
                self._console_clients.add(client_key)

                def _on_console(event: dict, _session_id: Optional[str] = None) -> None:
                    level = event.get("type", "log")
                    args = event.get("args", []) or []
                    text = " ".join(self._format_remote_object(arg) for arg in args)
                    self._console_logs.append(f"[{level}] {text}")

                def _on_exception(event: dict, _session_id: Optional[str] = None) -> None:
                    details = event.get("exceptionDetails", {}) or {}
                    exception = details.get("exception", {}) or {}
                    text = (
                        exception.get("description")
                        or details.get("text")
                        or "Uncaught exception"
                    )
                    self._console_logs.append(f"[error] {text}")

                cdp_session.cdp_client.register.Runtime.consoleAPICalled(_on_console)
                cdp_session.cdp_client.register.Runtime.exceptionThrown(_on_exception)

            session_key = str(cdp_session.session_id)
            if session_key not in self._console_enabled_sessions:
                self._console_enabled_sessions.add(session_key)
                await cdp_session.cdp_client.send.Runtime.enable(session_id=cdp_session.session_id)
        except Exception as exc:
            logger.warning("Failed to set up console capture: %s", exc)

    # ------------------------------------------------------------------
    # Browser state helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _truncate(text: str, limit: int, note: str) -> str:
        if len(text) <= limit:
            return text
        return text[:limit] + f"... [{note}]"

    def _build_state_data(
        self,
        state: BrowserStateSummary,
        content: Optional[str] = None,
    ) -> dict:
        """Build the tool payload from a BrowserStateSummary.

        Mirrors the layout of browser-use's own <browser_state> agent message:
        url/title, tabs, scroll position in pages, then the serialized element
        tree wrapped in [Start of page]/[End of page] markers.
        """
        data: dict = {"url": state.url, "title": state.title}

        if len(state.tabs) > 1:
            data["tabs"] = [
                f"Tab {tab.target_id[-4:]}: {tab.url} - {(tab.title or '')[:40]}"
                for tab in state.tabs
            ]

        viewport_height = DEFAULT_VIEWPORT_HEIGHT
        pixels_above = state.pixels_above
        pixels_below = state.pixels_below
        if state.page_info:
            viewport_height = state.page_info.viewport_height or DEFAULT_VIEWPORT_HEIGHT
            pixels_above = state.page_info.pixels_above
            pixels_below = state.page_info.pixels_below
        data["scroll_position"] = (
            f"{pixels_above / viewport_height:.1f} pages above, "
            f"{pixels_below / viewport_height:.1f} pages below"
        )

        tree = ""
        if state.dom_state is not None:
            tree = state.dom_state.llm_representation() or ""
        tree = self._truncate(
            tree, MAX_ELEMENT_TREE_CHARS, "element tree truncated, scroll to see more"
        )
        if pixels_above <= 0:
            tree = "[Start of page]\n" + tree
        if pixels_below <= 0:
            tree = tree + "\n[End of page]"
        data["interactive_elements"] = tree

        if content is not None:
            data["content"] = self._truncate(
                content, MAX_MARKDOWN_CHARS, "content truncated, scroll to see more"
            )
        return data

    async def _get_state_data(self, include_content: bool = True) -> dict:
        """Return the current page state (and optionally Markdown content)."""
        session = await self._ensure_session()
        await self._ensure_console_capture()
        state = await session.get_browser_state_summary(include_screenshot=False)

        content: Optional[str] = None
        if include_content:
            try:
                content, _stats = await extract_clean_markdown(
                    browser_session=session, extract_links=False, extract_images=False
                )
            except Exception as exc:
                logger.warning("Markdown extraction failed: %s", exc)

        return self._build_state_data(state, content)

    async def _get_node(self, index: int):
        session = await self._ensure_session()
        node = await session.get_element_by_index(index)
        if node is None:
            raise ValueError(
                f"Element index {index} not available - page may have changed. "
                "Use browser_view to refresh the element list."
            )
        return node

    async def _detect_new_tab_opened(self, tabs_before: set) -> str:
        """Detect if an action opened a new tab and automatically switch to it.

        Same behaviour as browser_use/tools/service.py::_detect_new_tab_opened.
        """
        try:
            await asyncio.sleep(0.05)
            session = await self._ensure_session()
            tabs_after = await session.get_tabs()
            new_tabs = [t for t in tabs_after if t.target_id not in tabs_before]
            if new_tabs:
                new_tab = new_tabs[0]
                try:
                    await self._dispatch(SwitchTabEvent(target_id=new_tab.target_id))
                    await self._ensure_console_capture()
                    return f". Automatically switched to new tab ({new_tab.url})"
                except Exception:
                    return f". Note: this opened a new tab ({new_tab.url})"
        except Exception:
            pass
        return ""

    async def _viewport_height(self) -> int:
        """Return the CSS viewport height, matching the official scroll tool."""
        try:
            session = await self._ensure_session()
            cdp_session = await session.get_or_create_cdp_session()
            metrics = await cdp_session.cdp_client.send.Page.getLayoutMetrics(
                session_id=cdp_session.session_id
            )
            viewport = metrics.get("cssVisualViewport") or metrics.get("cssLayoutViewport") or {}
            height = int(viewport.get("clientHeight", 0))
            return height or DEFAULT_VIEWPORT_HEIGHT
        except Exception:
            return DEFAULT_VIEWPORT_HEIGHT

    # ------------------------------------------------------------------
    # Browser Protocol implementation
    # ------------------------------------------------------------------

    async def view_page(self) -> ToolResult:
        """Return the current page state, element tree and Markdown content."""
        try:
            return ToolResult(success=True, data=await self._get_state_data())
        except Exception as exc:
            return ToolResult(success=False, message=f"Failed to view page: {exc}")

    async def navigate(self, url: str) -> ToolResult:
        """Navigate to the given URL and return the resulting page state."""
        try:
            await self._dispatch(NavigateToUrlEvent(url=url))
            return ToolResult(success=True, data=await self._get_state_data())
        except Exception as exc:
            return ToolResult(success=False, message=f"Failed to navigate to {url}: {exc}")

    async def restart(self, url: str) -> ToolResult:
        """Restart the browser session and navigate to the given URL."""
        await self.cleanup()
        return await self.navigate(url)

    async def click(
        self,
        index: Optional[int] = None,
        coordinate_x: Optional[float] = None,
        coordinate_y: Optional[float] = None,
    ) -> ToolResult:
        """Click an element by DOM index or by viewport coordinates."""
        try:
            session = await self._ensure_session()
            tabs_before = {t.target_id for t in await session.get_tabs()}

            if coordinate_x is not None and coordinate_y is not None:
                await self._dispatch(
                    ClickCoordinateEvent(
                        coordinate_x=int(coordinate_x),
                        coordinate_y=int(coordinate_y),
                        force=True,
                    )
                )
                message = f"Clicked at coordinates ({coordinate_x:.0f}, {coordinate_y:.0f})"
            elif index is not None:
                node = await self._get_node(index)
                metadata = await self._dispatch(ClickElementEvent(node=node))
                if isinstance(metadata, dict) and "validation_error" in metadata:
                    error_msg = str(metadata["validation_error"])
                    if "Cannot click on <select>" in error_msg:
                        return ToolResult(
                            success=False,
                            message=(
                                f"Element {index} is a dropdown; "
                                f"use browser_select_option instead."
                            ),
                        )
                    return ToolResult(success=False, message=error_msg)
                message = f"Clicked element [{index}]"
            else:
                return ToolResult(
                    success=False,
                    message="Either index or coordinate_x/coordinate_y must be provided",
                )

            message += await self._detect_new_tab_opened(tabs_before)
            return ToolResult(success=True, message=message)
        except Exception as exc:
            return ToolResult(success=False, message=f"Failed to click element: {exc}")

    async def input(
        self,
        text: str,
        press_enter: bool,
        index: Optional[int] = None,
        coordinate_x: Optional[float] = None,
        coordinate_y: Optional[float] = None,
    ) -> ToolResult:
        """Type text into an element identified by DOM index or coordinates."""
        try:
            if index is not None:
                node = await self._get_node(index)
                await self._dispatch(TypeTextEvent(node=node, text=text, clear=True))
            elif coordinate_x is not None and coordinate_y is not None:
                # Click to focus the element under the cursor, then insert text.
                await self._dispatch(
                    ClickCoordinateEvent(
                        coordinate_x=int(coordinate_x),
                        coordinate_y=int(coordinate_y),
                        force=True,
                    )
                )
                session = await self._ensure_session()
                cdp_session = await session.get_or_create_cdp_session()
                await cdp_session.cdp_client.send.Input.insertText(
                    params={"text": text},
                    session_id=cdp_session.session_id,
                )
            else:
                return ToolResult(
                    success=False,
                    message="Either index or coordinate_x/coordinate_y must be provided",
                )

            if press_enter:
                await self._dispatch(SendKeysEvent(keys="Enter"))

            return ToolResult(success=True)
        except Exception as exc:
            return ToolResult(success=False, message=f"Failed to input text: {exc}")

    async def move_mouse(
        self,
        coordinate_x: float,
        coordinate_y: float,
    ) -> ToolResult:
        """Move the mouse cursor to the given coordinates."""
        try:
            session = await self._ensure_session()
            page = await session.get_current_page()
            if page is None:
                return ToolResult(success=False, message="No active page")
            mouse = await page.mouse
            await mouse.move(int(coordinate_x), int(coordinate_y))
            return ToolResult(success=True)
        except Exception as exc:
            return ToolResult(success=False, message=f"Failed to move mouse: {exc}")

    async def press_key(self, key: str) -> ToolResult:
        """Simulate a key press or shortcut (e.g. Enter, Control+A)."""
        try:
            await self._dispatch(SendKeysEvent(keys=key))
            return ToolResult(success=True)
        except Exception as exc:
            return ToolResult(success=False, message=f"Failed to press key: {exc}")

    async def select_option(self, index: int, option: int) -> ToolResult:
        """Select an option (by position) in a dropdown identified by DOM index."""
        try:
            node = await self._get_node(index)

            options_result = await self._dispatch(GetDropdownOptionsEvent(node=node))
            options: List[dict] = []
            if isinstance(options_result, dict) and options_result.get("options"):
                try:
                    options = json.loads(options_result["options"])
                except (TypeError, ValueError):
                    options = []
            if not options:
                return ToolResult(
                    success=False,
                    message=f"No options found in dropdown at index {index}",
                )

            selected = next((o for o in options if o.get("index") == option), None)
            if selected is None and 0 <= option < len(options):
                selected = options[option]
            if selected is None:
                available = ", ".join(
                    f"{o.get('index')}: {o.get('text')}" for o in options
                )
                return ToolResult(
                    success=False,
                    message=(
                        f"Option {option} not found in dropdown at index {index}. "
                        f"Available options: {available}"
                    ),
                )

            result = await self._dispatch(
                SelectDropdownOptionEvent(node=node, text=str(selected.get("text", "")))
            )
            message = None
            if isinstance(result, dict):
                message = result.get("message")
            return ToolResult(
                success=True,
                message=message or f"Selected option {option}: {selected.get('text')}",
            )
        except Exception as exc:
            return ToolResult(success=False, message=f"Failed to select option: {exc}")

    async def scroll_up(self, to_top: Optional[bool] = None) -> ToolResult:
        """Scroll up one viewport, or jump to the page top when to_top is True."""
        try:
            if to_top:
                await self._evaluate_expression("window.scrollTo(0, 0)")
            else:
                amount = await self._viewport_height()
                await self._dispatch(ScrollEvent(direction="up", amount=amount))
            return ToolResult(success=True)
        except Exception as exc:
            return ToolResult(success=False, message=f"Failed to scroll up: {exc}")

    async def scroll_down(self, to_bottom: Optional[bool] = None) -> ToolResult:
        """Scroll down one viewport, or jump to the page bottom when to_bottom is True."""
        try:
            if to_bottom:
                await self._evaluate_expression(
                    "window.scrollTo(0, document.body.scrollHeight)"
                )
            else:
                amount = await self._viewport_height()
                await self._dispatch(ScrollEvent(direction="down", amount=amount))
            return ToolResult(success=True)
        except Exception as exc:
            return ToolResult(success=False, message=f"Failed to scroll down: {exc}")

    async def screenshot(self, full_page: Optional[bool] = False) -> bytes:
        """Return a PNG screenshot of the current page."""
        session = await self._ensure_session()
        return await session.take_screenshot(full_page=bool(full_page))

    async def _evaluate_expression(self, expression: str) -> Any:
        """Evaluate a JavaScript expression via CDP Runtime.evaluate.

        Unlike the actor Page.evaluate (which requires an arrow function),
        Runtime.evaluate accepts arbitrary console-style expressions and
        reports exceptions, matching browser-console semantics.
        """
        session = await self._ensure_session()
        cdp_session = await session.get_or_create_cdp_session()
        result = await cdp_session.cdp_client.send.Runtime.evaluate(
            params={
                "expression": expression,
                "returnByValue": True,
                "awaitPromise": True,
                "userGesture": True,
            },
            session_id=cdp_session.session_id,
        )
        exception_details = result.get("exceptionDetails")
        if exception_details:
            exception = exception_details.get("exception", {}) or {}
            raise RuntimeError(
                exception.get("description")
                or exception_details.get("text")
                or "JavaScript execution failed"
            )
        return result.get("result", {}).get("value")

    async def console_exec(self, javascript: str) -> ToolResult:
        """Execute JavaScript in the page with browser-console semantics."""
        try:
            await self._ensure_console_capture()
            value = await self._evaluate_expression(javascript)
            return ToolResult(success=True, data={"result": value})
        except Exception as exc:
            return ToolResult(success=False, message=f"Failed to execute JavaScript: {exc}")

    async def console_view(self, max_lines: Optional[int] = None) -> ToolResult:
        """Return console output captured via CDP Runtime events."""
        try:
            await self._ensure_console_capture()
            logs = list(self._console_logs)
            if max_lines is not None:
                logs = logs[-max_lines:]
            return ToolResult(success=True, data={"logs": logs})
        except Exception as exc:
            return ToolResult(success=False, message=f"Failed to view console: {exc}")
