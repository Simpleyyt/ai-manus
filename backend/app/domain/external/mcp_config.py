from typing import Protocol, Dict, Any, Optional, List

class MCPConfigProvider(Protocol):
    """MCP配置提供者接口"""
    
    async def get_servers_config(self) -> Dict[str, Dict[str, Any]]:
        """获取MCP服务器配置
        
        Returns:
            服务器配置字典，格式：
            {
                "server_name": {
                    "enabled": bool,
                    "transport": str,
                    "command": str,
                    "args": list,
                    ...
                }
            }
        """
        ...


class MCPConfigManager(MCPConfigProvider, Protocol):
    """MCP配置管理器接口 - 扩展了基本提供者接口，支持CRUD操作
    
    这是一个可选的扩展接口，用于未来需要配置管理功能时使用。
    当前系统只依赖MCPConfigProvider接口。
    """
    
    async def list_configurations(self) -> List[Dict[str, Any]]:
        """列出所有配置
        
        Returns:
            配置列表
        """
        ...
    
    async def get_configuration(self, config_id: str) -> Optional[Dict[str, Any]]:
        """获取指定配置
        
        Args:
            config_id: 配置ID
            
        Returns:
            配置对象，如果不存在则返回None
        """
        ...
    
    async def create_configuration(self, name: str, servers: Dict[str, Dict[str, Any]]) -> str:
        """创建新配置
        
        Args:
            name: 配置名称
            servers: 服务器配置字典
            
        Returns:
            创建的配置ID
        """
        ...
    
    async def update_configuration(self, config_id: str, servers: Dict[str, Dict[str, Any]]) -> None:
        """更新配置
        
        Args:
            config_id: 配置ID
            servers: 新的服务器配置字典
        """
        ...
    
    async def delete_configuration(self, config_id: str) -> None:
        """删除配置
        
        Args:
            config_id: 配置ID
        """
        ...
    
    async def set_active_configuration(self, config_id: str) -> None:
        """设置活动配置
        
        Args:
            config_id: 要激活的配置ID
        """
        ... 