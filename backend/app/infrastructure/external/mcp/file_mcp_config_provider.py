import json
import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from app.domain.external.mcp_config import MCPConfigProvider
from app.infrastructure.config import get_settings

logger = logging.getLogger(__name__)


class FileMCPConfigProvider(MCPConfigProvider):
    """基于文件的MCP配置提供者实现"""
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化配置提供者
        
        Args:
            config_path: 配置文件路径，如果不提供则从设置中获取
        """
        self._config_path = config_path
        self._cached_config: Optional[Dict[str, Dict[str, Any]]] = None
        
    async def get_servers_config(self) -> Dict[str, Dict[str, Any]]:
        """获取MCP服务器配置"""
        if self._cached_config is not None:
            return self._cached_config
            
        config_path = self._get_config_path()
        if not config_path:
            logger.warning("cannot find mcp config path")
            return {}
            
        try:
            config_file = Path(config_path)
            if not config_file.exists():
                logger.warning(f"mcp config file not found: {config_path}")
                return {}
                
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            logger.info(f"mcp config: {config}")
            self._cached_config = config.get('mcpServers', {})
            logger.info(f"loaded {len(self._cached_config)} mcp servers config")
            
            # 处理相对路径
            logger.debug(f"processed mcp servers config: {self._cached_config}")
            self._process_paths(self._cached_config)
            
            return self._cached_config
            
        except Exception as e:
            logger.error(f"load mcp config failed: {e}")
            return {}
    
    def _get_config_path(self) -> Optional[str]:
        """获取配置文件路径"""
        if self._config_path:
            return self._config_path
            
        settings = get_settings()
        if hasattr(settings, 'mcp_config_path') and settings.mcp_config_path:
            config_path = settings.mcp_config_path
            
            # 如果是相对路径且文件不存在，尝试在当前目录查找
            if not os.path.isabs(config_path):
                if not os.path.exists(config_path):
                    # 尝试在当前目录下查找
                    local_path = os.path.join(os.path.dirname(__file__), "../../../../", config_path)
                    if os.path.exists(local_path):
                        return local_path
            
            return config_path
            
        # 默认使用应用根目录下的配置
        return "/app/mcp.json"
    
    def _process_paths(self, config: Dict[str, Dict[str, Any]]) -> None:
        """处理配置中的相对路径"""
        for server_config in config.values():
            # 处理命令参数中的相对路径
            if 'args' in server_config:
                processed_args = []
                for arg in server_config['args']:
                    if isinstance(arg, str) and arg.startswith('../'):
                        # 将相对路径转换为绝对路径
                        processed_args.append(os.path.join('/app', arg[3:]))
                    elif isinstance(arg, str) and not os.path.isabs(arg) and '/' in arg:
                        processed_args.append(os.path.join('/app', arg))
                    else:
                        processed_args.append(arg)
                server_config['args'] = processed_args 