#!/bin/bash

echo "=== Docker Crawl4AI Browser Test ==="

# 构建新的 Docker 镜像
echo "Building Docker image with Playwright browsers..."
docker-compose build backend

# 启动服务
echo "Starting services..."
docker-compose up -d

# 等待服务启动
echo "Waiting for services to start..."
sleep 10

# 测试 Crawl4AI 浏览器
echo "Testing Crawl4AI browser..."
docker-compose exec backend python -c "
import asyncio
import sys
import os
sys.path.append('/app')

from app.infrastructure.external.browser.crawl4ai_browser import Crawl4AIBrowser

async def test_crawl4ai():
    browser = Crawl4AIBrowser()
    
    # 测试基本功能
    print('Testing Crawl4AI browser...')
    
    # 测试页面浏览
    result = await browser.view_page('https://www.baidu.com')
    print(f'View page result: {result.success}')
    if result.success:
        print(f'Content length: {len(result.data.get(\"content\", \"\"))}')
        print(f'Interactive elements: {len(result.data.get(\"interactive_elements\", []))}')
    
    # 测试导航
    result = await browser.navigate('https://www.google.com')
    print(f'Navigate result: {result.success}')
    
    # 测试点击（模拟）
    result = await browser.click(0)
    print(f'Click result: {result.success}')
    
    # 测试输入（模拟）
    result = await browser.input('test', True)
    print(f'Input result: {result.success}')
    
    await browser.cleanup()
    print('Crawl4AI test completed!')

asyncio.run(test_crawl4ai())
"

# 测试传统浏览器
echo "Testing traditional browser..."
docker-compose exec backend python -c "
import asyncio
import sys
import os
sys.path.append('/app')

from app.infrastructure.external.browser.playwright_browser import PlaywrightBrowser

async def test_playwright():
    browser = PlaywrightBrowser()
    
    # 测试基本功能
    print('Testing Playwright browser...')
    
    # 测试页面浏览
    result = await browser.view_page('https://www.baidu.com')
    print(f'View page result: {result.success}')
    if result.success:
        print(f'Content length: {len(result.data.get(\"content\", \"\"))}')
        print(f'Screenshot size: {len(result.data.get(\"screenshot\", b\"\"))}')
    
    # 测试导航
    result = await browser.navigate('https://www.google.com')
    print(f'Navigate result: {result.success}')
    
    await browser.cleanup()
    print('Playwright test completed!')

asyncio.run(test_playwright())
"

# 测试浏览器工具类
echo "Testing browser tool class..."
docker-compose exec backend python -c "
import asyncio
import sys
import os
sys.path.append('/app')

from app.infrastructure.external.browser.browser_tool import BrowserTool

async def test_browser_tool():
    tool = BrowserTool()
    
    print('Testing browser tool class...')
    
    # 测试快速模式
    print('Testing fast mode (Crawl4AI)...')
    result = await tool.view_page('https://www.baidu.com', use_fast_mode=True)
    print(f'Fast mode result: {result.success}')
    
    # 测试完整模式
    print('Testing full mode (Playwright)...')
    result = await tool.view_page('https://www.google.com', use_fast_mode=False)
    print(f'Full mode result: {result.success}')
    
    await tool.cleanup()
    print('Browser tool test completed!')

asyncio.run(test_browser_tool())
"

echo "=== Docker Test Completed ==="
echo "You can now access the application at:"
echo "- Frontend: http://localhost:5173"
echo "- Backend: http://localhost:8000" 