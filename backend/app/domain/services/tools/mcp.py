import os
import logging
from typing import Dict, Any, List, Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import Tool as MCPTool

from app.domain.services.tools.base import BaseTool, tool
from app.domain.models.tool_result import ToolResult
from app.domain.models.mcp_config import MCPConfig, MCPServerConfig

logger = logging.getLogger(__name__)


class MCPClientManager:
    """MCP 客户端管理器"""
    
    def __init__(self, config: Optional[MCPConfig] = None):
        self._clients: Dict[str, ClientSession] = {}
        self._exit_stack = AsyncExitStack()
        self._tools_cache: Dict[str, List[MCPTool]] = {}
        self._initialized = False
        self._config = config
    
    async def initialize(self):
        """初始化 MCP 客户端管理器"""
        if self._initialized:
            return
        
        try:
            logger.info(f"从配置加载了 {len(self._config.mcpServers)} 个 MCP 服务器配置")
            
            # 连接到所有启用的服务器
            await self._connect_servers()
            
            self._initialized = True
            logger.info("MCP 客户端管理器初始化成功")
            
        except Exception as e:
            logger.error(f"MCP 客户端管理器初始化失败: {e}")
            raise

    
    async def _connect_servers(self):
        """连接到所有启用的 MCP 服务器"""
        for server_name, server_config in self._config.mcpServers.items():
            if not server_config.enabled:
                continue
                
            try:
                await self._connect_server(server_name, server_config)
            except Exception as e:
                logger.error(f"连接到 MCP 服务器 {server_name} 失败: {e}")
                # 继续连接其他服务器
                continue
    
    async def _connect_server(self, server_name: str, server_config: MCPServerConfig):
        """连接到单个 MCP 服务器"""
        try:
            transport_type = server_config.transport
            
            if transport_type == 'stdio':
                await self._connect_stdio_server(server_name, server_config)
            elif transport_type == 'http' or transport_type == 'sse':
                await self._connect_http_server(server_name, server_config)
            elif transport_type == 'streamable-http':
                await self._connect_streamable_http_server(server_name, server_config)
            else:
                logger.error(f"不支持的传输类型: {transport_type}")
                
        except Exception as e:
            logger.error(f"连接 MCP 服务器 {server_name} 失败: {e}")
            raise
    
    async def _connect_stdio_server(self, server_name: str, server_config: MCPServerConfig):
        """连接到 stdio MCP 服务器"""
        command = server_config.command
        args = server_config.args or []
        env = server_config.env or {}
        
        if not command:
            raise ValueError(f"服务器 {server_name} 缺少 command 配置")
        

        # 创建服务器参数（路径处理已在配置提供者中完成）
        server_params = StdioServerParameters(
            command=command,
            args=args,
            env={**os.environ, **env}
        )
        
        try:
            # 建立连接
            stdio_transport = await self._exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            read_stream, write_stream = stdio_transport
            
            # 创建会话
            session = await self._exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            
            # 初始化会话
            await session.initialize()
            
            # 缓存客户端
            self._clients[server_name] = session
            
            # 获取并缓存工具列表
            await self._cache_server_tools(server_name, session)
            
            logger.info(f"成功连接到 stdio MCP 服务器: {server_name}")
            
        except Exception as e:
            logger.error(f"连接到 stdio MCP 服务器 {server_name} 失败: {e}")
            raise
    
    async def _connect_http_server(self, server_name: str, server_config: MCPServerConfig):
        """连接到 HTTP MCP 服务器"""
        url = server_config.url
        if not url:
            raise ValueError(f"服务器 {server_name} 缺少 url 配置")
        
        try:
            # 建立 SSE 连接
            sse_transport = await self._exit_stack.enter_async_context(
                sse_client(url)
            )
            read_stream, write_stream = sse_transport
            
            # 创建会话
            session = await self._exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            
            # 初始化会话
            await session.initialize()
            
            # 缓存客户端
            self._clients[server_name] = session
            
            # 获取并缓存工具列表
            await self._cache_server_tools(server_name, session)
            
            logger.info(f"成功连接到 HTTP MCP 服务器: {server_name}")
            
        except Exception as e:
            logger.error(f"连接到 HTTP MCP 服务器 {server_name} 失败: {e}")
            raise
    
    async def _connect_streamable_http_server(self, server_name: str, server_config: MCPServerConfig):
        """连接到 streamable-http MCP 服务器
        
        配置选项：
        - url: 服务器 URL (必需)
        - headers: 自定义 HTTP 头 (可选)
        """
        url = server_config.url
        if not url:
            raise ValueError(f"服务器 {server_name} 缺少 url 配置")
        
        # 获取可选配置
        headers = server_config.headers or {}
        
        try:
            # 准备连接参数
            client_params = {"url": url}
            
            # 添加自定义 headers
            if headers:
                client_params["headers"] = headers
            
            # 建立 streamable-http 连接
            streamable_transport = await self._exit_stack.enter_async_context(
                streamablehttp_client(**client_params)
            )
            
            # 解包返回的流和可选的第三个参数
            if len(streamable_transport) == 3:
                read_stream, write_stream, _ = streamable_transport
            else:
                read_stream, write_stream = streamable_transport
            
            # 创建 MCP 会话
            session = await self._exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            
            # 初始化会话
            await session.initialize()
            
            # 缓存客户端
            self._clients[server_name] = session
            
            # 获取并缓存工具列表
            await self._cache_server_tools(server_name, session)
            
            logger.info(f"成功连接到 streamable-http MCP 服务器: {server_name} ({url})")
            
        except Exception as e:
            logger.error(f"连接到 streamable-http MCP 服务器 {server_name} 失败: {e}")
            raise
    
    async def _cache_server_tools(self, server_name: str, session: ClientSession):
        """缓存服务器工具列表"""
        try:
            tools_response = await session.list_tools()
            tools = tools_response.tools if tools_response else []
            self._tools_cache[server_name] = tools
            logger.info(f"服务器 {server_name} 提供 {len(tools)} 个工具")
            
        except Exception as e:
            logger.error(f"获取服务器 {server_name} 工具列表失败: {e}")
            self._tools_cache[server_name] = []
    
    async def get_all_tools(self) -> List[Dict[str, Any]]:
        """获取所有 MCP 工具"""
        all_tools = []
        
        for server_name, tools in self._tools_cache.items():
            for tool in tools:
                # 生成工具名称，避免重复的 mcp_ 前缀
                if server_name.startswith('mcp_'):
                    tool_name = f"{server_name}_{tool.name}"
                else:
                    tool_name = f"mcp_{server_name}_{tool.name}"
                
                # 转换为标准工具格式
                tool_schema = {
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "description": f"[{server_name}] {tool.description or tool.name}",
                        "parameters": tool.inputSchema
                    }
                }
                all_tools.append(tool_schema)
        
        return all_tools
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
        """调用 MCP 工具"""
        try:
            # 解析工具名称
            server_name = None
            original_tool_name = None
            
            # 查找匹配的服务器名称
            for srv_name in self._config.mcpServers.keys():
                expected_prefix = srv_name if srv_name.startswith('mcp_') else f"mcp_{srv_name}"
                if tool_name.startswith(f"{expected_prefix}_"):
                    server_name = srv_name
                    original_tool_name = tool_name[len(expected_prefix) + 1:]
                    break
            
            if not server_name or not original_tool_name:
                raise ValueError(f"无法解析 MCP 工具名称: {tool_name}")
            
            # 获取客户端会话
            session = self._clients.get(server_name)
            if not session:
                return ToolResult(
                    success=False,
                    message=f"MCP 服务器 {server_name} 未连接"
                )
            
            # 调用工具
            result = await session.call_tool(original_tool_name, arguments)
            
            # 处理结果
            if result:
                content = []
                if hasattr(result, 'content') and result.content:
                    for item in result.content:
                        if hasattr(item, 'text'):
                            content.append(item.text)
                        else:
                            content.append(str(item))
                
                return ToolResult(
                    success=True,
                    data='\n'.join(content) if content else "工具执行成功"
                )
            else:
                return ToolResult(
                    success=True,
                    data="工具执行成功"
                )
                
        except Exception as e:
            logger.error(f"调用 MCP 工具 {tool_name} 失败: {e}")
            return ToolResult(
                success=False,
                message=f"调用 MCP 工具失败: {str(e)}"
            )

    async def cleanup(self):
        """清理资源"""
        try:
            await self._exit_stack.aclose()
            self._clients.clear()
            self._tools_cache.clear()
            self._initialized = False
            logger.info("MCP 客户端管理器已清理")
            
        except Exception as e:
            logger.error(f"清理 MCP 客户端管理器失败: {e}")


class MCPTool(BaseTool):
    """MCP 工具类"""
    
    name = "mcp"
    
    def __init__(self):
        super().__init__()
        self._initialized = False
        self._tools = []
    
    async def initialized(self, config: Optional[MCPConfig] = None):
        """确保管理器已初始化"""
        if not self._initialized:
            self.manager = MCPClientManager(config)
            await self.manager.initialize()
            self._tools = await self.manager.get_all_tools()
            self._initialized = True

    def get_tools(self) -> List[Dict[str, Any]]:
        """获取同步工具定义（基础工具）"""
        return self._tools

    def has_function(self, function_name: str) -> bool:
        """检查指定函数是否存在（包括动态 MCP 工具）"""
        # 检查是否是 MCP 工具
        for tool in self._tools:
            if tool['function']['name'] == function_name:
                return True
        return False
    
    async def invoke_function(self, function_name: str, **kwargs) -> ToolResult:
        """调用工具函数"""
        return await self.manager.call_tool(function_name, kwargs)
    
    async def cleanup(self):
        """清理资源"""
        if self.manager:
            await self.manager.cleanup() 
