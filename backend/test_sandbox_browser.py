#!/usr/bin/env python3
"""
沙盒浏览器功能测试脚本
测试沙盒中的浏览器工具是否正常工作
"""

import asyncio
import sys
import os
import time
from typing import List, Dict, Any

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.domain.services.tools.browser import BrowserTool
from app.infrastructure.external.browser.crawl4ai_browser import Crawl4AIBrowser
from app.domain.models.tool_result import ToolResult

class SandboxBrowserTester:
    def __init__(self):
        self.crawl4ai_browser = Crawl4AIBrowser()
        self.test_results = []
        
    async def test_sandbox_browser(self) -> bool:
        """测试沙盒中的浏览器功能"""
        print("🧪 开始测试沙盒浏览器功能...")
        
        try:
            # 测试页面浏览
            url = "https://httpbin.org/html"
            print(f"📄 正在访问: {url}")
            
            result = await self.crawl4ai_browser.view_page(url)
            
            if result.success:
                print("✅ 页面查看成功")
                if result.data and 'content' in result.data:
                    content = result.data['content']
                    print(f"📝 内容长度: {len(content)} 字符")
                    print(f"📝 内容预览: {content[:200]}...")
                    return True
                else:
                    print("❌ 没有返回内容数据")
                    return False
            else:
                print(f"❌ 页面查看失败: {result.message}")
                return False
                
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            return False

async def main():
    print("🚀 开始沙盒浏览器功能测试")
    print("=" * 60)
    
    tester = SandboxBrowserTester()
    
    start_time = time.time()
    
    # 测试沙盒浏览器
    success = await tester.test_sandbox_browser()
    
    end_time = time.time()
    duration = end_time - start_time
    
    print("=" * 60)
    if success:
        print("✅ 沙盒浏览器测试通过")
    else:
        print("❌ 沙盒浏览器测试失败")
    print(f"⏱️ 总耗时: {duration:.2f} 秒")

if __name__ == "__main__":
    asyncio.run(main()) 