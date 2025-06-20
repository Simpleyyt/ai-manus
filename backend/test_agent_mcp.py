#!/usr/bin/env python3
"""
测试Agent中MCP工具的发现和初始化

这个脚本模拟真实的Agent创建流程，验证MCP工具是否能被正确发现
"""

import asyncio
import logging
import sys
import os

# 添加项目路径到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.domain.services.agents.execution import ExecutionAgent
from app.infrastructure.repositories.mongo_agent_repository import MongoAgentRepository
from app.infrastructure.external.llm.openai_llm import OpenAILLM
from app.infrastructure.external.sandbox.docker_sandbox import DockerSandbox
from app.infrastructure.external.browser.playwright_browser import PlaywrightBrowser
from app.infrastructure.utils.llm_json_parser import LLMJsonParser

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockAgentRepository:
    """模拟Agent仓库"""
    async def get_memory(self, agent_id, agent_name):
        from app.domain.models.memory import Memory
        return Memory()
    
    async def save_memory(self, agent_id, agent_name, memory):
        pass


class MockSandbox:
    """模拟沙箱"""
    pass


class MockBrowser:
    """模拟浏览器"""
    pass


async def test_execution_agent_mcp_tools():
    """测试ExecutionAgent中MCP工具的发现"""
    logger.info("开始测试ExecutionAgent中的MCP工具发现...")
    
    try:
        # 创建模拟依赖
        agent_repository = MockAgentRepository()
        llm = OpenAILLM()  # 实际的LLM，但不会真正调用
        sandbox = MockSandbox()
        browser = MockBrowser()
        json_parser = LLMJsonParser()
        
        # 创建ExecutionAgent
        agent = ExecutionAgent(
            agent_id="test-agent",
            agent_repository=agent_repository,
            llm=llm,
            sandbox=sandbox,
            browser=browser,
            json_parser=json_parser
        )
        
        logger.info("ExecutionAgent创建成功")
        
        # 测试获取工具列表（异步）
        tools = await agent.get_available_tools_async()
        
        logger.info(f"发现总工具数: {len(tools)}")
        
        # 统计MCP工具
        mcp_tools = [tool for tool in tools if tool["function"]["name"].startswith("mcp_")]
        base_tools = [tool for tool in tools if not tool["function"]["name"].startswith("mcp_")]
        
        logger.info(f"基础工具数: {len(base_tools)}")
        logger.info(f"MCP工具数: {len(mcp_tools)}")
        
        # 打印所有工具名称
        logger.info("所有工具列表:")
        for tool in tools:
            tool_name = tool["function"]["name"]
            description = tool["function"]["description"]
            logger.info(f"  - {tool_name}: {description}")
        
        # 验证是否包含预期的MCP工具
        expected_mcp_tools = [
            "mcp_fofa-mcp-server_fofa_search",
            "mcp_amap-location_maps_geo",
            "mcp_mcp_server_sec_agent_alert_investigator"
        ]
        
        found_mcp_tools = [tool["function"]["name"] for tool in mcp_tools]
        
        success_count = 0
        for expected_tool in expected_mcp_tools:
            if any(expected_tool in found_tool for found_tool in found_mcp_tools):
                logger.info(f"✅ 找到预期的MCP工具: {expected_tool}")
                success_count += 1
            else:
                logger.warning(f"❌ 未找到预期的MCP工具: {expected_tool}")
        
        # 测试基础工具
        base_tool_names = [tool["function"]["name"] for tool in base_tools]
        expected_base_tools = ["list_mcp_servers", "list_mcp_tools"]
        
        for expected_tool in expected_base_tools:
            if expected_tool in base_tool_names:
                logger.info(f"✅ 找到预期的基础工具: {expected_tool}")
                success_count += 1
            else:
                logger.warning(f"❌ 未找到预期的基础工具: {expected_tool}")
        
        # 清理资源
        await agent.cleanup()
        
        logger.info("=" * 60)
        logger.info("测试结果汇总:")
        logger.info(f"总工具数: {len(tools)}")
        logger.info(f"MCP工具数: {len(mcp_tools)}")
        logger.info(f"基础工具数: {len(base_tools)}")
        logger.info(f"成功验证项: {success_count}/5")
        
        if len(mcp_tools) > 0 and success_count >= 3:
            logger.info("🎉 测试通过！ExecutionAgent可以正确发现MCP工具")
            return True
        else:
            logger.error("⚠️ 测试失败！ExecutionAgent无法正确发现MCP工具")
            return False
            
    except Exception as e:
        logger.error(f"测试执行失败: {e}")
        return False


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("ExecutionAgent MCP工具发现测试")
    logger.info("=" * 60)
    
    success = await test_execution_agent_mcp_tools()
    
    if success:
        logger.info("🎉 所有测试通过！")
        return 0
    else:
        logger.error("❌ 测试失败")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 