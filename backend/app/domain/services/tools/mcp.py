import json
import logging
import os
from typing import Dict, Any, List, Optional
from contextlib import AsyncExitStack
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
from mcp.types import Tool as MCPTool

from app.domain.services.tools.base import BaseTool, tool
from app.domain.models.tool_result import ToolResult

logger = logging.getLogger(__name__)


class MCPClientManager:
    """MCP 客户端管理器"""
    
    def __init__(self):
        self._clients: Dict[str, ClientSession] = {}
        self._exit_stack = AsyncExitStack()
        self._server_configs: Dict[str, Dict[str, Any]] = {}
        self._tools_cache: Dict[str, List[MCPTool]] = {}
        self._initialized = False
    
    async def initialize(self, config_path: Optional[str] = None):
        """初始化 MCP 客户端管理器"""
        if self._initialized:
            return
            
        if not config_path:
            # Try multiple possible paths for config file
            possible_paths = [
                os.path.join(os.path.dirname(__file__), "../../../../../mcp_servers/config.json"),  # 本地开发环境
                "/app/mcp_servers/config.json",  # Docker环境
                os.path.join("/app", "mcp_servers", "config.json"),  # Docker环境备选
            ]
            
            config_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    config_path = path
                    break
            
            if not config_path:
                config_path = possible_paths[0]  # 默认使用第一个路径
        
        try:
            # 加载配置
            await self._load_config(config_path)
            
            # 连接到所有启用的服务器
            await self._connect_servers()
            
            self._initialized = True
            logger.info("MCP 客户端管理器初始化成功")
            
        except Exception as e:
            logger.error(f"MCP 客户端管理器初始化失败: {e}")
            raise
    
    async def _load_config(self, config_path: str):
        """加载 MCP 服务器配置"""
        try:
            config_file = Path(config_path)
            if not config_file.exists():
                logger.warning(f"MCP 配置文件不存在: {config_path}")
                return
                
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self._server_configs = config.get('mcp_servers', {})
            logger.info(f"加载了 {len(self._server_configs)} 个 MCP 服务器配置")
            
        except Exception as e:
            logger.error(f"加载 MCP 配置失败: {e}")
            raise
    
    async def _connect_servers(self):
        """连接到所有启用的 MCP 服务器"""
        for server_name, config in self._server_configs.items():
            if not config.get('enabled', True):
                continue
                
            if not config.get('auto_connect', True):
                continue
                
            try:
                await self._connect_server(server_name, config)
            except Exception as e:
                logger.error(f"连接到 MCP 服务器 {server_name} 失败: {e}")
                # 继续连接其他服务器
                continue
    
    async def _connect_server(self, server_name: str, config: Dict[str, Any]):
        """连接到单个 MCP 服务器"""
        try:
            transport_type = config.get('transport', 'stdio')
            
            if transport_type == 'stdio':
                await self._connect_stdio_server(server_name, config)
            elif transport_type == 'http':
                await self._connect_http_server(server_name, config)
            else:
                logger.error(f"不支持的传输类型: {transport_type}")
                
        except Exception as e:
            logger.error(f"连接 MCP 服务器 {server_name} 失败: {e}")
            raise
    
    async def _connect_stdio_server(self, server_name: str, config: Dict[str, Any]):
        """连接到 stdio MCP 服务器"""
        command = config.get('command')
        args = config.get('args', [])
        env = config.get('env', {})
        
        if not command:
            raise ValueError(f"服务器 {server_name} 缺少 command 配置")
        
        # 处理相对路径参数，转换为绝对路径
        processed_args = []
        for arg in args:
            if isinstance(arg, str) and arg.startswith('../'):
                # 将相对路径转换为基于工作目录的绝对路径
                processed_args.append(os.path.join('/app', arg[3:]))
            elif isinstance(arg, str) and not os.path.isabs(arg) and '/' in arg:
                # 处理其他相对路径情况
                processed_args.append(os.path.join('/app', arg))
            else:
                processed_args.append(arg)
        
        # 准备环境变量
        server_env = os.environ.copy()
        server_env.update(env)
        
        # 创建服务器参数
        server_params = StdioServerParameters(
            command=command,
            args=processed_args,
            env=server_env
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
    
    async def _connect_http_server(self, server_name: str, config: Dict[str, Any]):
        """连接到 HTTP MCP 服务器"""
        url = config.get('url')
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
            for srv_name in self._server_configs.keys():
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
    
    async def get_servers_info(self) -> Dict[str, Any]:
        """获取所有服务器信息"""
        servers_info = {}
        
        for server_name, config in self._server_configs.items():
            tools_count = len(self._tools_cache.get(server_name, []))
            connected = server_name in self._clients
            
            servers_info[server_name] = {
                "description": config.get('description', ''),
                "transport": config.get('transport', 'stdio'),
                "enabled": config.get('enabled', True),
                "auto_connect": config.get('auto_connect', True),
                "connected": connected,
                "tools_count": tools_count
            }
        
        return servers_info
    
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
        self.manager = MCPClientManager()
        self._initialized = False
    
    async def _ensure_initialized(self):
        """确保管理器已初始化"""
        if not self._initialized:
            await self.manager.initialize()
            self._initialized = True
    
    @tool(
        name="list_mcp_servers",
        description="列出所有可用的 MCP 服务器及其状态",
        parameters={},
        required=[]
    )
    async def list_mcp_servers(self) -> ToolResult:
        """列出所有 MCP 服务器"""
        try:
            await self._ensure_initialized()
            servers_info = await self.manager.get_servers_info()
            
            result_text = "MCP 服务器列表:\n"
            for server_name, info in servers_info.items():
                status = "已连接" if info['connected'] else "未连接"
                result_text += f"\n- {server_name}: {status}\n"
                result_text += f"  描述: {info['description']}\n"
                result_text += f"  传输类型: {info['transport']}\n"
                result_text += f"  工具数量: {info['tools_count']}\n"
            
            return ToolResult(
                success=True,
                data=result_text
            )
            
        except Exception as e:
            logger.error(f"列出 MCP 服务器失败: {e}")
            return ToolResult(
                success=False,
                message=f"列出 MCP 服务器失败: {str(e)}"
            )
    
    @tool(
        name="list_mcp_tools",
        description="列出所有可用的 MCP 工具",
        parameters={},
        required=[]
    )
    async def list_mcp_tools(self) -> ToolResult:
        """列出所有 MCP 工具"""
        try:
            await self._ensure_initialized()
            tools = await self.manager.get_all_tools()
            
            if not tools:
                return ToolResult(
                    success=True,
                    data="没有可用的 MCP 工具"
                )
            
            result_text = f"可用的 MCP 工具 ({len(tools)} 个):\n"
            for tool in tools:
                func_info = tool["function"]
                result_text += f"\n- {func_info['name']}: {func_info['description']}\n"
            
            return ToolResult(
                success=True,
                data=result_text
            )
            
        except Exception as e:
            logger.error(f"列出 MCP 工具失败: {e}")
            return ToolResult(
                success=False,
                message=f"列出 MCP 工具失败: {str(e)}"
            )
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """获取同步工具定义（基础工具）"""
        return super().get_tools()
    
    async def get_tools_async(self) -> List[Dict[str, Any]]:
        """获取所有工具定义（包括异步的 MCP 工具）"""
        try:
            await self._ensure_initialized()
            
            # 获取基础工具
            base_tools = super().get_tools()
            
            # 获取 MCP 工具并添加到列表
            mcp_tools = await self.manager.get_all_tools()
            
            return base_tools + mcp_tools
            
        except Exception as e:
            logger.error(f"获取 MCP 工具失败: {e}")
            return super().get_tools()  # 返回基础工具
    
    def has_function(self, function_name: str) -> bool:
        """检查指定函数是否存在（包括动态 MCP 工具）"""
        # 首先检查基础工具
        if super().has_function(function_name):
            return True
        
        # 检查是否是 MCP 工具
        if function_name.startswith('mcp_') or any(function_name.startswith(f"{srv_name}_") for srv_name in self.manager._server_configs.keys() if srv_name.startswith('mcp_')):
            return True
        
        return False
    
    async def invoke_function(self, function_name: str, **kwargs) -> ToolResult:
        """调用工具函数"""
        try:
            await self._ensure_initialized()
            
            # 检查是否是 MCP 工具
            if function_name.startswith('mcp_'):
                return await self.manager.call_tool(function_name, kwargs)
            
            # 否则调用基础工具
            return await super().invoke_function(function_name, **kwargs)
            
        except Exception as e:
            logger.error(f"调用工具 {function_name} 失败: {e}")
            return ToolResult(
                success=False,
                message=f"调用工具失败: {str(e)}"
            )
    
    async def cleanup(self):
        """清理资源"""
        if self.manager:
            await self.manager.cleanup() 
