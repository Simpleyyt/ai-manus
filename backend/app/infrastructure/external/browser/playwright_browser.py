from typing import Dict, Any, Optional, List
from playwright.async_api import async_playwright, Browser, Page
import asyncio
from markdownify import markdownify
from app.infrastructure.external.llm.openai_llm import OpenAILLM
from app.core.config import get_settings
from app.domain.models.tool_result import ToolResult
import logging

# Set up logger for this module
logger = logging.getLogger(__name__)

class PlaywrightBrowser:
    """Playwright client that provides specific implementation of browser operations
    
    Enhanced with:
    - Vision-Enhanced Navigation (bounding boxes)
    - Smart scroll for infinite scroll pages
    - Automatic error handling (popups, cookie banners, timeouts)
    """
    
    def __init__(self, cdp_url: str):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self.llm = OpenAILLM()
        self.settings = get_settings()
        self.cdp_url = cdp_url
        
    async def initialize(self):
        """Initialize and ensure resources are available"""
        # Add retry logic
        max_retries = 5
        retry_delay = 1  # Initial wait 1 second
        for attempt in range(max_retries):
            try:
                self.playwright = await async_playwright().start()
                # Connect to existing Chrome instance
                self.browser = await self.playwright.chromium.connect_over_cdp(self.cdp_url)
                # Get all contexts
                contexts = self.browser.contexts
                if contexts and len(contexts[0].pages) == 1:
                    # Check if it's the initial page (by URL)
                    page = contexts[0].pages[0]
                    page_url = await page.evaluate("window.location.href")
                    if (
                        page_url == "about:blank" or 
                        page_url == "chrome://newtab/" or 
                        page_url == "chrome://new-tab-page/" or 
                        not page_url
                    ):
                        # Only use it when it's the initial page and only one tab
                        self.page = page
                    else:
                        # Not the initial page, create a new page
                        self.page = await contexts[0].new_page()
                else:
                    # Create a new page in other cases
                    context = contexts[0] if contexts else await self.browser.new_context()
                    self.page = await context.new_page()
                return True
            except Exception as e:
                # Clean up failed resources
                await self.cleanup()
                
                # Return error if maximum retry count is reached
                if attempt == max_retries - 1:
                    logger.error(f"Initialization failed (retried {max_retries} times): {e}")
                    return False
                
                # Otherwise increase waiting time (exponential backoff strategy)
                retry_delay = min(retry_delay * 2, 10)  # Maximum wait 10 seconds
                logger.warning(f"Initialization failed, will retry in {retry_delay} seconds: {e}")
                await asyncio.sleep(retry_delay)

    async def cleanup(self):
        """Clean up Playwright resources, first close all tabs, then close the browser"""
        try:
            # If browser exists, first close all tabs
            if self.browser:
                # Get all contexts
                contexts = self.browser.contexts
                if contexts:
                    for context in contexts:
                        # Get all pages in the context
                        pages = context.pages
                        # Close all pages
                        for page in pages:
                            # Avoid closing self.page multiple times
                            if page != self.page or (self.page and not self.page.is_closed()):
                                await page.close()
            
            # Ensure the current page is closed (if it exists and is not closed)
            if self.page and not self.page.is_closed():
                await self.page.close()
                
            # Close the browser
            if self.browser:
                await self.browser.close()
                
            # Stop playwright
            if self.playwright:
                await self.playwright.stop()
                
        except Exception as e:
            logger.error(f"Error occurred when cleaning up resources: {e}")
        finally:
            # Reset references
            self.page = None
            self.browser = None
            self.playwright = None
    
    async def _ensure_browser(self):
        """Ensure the browser is started"""
        if not self.browser or not self.page:
            if not await self.initialize():
                raise Exception("Unable to initialize browser resources")
    
    async def _ensure_page(self):
        """Ensure the page is created and update to the current active tab (rightmost tab)"""
        await self._ensure_browser()
        if not self.page:
            self.page = await self.browser.new_page()
        else:
            # Get all contexts
            contexts = self.browser.contexts
            if contexts:
                # Get all pages in the current context
                current_context = contexts[0]
                pages = current_context.pages
                
                if pages:
                    # Get the rightmost tab (usually the most recently opened page)
                    rightmost_page = pages[-1]
                    
                    # Update if the current page is not the rightmost tab
                    if self.page != rightmost_page:
                        # Update to the rightmost tab
                        self.page = rightmost_page
    
    async def wait_for_page_load(self, timeout: int = 15) -> bool:
        """Wait for the page to finish loading, waiting up to the specified timeout
        
        Args:
            timeout: Maximum wait time (seconds), default is 15 seconds
            
        Returns:
            bool: Whether successfully waited for the page to load completely
        """
        await self._ensure_page()
        
        start_time = asyncio.get_event_loop().time()
        check_interval = 5  # Check every 5 seconds
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            # Check if the page has completely loaded
            is_loaded = await self.page.evaluate("""() => {
                return document.readyState === 'complete';
            }""")
            
            if is_loaded:
                return True
                
            # Wait for a while before checking again
            await asyncio.sleep(check_interval)
        
        # Timeout, page loading not completed
        return False
    
    async def _extract_content(self) -> Dict[str, Any]:
        """Extract content from the current page"""

        # Execute JavaScript to get elements in the viewport    
        visible_content = await self.page.evaluate("""() => {
            const visibleElements = [];
            const viewportHeight = window.innerHeight;
            const viewportWidth = window.innerWidth;
            
            // Get all potentially relevant elements
            const elements = document.querySelectorAll('body *');
            
            for (const element of elements) {
                // Check if the element is in the viewport and visible
                const rect = element.getBoundingClientRect();
                
                // Element must have some dimensions
                if (rect.width === 0 || rect.height === 0) continue;
                
                // Element must be within the viewport
                if (
                    rect.bottom < 0 || 
                    rect.top > viewportHeight ||
                    rect.right < 0 || 
                    rect.left > viewportWidth
                ) continue;
                
                // Check if the element is visible (not hidden by CSS)
                const style = window.getComputedStyle(element);
                if (
                    style.display === 'none' || 
                    style.visibility === 'hidden' || 
                    style.opacity === '0'
                ) continue;
                
                // If it's a text node or meaningful element, add it to the results
                if (
                    element.innerText || 
                    element.tagName === 'IMG' || 
                    element.tagName === 'INPUT' || 
                    element.tagName === 'BUTTON'
                ) {
                    visibleElements.push(element.outerHTML);
                }
            }
            
            // Build HTML containing these visible elements
            return '<div>' + visibleElements.join('') + '</div>';
        }""")

        
        # Convert to Markdown
        markdown_content = markdownify(visible_content)

        max_content_length = min(50000, len(markdown_content))
        response = await self.llm.ask([{
            "role": "system",
            "content": "You are a professional web page information extraction assistant. Please extract all information from the current page content and convert it to Markdown format."
        },
        {
            "role": "user",
            "content": markdown_content[:max_content_length]
        }
        ])
        
        return response.get("content", "")
    
    async def view_page(self) -> ToolResult:
        """View visible elements within the current page's viewport and convert to Markdown format"""
        await self._ensure_page()
        
        # Wait for the page to load completely, maximum wait 15 seconds
        await self.wait_for_page_load()
        
        # First update the interactive elements cache
        interactive_elements = await self._extract_interactive_elements()
        
        return ToolResult(
            success=True,
            data={
                "interactive_elements": interactive_elements,
                "content": await self._extract_content(),
            }
        )
    
    async def _extract_interactive_elements(self) -> List[str]:
        """Return a list of visible interactive elements on the page, formatted as index:<tag>text</tag>"""
        await self._ensure_page()
        
        # Clear the current page's cache to ensure we always get the latest list of elements
        self.page.interactive_elements_cache = []
        
        # Execute JavaScript to get interactive elements in the viewport
        interactive_elements = await self.page.evaluate("""() => {
            const interactiveElements = [];
            const viewportHeight = window.innerHeight;
            const viewportWidth = window.innerWidth;
            
            // Get all potentially relevant interactive elements
            const elements = document.querySelectorAll('button, a, input, textarea, select, [role="button"], [tabindex]:not([tabindex="-1"])');
            
            let validElementIndex = 0; // For generating consecutive indices
            
            for (let i = 0; i < elements.length; i++) {
                const element = elements[i];
                // Check if the element is in the viewport and visible
                const rect = element.getBoundingClientRect();
                
                // Element must have some dimensions
                if (rect.width === 0 || rect.height === 0) continue;
                
                // Element must be within the viewport
                if (
                    rect.bottom < 0 || 
                    rect.top > viewportHeight ||
                    rect.right < 0 || 
                    rect.left > viewportWidth
                ) continue;
                
                // Check if the element is visible (not hidden by CSS)
                const style = window.getComputedStyle(element);
                if (
                    style.display === 'none' || 
                    style.visibility === 'hidden' || 
                    style.opacity === '0'
                ) continue;
                
                
                // Get element type and text
                let tagName = element.tagName.toLowerCase();
                let text = '';
                
                if (element.value && ['input', 'textarea', 'select'].includes(tagName)) {
                    text = element.value;
                    
                    // Add label and placeholder information for input elements
                    if (tagName === 'input') {
                        // Get associated label text
                        let labelText = '';
                        if (element.id) {
                            const label = document.querySelector(`label[for="${element.id}"]`);
                            if (label) {
                                labelText = label.innerText.trim();
                            }
                        }
                        
                        // Look for parent or sibling label
                        if (!labelText) {
                            const parentLabel = element.closest('label');
                            if (parentLabel) {
                                labelText = parentLabel.innerText.trim().replace(element.value, '').trim();
                            }
                        }
                        
                        // Add label information
                        if (labelText) {
                            text = `[Label: ${labelText}] ${text}`;
                        }
                        
                        // Add placeholder information
                        if (element.placeholder) {
                            text = `${text} [Placeholder: ${element.placeholder}]`;
                        }
                    }
                } else if (element.innerText) {
                    text = element.innerText.trim().replace(/\\s+/g, ' ');
                } else if (element.alt) { // For image buttons
                    text = element.alt;
                } else if (element.title) { // For elements with title
                    text = element.title;
                } else if (element.placeholder) { // For placeholder text
                    text = `[Placeholder: ${element.placeholder}]`;
                } else if (element.type) { // For input type
                    text = `[${element.type}]`;
                    
                    // Add label and placeholder information for text-less input elements
                    if (tagName === 'input') {
                        // Get associated label text
                        let labelText = '';
                        if (element.id) {
                            const label = document.querySelector(`label[for="${element.id}"]`);
                            if (label) {
                                labelText = label.innerText.trim();
                            }
                        }
                        
                        // Look for parent or sibling label
                        if (!labelText) {
                            const parentLabel = element.closest('label');
                            if (parentLabel) {
                                labelText = parentLabel.innerText.trim();
                            }
                        }
                        
                        // Add label information
                        if (labelText) {
                            text = `[Label: ${labelText}] ${text}`;
                        }
                        
                        // Add placeholder information
                        if (element.placeholder) {
                            text = `${text} [Placeholder: ${element.placeholder}]`;
                        }
                    }
                } else {
                    text = '[No text]';
                }
                
                // Maximum limit on text length to keep it clear
                if (text.length > 100) {
                    text = text.substring(0, 97) + '...';
                }
                
                // Only add data-manus-id attribute to elements that meet the conditions
                element.setAttribute('data-manus-id', `manus-element-${validElementIndex}`);
                                                        
                // Build selector - using only data-manus-id
                const selector = `[data-manus-id="manus-element-${validElementIndex}"]`;
                
                // Add element information to the array
                interactiveElements.push({
                    index: validElementIndex,  // Use consecutive index
                    tag: tagName,
                    text: text,
                    selector: selector
                });
                
                validElementIndex++; // Increment valid element counter
            }
            
            return interactiveElements;
        }""")
        
        # Update cache
        self.page.interactive_elements_cache = interactive_elements
        
        # Format element information in specified format
        formatted_elements = []
        for el in interactive_elements:
            formatted_elements.append(f"{el['index']}:<{el['tag']}>{el['text']}</{el['tag']}>")
        
        return formatted_elements
    
    async def navigate(self, url: str, timeout: Optional[int] = 15000) -> ToolResult:
        """Navigate to the specified URL
        
        Args:
            url: URL to navigate to
            timeout: Navigation timeout (milliseconds), default is 60 seconds
        """
        await self._ensure_page()
        try:
            # Clear cache as the page is about to change
            self.page.interactive_elements_cache = []
            try:
                await self.page.goto(url, timeout=timeout)
            except Exception as e:
                logger.warning(f"Failed to navigate to {url}: {str(e)}")
            return ToolResult(
                success=True,
                data={
                    "interactive_elements": await self._extract_interactive_elements(),
                }
            )
        except Exception as e:
            return ToolResult(success=False, message=f"Failed to navigate to {url}: {str(e)}")
    
    async def restart(self, url: str) -> ToolResult:
        """Restart the browser and navigate to the specified URL"""
        await self.cleanup()
        return await self.navigate(url)

    
    async def _get_element_by_index(self, index: int) -> Optional[Any]:
        """Get element by index using data-manus-id selector
        
        Args:
            index: Element index
            
        Returns:
            The found element, or None if not found
        """
        # Check if there are cached elements
        if not hasattr(self.page, 'interactive_elements_cache') or not self.page.interactive_elements_cache or index >= len(self.page.interactive_elements_cache):
            return None
        
        # Use data-manus-id selector
        selector = f'[data-manus-id="manus-element-{index}"]'
        return await self.page.query_selector(selector)
    
    async def click(
        self,
        index: Optional[int] = None,
        coordinate_x: Optional[float] = None,
        coordinate_y: Optional[float] = None
    ) -> ToolResult:
        """Click an element"""
        await self._ensure_page()
        if coordinate_x is not None and coordinate_y is not None:
            await self.page.mouse.click(coordinate_x, coordinate_y)
        elif index is not None:
            try:
                element = await self._get_element_by_index(index)
                if not element:
                    return ToolResult(success=False, message=f"Cannot find interactive element with index {index}")
                
                # Check if the element is visible
                is_visible = await self.page.evaluate("""(element) => {
                    if (!element) return false;
                    const rect = element.getBoundingClientRect();
                    const style = window.getComputedStyle(element);
                    return !(
                        rect.width === 0 || 
                        rect.height === 0 || 
                        style.display === 'none' || 
                        style.visibility === 'hidden' || 
                        style.opacity === '0'
                    );
                }""", element)
                
                if not is_visible:
                    # Try to scroll to the element position
                    await self.page.evaluate("""(element) => {
                        if (element) {
                            element.scrollIntoView({behavior: 'smooth', block: 'center'});
                        }
                    }""", element)
                    # Wait for the element to become visible
                    await asyncio.sleep(1)
                
                # Try to click the element
                await element.click(timeout=5000)
            except Exception as e:
                return ToolResult(success=False, message=f"Failed to click element: {str(e)}")
        return ToolResult(success=True)
    
    async def input(
        self,
        text: str,
        press_enter: bool,
        index: Optional[int] = None,
        coordinate_x: Optional[float] = None,
        coordinate_y: Optional[float] = None
    ) -> ToolResult:
        """Input text"""
        await self._ensure_page()
        if coordinate_x is not None and coordinate_y is not None:
            await self.page.mouse.click(coordinate_x, coordinate_y)
            await self.page.keyboard.type(text)
        elif index is not None:
            try:
                element = await self._get_element_by_index(index)
                if not element:
                    return ToolResult(success=False, message=f"Cannot find interactive element with index {index}")
                
                # Try to use fill() method, but catch possible errors
                try:
                    await element.fill("")
                    await element.type(text)
                except Exception as e:
                    # If fill() fails, use type() method directly
                    await element.click()
                    await self.page.keyboard.type(text)
            except Exception as e:
                return ToolResult(success=False, message=f"Failed to input text: {str(e)}")
        
        if press_enter:
            await self.page.keyboard.press("Enter")
        return ToolResult(success=True)
    
    async def move_mouse(
        self,
        coordinate_x: float,
        coordinate_y: float
    ) -> ToolResult:
        """Move the mouse"""
        await self._ensure_page()
        await self.page.mouse.move(coordinate_x, coordinate_y)
        return ToolResult(success=True)
    
    async def press_key(self, key: str) -> ToolResult:
        """Simulate key press"""
        await self._ensure_page()
        await self.page.keyboard.press(key)
        return ToolResult(success=True)
    
    async def select_option(
        self,
        index: int,
        option: int
    ) -> ToolResult:
        """Select dropdown option"""
        await self._ensure_page()
        try:
            element = await self._get_element_by_index(index)
            if not element:
                return ToolResult(success=False, message=f"Cannot find selector element with index {index}")
            
            # Try to select the option
            await element.select_option(index=option)
            return ToolResult(success=True)
        except Exception as e:
            return ToolResult(success=False, message=f"Failed to select option: {str(e)}")
    
    async def scroll_up(
        self,
        to_top: Optional[bool] = None
    ) -> ToolResult:
        """Scroll up"""
        await self._ensure_page()
        if to_top:
            await self.page.evaluate("window.scrollTo(0, 0)")
        else:
            await self.page.evaluate("window.scrollBy(0, -window.innerHeight)")
        return ToolResult(success=True)
    
    async def scroll_down(
        self,
        to_bottom: Optional[bool] = None
    ) -> ToolResult:
        """Scroll down"""
        await self._ensure_page()
        if to_bottom:
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        else:
            await self.page.evaluate("window.scrollBy(0, window.innerHeight)")
        return ToolResult(success=True)
    
    async def screenshot(
        self,
        full_page: Optional[bool] = False
    ) -> bytes:
        """Take a screenshot of the current page
        
        Args:
            full_page: Whether to capture the full page or just the viewport
            
        Returns:
            bytes: PNG screenshot data
        """
        await self._ensure_page()
        
        # Configure screenshot options
        screenshot_options = {
            "full_page": full_page,
            "type": "png"
        }
        
        # Return bytes data directly
        return await self.page.screenshot(**screenshot_options)
    
    async def console_exec(self, javascript: str) -> ToolResult:
        """Execute JavaScript code"""
        await self._ensure_page()
        result = await self.page.evaluate(javascript)
        return ToolResult(success=True, data={"result": result})
    
    async def console_view(self, max_lines: Optional[int] = None) -> ToolResult:
        """View browser console output"""
        await self._ensure_page()
        logs = await self.page.evaluate("""() => {
            return window.console.logs || [];
        }""")
        if max_lines is not None:
            logs = logs[-max_lines:]
        return ToolResult(success=True, data={"logs": logs})
    
    # ========== Enhanced Features ==========
    
    async def _handle_common_popups(self) -> None:
        """
        Automatically detect and close common popups, cookie banners, and overlays.
        This prevents them from blocking interactions with the main page content.
        """
        # Common cookie banner selectors
        cookie_selectors = [
            # Generic patterns
            'button:has-text("Accept")',
            'button:has-text("Accept All")',
            'button:has-text("Accept Cookies")',
            'button:has-text("I Accept")',
            'button:has-text("Agree")',
            'button:has-text("OK")',
            'button:has-text("Got it")',
            'button:has-text("Allow")',
            '[class*="cookie"] button:has-text("Accept")',
            '[class*="cookie"] button:has-text("OK")',
            '[class*="gdpr"] button:has-text("Accept")',
            '[id*="cookie"] button:has-text("Accept")',
            # Specific frameworks
            '.cc-banner button.cc-allow',
            '.cc-compliance button.cc-allow',
            '#onetrust-accept-btn-handler',
            '.optanon-allow-all-button',
            '[aria-label*="Accept cookies"]',
            '[aria-label*="Accept all"]',
        ]
        
        # Try to close cookie banners
        for selector in cookie_selectors:
            try:
                element = await self.page.query_selector(selector)
                if element:
                    is_visible = await element.is_visible()
                    if is_visible:
                        await element.click(timeout=2000)
                        logger.info(f"Closed cookie banner using selector: {selector}")
                        await asyncio.sleep(0.5)
                        break
            except Exception:
                continue
        
        # Close modal dialogs and popups
        modal_selectors = [
            '[class*="modal"] button[class*="close"]',
            '[class*="popup"] button[class*="close"]',
            '[class*="overlay"] button[class*="close"]',
            'button[aria-label="Close"]',
            'button[aria-label="close"]',
            '[class*="close-button"]',
            '.modal-close',
            '.popup-close',
        ]
        
        for selector in modal_selectors:
            try:
                elements = await self.page.query_selector_all(selector)
                for element in elements:
                    is_visible = await element.is_visible()
                    if is_visible:
                        await element.click(timeout=2000)
                        logger.info(f"Closed modal using selector: {selector}")
                        await asyncio.sleep(0.3)
            except Exception:
                continue
    
    async def smart_scroll(
        self,
        direction: str = "down",
        max_scrolls: int = 10,
        check_for_new_content: bool = True
    ) -> ToolResult:
        """
        Smart scrolling that handles infinite scroll pages intelligently.
        
        Args:
            direction: 'down' or 'up'
            max_scrolls: Maximum number of scroll attempts
            check_for_new_content: If True, stops when no new content is loaded
            
        Returns:
            ToolResult with scroll statistics
        """
        await self._ensure_page()
        
        stats = {
            "scrolls_performed": 0,
            "content_height_start": 0,
            "content_height_end": 0,
            "new_content_loaded": False
        }
        
        # Get initial page height
        initial_height = await self.page.evaluate("document.body.scrollHeight")
        stats["content_height_start"] = initial_height
        
        scroll_pause_time = 1.5  # Wait for content to load
        last_height = initial_height
        scrolls_without_change = 0
        max_scrolls_without_change = 3
        
        for scroll_num in range(max_scrolls):
            # Perform scroll
            if direction == "down":
                await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            else:  # up
                await self.page.evaluate("window.scrollTo(0, 0)")
            
            stats["scrolls_performed"] += 1
            
            # Wait for new content to load
            await asyncio.sleep(scroll_pause_time)
            
            if check_for_new_content and direction == "down":
                # Check if new content loaded
                new_height = await self.page.evaluate("document.body.scrollHeight")
                
                if new_height > last_height:
                    stats["new_content_loaded"] = True
                    scrolls_without_change = 0
                    logger.info(f"New content loaded: {new_height} > {last_height}")
                else:
                    scrolls_without_change += 1
                    logger.info(f"No new content after scroll {scroll_num + 1}")
                
                last_height = new_height
                
                # Stop if no new content for multiple scrolls
                if scrolls_without_change >= max_scrolls_without_change:
                    logger.info("Reached end of content (infinite scroll)")
                    break
        
        # Get final height
        final_height = await self.page.evaluate("document.body.scrollHeight")
        stats["content_height_end"] = final_height
        
        return ToolResult(success=True, data=stats)
    
    async def navigate_with_error_handling(
        self,
        url: str,
        max_retries: int = 3,
        handle_popups: bool = True,
        timeout: int = 30000
    ) -> ToolResult:
        """
        Navigate to URL with automatic retry and error handling.
        Automatically handles popups, cookie banners, and timeouts.
        
        Args:
            url: Target URL
            max_retries: Number of retry attempts
            handle_popups: Auto-close popups after navigation
            timeout: Navigation timeout in milliseconds
            
        Returns:
            ToolResult with navigation result
        """
        await self._ensure_page()
        
        result = {
            "success": False,
            "url": url,
            "attempts": 0,
            "error": None,
            "interactive_elements": []
        }
        
        for attempt in range(max_retries):
            result["attempts"] = attempt + 1
            
            try:
                logger.info(f"Navigation attempt {attempt + 1}/{max_retries} to {url}")
                
                # Try to navigate
                response = await self.page.goto(
                    url,
                    timeout=timeout,
                    wait_until="domcontentloaded"  # More forgiving than "load"
                )
                
                # Wait a bit for JavaScript to initialize
                await asyncio.sleep(1)
                
                # Handle popups if requested
                if handle_popups:
                    await self._handle_common_popups()
                
                # Extract interactive elements
                result["interactive_elements"] = await self._extract_interactive_elements()
                
                result["success"] = True
                result["status_code"] = response.status if response else None
                logger.info(f"Successfully navigated to {url}")
                break
                
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Navigation attempt {attempt + 1} failed: {error_msg}")
                result["error"] = error_msg
                
                # Don't retry certain errors
                if "net::ERR_NAME_NOT_RESOLVED" in error_msg:
                    logger.error(f"DNS resolution failed for {url}, not retrying")
                    break
                
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(f"Waiting {wait_time}s before retry...")
                    await asyncio.sleep(wait_time)
        
        return ToolResult(success=result["success"], data=result, message=result.get("error"))
