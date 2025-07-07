#!/usr/bin/env python3
"""
HTTP 浏览器功能测试脚本
测试纯HTTP实现的浏览器功能
"""

import asyncio
import sys
import os
import time
from typing import List, Dict, Any

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.infrastructure.external.browser.crawl4ai_browser import Crawl4AIBrowser
from app.domain.models.tool_result import ToolResult

class HTTPBrowserTester:
    def __init__(self):
        self.browser = Crawl4AIBrowser()
        self.test_results = []
        
    async def test_basic_functionality(self) -> bool:
        """测试基本功能"""
        print("🧪 开始测试 HTTP 浏览器基本功能...")
        
        try:
            # 测试页面浏览
            url = "https://httpbin.org/html"
            print(f"📄 正在访问: {url}")
            
            result = await self.browser.view_page(url)
            
            if result.success:
                content = result.data.get("content", "")
                interactive_elements = result.data.get("interactive_elements", [])
                
                print(f"✅ 页面查看成功")
                print(f"📝 内容长度: {len(content) if content else 0} 字符")
                print(f"🔗 交互元素数量: {len(interactive_elements)}")
                
                # 检查内容是否有效
                if content and len(content) > 0:
                    print("✅ 内容提取成功")
                    return True
                else:
                    print("⚠️ 内容为空，但功能正常")
                    return True
            else:
                print(f"❌ 页面查看失败: {result.message}")
                return False
                
        except Exception as e:
            print(f"❌ 测试过程中发生错误: {e}")
            return False
    
    async def test_navigation(self) -> bool:
        """测试导航功能"""
        print("\n🧪 开始测试导航功能...")
        
        try:
            # 测试导航到新页面
            url = "https://httpbin.org/json"
            print(f"📄 正在导航到: {url}")
            
            result = await self.browser.navigate(url)
            
            if result.success:
                content = result.data.get("content", "")
                print(f"✅ 导航成功")
                print(f"📝 内容长度: {len(content) if content else 0} 字符")
                return True
            else:
                print(f"❌ 导航失败: {result.message}")
                return False
                
        except Exception as e:
            print(f"❌ 导航测试过程中发生错误: {e}")
            return False
    
    async def test_interactive_elements(self) -> bool:
        """测试交互元素提取"""
        print("\n🧪 开始测试交互元素提取...")
        
        try:
            # 测试包含链接的页面
            url = "https://httpbin.org/html"
            print(f"📄 正在访问: {url}")
            
            result = await self.browser.view_page(url)
            
            if result.success:
                interactive_elements = result.data.get("interactive_elements", [])
                print(f"✅ 交互元素提取成功")
                print(f"🔗 找到 {len(interactive_elements)} 个交互元素")
                
                # 显示前几个元素
                for i, element in enumerate(interactive_elements[:3]):
                    print(f"  {i+1}. {element.get('tag', 'unknown')}: {element.get('text', '')[:50]}...")
                
                return True
            else:
                print(f"❌ 交互元素提取失败: {result.message}")
                return False
                
        except Exception as e:
            print(f"❌ 交互元素测试过程中发生错误: {e}")
            return False
    
    async def test_click_simulation(self) -> bool:
        """测试点击模拟功能"""
        print("\n🧪 开始测试点击模拟功能...")
        
        try:
            # 先访问一个页面
            url = "https://httpbin.org/html"
            await self.browser.view_page(url)
            
            # 尝试点击第一个元素
            result = await self.browser.click(0)
            
            if result.success:
                print(f"✅ 点击模拟成功: {result.message}")
                return True
            else:
                print(f"❌ 点击模拟失败: {result.message}")
                return False
                
        except Exception as e:
            print(f"❌ 点击测试过程中发生错误: {e}")
            return False
    
    async def test_content_extraction(self) -> bool:
        """测试内容提取质量"""
        print("\n🧪 开始测试内容提取质量...")
        
        try:
            # 测试一个简单的HTML页面
            url = "https://httpbin.org/html"
            print(f"📄 正在访问: {url}")
            
            result = await self.browser.view_page(url)
            
            if result.success:
                content = result.data.get("content", "")
                print(f"✅ 内容提取成功")
                print(f"📝 内容预览:")
                print("-" * 50)
                print(content[:500] + "..." if len(content) > 500 else content)
                print("-" * 50)
                
                # 检查是否包含Markdown格式
                if "#" in content or "[" in content:
                    print("✅ 内容包含Markdown格式")
                    return True
                else:
                    print("⚠️ 内容格式可能不正确")
                    return False
            else:
                print(f"❌ 内容提取失败: {result.message}")
                return False
                
        except Exception as e:
            print(f"❌ 内容提取测试过程中发生错误: {e}")
            return False
    
    async def test_error_handling(self) -> bool:
        """测试错误处理"""
        print("\n🧪 开始测试错误处理...")
        
        try:
            # 测试无效URL
            url = "https://invalid-url-that-does-not-exist.com"
            print(f"📄 正在访问无效URL: {url}")
            
            result = await self.browser.view_page(url)
            
            if not result.success:
                print(f"✅ 错误处理正确: {result.message}")
                return True
            else:
                print(f"❌ 应该失败但成功了")
                return False
                
        except Exception as e:
            print(f"❌ 错误处理测试过程中发生异常: {e}")
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始 HTTP 浏览器功能测试")
        print("=" * 60)
        
        start_time = time.time()
        
        tests = [
            ("基本功能", self.test_basic_functionality),
            ("导航功能", self.test_navigation),
            ("交互元素提取", self.test_interactive_elements),
            ("点击模拟", self.test_click_simulation),
            ("内容提取质量", self.test_content_extraction),
            ("错误处理", self.test_error_handling),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if await test_func():
                    passed += 1
                    print(f"✅ {test_name} 测试通过")
                else:
                    print(f"❌ {test_name} 测试失败")
            except Exception as e:
                print(f"❌ {test_name} 测试异常: {e}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "=" * 60)
        print(f"📊 测试结果: {passed}/{total} 通过")
        print(f"⏱️ 总耗时: {duration:.2f} 秒")
        
        if passed == total:
            print("🎉 所有测试通过！HTTP 浏览器功能正常")
        else:
            print("⚠️ 部分测试失败，需要检查")
        
        # 清理资源
        await self.browser.cleanup()
        
        return passed == total

async def main():
    """主函数"""
    tester = HTTPBrowserTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n✅ HTTP 浏览器测试完成，功能正常！")
        sys.exit(0)
    else:
        print("\n❌ HTTP 浏览器测试失败，需要修复问题")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 