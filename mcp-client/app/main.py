"""
MCP Client 主应用程序
独立的 MCP 客户端服务，提供 HTTP API 接口
"""

import logging
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router as mcp_router
from .services.mcp_client_service import MCPClientService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局 MCP 服务实例
mcp_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global mcp_service
    
    # 启动时初始化 MCP 服务
    logger.info("Initializing MCP Client Service...")
    mcp_service = MCPClientService()
    
    # 自动连接预设服务器
    try:
        logger.info("Auto-connecting to preset MCP servers...")
        result = await mcp_service.auto_connect_presets()
        logger.info(f"Auto-connect completed: {result['success_count']}/{result['total_servers']} servers connected")
    except Exception as e:
        logger.error(f"Failed to auto-connect preset servers: {e}")
    
    yield
    
    # 关闭时清理资源
    logger.info("Cleaning up MCP Client Service...")
    if mcp_service:
        await mcp_service.cleanup()


# 创建 FastAPI 应用
app = FastAPI(
    title="MCP Client Service",
    description="Model Context Protocol Client Service - Provides HTTP API for MCP functionality",
    version="1.0.0",
    lifespan=lifespan
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(mcp_router)


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "MCP Client",
        "version": "1.0.0",
        "description": "Model Context Protocol Client Service",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "service": "MCP Client"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    ) 