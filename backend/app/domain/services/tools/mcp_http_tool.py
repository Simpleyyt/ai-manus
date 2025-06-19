"""
MCP HTTP Tool - 通过HTTP调用独立的MCP Client服务
"""

import os
import logging
from typing import Dict, Any, Optional
import httpx

from app.domain.services.tools.base import tool, BaseTool
from app.domain.models.tool_result import ToolResult

logger = logging.getLogger(__name__)


class MCPHttpTool(BaseTool):
    """MCP HTTP工具类，通过HTTP调用独立的MCP Client服务"""

    name: str = "mcp_http_tool"
    
    def __init__(self):
        """初始化MCP HTTP工具"""
        super().__init__()
        self.mcp_client_url = os.getenv("MCP_CLIENT_URL", "http://mcp-client:8001")
        
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """发送HTTP请求到MCP Client服务"""
        url = f"{self.mcp_client_url}{endpoint}"
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                if method.upper() == "GET":
                    response = await client.get(url)
                elif method.upper() == "POST":
                    response = await client.post(url, json=data)
                else:
                    logger.error(f"Unsupported HTTP method: {method}")
                    return None
                
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPError as e:
                logger.error(f"HTTP request failed: {e}")
                return None
            except Exception as e:
                logger.error(f"Unexpected error in HTTP request: {e}")
                return None
    
    @tool(
        name="mcp_list_servers",
        description="List all available MCP servers. Use this to see what MCP servers are configured and available.",
        parameters={},
        required=[]
    )
    async def mcp_list_servers(self) -> ToolResult:
        """列出所有可用的MCP服务器"""
        try:
            result = await self._make_request("GET", "/api/mcp/servers")
            
            if result and result.get("success"):
                servers = result.get("data", {}).get("preset_servers", [])
                server_info = []
                for server in servers:
                    server_info.append({
                        "id": server.get("server_id"),
                        "description": server.get("description"),
                        "transport": server.get("transport", "stdio"),
                        "enabled": server.get("enabled", True)
                    })
                
                return ToolResult(
                    success=True,
                    message=f"Found {len(server_info)} MCP servers",
                    data={
                        "servers": server_info,
                        "total_count": len(server_info)
                    }
                )
            else:
                return ToolResult(
                    success=False,
                    message="Failed to list MCP servers"
                )
                
        except Exception as e:
            logger.error(f"Failed to list MCP servers: {e}")
            return ToolResult(
                success=False,
                message=f"Failed to list MCP servers: {str(e)}"
            )
    
    @tool(
        name="mcp_connect_server",
        description="Connect to a specific MCP server. Use this to establish connection with an MCP server before using its tools.",
        parameters={
            "server_id": {
                "type": "string",
                "description": "The ID of the MCP server to connect to"
            }
        },
        required=["server_id"]
    )
    async def mcp_connect_server(self, server_id: str) -> ToolResult:
        """连接到指定的MCP服务器"""
        try:
            result = await self._make_request("POST", f"/api/mcp/servers/{server_id}/connect")
            
            if result and result.get("success"):
                return ToolResult(
                    success=True,
                    message=result.get("message", f"Successfully connected to server: {server_id}"),
                    data={"server_id": server_id}
                )
            else:
                return ToolResult(
                    success=False,
                    message=f"Failed to connect to server: {server_id}"
                )
                
        except Exception as e:
            logger.error(f"Failed to connect to server {server_id}: {e}")
            return ToolResult(
                success=False,
                message=f"Failed to connect to server {server_id}: {str(e)}"
            )
    
    @tool(
        name="mcp_auto_connect",
        description="Auto-connect to all available MCP servers. Use this to initialize all MCP servers at once.",
        parameters={},
        required=[]
    )
    async def mcp_auto_connect(self) -> ToolResult:
        """自动连接所有可用的MCP服务器"""
        try:
            result = await self._make_request("POST", "/api/mcp/servers/auto-connect")
            
            if result and result.get("success"):
                data = result.get("data", {})
                return ToolResult(
                    success=True,
                    message=f"Auto-connect completed: {data.get('success_count', 0)}/{data.get('total_servers', 0)} servers connected",
                    data=data
                )
            else:
                return ToolResult(
                    success=False,
                    message="Failed to auto-connect MCP servers"
                )
                
        except Exception as e:
            logger.error(f"Failed to auto-connect MCP servers: {e}")
            return ToolResult(
                success=False,
                message=f"Failed to auto-connect MCP servers: {str(e)}"
            )
    
    @tool(
        name="mcp_list_server_tools",
        description="List all tools available on a specific MCP server. Use this to discover what tools are available on a server.",
        parameters={
            "server_id": {
                "type": "string",
                "description": "The ID of the MCP server to list tools from"
            }
        },
        required=["server_id"]
    )
    async def mcp_list_server_tools(self, server_id: str) -> ToolResult:
        """列出指定服务器的工具"""
        try:
            result = await self._make_request("GET", f"/api/mcp/servers/{server_id}/tools")
            
            if result and result.get("success"):
                data = result.get("data", {})
                tools = data.get("tools", [])
                tool_info = []
                for tool in tools:
                    tool_info.append({
                        "name": tool.get("name"),
                        "description": tool.get("description"),
                        "parameters": tool.get("inputSchema", {})
                    })
                
                return ToolResult(
                    success=True,
                    message=f"Found {len(tool_info)} tools on server: {server_id}",
                    data={
                        "server_id": server_id,
                        "tools": tool_info,
                        "tool_count": len(tool_info)
                    }
                )
            else:
                return ToolResult(
                    success=False,
                    message=f"Failed to list tools from server: {server_id}"
                )
                
        except Exception as e:
            logger.error(f"Failed to list tools from server {server_id}: {e}")
            return ToolResult(
                success=False,
                message=f"Failed to list tools from server {server_id}: {str(e)}"
            )
    
    @tool(
        name="mcp_call_tool",
        description="Call a tool on an MCP server. Use this to execute tools available on MCP servers.",
        parameters={
            "server_id": {
                "type": "string",
                "description": "The ID of the MCP server containing the tool"
            },
            "tool_name": {
                "type": "string",
                "description": "The name of the tool to call"
            },
            "arguments": {
                "type": "object",
                "description": "Arguments to pass to the tool"
            }
        },
        required=["server_id", "tool_name"]
    )
    async def mcp_call_tool(self, server_id: str, tool_name: str, arguments: Dict[str, Any] = None) -> ToolResult:
        """调用MCP服务器上的工具"""
        # 为arguments提供默认值，避免AI模型调用时缺少参数
        if arguments is None:
            arguments = {}
        try:
            request_data = {
                "server_id": server_id,
                "tool_name": tool_name,
                "arguments": arguments
            }
            
            result = await self._make_request("POST", "/api/mcp/tools/call", request_data)
            
            if result and result.get("success"):
                data = result.get("data", {})
                return ToolResult(
                    success=True,
                    message=f"Successfully executed tool {tool_name} on server {server_id}",
                    data=data
                )
            else:
                return ToolResult(
                    success=False,
                    message=f"Failed to execute tool {tool_name} on server {server_id}"
                )
                
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name} on server {server_id}: {e}")
            return ToolResult(
                success=False,
                message=f"Failed to call tool {tool_name} on server {server_id}: {str(e)}"
            )
    
    @tool(
        name="mcp_get_server_status",
        description="Get the connection status of an MCP server. Use this to check if a server is connected and available.",
        parameters={
            "server_id": {
                "type": "string",
                "description": "The ID of the MCP server to check status for"
            }
        },
        required=["server_id"]
    )
    async def mcp_get_server_status(self, server_id: str) -> ToolResult:
        """获取MCP服务器的连接状态"""
        try:
            result = await self._make_request("GET", f"/api/mcp/servers/{server_id}/status")
            
            if result and result.get("success"):
                data = result.get("data", {})
                return ToolResult(
                    success=True,
                    message=f"Server {server_id} status: {data.get('status', 'unknown')}",
                    data=data
                )
            else:
                return ToolResult(
                    success=False,
                    message=f"Failed to get status for server: {server_id}"
                )
                
        except Exception as e:
            logger.error(f"Failed to get status for server {server_id}: {e}")
            return ToolResult(
                success=False,
                message=f"Failed to get status for server {server_id}: {str(e)}"
            )
    
    # 兼容性别名工具，确保与planner和execution提示的工具名称一致
    @tool(
        name="mcp_auto_connect_presets",
        description="Auto-connect to all preset MCP servers that have auto_connect enabled. Use this to initialize all configured servers.",
        parameters={},
        required=[]
    )
    async def mcp_auto_connect_presets(self) -> ToolResult:
        """自动连接所有预设的MCP服务器（别名）"""
        return await self.mcp_auto_connect()
    
    @tool(
        name="mcp_list_preset_servers",
        description="List all preset MCP servers available for connection. Use this to see what servers are pre-configured.",
        parameters={},
        required=[]
    )
    async def mcp_list_preset_servers(self) -> ToolResult:
        """列出所有预设MCP服务器（别名）"""
        return await self.mcp_list_servers()
    
    @tool(
        name="mcp_list_tools",
        description="List available tools from a connected MCP server. Use this to discover what tools are available on the server.",
        parameters={
            "server_id": {
                "type": "string",
                "description": "Unique identifier for the MCP server connection"
            }
        },
        required=["server_id"]
    )
    async def mcp_list_tools(self, server_id: str) -> ToolResult:
        """列出指定服务器的工具（别名）"""
        return await self.mcp_list_server_tools(server_id)
    
    @tool(
        name="mcp_check_connection_status",
        description="Check if MCP servers are already connected and ready to use. Use this FIRST before attempting to connect servers.",
        parameters={},
        required=[]
    )
    async def mcp_check_connection_status(self) -> ToolResult:
        """检查MCP服务器连接状态，避免重复初始化"""
        try:
            # 获取所有服务器列表
            servers_result = await self._make_request("GET", "/api/mcp/servers")
            
            if not servers_result or not servers_result.get("success"):
                return ToolResult(
                    success=False,
                    message="Failed to get MCP servers list"
                )
            
            servers = servers_result.get("data", {}).get("preset_servers", [])
            connected_servers = []
            available_tools_count = 0
            
            # 检查每个启用的服务器的工具
            for server in servers:
                if server.get("enabled", False):
                    server_id = server.get("server_id")
                    # 尝试获取服务器工具列表来判断连接状态
                    tools_result = await self._make_request("GET", f"/api/mcp/servers/{server_id}/tools")
                    if tools_result and tools_result.get("success"):
                        tools = tools_result.get("data", {}).get("tools", [])
                        if tools:
                            connected_servers.append({
                                "server_id": server_id,
                                "description": server.get("description", ""),
                                "tool_count": len(tools),
                                "tools": [tool.get("name") for tool in tools[:5]]  # 只显示前5个工具名称
                            })
                            available_tools_count += len(tools)
            
            if connected_servers:
                return ToolResult(
                    success=True,
                    message=f"MCP servers are already connected and ready. Found {len(connected_servers)} active servers with {available_tools_count} tools total.",
                    data={
                        "already_connected": True,
                        "connected_servers": connected_servers,
                        "total_servers": len(connected_servers),
                        "total_tools": available_tools_count,
                        "need_initialization": False
                    }
                )
            else:
                return ToolResult(
                    success=True,
                    message="No MCP servers are currently connected. Initialization may be needed.",
                    data={
                        "already_connected": False,
                        "connected_servers": [],
                        "total_servers": 0,
                        "total_tools": 0,
                        "need_initialization": True
                    }
                )
                
        except Exception as e:
            logger.error(f"Failed to check MCP connection status: {e}")
            return ToolResult(
                success=False,
                message=f"Failed to check MCP connection status: {str(e)}"
            ) 