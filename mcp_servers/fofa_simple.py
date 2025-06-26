import asyncio
import json
import os
import base64
import time
import sys
from typing import Any, Sequence
import requests  # 使用同步的requests库
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource


class FofaService:
    def __init__(self):
        self.api_base = "https://fofa.info/api/v1/search/all"
        self.user_agent = "fofa-app/1.0"
        self.email = os.environ.get("FOFA_EMAIL")
        self.key = os.environ.get("FOFA_KEY")
    
    def make_fofa_request(self, url: str) -> dict[str, Any] | None:
        """向FOFA API发送请求并处理响应 - 同步版本"""
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code != 200:
                print(f"FOFA API错误: {response.status_code} - {response.text}", file=sys.stderr)
                return None
            return response.json()
        except requests.exceptions.Timeout:
            print("FOFA API请求超时", file=sys.stderr)
            return None
        except requests.exceptions.RequestException as e:
            print(f"FOFA API请求错误: {e}", file=sys.stderr)
            return None
        except Exception as e:
            print(f"FOFA API未知错误: {e}", file=sys.stderr)
            return None

    def format_alerts(self, alerts: list[list[str]]) -> str:
        """格式化FOFA搜索结果"""
        if not alerts:
            return "无搜索结果"
        
        formatted_text = []
        for i, result in enumerate(alerts[:10]):  # 只显示前10个结果
            if len(result) >= 3:
                hostname, ip, port = result[0], result[1], result[2]
                formatted_text.append(f"{i+1}. 主机名: {hostname}\n   IP地址: {ip}\n   端口: {port}")
        
        if len(alerts) > 10:
            formatted_text.append(f"\n... 还有 {len(alerts) - 10} 个结果未显示")
        
        return "\n\n".join(formatted_text)

    def search_assets(self, **kwargs) -> dict[str, Any]:
        """FOFA资产搜索 - 同步版本"""
        if not self.email or not self.key:
            return {"error": "未配置FOFA_EMAIL或FOFA_KEY环境变量"}

        # 构建查询参数
        params = {}
        query_parts = []
        raw_query_params = {}

        # 处理查询参数
        for key, value in kwargs.items():
            if value:
                if key == "status_code":
                    query_parts.append(f'{key}={value}')
                else:
                    query_parts.append(f'{key}="{value}"')
                raw_query_params[key] = value

        if not query_parts:
            return {"error": "至少需要一个查询参数"}

        query_str = '&&'.join(query_parts)
        
        try:
            params['qbase64'] = base64.b64encode(query_str.encode()).decode()
            params['email'] = self.email
            params['key'] = self.key
            params['size'] = '50'  # 减少结果数量以提高性能
            params['fields'] = 'host,ip,port'

            # 使用requests构建URL
            import urllib.parse
            query_string = urllib.parse.urlencode(params)
            url = f"{self.api_base}?{query_string}"
            
            # 发送请求
            result = self.make_fofa_request(url)
            
            if result is None:
                return {"error": "FOFA API请求失败或无响应"}

            if 'error' in result and result['error']:
                return {"error": f"FOFA API错误: {result.get('errmsg', '未知错误')}"}

            if result and 'results' in result and result['results']:
                formatted_data = self.format_alerts(result['results'])
                query_params_str = ', '.join([f'{k}="{v}"' for k, v in raw_query_params.items()])
                
                return {
                    "success": True,
                    "query_params": query_params_str,
                    "data": formatted_data,
                    "total_results": len(result['results'])
                }
            else:
                return {"error": "未找到匹配的资产"}
                
        except Exception as e:
            return {"error": f"搜索过程中发生错误: {str(e)}"}


async def serve() -> None:
    server = Server("fofa-mcp-server")
    fofa_service = FofaService()

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """返回可用工具列表"""
        return [
            Tool(
                name="fofa_search",
                description="FOFA网络资产搜索工具，支持域名、IP、端口等多种查询方式",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "domain": {
                            "type": "string",
                            "description": "域名"
                        },
                        "ip": {
                            "type": "string", 
                            "description": "IP地址"
                        },
                        "port": {
                            "type": "string",
                            "description": "端口号"
                        },
                        "host": {
                            "type": "string",
                            "description": "主机名"
                        },
                        "body": {
                            "type": "string",
                            "description": "网页内容"
                        },
                        "status_code": {
                            "type": "string",
                            "description": "HTTP状态码",
                            "default": "200"
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="fofa_health_check",
                description="FOFA MCP服务器健康检查",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            )
        ]

    @server.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        """处理工具调用"""
        try:
            if name == "fofa_search":
                # 使用同步调用
                result = fofa_service.search_assets(**arguments)
                
                if "error" in result:
                    return [TextContent(type="text", text=f"错误: {result['error']}")]
                
                response_text = f"""FOFA 搜索结果：

查询参数: {result.get('query_params', 'N/A')}
找到结果数: {result.get('total_results', 0)}

资产详情:
{result.get('data', '无数据')}

黑客工具常见端口默认服务:
- 50050: Cobalt Strike Beacon
- 8834: Nessus

安全分析建议:
基于以上发现的资产，建议进行以下安全检查：
1. 检查暴露的服务是否为最新版本
2. 验证是否存在默认密码或弱密码
3. 确认服务配置的安全性
4. 检查是否有已知漏洞
"""
                return [TextContent(type="text", text=response_text)]
                
            elif name == "fofa_health_check":
                health_status = {
                    "status": "ok",
                    "message": "FOFA MCP server is running normally",
                    "timestamp": time.time(),
                    "api_key_configured": bool(fofa_service.key),
                    "email_configured": bool(fofa_service.email),
                    "version": "simple-1.0.0"
                }
                
                return [TextContent(type="text", text=json.dumps(health_status, indent=2, ensure_ascii=False))]
            
            else:
                return [TextContent(type="text", text=f"未知工具: {name}")]
                
        except Exception as e:
            return [TextContent(type="text", text=f"工具执行错误: {str(e)}")]

    # 启动服务器
    options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options)


if __name__ == "__main__":
    # 检查环境变量
    fofa_email = os.environ.get("FOFA_EMAIL")
    fofa_key = os.environ.get("FOFA_KEY")
    
    print("FOFA MCP 服务正在启动...", file=sys.stderr)
    print(f"API邮箱已配置: {'是' if fofa_email else '否'}", file=sys.stderr)
    print(f"API密钥已配置: {'是' if fofa_key else '否'}", file=sys.stderr)
    
    if not fofa_email or not fofa_key:
        print("警告: FOFA_EMAIL 或 FOFA_KEY 环境变量未设置. FOFA搜索功能将不可用。", file=sys.stderr)
    
    print("等待客户端连接...", file=sys.stderr)
    
    try:
        asyncio.run(serve())
    except KeyboardInterrupt:
        print("MCP 服务已停止", file=sys.stderr)
    except Exception as e:
        print(f"MCP 服务启动失败: {e}", file=sys.stderr)
        sys.exit(1) 
