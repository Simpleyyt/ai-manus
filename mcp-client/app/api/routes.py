"""
MCP Client HTTP API 路由
提供 RESTful API 接口来访问 MCP 功能
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging

from ..services.mcp_client_service import MCPClientService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/mcp", tags=["MCP Client"])

# 全局 MCP 客户端服务实例
mcp_service = MCPClientService()


class ToolCallRequest(BaseModel):
    server_id: str
    tool_name: str
    arguments: Dict[str, Any]


class ConnectRequest(BaseModel):
    server_id: str
    command: Optional[str] = None
    args: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None


@router.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "service": "MCP Client"}


@router.get("/servers")
async def list_preset_servers():
    """列出预设服务器"""
    try:
        result = mcp_service.list_preset_servers()
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"Failed to list preset servers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/servers/{server_id}/connect")
async def connect_server(server_id: str):
    """连接到预设服务器"""
    try:
        success = await mcp_service.test_server_connection(server_id)
        if success:
            return {
                "success": True,
                "message": f"Successfully connected to server: {server_id}"
            }
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to connect to server: {server_id}"
            )
    except Exception as e:
        logger.error(f"Failed to connect to server {server_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/servers/auto-connect")
async def auto_connect_servers():
    """自动连接所有预设服务器"""
    try:
        result = await mcp_service.auto_connect_presets()
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"Failed to auto-connect servers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/servers/{server_id}/tools")
async def list_server_tools(server_id: str):
    """列出服务器的工具"""
    try:
        tools = await mcp_service.list_server_tools(server_id)
        if tools is not None:
            return {
                "success": True,
                "data": {
                    "server_id": server_id,
                    "tools": tools,
                    "tool_count": len(tools)
                }
            }
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to list tools from server: {server_id}"
            )
    except Exception as e:
        logger.error(f"Failed to list tools from server {server_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tools/call")
async def call_tool(request: ToolCallRequest):
    """调用MCP工具"""
    try:
        result = await mcp_service.call_server_tool(
            request.server_id,
            request.tool_name,
            request.arguments
        )
        
        if result is not None:
            return {
                "success": True,
                "data": {
                    "server_id": request.server_id,
                    "tool_name": request.tool_name,
                    "arguments": request.arguments,
                    "result": result
                }
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to execute tool {request.tool_name} on server {request.server_id}"
            )
    except Exception as e:
        logger.error(f"Failed to call tool {request.tool_name} on server {request.server_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/servers/{server_id}/status")
async def get_server_status(server_id: str):
    """获取服务器连接状态"""
    try:
        is_connected = await mcp_service.test_server_connection(server_id)
        return {
            "success": True,
            "data": {
                "server_id": server_id,
                "connected": is_connected,
                "status": "connected" if is_connected else "disconnected"
            }
        }
    except Exception as e:
        logger.error(f"Failed to get status for server {server_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 