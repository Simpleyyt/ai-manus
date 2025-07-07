from typing import Optional, Dict, Any, List
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from app.domain.models.tool_result import ToolResult
import logging
import re
import json
import os
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

class Crawl4AIBrowser:
    """Pure HTTP based browser implementation for fast content extraction"""
    
    def __init__(self):
        self.session = None
        self.current_url = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        self.retry_count = 0
        self.max_retries = 3
        
    async def _get_session(self):
        """Get or create aiohttp session"""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout, headers=self.headers)
        return self.session
        
    async def view_page(self, url: str = None) -> ToolResult:
        """View page content using pure HTTP requests"""
        if url:
            self.current_url = url
            
        if not self.current_url:
            return ToolResult(success=False, message="No URL provided")
            
        try:
            logger.info(f"HTTP Browser: Viewing page {self.current_url}")
            
            session = await self._get_session()
            
            # 发送HTTP请求获取页面内容
            async with session.get(self.current_url) as response:
                if response.status != 200:
                    return ToolResult(success=False, message=f"HTTP {response.status}: {response.reason}")
                
                content_type = response.headers.get('content-type', '').lower()
                
                if 'text/html' in content_type:
                    # HTML页面，解析内容
                    try:
                        html_content = await response.text()
                    except UnicodeDecodeError:
                        # 如果UTF-8解码失败，尝试其他编码
                        html_content = await response.read()
                        html_content = html_content.decode('gbk', errors='ignore')
                    
                    # 检查是否遇到反爬虫验证码
                    if self._is_anti_bot_page(html_content):
                        logger.warning(f"Detected anti-bot verification page for {self.current_url}")
                        return ToolResult(
                            success=False, 
                            message=f"遇到反爬虫验证码，请稍后重试或更换数据源。当前页面: {self.current_url}"
                        )
                    
                    content = await self._extract_content_from_html(html_content, self.current_url)
                    interactive_elements = await self._extract_interactive_elements_from_html(html_content, self.current_url)
                else:
                    # 非HTML内容，直接返回
                    try:
                        content = await response.text()
                    except UnicodeDecodeError:
                        # 如果UTF-8解码失败，尝试其他编码
                        content_bytes = await response.read()
                        content = content_bytes.decode('gbk', errors='ignore')
                    interactive_elements = []
                
                return ToolResult(
                    success=True,
                    data={
                        "content": content,
                        "interactive_elements": interactive_elements,
                        "url": self.current_url,
                        "screenshot": None
                    }
                )
                
        except Exception as e:
            logger.error(f"HTTP Browser view failed: {e}")
            return ToolResult(success=False, message=f"Failed to view page: {str(e)}")
    
    def _is_anti_bot_page(self, html_content: str) -> bool:
        """检测是否为反爬虫验证页面"""
        anti_bot_indicators = [
            "访问过于频繁",
            "验证码校验",
            "antibot",
            "verifycode",
            "captcha",
            "请完成验证",
            "请在五分钟内完成验证"
        ]
        
        html_lower = html_content.lower()
        for indicator in anti_bot_indicators:
            if indicator.lower() in html_lower:
                return True
        return False
    
    async def _extract_content_from_html(self, html_content: str, base_url: str) -> str:
        """Extract readable content from HTML"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 移除脚本和样式标签
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # 获取页面标题
            title = soup.find('title')
            title_text = title.get_text().strip() if title else ""
            
            # 获取主要内容
            content_parts = []
            
            # 添加标题
            if title_text:
                content_parts.append(f"# {title_text}\n")
            
            # 提取段落和标题
            for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div']):
                text = element.get_text().strip()
                if text and len(text) > 10:  # 过滤太短的文本
                    tag_name = element.name
                    if tag_name.startswith('h'):
                        level = int(tag_name[1])
                        content_parts.append(f"{'#' * level} {text}\n")
                    else:
                        content_parts.append(f"{text}\n\n")
            
            # 提取链接
            links = soup.find_all('a', href=True)
            if links:
                content_parts.append("\n## 链接\n")
                for i, link in enumerate(links[:10]):  # 限制链接数量
                    href = link.get('href')
                    text = link.get_text().strip()
                    if text and href:
                        # 处理相对URL
                        if not href.startswith('http'):
                            href = urljoin(base_url, href)
                        content_parts.append(f"{i+1}. [{text}]({href})\n")
            
            return '\n'.join(content_parts)
            
        except Exception as e:
            logger.error(f"Failed to extract content from HTML: {e}")
            return "Content extraction failed"
    
    async def _extract_interactive_elements_from_html(self, html_content: str, base_url: str) -> List[Dict[str, Any]]:
        """Extract interactive elements from HTML"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            elements = []
            index = 0
            
            # 提取链接
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                text = link.get_text().strip()
                if text and href:
                    if not href.startswith('http'):
                        href = urljoin(base_url, href)
                    elements.append({
                        'index': index,
                        'tag': 'a',
                        'text': text,
                        'href': href
                    })
                    index += 1
            
            # 提取按钮
            for button in soup.find_all(['button', 'input']):
                if button.name == 'button':
                    text = button.get_text().strip()
                    if text:
                        elements.append({
                            'index': index,
                            'tag': 'button',
                            'text': text
                        })
                        index += 1
                elif button.name == 'input':
                    input_type = button.get('type', 'text')
                    placeholder = button.get('placeholder', '')
                    value = button.get('value', '')
                    text = placeholder or value or f"Input ({input_type})"
                    elements.append({
                        'index': index,
                        'tag': 'input',
                        'text': text,
                        'type': input_type
                    })
                    index += 1
            
            return elements
            
        except Exception as e:
            logger.error(f"Failed to extract interactive elements: {e}")
            return []
    
    async def navigate(self, url: str) -> ToolResult:
        """Navigate to URL and get content"""
        self.current_url = url
        return await self.view_page()
    
    async def restart(self, url: str) -> ToolResult:
        """Restart and navigate to URL"""
        self.current_url = url
        return await self.view_page()
    
    async def click(self, index: Optional[int] = None, coordinate_x: Optional[float] = None, coordinate_y: Optional[float] = None) -> ToolResult:
        """Simulate clicking by following links"""
        if not self.current_url:
            return ToolResult(success=False, message="No current page to click on")
            
        try:
            # 重新获取当前页面的交互元素
            session = await self._get_session()
            async with session.get(self.current_url) as response:
                if response.status != 200:
                    return ToolResult(success=False, message=f"Failed to get current page: HTTP {response.status}")
                
                html_content = await response.text()
                interactive_elements = await self._extract_interactive_elements_from_html(html_content, self.current_url)
            
            if index is not None and index < len(interactive_elements):
                element = interactive_elements[index]
                if 'href' in element and element['href']:
                    # 如果是链接，直接导航
                    target_url = element['href']
                    return await self.navigate(target_url)
                else:
                    return ToolResult(success=True, message=f"Clicked element {index}: {element.get('text', '')}")
            else:
                return ToolResult(success=False, message=f"Invalid element index: {index}")
                
        except Exception as e:
            return ToolResult(success=False, message=f"Click failed: {e}")
    
    async def input(self, text: str, press_enter: bool, index: Optional[int] = None, coordinate_x: Optional[float] = None, coordinate_y: Optional[float] = None) -> ToolResult:
        """Simulate text input (not fully supported in HTTP mode)"""
        return ToolResult(success=True, message=f"Input '{text}' simulated (HTTP mode)")
    
    async def move_mouse(self, coordinate_x: float, coordinate_y: float) -> ToolResult:
        """Move mouse (not applicable in HTTP mode)"""
        return ToolResult(success=True, message="Mouse movement simulated (HTTP mode)")
    
    async def press_key(self, key: str) -> ToolResult:
        """Simulate key press (not applicable in HTTP mode)"""
        return ToolResult(success=True, message=f"Key '{key}' pressed (HTTP mode)")
    
    async def select_option(self, index: int, option: int) -> ToolResult:
        """Select dropdown option (not fully supported in HTTP mode)"""
        return ToolResult(success=True, message=f"Selected option {option} from element {index} (HTTP mode)")
    
    async def scroll_up(self, to_top: Optional[bool] = None) -> ToolResult:
        """Scroll up (not applicable in HTTP mode)"""
        return ToolResult(success=True, message="Scroll up simulated (HTTP mode)")
    
    async def scroll_down(self, to_bottom: Optional[bool] = None) -> ToolResult:
        """Scroll down (not applicable in HTTP mode)"""
        return ToolResult(success=True, message="Scroll down simulated (HTTP mode)")
    
    async def screenshot(self, full_page: Optional[bool] = False) -> bytes:
        """Take screenshot (not supported in HTTP mode)"""
        return b''
    
    async def console_exec(self, javascript: str) -> ToolResult:
        """Execute JavaScript (not supported in HTTP mode)"""
        return ToolResult(success=False, message="JavaScript execution not supported in HTTP mode")
    
    async def console_view(self, max_lines: Optional[int] = None) -> ToolResult:
        """View console output (not applicable in HTTP mode)"""
        return ToolResult(success=True, data={"logs": []})
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
            self.session = None 