"""
MCP Client 核心服务
提供 Model Context Protocol 客户端功能
"""

import asyncio
import json
import os
import subprocess
import logging
from typing import Dict, Any, Optional, List

from .mcp_http_client import MCPHttpClient

logger = logging.getLogger(__name__)


class MCPClientService:
    """MCP Client 服务类，提供 Model Context Protocol 客户端功能"""

    def __init__(self):
        """初始化 MCP Client 服务"""
        self._preset_servers: Dict[str, Dict[str, Any]] = {}
        self._http_clients: Dict[str, MCPHttpClient] = {}
        self._load_preset_servers()
        
    def _load_preset_servers(self):
        """加载预设服务器配置"""
        config_paths = [
            "/mcp_servers/config.json",       # Docker容器路径 (优先)
            "mcp_servers/config.json",        # 开发环境路径
            "../mcp_servers/config.json"      # 相对路径
        ]
        
        for config_path in config_paths:
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        preset_servers = config.get("preset_servers", {})
                        
                        # 自动补全配置
                        for server_id, server_config in preset_servers.items():
                            self._normalize_server_config(server_id, server_config)
                        
                        self._preset_servers = preset_servers
                        logger.info(f"Loaded {len(self._preset_servers)} preset servers from {config_path}")
                        return
                except Exception as e:
                    logger.warning(f"Failed to load config from {config_path}: {e}")
                    continue
        
        logger.warning("No MCP server configuration found")
    
    def _normalize_server_config(self, server_id: str, server_config: Dict[str, Any]) -> None:
        """标准化服务器配置，自动补全缺失字段"""
        # 如果有URL字段但没有指定transport，自动设置为http
        if "url" in server_config and "transport" not in server_config:
            server_config["transport"] = "http"
            logger.debug(f"Auto-set transport=http for server {server_id} (has URL)")
        
        # 自动检测协议类型
        if server_config.get("transport") == "http" and "protocol" not in server_config:
            url = server_config.get("url", "")
            if "/sse" in url or "sse?" in url:
                server_config["protocol"] = "sse"
                logger.debug(f"Auto-detected protocol=sse for server {server_id} (SSE URL)")
            else:
                server_config["protocol"] = "rest"
                logger.debug(f"Auto-set protocol=rest for server {server_id}")
        
        # 设置默认值
        if "enabled" not in server_config:
            server_config["enabled"] = True
            logger.debug(f"Auto-set enabled=true for server {server_id}")
        
        if "auto_connect" not in server_config:
            server_config["auto_connect"] = True  # 修改默认值为True
            logger.debug(f"Auto-set auto_connect=true for server {server_id}")
        
        if "description" not in server_config:
            server_config["description"] = f"MCP Server: {server_id}"
            logger.debug(f"Auto-set description for server {server_id}")
    
    def _prepare_env(self, server_config: Dict[str, Any]) -> Dict[str, str]:
        """准备环境变量"""
        env = os.environ.copy()
        
        # 添加服务器特定的环境变量
        server_env = server_config.get("env", {})
        for key, value in server_env.items():
            if isinstance(value, str):
                # 使用统一的环境变量替换方法
                env[key] = self._substitute_env_vars(value)
            else:
                env[key] = str(value)
        
        return env
    
    async def _communicate_with_server(
        self, 
        server_id: str, 
        server_config: Dict[str, Any], 
        messages: List[Dict[str, Any]], 
        timeout: int = 15
    ) -> Optional[List[Dict[str, Any]]]:
        """与 MCP 服务器通信（stdio）"""
        try:
            command = server_config.get("command", "python")
            args = server_config.get("args", [])
            
            # 智能路径解析
            if args:
                script_path = args[0]
                if script_path.startswith("mcp_servers/"):
                    abs_path = "/" + script_path
                    if os.path.exists(abs_path):
                        args = [abs_path] + args[1:]
                        logger.debug(f"Using absolute path: {abs_path}")
            
            env = self._prepare_env(server_config)
            
            logger.debug(f"Starting MCP server {server_id}: {command} {' '.join(args)}")
            
            # 启动服务器进程
            process = subprocess.Popen(
                [command] + args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                text=True,
                cwd="/"
            )
            
            # 准备输入数据
            input_data = '\n'.join(json.dumps(msg) for msg in messages) + '\n'
            
            try:
                # 发送消息并等待响应
                stdout, stderr = process.communicate(input=input_data, timeout=timeout)
                
                if stderr:
                    logger.debug(f"MCP server {server_id} stderr: {stderr[:200]}...")
                    # 对于ZoomEye服务器，stderr中的日志信息是正常的
                    if server_id == "zoomeye-mcp-server" and "ZoomEye MCP server is running" in stderr:
                        logger.info(f"ZoomEye MCP server {server_id} started successfully")
                
                if not stdout:
                    logger.warning(f"No output from MCP server {server_id}")
                    if stderr and "Missing ZOOMEYE_API_KEY" in stderr:
                        logger.error(f"ZoomEye API key missing for server {server_id}")
                    return None
                
                # 解析响应
                responses = []
                lines = stdout.strip().split('\n')
                for line in lines:
                    if line.strip():
                        try:
                            response = json.loads(line)
                            responses.append(response)
                        except json.JSONDecodeError:
                            logger.debug(f"Invalid JSON line from {server_id}: {line[:100]}...")
                            continue
                
                if responses:
                    logger.debug(f"Received {len(responses)} responses from {server_id}")
                    return responses
                else:
                    logger.warning(f"No valid JSON responses from {server_id}")
                    return None
                    
            except subprocess.TimeoutExpired:
                logger.warning(f"Communication timeout with {server_id}")
                process.kill()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.terminate()
                return None
                
        except Exception as e:
            logger.error(f"Error communicating with {server_id}: {str(e)}")
            return None
    
    def _substitute_env_vars(self, text: str) -> str:
        """替换文本中的环境变量"""
        import re
        
        def replace_var(match):
            var_expr = match.group(1)
            if ':-' in var_expr:
                # 支持默认值语法 ${VAR:-default}
                var_name, default_value = var_expr.split(':-', 1)
                return os.environ.get(var_name, default_value)
            else:
                # 简单变量替换 ${VAR}
                return os.environ.get(var_expr, match.group(0))
        
        return re.sub(r'\$\{([^}]+)\}', replace_var, text)

    async def _get_http_client(self, server_id: str) -> Optional[MCPHttpClient]:
        """获取或创建 HTTP 客户端"""
        if server_id not in self._preset_servers:
            logger.error(f"Server {server_id} not found in preset servers")
            return None
            
        server_config = self._preset_servers[server_id]
        transport = server_config.get("transport", "stdio")
        
        if transport != "http":
            return None
            
        if server_id not in self._http_clients:
            base_url = server_config.get("url")
            if not base_url:
                logger.error(f"No URL configured for HTTP server {server_id}")
                return None
            
            # 替换URL中的环境变量
            base_url = self._substitute_env_vars(base_url)
            protocol = server_config.get("protocol", "rest")
            client = MCPHttpClient(base_url, protocol=protocol)
            self._http_clients[server_id] = client
            logger.debug(f"Created HTTP client for {server_id} with protocol: {protocol}")
            
        return self._http_clients[server_id]
    
    async def _communicate_with_http_server(
        self, 
        server_id: str, 
        method: str, 
        params: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """与 HTTP MCP 服务器通信"""
        client = await self._get_http_client(server_id)
        if not client:
            return None
            
        try:
            async with client:
                if method == "initialize":
                    return await client.initialize()
                elif method == "tools/list":
                    return await client.list_tools()
                elif method == "tools/call" and params:
                    tool_name = params.get("name")
                    arguments = params.get("arguments", {})
                    return await client.call_tool(tool_name, arguments)
                else:
                    logger.error(f"Unsupported HTTP method: {method}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error communicating with HTTP server {server_id}: {e}")
            return None
    
    async def test_server_connection(self, server_id: str) -> bool:
        """测试服务器连接"""
        if server_id not in self._preset_servers:
            logger.error(f"Server {server_id} not found in preset servers")
            return False
        
        server_config = self._preset_servers[server_id]
        transport = server_config.get("transport", "stdio")
        
        try:
            if transport == "http":
                # 测试 HTTP 连接
                result = await self._communicate_with_http_server(server_id, "initialize")
                if result:
                    logger.info(f"Successfully connected to HTTP server {server_id}")
                    return True
                else:
                    logger.warning(f"Failed to initialize HTTP connection to {server_id}")
                    return False
            else:
                # 测试 stdio 连接
                responses = await self._communicate_with_server(
                    server_id, 
                    server_config, 
                    [
                        self._create_init_message(),
                        {
                            "jsonrpc": "2.0",
                            "method": "notifications/initialized"
                        }
                    ],
                    timeout=15
                )
                
                if responses:
                    for response in responses:
                        if response.get('id') == 1 and 'result' in response:
                            logger.info(f"Successfully connected to stdio server {server_id}")
                            return True
                
                logger.warning(f"Failed to initialize stdio connection to {server_id}")
                return False
            
        except Exception as e:
            logger.error(f"Connection test failed for {server_id}: {str(e)}")
            return False
    
    def _create_init_message(self) -> Dict[str, Any]:
        """创建标准初始化消息"""
        return {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "ai-manus-mcp-client",
                    "version": "1.0.0"
                }
            }
        }

    async def list_server_tools(self, server_id: str) -> Optional[List[Dict[str, Any]]]:
        """列出服务器工具"""
        if server_id not in self._preset_servers:
            logger.error(f"Server {server_id} not found in preset servers")
            return None
        
        server_config = self._preset_servers[server_id]
        transport = server_config.get("transport", "stdio")
        
        try:
            if transport == "http":
                # HTTP 服务器工具列表
                return await self._communicate_with_http_server(server_id, "tools/list")
            else:
                # stdio 服务器工具列表
                messages = [
                    self._create_init_message(),
                    {
                        "jsonrpc": "2.0",
                        "method": "notifications/initialized"
                    },
                    {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "tools/list"
                    }
                ]
                
                responses = await self._communicate_with_server(
                    server_id,
                    server_config,
                    messages,
                    timeout=15
                )
                
                if responses:
                    for response in responses:
                        if response.get('id') == 2 and 'result' in response:
                            return response['result'].get('tools', [])
                
                return None
            
        except Exception as e:
            logger.error(f"Failed to list tools from {server_id}: {str(e)}")
            return None
    
    async def call_server_tool(self, server_id: str, tool_name: str, arguments: Dict[str, Any]) -> Optional[Any]:
        """调用服务器工具"""
        if server_id not in self._preset_servers:
            logger.error(f"Server {server_id} not found in preset servers")
            return None
        
        server_config = self._preset_servers[server_id]
        transport = server_config.get("transport", "stdio")
        
        try:
            if transport == "http":
                # HTTP 服务器工具调用
                result = await self._communicate_with_http_server(
                    server_id, 
                    "tools/call", 
                    {"name": tool_name, "arguments": arguments}
                )
                if result is not None:
                    logger.info(f"Tool {tool_name} executed successfully on HTTP server {server_id}")
                    return result
                else:
                    logger.warning(f"Failed to execute tool {tool_name} on HTTP server {server_id}")
                    return None
            else:
                # stdio 服务器工具调用
                messages = [
                    self._create_init_message(),
                    {
                        "jsonrpc": "2.0",
                        "method": "notifications/initialized"
                    },
                    {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "tools/call",
                        "params": {
                            "name": tool_name,
                            "arguments": arguments
                        }
                    }
                ]
                
                timeout_duration = 120 if server_id == "zoomeye-mcp-server" else 60  # ZoomEye需要更长时间
                responses = await self._communicate_with_server(
                    server_id,
                    server_config,
                    messages,
                    timeout=timeout_duration
                )
                
                if responses:
                    for response in responses:
                        if response.get('id') == 2:
                            if 'result' in response:
                                logger.info(f"Tool {tool_name} executed successfully on stdio server {server_id}")
                                return response['result']
                            elif 'error' in response:
                                logger.error(f"Tool {tool_name} execution failed on stdio server {server_id}: {response['error']}")
                                return None
                
                logger.warning(f"Failed to execute tool {tool_name} on stdio server {server_id}")
                return None
            
        except Exception as e:
            logger.error(f"Tool execution failed for {tool_name} on {server_id}: {str(e)}")
            return None
    
    async def auto_connect_presets(self) -> Dict[str, Any]:
        """自动连接预设服务器"""
        results = {}
        success_count = 0
        total_servers = 0
        
        for server_id, config in self._preset_servers.items():
            if config.get("enabled", True):
                total_servers += 1
                logger.info(f"Testing connection to preset MCP server: {server_id}")
                success = await self.test_server_connection(server_id)
                results[server_id] = success
                if success:
                    success_count += 1
                    logger.info(f"Successfully connected to preset MCP server: {server_id}")
                else:
                    logger.warning(f"Failed to connect to preset MCP server: {server_id}")
        
        return {
            "results": results,
            "success_count": success_count,
            "total_servers": total_servers,
            "success_rate": success_count / total_servers if total_servers > 0 else 0
        }
    
    def list_preset_servers(self) -> Dict[str, Any]:
        """列出预设服务器"""
        preset_servers = []
        for server_id, config in self._preset_servers.items():
            server_info = {
                "server_id": server_id,
                "description": config.get("description", "No description"),
                "command": config.get("command"),
                "transport": config.get("transport", "stdio"),
                "url": config.get("url"),
                "enabled": config.get("enabled", True),
                "auto_connect": config.get("auto_connect", False)
            }
            preset_servers.append(server_info)
        
        return {
            "preset_servers": preset_servers,
            "total_servers": len(preset_servers)
        }
    
    async def cleanup(self):
        """清理资源"""
        for client in self._http_clients.values():
            try:
                if hasattr(client, 'client') and client.client:
                    await client.client.aclose()
            except Exception as e:
                logger.error(f"Error closing HTTP client: {e}")
        
        self._http_clients.clear()
        logger.info("MCP Client Service cleaned up") 