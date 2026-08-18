"""Browser implementation built on Playwright over CDP, following mainstream
patterns (Playwright MCP style):

- Connects to the sandbox Chrome via ``connect_over_cdp`` — no local browser
  binaries needed.
- Page state is a lightweight in-page snapshot of visible interactive
  elements, emitted in the same ``[index]<tag ... />`` format (1-based
  indexes) as the browser-use engine, so both engines are interchangeable
  for the agent.
- Page content is converted to Markdown with ``markdownify`` — no LLM call.
- Console output is captured with Playwright's native ``page.on("console")``
  and ``page.on("pageerror")`` listeners.
"""

from typing import Any, List, Optional
import asyncio
import logging
import re
from collections import deque

from playwright.async_api import Browser as PlaywrightBrowserHandle
from playwright.async_api import Page, async_playwright
from markdownify import markdownify

from app.domain.models.tool_result import ToolResult

logger = logging.getLogger(__name__)

# Keep payload caps aligned with BrowserUseBrowser (the agent truncates whole
# tool results at ~16000 chars).
MAX_ELEMENT_TREE_CHARS = 6000
MAX_MARKDOWN_CHARS = 8000
MAX_CONSOLE_LOG_ENTRIES = 500

# Snapshot of visible interactive elements. Tags each element with a
# data-manus-id attribute so later actions can address it by index, and
# returns page/scroll metadata in the same shape the browser-use engine uses.
_SNAPSHOT_SCRIPT = """() => {
    const SELECTOR = [
        'a', 'button', 'input', 'textarea', 'select',
        '[role="button"]', '[role="link"]', '[role="checkbox"]',
        '[role="radio"]', '[role="combobox"]', '[role="menuitem"]',
        '[contenteditable="true"]', '[tabindex]:not([tabindex="-1"])',
    ].join(', ');

    const viewportHeight = window.innerHeight;
    const viewportWidth = window.innerWidth;
    const lines = [];
    let index = 1;  // 1-based, matching browser-use serializer

    const describe = (el) => {
        const tag = el.tagName.toLowerCase();
        const attrs = [];
        for (const name of ['type', 'placeholder', 'aria-label', 'title', 'alt', 'name', 'value', 'id']) {
            const value = el.getAttribute(name);
            if (value) attrs.push(`${name}=${value.length > 40 ? value.slice(0, 37) + '...' : value}`);
        }
        let text = (el.innerText || el.value || '').trim().replace(/\\s+/g, ' ');
        if (el.id) {
            const label = document.querySelector(`label[for="${el.id}"]`);
            if (label && label.innerText.trim()) attrs.push(`label=${label.innerText.trim()}`);
        }
        if (text.length > 100) text = text.slice(0, 97) + '...';
        const attrStr = attrs.length ? ' ' + attrs.join(' ') : '';
        return `[${index}]<${tag}${attrStr}>${text}</${tag}>`;
    };

    for (const el of document.querySelectorAll(SELECTOR)) {
        const rect = el.getBoundingClientRect();
        if (rect.width === 0 || rect.height === 0) continue;
        if (rect.bottom < 0 || rect.top > viewportHeight ||
            rect.right < 0 || rect.left > viewportWidth) continue;
        const style = window.getComputedStyle(el);
        if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') continue;

        el.setAttribute('data-manus-id', `manus-element-${index}`);
        lines.push(describe(el));
        index += 1;
    }

    return {
        elements: lines.join('\\n'),
        scrollY: window.scrollY,
        viewportHeight: viewportHeight,
        scrollHeight: Math.max(document.documentElement.scrollHeight, document.body.scrollHeight),
    };
}"""

# Return the page HTML with non-content tags removed, for Markdown conversion.
_CONTENT_HTML_SCRIPT = """() => {
    const clone = document.body ? document.body.cloneNode(true) : null;
    if (!clone) return '';
    for (const el of clone.querySelectorAll('script, style, noscript, template, svg')) el.remove();
    return clone.innerHTML;
}"""


