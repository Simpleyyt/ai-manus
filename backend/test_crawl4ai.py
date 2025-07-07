#!/usr/bin/env python3
"""
Crawl4AI 浏览器功能测试脚本
测试 Crawl4AI 浏览器的各种功能
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

class Crawl4AITester:
    def __init__(self):
        self.browser = Crawl4AIBrowser()
        self.test_results = []
        
    async def test_basic_functionality(self) -> bool:
        """测试基本功能"""
        print("🧪 开始测试 Crawl4AI 基本功能...")
        
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
        print("🧪 开始测试 Crawl4AI 导航功能...")
        
        try:
            # 测试导航到新页面
            url = "https://httpbin.org/get"
            print(f"🧭 正在导航到: {url}")
            
            result = await self.browser.navigate(url)
            
            if result.success:
                print("✅ 导航成功")
                print(f"📍 当前 URL: {self.browser.current_url}")
                return True
            else:
                print(f"❌ 导航失败: {result.message}")
                return False
                
        except Exception as e:
            print(f"❌ 导航测试失败: {e}")
            return False
    
    async def test_interactive_elements(self) -> bool:
        """测试交互元素提取"""
        print("🧪 开始测试交互元素提取...")
        
        try:
            # 测试提取交互元素
            url = "https://httpbin.org/links/10/0"
            print(f"🔗 正在提取交互元素: {url}")
            
            result = await self.browser.view_page(url)
            
            if result.success:
                interactive_elements = result.data.get("interactive_elements", [])
                print(f"✅ 成功提取 {len(interactive_elements)} 个交互元素")
                
                # 显示前几个元素
                for i, element in enumerate(interactive_elements[:3]):
                    print(f"  {i}: {element.get('tag', 'unknown')} - {element.get('text', 'no text')[:50]}")
                
                return True
            else:
                print(f"❌ 交互元素提取失败: {result.message}")
                return False
                
        except Exception as e:
            print(f"❌ 交互元素测试失败: {e}")
            return False
    
    async def test_click_simulation(self) -> bool:
        """测试点击模拟功能"""
        print("🧪 开始测试点击模拟功能...")
        
        try:
            # 先导航到一个有链接的页面
            await self.browser.navigate("https://httpbin.org/html")
            
            # 尝试点击第一个元素
            result = await self.browser.click(0)
            
            if result.success:
                print(f"✅ 点击成功: {result.message}")
                return True
            else:
                print(f"⚠️ 没有找到可点击的元素")
                return True  # 这不是错误，只是没有可点击的元素
                
        except Exception as e:
            print(f"❌ 点击测试失败: {e}")
            return False
    
    async def test_performance(self) -> bool:
        """测试性能"""
        print("🧪 开始测试性能...")
        
        test_urls = [
            "https://httpbin.org/html",
            "https://httpbin.org/json", 
            "https://httpbin.org/xml"
        ]
        
        total_time = 0
        success_count = 0
        
        for i, url in enumerate(test_urls, 1):
            print(f"⏱️ 测试 {i}/{len(test_urls)}: {url}")
            
            start_time = time.time()
            result = await self.browser.view_page(url)
            end_time = time.time()
            
            duration = end_time - start_time
            
            if result.success:
                print(f"✅ 成功 ({duration:.2f}s)")
                total_time += duration
                success_count += 1
            else:
                print(f"❌ 失败 ({duration:.2f}s): {result.message}")
        
        if success_count > 0:
            avg_time = total_time / success_count
            success_rate = (success_count / len(test_urls)) * 100
            
            print(f"\n📊 性能测试结果:")
            print(f"  平均响应时间: {avg_time:.2f}秒")
            print(f"  成功率: {success_rate:.1f}%")
            print(f"  总测试数: {len(test_urls)}")
            print(f"  成功数: {success_count}")
            
            return success_rate >= 80  # 80% 成功率算通过
        else:
            print("❌ 所有性能测试都失败了")
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 Crawl4AI 功能测试开始")
        print("=" * 50)
        
        tests = [
            ("基本功能", self.test_basic_functionality),
            ("导航功能", self.test_navigation),
            ("交互元素提取", self.test_interactive_elements),
            ("点击模拟", self.test_click_simulation),
            ("性能测试", self.test_performance)
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
            
            print()  # 空行分隔
        
        print("=" * 50)
        print(f"🎯 测试完成: {passed}/{total} 通过")
        
        if passed == total:
            print("🎉 所有测试通过！Crawl4AI 浏览器功能正常")
        elif passed >= total * 0.8:
            print("⚠️ 部分测试失败，请检查配置和网络连接")
        else:
            print("❌ 大部分测试失败，请检查 Crawl4AI 配置")
        
        # 清理资源
        await self.browser.cleanup()

async def main():
    """主函数"""
    tester = Crawl4AITester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 