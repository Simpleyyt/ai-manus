#!/usr/bin/env python3
"""
MCP 集成测试脚本

此脚本用于测试 ai-agent 项目中的 MCP 客户端集成功能
"""

import asyncio
import logging
import sys
import os

# 添加项目路径到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.domain.services.tools.mcp import MCPTool, MCPClientManager

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_mcp_client_manager():
    """测试 MCP 客户端管理器"""
    logger.info("开始测试 MCP 客户端管理器...")
    
    manager = MCPClientManager()
    
    try:
        # 初始化管理器
        await manager.initialize()
        
        # 获取服务器信息
        servers_info = await manager.get_servers_info()
        logger.info(f"发现 {len(servers_info)} 个 MCP 服务器:")
        for server_name, info in servers_info.items():
            status = "已连接" if info['connected'] else "未连接"
            logger.info(f"  - {server_name}: {status} ({info['tools_count']} 个工具)")
        
        # 获取所有工具
        tools = await manager.get_all_tools()
        logger.info(f"总共可用 {len(tools)} 个 MCP 工具:")
        for tool in tools[:5]:  # 只显示前5个工具
            func_info = tool["function"]
            logger.info(f"  - {func_info['name']}: {func_info['description']}")
        
        if len(tools) > 5:
            logger.info(f"  ... 还有 {len(tools) - 5} 个工具")
        
        return True
        
    except Exception as e:
        logger.error(f"测试 MCP 客户端管理器失败: {e}")
        return False
    
    finally:
        await manager.cleanup()


async def test_mcp_tool():
    """测试 MCP 工具类"""
    logger.info("开始测试 MCP 工具类...")
    
    mcp_tool = MCPTool()
    
    try:
        # 测试列出服务器
        result = await mcp_tool.list_mcp_servers()
        logger.info("列出 MCP 服务器结果:")
        logger.info(result.data if result.success else f"错误: {result.message}")
        
        # 测试列出工具
        result = await mcp_tool.list_mcp_tools()
        logger.info("列出 MCP 工具结果:")
        logger.info(result.data if result.success else f"错误: {result.message}")
        
        # 测试获取工具定义
        tools = await mcp_tool.get_tools_async()
        logger.info(f"MCP 工具类提供 {len(tools)} 个工具")
        
        return True
        
    except Exception as e:
        logger.error(f"测试 MCP 工具类失败: {e}")
        return False
    
    finally:
        await mcp_tool.cleanup()


async def test_mcp_tool_invocation():
    """测试 MCP 工具调用"""
    logger.info("开始测试 MCP 工具调用...")
    
    mcp_tool = MCPTool()
    
    try:
        # 获取可用工具
        tools = await mcp_tool.get_tools_async()
        mcp_tools = [t for t in tools if t["function"]["name"].startswith("mcp_")]
        
        if not mcp_tools:
            logger.warning("没有找到可用的 MCP 工具")
            return True
        
        # 尝试调用第一个 MCP 工具
        first_tool = mcp_tools[0]
        tool_name = first_tool["function"]["name"]
        logger.info(f"尝试调用工具: {tool_name}")
        
        # 如果是 FOFA 搜索工具，尝试调用
        if "fofa" in tool_name.lower():
            result = await mcp_tool.invoke_function(tool_name, domain="baidu.com")
            logger.info("FOFA 搜索结果:")
            logger.info(result.data if result.success else f"错误: {result.message}")
        else:
            # 尝试不带参数调用
            result = await mcp_tool.invoke_function(tool_name)
            logger.info(f"工具 {tool_name} 调用结果:")
            logger.info(result.data if result.success else f"错误: {result.message}")
        
        return True
        
    except Exception as e:
        logger.error(f"测试 MCP 工具调用失败: {e}")
        return False
    
    finally:
        await mcp_tool.cleanup()


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("AI-Agent MCP 集成测试")
    logger.info("=" * 60)
    
    test_results = []
    
    # 测试 MCP 客户端管理器
    result = await test_mcp_client_manager()
    test_results.append(("MCP 客户端管理器", result))
    
    # 测试 MCP 工具类
    result = await test_mcp_tool()
    test_results.append(("MCP 工具类", result))
    
    # 测试 MCP 工具调用
    result = await test_mcp_tool_invocation()
    test_results.append(("MCP 工具调用", result))
    
    # 输出测试结果
    logger.info("=" * 60)
    logger.info("测试结果汇总:")
    logger.info("=" * 60)
    
    all_passed = True
    for test_name, passed in test_results:
        status = "✅ 通过" if passed else "❌ 失败"
        logger.info(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    logger.info("=" * 60)
    if all_passed:
        logger.info("🎉 所有测试通过！MCP 集成功能正常工作。")
    else:
        logger.error("⚠️  部分测试失败，请检查配置和连接。")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("测试被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"测试过程中发生未预期的错误: {e}")
        sys.exit(1) 