class PlaywrightBrowser:
    """Browser implementation using Playwright connected over CDP."""

    def __init__(self, cdp_url: str):
        self.cdp_url = cdp_url
        self.playwright = None
        self.browser: Optional[PlaywrightBrowserHandle] = None
        self.page: Optional[Page] = None
        self._console_logs: deque[str] = deque(maxlen=MAX_CONSOLE_LOG_ENTRIES)

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    async def _initialize(self) -> None:
        max_retries = 5
        retry_delay = 1.0

        for attempt in range(max_retries):
            try:
                self.playwright = await async_playwright().start()
                self.browser = await self.playwright.chromium.connect_over_cdp(self.cdp_url)
                context = (
                    self.browser.contexts[0]
                    if self.browser.contexts
                    else await self.browser.new_context()
                )
                context.on("page", self._attach_console_listeners)
                for page in context.pages:
                    self._attach_console_listeners(page)
                return
            except Exception as exc:
                await self.cleanup()
                if attempt == max_retries - 1:
                    logger.error(
                        "Failed to connect Playwright over CDP after %d attempts: %s",
                        max_retries,
                        exc,
                    )
                    raise
                retry_delay = min(retry_delay * 2, 10.0)
                logger.warning(
                    "Playwright CDP connect failed (attempt %d/%d), retrying in %.1fs: %s",
                    attempt + 1,
                    max_retries,
                    retry_delay,
                    exc,
                )
                await asyncio.sleep(retry_delay)

    async def cleanup(self) -> None:
        """Close all tabs and disconnect, releasing Playwright resources."""
        try:
            if self.browser:
                for context in self.browser.contexts:
                    for page in list(context.pages):
                        try:
                            await page.close()
                        except Exception:
                            pass
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as exc:
            logger.error("Error cleaning up Playwright resources: %s", exc)
        finally:
            self.page = None
            self.browser = None
            self.playwright = None

    async def _ensure_page(self) -> Page:
        """Return the active page, connecting and focusing the newest tab."""
        if not self.browser or not self.browser.is_connected():
            await self._initialize()

        context = self.browser.contexts[0]
        pages = [p for p in context.pages if not p.is_closed()]
        if not pages:
            self.page = await context.new_page()
            self._attach_console_listeners(self.page)
        elif self.page is None or self.page.is_closed() or self.page not in pages:
            self.page = pages[-1]
        return self.page

    def _attach_console_listeners(self, page: Page) -> None:
        if getattr(page, "_manus_console_attached", False):
            return
        page._manus_console_attached = True
        page.on(
            "console",
            lambda msg: self._console_logs.append(f"[{msg.type}] {msg.text}"),
        )
        page.on(
            "pageerror",
            lambda err: self._console_logs.append(f"[error] {err}"),
        )

    # ------------------------------------------------------------------
    # Browser state helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _truncate(text: str, limit: int, note: str) -> str:
        if len(text) <= limit:
            return text
        return text[:limit] + f"... [{note}]"

    async def _wait_for_load(self, page: Page, timeout_ms: int = 10000) -> None:
        try:
            await page.wait_for_load_state("load", timeout=timeout_ms)
        except Exception:
            logger.debug("Page load wait timed out; continuing with current state")

    async def _extract_markdown(self, page: Page) -> Optional[str]:
        try:
            html = await page.evaluate(_CONTENT_HTML_SCRIPT)
            content = markdownify(html or "")
            content = re.sub(r"\n{3,}", "\n\n", content).strip()
            return content
        except Exception as exc:
            logger.warning("Markdown extraction failed: %s", exc)
            return None

    async def _get_state_data(self, include_content: bool = True) -> dict:
        """Build the same payload shape as the browser-use engine."""
        page = await self._ensure_page()
        await self._wait_for_load(page)

        snapshot = await page.evaluate(_SNAPSHOT_SCRIPT)
        data: dict = {"url": page.url, "title": await page.title()}

        context_pages = [p for p in self.browser.contexts[0].pages if not p.is_closed()]
        if len(context_pages) > 1:
            tabs = []
            for i, tab in enumerate(context_pages):
                try:
                    tabs.append(f"Tab {i}: {tab.url} - {(await tab.title())[:40]}")
                except Exception:
                    tabs.append(f"Tab {i}: {tab.url}")
            data["tabs"] = tabs

        viewport_height = snapshot.get("viewportHeight") or 1
        pixels_above = snapshot.get("scrollY", 0)
        pixels_below = max(
            0, snapshot.get("scrollHeight", 0) - pixels_above - viewport_height
        )
        data["scroll_position"] = (
            f"{pixels_above / viewport_height:.1f} pages above, "
            f"{pixels_below / viewport_height:.1f} pages below"
        )

        tree = self._truncate(
            snapshot.get("elements", ""),
            MAX_ELEMENT_TREE_CHARS,
            "element tree truncated, scroll to see more",
        )
        if pixels_above <= 0:
            tree = "[Start of page]\n" + tree
        if pixels_below <= 0:
            tree = tree + "\n[End of page]"
        data["interactive_elements"] = tree

        if include_content:
            content = await self._extract_markdown(page)
            if content is not None:
                data["content"] = self._truncate(
                    content, MAX_MARKDOWN_CHARS, "content truncated, scroll to see more"
                )
        return data

    def _locator_by_index(self, page: Page, index: int):
        return page.locator(f'[data-manus-id="manus-element-{index}"]')

    async def _get_element(self, page: Page, index: int):
        locator = self._locator_by_index(page, index)
        if await locator.count() == 0:
            raise ValueError(
                f"Element index {index} not available - page may have changed. "
                "Use browser_view to refresh the element list."
            )
        return locator.first

    async def _detect_new_tab_opened(self, pages_before: List[Page]) -> str:
        """Detect if an action opened a new tab and switch to it."""
        try:
            await asyncio.sleep(0.1)
            context = self.browser.contexts[0]
            new_pages = [p for p in context.pages if p not in pages_before]
            if new_pages:
                self.page = new_pages[0]
                self._attach_console_listeners(self.page)
                await self._wait_for_load(self.page)
                return f". Automatically switched to new tab ({self.page.url})"
        except Exception:
            pass
        return ""

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
            page = await self._ensure_page()
            try:
                await page.goto(url, timeout=30000, wait_until="load")
            except Exception as exc:
                logger.warning("Navigation to %s did not complete cleanly: %s", url, exc)
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
            page = await self._ensure_page()
            pages_before = list(self.browser.contexts[0].pages)

            if coordinate_x is not None and coordinate_y is not None:
                await page.mouse.click(coordinate_x, coordinate_y)
                message = f"Clicked at coordinates ({coordinate_x:.0f}, {coordinate_y:.0f})"
            elif index is not None:
                element = await self._get_element(page, index)
                tag = (await element.evaluate("el => el.tagName") or "").lower()
                if tag == "select":
                    return ToolResult(
                        success=False,
                        message=(
                            f"Element {index} is a dropdown; "
                            f"use browser_select_option instead."
                        ),
                    )
                await element.click(timeout=5000)
                message = f"Clicked element [{index}]"
            else:
                return ToolResult(
                    success=False,
                    message="Either index or coordinate_x/coordinate_y must be provided",
                )

            message += await self._detect_new_tab_opened(pages_before)
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
            page = await self._ensure_page()

            if index is not None:
                element = await self._get_element(page, index)
                try:
                    await element.fill(text, timeout=5000)
                except Exception:
                    # Non-fillable targets (e.g. contenteditable widgets)
                    await element.click(timeout=5000)
                    await page.keyboard.insert_text(text)
            elif coordinate_x is not None and coordinate_y is not None:
                await page.mouse.click(coordinate_x, coordinate_y)
                await page.keyboard.insert_text(text)
            else:
                return ToolResult(
                    success=False,
                    message="Either index or coordinate_x/coordinate_y must be provided",
                )

            if press_enter:
                await page.keyboard.press("Enter")

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
            page = await self._ensure_page()
            await page.mouse.move(coordinate_x, coordinate_y)
            return ToolResult(success=True)
        except Exception as exc:
            return ToolResult(success=False, message=f"Failed to move mouse: {exc}")

    async def press_key(self, key: str) -> ToolResult:
        """Simulate a key press or shortcut (e.g. Enter, Control+A)."""
        try:
            page = await self._ensure_page()
            await page.keyboard.press(key)
            return ToolResult(success=True)
        except Exception as exc:
            return ToolResult(success=False, message=f"Failed to press key: {exc}")

    async def select_option(self, index: int, option: int) -> ToolResult:
        """Select an option (by position) in a dropdown identified by DOM index."""
        try:
            page = await self._ensure_page()
            element = await self._get_element(page, index)
            values = await element.select_option(index=option, timeout=5000)
            label = await element.evaluate(
                "el => el.selectedIndex >= 0 ? el.options[el.selectedIndex].text : ''"
            )
            return ToolResult(
                success=True,
                message=f"Selected option {option}: {label or (values[0] if values else '')}",
            )
        except Exception as exc:
            return ToolResult(success=False, message=f"Failed to select option: {exc}")

    async def scroll_up(self, to_top: Optional[bool] = None) -> ToolResult:
        """Scroll up one viewport, or jump to the page top when to_top is True."""
        try:
            page = await self._ensure_page()
            if to_top:
                await page.evaluate("window.scrollTo(0, 0)")
            else:
                await page.evaluate("window.scrollBy(0, -window.innerHeight)")
            return ToolResult(success=True)
        except Exception as exc:
            return ToolResult(success=False, message=f"Failed to scroll up: {exc}")

    async def scroll_down(self, to_bottom: Optional[bool] = None) -> ToolResult:
        """Scroll down one viewport, or jump to the page bottom when to_bottom is True."""
        try:
            page = await self._ensure_page()
            if to_bottom:
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            else:
                await page.evaluate("window.scrollBy(0, window.innerHeight)")
            return ToolResult(success=True)
        except Exception as exc:
            return ToolResult(success=False, message=f"Failed to scroll down: {exc}")

    async def screenshot(self, full_page: Optional[bool] = False) -> bytes:
        """Return a PNG screenshot of the current page."""
        page = await self._ensure_page()
        return await page.screenshot(full_page=bool(full_page), type="png")

    async def console_exec(self, javascript: str) -> ToolResult:
        """Execute JavaScript in the page with browser-console semantics."""
        try:
            page = await self._ensure_page()
            result = await page.evaluate(javascript)
            return ToolResult(success=True, data={"result": result})
        except Exception as exc:
            return ToolResult(success=False, message=f"Failed to execute JavaScript: {exc}")

    async def console_view(self, max_lines: Optional[int] = None) -> ToolResult:
        """Return console output captured via Playwright console events."""
        try:
            await self._ensure_page()
            logs = list(self._console_logs)
            if max_lines is not None:
                logs = logs[-max_lines:]
            return ToolResult(success=True, data={"logs": logs})
        except Exception as exc:
            return ToolResult(success=False, message=f"Failed to view console: {exc}")
