#!/usr/bin/env python3
"""
简化的MCP工具发现测试

直接测试MCPTool的初始化和工具发现功能
"""

import asyncio
import logging
import sys
import os

# 添加项目路径到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.domain.services.tools.mcp import MCPTool

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_mcp_tool_integration():
    """测试MCPTool的工具发现和异步初始化"""
    logger.info("开始测试MCPTool的异步初始化...")
    
    try:
        # 创建MCPTool实例
        mcp_tool = MCPTool()
        logger.info("MCPTool实例创建成功")
        
        # 测试异步工具获取（这会触发初始化）
        logger.info("调用get_tools_async()方法...")
        tools = await mcp_tool.get_tools_async()
        
        logger.info(f"发现总工具数: {len(tools)}")
        
        # 统计不同类型的工具
        mcp_tools = [tool for tool in tools if tool["function"]["name"].startswith("mcp_")]
        base_tools = [tool for tool in tools if not tool["function"]["name"].startswith("mcp_")]
        
        logger.info(f"基础工具数: {len(base_tools)}")
        logger.info(f"MCP工具数: {len(mcp_tools)}")
        
        # 打印前5个工具作为示例
        logger.info("工具示例 (前5个):")
        for i, tool in enumerate(tools[:5]):
            tool_name = tool["function"]["name"]
            description = tool["function"]["description"][:100] + "..." if len(tool["function"]["description"]) > 100 else tool["function"]["description"]
            logger.info(f"  {i+1}. {tool_name}: {description}")
        
        if len(tools) > 5:
            logger.info(f"  ... 还有 {len(tools) - 5} 个工具")
        
        # 验证预期的工具类型
        fofa_tools = [tool for tool in mcp_tools if "fofa" in tool["function"]["name"]]
        amap_tools = [tool for tool in mcp_tools if "amap" in tool["function"]["name"]]
        sec_tools = [tool for tool in mcp_tools if "sec_agent" in tool["function"]["name"]]
        
        logger.info(f"FOFA工具数: {len(fofa_tools)}")
        logger.info(f"高德地图工具数: {len(amap_tools)}")
        logger.info(f"安全代理工具数: {len(sec_tools)}")
        
        # 测试基础MCP管理工具
        base_tool_names = [tool["function"]["name"] for tool in base_tools]
        has_list_servers = "list_mcp_servers" in base_tool_names
        has_list_tools = "list_mcp_tools" in base_tool_names
        
        logger.info(f"包含list_mcp_servers: {has_list_servers}")
        logger.info(f"包含list_mcp_tools: {has_list_tools}")
        
        # 清理资源
        await mcp_tool.cleanup()
        logger.info("资源清理完成")
        
        # 评估测试结果
        success = (
            len(tools) > 2 and  # 至少有一些工具
            len(mcp_tools) > 0 and  # 有MCP工具
            has_list_servers and  # 有基础管理工具
            has_list_tools
        )
        
        logger.info("=" * 60)
        logger.info("测试结果汇总:")
        logger.info(f"总工具数: {len(tools)}")
        logger.info(f"MCP工具数: {len(mcp_tools)}")
        logger.info(f"基础工具数: {len(base_tools)}")
        logger.info(f"FOFA工具: {len(fofa_tools)}")
        logger.info(f"高德地图工具: {len(amap_tools)}")
        logger.info(f"安全代理工具: {len(sec_tools)}")
        
        if success:
            logger.info("🎉 测试通过！MCPTool可以正确发现和初始化MCP工具")
            return True
        else:
            logger.error("⚠️ 测试失败！MCPTool无法正确工作")
            return False
            
    except Exception as e:
        logger.error(f"测试执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("简化MCP工具发现测试")
    logger.info("=" * 60)
    
    success = await test_mcp_tool_integration()
    
    if success:
        logger.info("🎉 所有测试通过！")
        return 0
    else:
        logger.error("❌ 测试失败")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 