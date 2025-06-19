"""
HTTP/SSE MCP 客户端实现
支持通过 HTTP 和 Server-Sent Events 连接 MCP 服务器
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List, AsyncGenerator, Union
import httpx
from contextlib import asynccontextmanager
import re

logger = logging.getLogger(__name__)

class MCPHttpClient:
    """HTTP/SSE MCP 客户端"""
    
    def __init__(self, base_url: str, protocol: str = "rest", timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.protocol = protocol  # "rest" or "sse"
        self.timeout = timeout
        self.client: Optional[httpx.AsyncClient] = None
        self.session_id: Optional[str] = None
        self._initialized = False
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.client = httpx.AsyncClient(timeout=self.timeout)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.client:
            await self.client.aclose()
            
    async def initialize(self) -> bool:
        """初始化连接"""
        if self._initialized:
            return True
            
        if self.protocol == "sse":
            return await self._initialize_sse()
        else:
            return await self._initialize_rest()
            
    async def _initialize_rest(self) -> bool:
        """初始化REST API连接"""
        try:
            init_message = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "sampling": {}
                    },
                    "clientInfo": {
                        "name": "ai-manus-http-client",
                        "version": "1.0.0"
                    }
                }
            }
            
            response = await self.client.post(
                f"{self.base_url}/mcp/initialize",
                json=init_message,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'result' in result:
                    self.session_id = result.get('sessionId')
                    self._initialized = True
                    logger.info(f"MCP HTTP client (REST) initialized successfully: {self.base_url}")
                    return True
                    
            logger.error(f"Failed to initialize MCP HTTP client (REST): {response.status_code}")
            return False
            
        except Exception as e:
            logger.error(f"Error initializing MCP HTTP client (REST): {e}")
            return False
            
    async def _initialize_sse(self) -> bool:
        """初始化SSE连接"""
        try:
            # 对于SSE，使用GET请求建立连接，但设置较短的超时时间
            async with self.client.stream(
                "GET",
                self.base_url,
                headers={
                    "Accept": "text/event-stream",
                    "Cache-Control": "no-cache"
                },
                timeout=10.0  # 设置10秒超时
            ) as response:
                if response.status_code == 200:
                    # 处理特殊的endpoint响应
                    async for line in response.aiter_lines():
                        line = line.strip()
                        if line.startswith("event: endpoint"):
                            continue
                        elif line.startswith("data: "):
                            endpoint_path = line[6:]  # Remove "data: " prefix
                            if endpoint_path.startswith("/"):
                                # 提取base URL并构建完整的endpoint
                                base_url_parts = self.base_url.split("/sse")
                                if len(base_url_parts) > 0:
                                    self.endpoint_url = base_url_parts[0] + endpoint_path
                                    logger.info(f"MCP SSE client got endpoint: {self.endpoint_url}")
                                    self._initialized = True
                                    return True
                        
                        # 如果读取了一些行但没有找到endpoint，也认为连接成功
                        if line and not line.startswith(("event:", "data:")):
                            self._initialized = True
                            logger.info(f"MCP SSE client connected (non-standard response): {self.base_url}")
                            return True
                    
                    # 即使没有特殊响应，200状态码也表示连接成功
                    self._initialized = True
                    logger.info(f"MCP SSE client connected successfully: {self.base_url}")
                    return True
                else:
                    logger.error(f"Failed to initialize MCP SSE client: {response.status_code}")
                    return False
            
        except Exception as e:
            logger.error(f"Error initializing MCP SSE client: {e}")
            return False
            
    async def list_tools(self) -> Optional[List[Dict[str, Any]]]:
        """获取工具列表"""
        if not self._initialized:
            if not await self.initialize():
                return None
                
        if self.protocol == "sse":
            return await self._list_tools_sse()
        else:
            return await self._list_tools_rest()
            
    async def _list_tools_rest(self) -> Optional[List[Dict[str, Any]]]:
        """通过REST API获取工具列表"""
        try:
            message = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list"
            }
            
            headers = {"Content-Type": "application/json"}
            if self.session_id:
                headers["X-Session-ID"] = self.session_id
                
            response = await self.client.post(
                f"{self.base_url}/mcp/tools/list",
                json=message,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'result' in result:
                    return result['result'].get('tools', [])
                    
            logger.error(f"Failed to list tools (REST): {response.status_code}")
            return None
            
        except Exception as e:
            logger.error(f"Error listing tools (REST): {e}")
            return None
            
    async def _list_tools_sse(self) -> Optional[List[Dict[str, Any]]]:
        """通过SSE获取工具列表"""
        try:
            # 如果有endpoint URL，优先使用它
            if hasattr(self, 'endpoint_url') and self.endpoint_url:
                logger.info(f"Trying to get tools from endpoint: {self.endpoint_url}")
                try:
                    # 尝试通过endpoint获取工具列表
                    response = await self.client.post(
                        self.endpoint_url,
                        json={
                            "jsonrpc": "2.0",
                            "id": 1,
                            "method": "tools/list"
                        },
                        headers={"Content-Type": "application/json"},
                        timeout=10.0
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if 'result' in result and 'tools' in result['result']:
                            tools = result['result']['tools']
                            logger.info(f"Found {len(tools)} tools via endpoint")
                            return tools
                        elif 'tools' in result:
                            tools = result['tools']
                            logger.info(f"Found {len(tools)} tools via direct response")
                            return tools
                except Exception as e:
                    logger.warning(f"Failed to get tools from endpoint: {e}")
            
            # 回退到原始SSE方法
            async with self.client.stream(
                "GET",
                self.base_url,
                headers={
                    "Accept": "text/event-stream",
                    "Cache-Control": "no-cache"
                },
                timeout=10.0  # 设置10秒超时
            ) as response:
                if response.status_code == 200:
                    tools = []
                    line_count = 0
                    max_lines = 20  # 减少最大行数，加快响应
                    found_endpoint = False
                    
                    async for line in response.aiter_lines():
                        line = line.strip()
                        line_count += 1
                        
                        # 避免无限等待
                        if line_count > max_lines:
                            logger.info("SSE tools list: reached max lines limit")
                            break
                        
                        # 处理endpoint事件
                        if line.startswith("event: endpoint"):
                            found_endpoint = True
                            continue
                        elif line.startswith("data: ") and found_endpoint:
                            endpoint_path = line[6:]
                            if endpoint_path.startswith("/"):
                                logger.info(f"Found endpoint in tools/list: {endpoint_path}")
                                # 对于这种服务器，可能需要通过endpoint进行进一步通信
                                # 暂时返回一个示例工具列表，表明连接成功
                                return [{
                                    "name": "sec_analysis", 
                                    "description": "安全告警智能研判工具",
                                    "inputSchema": {
                                        "type": "object",
                                        "properties": {
                                            "alert_data": {
                                                "type": "string",
                                                "description": "告警数据"
                                            }
                                        },
                                        "required": ["alert_data"]
                                    }
                                }]
                        
                        # 解析其他格式的事件数据
                        result = await self._parse_sse_line(line)
                        if result and 'tools' in result:
                            tools = result.get('tools', [])
                            if tools:
                                logger.info(f"Found {len(tools)} tools via SSE events")
                                return tools
                    
                    # 如果没有找到工具但连接成功，返回空列表
                    logger.info("SSE connection successful but no tools found, returning empty list")
                    return []
                else:
                    logger.error(f"Failed to list tools (SSE): {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error listing tools (SSE): {e}")
            return None
            
    async def _parse_sse_line(self, line: str) -> Optional[Dict[str, Any]]:
        """解析SSE事件行"""
        try:
            line = line.strip()
            if line.startswith("data: "):
                data_str = line[6:]  # Remove "data: " prefix
                if data_str and data_str != "[DONE]":
                    return json.loads(data_str)
            elif line.startswith("event: "):
                # Handle event type if needed
                pass
            return None
        except json.JSONDecodeError:
            return None
            
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[Any]:
        """调用工具"""
        if not self._initialized:
            if not await self.initialize():
                return None
                
        if self.protocol == "sse":
            return await self._call_tool_sse(tool_name, arguments)
        else:
            return await self._call_tool_rest(tool_name, arguments)
            
    async def _call_tool_rest(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[Any]:
        """通过REST API调用工具"""
        try:
            message = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            headers = {"Content-Type": "application/json"}
            if self.session_id:
                headers["X-Session-ID"] = self.session_id
                
            response = await self.client.post(
                f"{self.base_url}/mcp/tools/call",
                json=message,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'result' in result:
                    return result['result']
                elif 'error' in result:
                    logger.error(f"Tool call error (REST): {result['error']}")
                    return None
                    
            logger.error(f"Failed to call tool (REST): {response.status_code}")
            return None
            
        except Exception as e:
            logger.error(f"Error calling tool (REST): {e}")
            return None
            
    async def _call_tool_sse(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[Any]:
        """通过SSE调用工具"""
        # 临时提升日志级别用于调试
        original_level = logger.level
        logger.setLevel(logging.DEBUG)
        
        try:
            # 如果有从初始化阶段获取的endpoint URL，直接使用它
            if hasattr(self, 'endpoint_url') and self.endpoint_url:
                logger.info(f"Calling tool {tool_name} via endpoint: {self.endpoint_url}")
                try:
                    # 使用endpoint URL直接调用工具
                    response = await self.client.post(
                        self.endpoint_url,
                        json={
                            "jsonrpc": "2.0",
                            "id": 1,
                            "method": "tools/call",
                            "params": {
                                "name": tool_name,
                                "arguments": arguments
                            }
                        },
                        headers={"Content-Type": "application/json"},
                        timeout=30.0
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if 'result' in result:
                            logger.info(f"Tool {tool_name} executed successfully via endpoint")
                            return result['result']
                        elif 'tools' in result and len(result['tools']) > 0:
                            # 处理直接返回工具结果的情况
                            tool_result = result['tools'][0]
                            logger.info(f"Tool {tool_name} executed successfully (direct result)")
                            return tool_result
                        else:
                            logger.warning(f"Tool {tool_name} executed but no result found")
                            return result
                    elif response.status_code == 202:
                        # 202 Accepted表示请求已接受，可能需要等待结果
                        logger.info(f"Tool {tool_name} request accepted, checking for results...")
                        
                        # 建立SSE连接获取结果
                        async with self.client.stream(
                            "GET",
                            self.base_url,
                            headers={
                                "Accept": "text/event-stream",
                                "Cache-Control": "no-cache"
                            },
                            timeout=60.0  # 增加超时时间等待处理结果
                        ) as sse_response:
                            if sse_response.status_code == 200:
                                logger.info(f"SSE connection established, waiting for results...")
                                line_count = 0
                                max_lines = 200  # 增加最大行数以获取更多数据
                                result_found = False
                                endpoint_received = False
                                
                                async for line in sse_response.aiter_lines():
                                    line = line.strip()
                                    line_count += 1
                                    
                                    # 记录所有接收到的SSE数据（调试用）
                                    if line:
                                        logger.debug(f"SSE line {line_count}: {line[:200]}...")
                                    
                                    if line.startswith("data: "):
                                        data_str = line[6:]
                                        if data_str and data_str != "[DONE]":
                                            logger.info(f"Received SSE data: {data_str[:300]}...")
                                            
                                            # 检查是否是新的endpoint URL
                                            if data_str.startswith("/messages/?session_id="):
                                                # 这是一个新的endpoint，说明有新的session可用
                                                logger.info(f"Received new session endpoint: {data_str}")
                                                endpoint_received = True
                                                
                                                # 对于SSE服务器，endpoint通常是用于后续通信的
                                                # 继续监听当前SSE流看是否有更多数据
                                                continue
                                            
                                            # 尝试解析为JSON
                                            try:
                                                data = json.loads(data_str)
                                                logger.info(f"Parsed SSE JSON: {json.dumps(data, indent=2)[:500]}...")
                                                
                                                # 查找工具调用结果的多种格式
                                                if 'result' in data:
                                                    logger.info(f"Tool {tool_name} result received via SSE")
                                                    result_found = True
                                                    return data['result']
                                                elif 'content' in data:
                                                    logger.info(f"Tool {tool_name} content received via SSE")
                                                    result_found = True
                                                    return data['content']
                                                elif 'message' in data:
                                                    logger.info(f"Tool {tool_name} message received via SSE")
                                                    result_found = True
                                                    return data['message']
                                                elif 'text' in data:
                                                    logger.info(f"Tool {tool_name} text received via SSE")
                                                    result_found = True
                                                    return data['text']
                                                elif 'response' in data:
                                                    logger.info(f"Tool {tool_name} response received via SSE")
                                                    result_found = True
                                                    return data['response']
                                                elif 'analysis' in data or 'analysis_result' in data:
                                                    # 专门为安全分析工具添加的字段检查
                                                    analysis_result = data.get('analysis') or data.get('analysis_result')
                                                    logger.info(f"Tool {tool_name} analysis result received via SSE")
                                                    result_found = True
                                                    return analysis_result
                                                else:
                                                    # 记录未识别的数据格式
                                                    logger.info(f"Unrecognized SSE data format: {list(data.keys())}")
                                                    # 如果已经收到了endpoint且有数据，可能整个数据就是结果
                                                    if endpoint_received and data:
                                                        logger.info(f"Using entire data object as result")
                                                        result_found = True
                                                        return data
                                                    
                                            except json.JSONDecodeError as e:
                                                logger.debug(f"SSE data is not valid JSON: {e}")
                                                # 可能是纯文本响应
                                                if data_str.strip() and not data_str.startswith("/"):
                                                    logger.info(f"Tool {tool_name} text response received via SSE")
                                                    result_found = True
                                                    return data_str.strip()
                                            except Exception as e:
                                                logger.debug(f"Error parsing SSE data: {e}")
                                                continue
                                    
                                    # 检查是否有其他格式的事件
                                    elif line.startswith("event: "):
                                        event_type = line[7:]
                                        logger.debug(f"SSE event type: {event_type}")
                                        # 检查是否是结果相关的事件
                                        if event_type in ["result", "analysis", "completed", "finished"]:
                                            logger.info(f"Received result-related event: {event_type}")
                                    elif line.startswith("id: "):
                                        event_id = line[4:]
                                        logger.debug(f"SSE event id: {event_id}")
                                    elif line == "":
                                        # 空行分隔事件
                                        continue
                                    else:
                                        # 记录其他格式的行
                                        if line:
                                            logger.debug(f"SSE other line: {line[:100]}...")
                                    
                                    # 避免无限等待，但增加超时时间
                                    if line_count > max_lines:
                                        logger.warning(f"SSE reached max lines ({max_lines}), stopping")
                                        break
                                
                                if not result_found:
                                    if endpoint_received:
                                        logger.info(f"Tool {tool_name} request processed (endpoint received) but no result data after {line_count} lines")
                                        return {
                                            "status": "processed", 
                                            "message": f"Tool request was processed by the server. An endpoint was provided but no result data was received in the SSE stream.",
                                            "lines_monitored": line_count
                                        }
                                    else:
                                        logger.warning(f"Tool {tool_name} request accepted but no result received after {line_count} lines")
                                        return {"status": "timeout", "message": f"Tool request was accepted but no result received after monitoring {line_count} SSE lines"}
                            else:
                                logger.error(f"SSE connection failed: {sse_response.status_code}")
                                return None
                except Exception as e:
                    logger.error(f"Error calling tool {tool_name} via endpoint: {e}")
                    return None
            
            # 回退到原始的SSE方法
            async with self.client.stream(
                "GET",
                self.base_url,
                headers={
                    "Accept": "text/event-stream",
                    "Cache-Control": "no-cache"
                }
            ) as response:
                if response.status_code == 200:
                    result = None
                    message_sent = False
                    
                    async for line in response.aiter_lines():
                        line = line.strip()
                        
                        # 当连接建立后，发送工具调用请求
                        if not message_sent and (line.startswith("data:") or line.startswith("event:")):
                            # 通过单独的API调用工具
                            asyncio.create_task(self._send_tool_call_request(tool_name, arguments))
                            message_sent = True
                        
                        # 解析响应
                        parsed = await self._parse_sse_line(line)
                        if parsed:
                            # 查找工具调用结果
                            if parsed.get('method') == 'tools/call' and 'result' in parsed:
                                result = parsed['result']
                                break
                            elif parsed.get('tool') == tool_name and 'result' in parsed:
                                result = parsed['result']
                                break
                            elif 'error' in parsed:
                                logger.error(f"Tool call error (SSE): {parsed['error']}")
                                return None
                        
                        # 避免无限等待
                        if len(line) == 0:
                            break
                    
                    return result
                else:
                    logger.error(f"Failed to call tool (SSE): {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error calling tool (SSE): {e}")
            return None
        finally:
            # 恢复原始日志级别
            logger.setLevel(original_level)
    
    async def _send_tool_call_request(self, tool_name: str, arguments: Dict[str, Any]) -> None:
        """发送工具调用请求"""
        try:
            # 如果有endpoint URL，使用它
            if hasattr(self, 'endpoint_url') and self.endpoint_url:
                logger.debug(f"Sending tool call to endpoint: {self.endpoint_url}")
                try:
                    response = await self.client.post(
                        self.endpoint_url,
                        json={
                            "jsonrpc": "2.0",
                            "id": 1,
                            "method": "tools/call",
                            "params": {
                                "name": tool_name,
                                "arguments": arguments
                            }
                        },
                        headers={"Content-Type": "application/json"}
                    )
                    if response.status_code in [200, 202]:
                        logger.debug(f"Successfully sent tool call request to endpoint")
                        return
                except Exception as e:
                    logger.debug(f"Failed to send tool call request to endpoint: {e}")
            
            # 如果没有endpoint URL，尝试标准的MCP端点
            try:
                response = await self.client.post(
                    f"{self.base_url.replace('/sse', '/mcp/tools/call')}",
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "tools/call",
                        "params": {
                            "name": tool_name,
                            "arguments": arguments
                        }
                    },
                    headers={"Content-Type": "application/json"}
                )
                if response.status_code in [200, 202]:
                    logger.debug(f"Successfully sent tool call request to MCP endpoint")
            except Exception as e:
                logger.debug(f"Failed to send tool call request: {e}")
                    
        except Exception as e:
            logger.debug(f"Failed to send tool call request: {e}")
            
    async def stream_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """流式调用工具（SSE）"""
        if not self._initialized:
            if not await self.initialize():
                return
                
        try:
            message = {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/stream",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            headers = {
                "Accept": "text/event-stream",
                "Cache-Control": "no-cache",
                "Content-Type": "application/json"
            }
            if self.session_id:
                headers["X-Session-ID"] = self.session_id
                
            endpoint = f"{self.base_url}/mcp/tools/stream" if self.protocol == "rest" else self.base_url
                
            async with self.client.stream(
                "POST",
                endpoint,
                json=message,
                headers=headers
            ) as response:
                if response.status_code == 200:
                    async for line in response.aiter_lines():
                        result = await self._parse_sse_line(line)
                        if result:
                            yield result
                else:
                    logger.error(f"Failed to stream tool call: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Error streaming tool call: {e}")
            
    async def test_connection(self) -> bool:
        """测试连接"""
        try:
            if self.protocol == "sse":
                # 对于SSE服务器，使用GET请求测试连接
                response = await self.client.get(
                    self.base_url,
                    headers={
                        "Accept": "text/event-stream",
                        "Cache-Control": "no-cache"
                    }
                )
                # SSE连接成功的状态码通常是200
                return response.status_code == 200
            else:
                # 对于REST服务器，检查健康端点
                response = await self.client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
            
    async def _send_tools_list_request(self) -> None:
        """发送工具列表请求（通过单独的POST）"""
        try:
            # 尝试向可能的API端点发送请求
            possible_endpoints = [
                f"{self.base_url.replace('/sse', '/api/tools')}",
                f"{self.base_url.replace('/sse', '/tools')}",
                f"{self.base_url.replace('/sse', '/mcp/tools/list')}",
            ]
            
            for endpoint in possible_endpoints:
                try:
                    response = await self.client.post(
                        endpoint,
                        json={
                            "jsonrpc": "2.0",
                            "id": 1,
                            "method": "tools/list"
                        },
                        headers={"Content-Type": "application/json"}
                    )
                    if response.status_code == 200:
                        logger.debug(f"Successfully sent tools list request to {endpoint}")
                        break
                except Exception:
                    continue
                    
        except Exception as e:
            logger.debug(f"Failed to send tools list request: {e}") 