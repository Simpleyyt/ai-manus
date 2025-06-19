"""
MCP HTTP初始化服务 - ai-manus-5版本
通过HTTP调用独立的MCP Client服务
"""

import asyncio
import logging
from typing import Optional
from app.domain.services.tools.mcp_http_tool import MCPHttpTool

logger = logging.getLogger(__name__)

class MCPInitializerService:
    """MCP初始化服务，负责初始化基于HTTP的MCP工具"""
    
    def __init__(self):
        self.mcp_tool: Optional[MCPHttpTool] = None
        self._initialized = False
    
    async def initialize(self):
        """初始化MCP服务"""
        if self._initialized:
            return
        
        try:
            logger.info("初始化MCP HTTP服务...")
            
            # 创建MCP HTTP工具实例
            self.mcp_tool = MCPHttpTool()
            
            # 自动连接预设服务器
            result = await self.mcp_tool.mcp_auto_connect()
            
            if result.success:
                logger.info(f"MCP HTTP服务初始化完成: {result.message}")
            else:
                logger.warning(f"MCP HTTP服务初始化失败: {result.message}")
            
        except Exception as e:
            logger.error(f"MCP HTTP服务初始化出错: {e}")
            # 不要抛出异常，让应用继续启动
            logger.warning("MCP HTTP服务初始化失败，但应用将继续运行")
        finally:
            # 无论成功还是失败，都标记为已初始化，避免重复初始化
            self._initialized = True
    
    async def get_mcp_tool(self) -> Optional[MCPHttpTool]:
        """获取MCP工具实例"""
        if not self._initialized:
            await self.initialize()
        return self.mcp_tool
    
    async def cleanup(self):
        """清理MCP连接"""
        if self.mcp_tool:
            # HTTP工具不需要特殊清理
            logger.info("MCP HTTP服务已清理")

# 全局实例
mcp_initializer = MCPInitializerService() 