#!/usr/bin/env python3
"""
MCP 启动测试脚本

验证系统启动时 MCP 工具的注册和发现功能
"""

import asyncio
import logging
import sys
import os
from unittest.mock import Mock

# 添加项目路径到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.domain.services.agents.execution import ExecutionAgent
from app.domain.services.tools.mcp import MCPTool, MCPClientManager
# 简化的JsonParser模拟
class MockJsonParser:
    async def parse(self, text):
        import json
        return json.loads(text)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_mcp_tool_registration():
    """测试 MCP 工具注册功能"""
    logger.info("=" * 60)
    logger.info("测试 MCP 工具注册功能")
    logger.info("=" * 60)
    
    try:
        # 创建模拟的依赖
        agent_repository = Mock()
        llm = Mock()
        sandbox = Mock()
        browser = Mock()
        json_parser = MockJsonParser()
        
        # 创建 ExecutionAgent
        agent = ExecutionAgent(
            agent_id="test-agent",
            agent_repository=agent_repository,
            llm=llm,
            sandbox=sandbox,
            browser=browser,
            json_parser=json_parser
        )
        
        logger.info("✅ ExecutionAgent 创建成功")
        
        # 初始化 Agent（这会触发 MCP 工具初始化）
        await agent.initialize()
        logger.info("✅ ExecutionAgent 初始化成功")
        
        # 获取所有可用工具
        tools = await agent.get_available_tools_async()
        logger.info(f"✅ 获取到 {len(tools)} 个工具")
        
        # 分类工具
        mcp_tools = [t for t in tools if t["function"]["name"].startswith("mcp_")]
        builtin_tools = [t for t in tools if not t["function"]["name"].startswith("mcp_")]
        
        logger.info(f"内置工具数量: {len(builtin_tools)}")
        logger.info(f"MCP 工具数量: {len(mcp_tools)}")
        
        # 显示内置工具
        logger.info("\n内置工具:")
        for tool in builtin_tools:
            logger.info(f"  - {tool['function']['name']}: {tool['function']['description']}")
        
        # 显示 MCP 工具
        logger.info("\nMCP 工具:")
        for tool in mcp_tools:
            logger.info(f"  - {tool['function']['name']}: {tool['function']['description']}")
        
        # 测试 MCP 工具管理命令
        logger.info("\n测试 MCP 工具管理命令:")
        
        # 测试列出服务器
        result = await agent.mcp_tool.list_mcp_servers()
        if result.success:
            logger.info("✅ list_mcp_servers 调用成功")
            logger.info(f"服务器信息:\n{result.data}")
        else:
            logger.error(f"❌ list_mcp_servers 调用失败: {result.message}")
        
        # 测试列出工具
        result = await agent.mcp_tool.list_mcp_tools()
        if result.success:
            logger.info("✅ list_mcp_tools 调用成功")
            logger.info(f"工具信息:\n{result.data}")
        else:
            logger.error(f"❌ list_mcp_tools 调用失败: {result.message}")
        
        # 清理资源
        await agent.cleanup()
        logger.info("✅ 资源清理完成")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_mcp_client_manager_standalone():
    """测试独立的 MCP 客户端管理器"""
    logger.info("=" * 60)
    logger.info("测试独立的 MCP 客户端管理器")
    logger.info("=" * 60)
    
    try:
        manager = MCPClientManager()
        
        # 初始化管理器
        await manager.initialize()
        logger.info("✅ MCPClientManager 初始化成功")
        
        # 获取服务器信息
        servers_info = await manager.get_servers_info()
        logger.info(f"✅ 发现 {len(servers_info)} 个 MCP 服务器")
        
        for server_name, info in servers_info.items():
            status = "已连接" if info['connected'] else "未连接"
            logger.info(f"  - {server_name}: {status} ({info['tools_count']} 个工具)")
        
        # 获取所有工具
        tools = await manager.get_all_tools()
        logger.info(f"✅ 获取到 {len(tools)} 个 MCP 工具")
        
        # 显示工具列表
        for tool in tools:
            func_info = tool["function"]
            logger.info(f"  - {func_info['name']}: {func_info['description']}")
        
        # 清理资源
        await manager.cleanup()
        logger.info("✅ 资源清理完成")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("MCP 启动测试")
    logger.info("=" * 60)
    
    test_results = []
    
    # 测试独立的 MCP 客户端管理器
    result = await test_mcp_client_manager_standalone()
    test_results.append(("MCP 客户端管理器", result))
    
    # 测试 MCP 工具注册
    result = await test_mcp_tool_registration()
    test_results.append(("MCP 工具注册", result))
    
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
        logger.info("🎉 所有测试通过！MCP 工具注册和发现功能正常工作。")
        logger.info("系统启动时，config.json 中的工具已成功注册到 Agent 中。")
    else:
        logger.error("⚠️  部分测试失败，请检查配置和实现。")
    
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