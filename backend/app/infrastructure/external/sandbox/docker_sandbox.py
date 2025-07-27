from typing import Dict, Any, Optional, List, BinaryIO
import uuid
import httpx
import docker
import socket
import logging
import asyncio
import io
from async_lru import alru_cache
from app.core.config import get_settings
from app.domain.models.tool_result import ToolResult
from app.domain.external.sandbox import Sandbox
from app.infrastructure.external.browser.playwright_browser import PlaywrightBrowser
from app.domain.external.browser import Browser
from app.domain.external.llm import LLM

logger = logging.getLogger(__name__)

class DockerSandbox(Sandbox):
    def __init__(self, ip: str = None, container_name: str = None):
        """Initialize Docker sandbox and API interaction client"""
        self.client = httpx.AsyncClient(timeout=600)
        self.ip = ip
        self.base_url = f"http://{self.ip}:8080"
        self._vnc_url = f"ws://{self.ip}:5901"
        self._cdp_url = f"http://{self.ip}:9222"
        self._container_name = container_name
    
    @property
    def id(self) -> str:
        """Sandbox ID"""
        if not self._container_name:
            return "dev-sandbox"
        return self._container_name
    
    
    @property
    def cdp_url(self) -> str:
        return self._cdp_url

    @property
    def vnc_url(self) -> str:
        return self._vnc_url

    @staticmethod
    def _get_container_ip(container) -> str:
        """Get container IP address from network settings
        
        Args:
            container: Docker container instance
            
        Returns:
            Container IP address
        """
        # Get container network settings
        network_settings = container.attrs['NetworkSettings']
        ip_address = network_settings['IPAddress']
        
        # If default network has no IP, try to get IP from other networks
        if not ip_address and 'Networks' in network_settings:
            networks = network_settings['Networks']
            # Try to get IP from first available network
            for network_name, network_config in networks.items():
                if 'IPAddress' in network_config and network_config['IPAddress']:
                    ip_address = network_config['IPAddress']
                    break
        
        return ip_address

    @staticmethod
    def _create_task() -> 'DockerSandbox':
        """Create a new Docker sandbox (static method)
        
        Args:
            image: Docker image name
            name_prefix: Container name prefix
            
        Returns:
            DockerSandbox instance
        """
        # Use configured default values
        settings = get_settings()

        image = settings.sandbox_image
        name_prefix = settings.sandbox_name_prefix
        container_name = f"{name_prefix}-{str(uuid.uuid4())[:8]}"
        
        try:
            # Create Docker client
            docker_client = docker.from_env()

            # Prepare container configuration
            container_config = {
                "image": image,
                "name": container_name,
                "detach": True,
                "remove": True,
                "environment": {
                    "SERVICE_TIMEOUT_MINUTES": settings.sandbox_ttl_minutes,
                    "CHROME_ARGS": settings.sandbox_chrome_args,
                    "HTTPS_PROXY": settings.sandbox_https_proxy,
                    "HTTP_PROXY": settings.sandbox_http_proxy,
                    "NO_PROXY": settings.sandbox_no_proxy
                }
            }
            
            # Add network to container config if configured
            if settings.sandbox_network:
                container_config["network"] = settings.sandbox_network
            
            # Create container
            container = docker_client.containers.run(**container_config)
            
            # Get container IP address
            container.reload()  # Refresh container info
            ip_address = DockerSandbox._get_container_ip(container)
            
            # Create and return DockerSandbox instance
            return DockerSandbox(
                ip=ip_address,
                container_name=container_name
            )
            
        except Exception as e:
            raise Exception(f"Failed to create Docker sandbox: {str(e)}")

    async def ensure_sandbox(self) -> None:
        """Ensure sandbox is ready by checking that all services are RUNNING"""
        max_retries = 30  # Maximum number of retries
        retry_interval = 2  # Seconds between retries
        
        for attempt in range(max_retries):
            try:
                response = await self.client.get(f"{self.base_url}/api/v1/supervisor/status")
                response.raise_for_status()
                
                # Parse response as ToolResult
                tool_result = ToolResult(**response.json())
                
                if not tool_result.success:
                    logger.warning(f"Supervisor status check failed: {tool_result.message}")
                    await asyncio.sleep(retry_interval)
                    continue
                
                services = tool_result.data or []
                if not services:
                    logger.warning("No services found in supervisor status")
                    await asyncio.sleep(retry_interval)
                    continue
                
                # Check if all services are RUNNING
                all_running = True
                non_running_services = []
                
                for service in services:
                    service_name = service.get("name", "unknown")
                    state_name = service.get("statename", "")
                    
                    if state_name != "RUNNING":
                        all_running = False
                        non_running_services.append(f"{service_name}({state_name})")
                
                if all_running:
                    logger.info(f"All {len(services)} services are RUNNING - sandbox is ready")
                    return  # Success - all services are running
                else:
                    logger.info(f"Waiting for services to start... Non-running: {', '.join(non_running_services)} (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(retry_interval)
                    
            except Exception as e:
                logger.warning(f"Failed to check supervisor status (attempt {attempt + 1}/{max_retries}): {str(e)}")
                await asyncio.sleep(retry_interval)
        
        # If we reach here, we've exhausted all retries
        error_message = f"Sandbox services failed to start after {max_retries} attempts ({max_retries * retry_interval} seconds)"
        logger.error(error_message)
        # TODO: find a way to handle this
        #raise Exception(error_message)

    async def exec_command(self, session_id: str, exec_dir: str, command: str) -> ToolResult:
        response = await self.client.post(
            f"{self.base_url}/api/v1/shell/exec",
            json={
                "id": session_id,
                "exec_dir": exec_dir,
                "command": command
            }
        )
        return ToolResult(**response.json())

    async def view_shell(self, session_id: str, console: bool = False) -> ToolResult:
        response = await self.client.post(
            f"{self.base_url}/api/v1/shell/view",
            json={
                "id": session_id,
                "console": console
            }
        )
        return ToolResult(**response.json())

    async def wait_for_process(self, session_id: str, seconds: Optional[int] = None) -> ToolResult:
        response = await self.client.post(
            f"{self.base_url}/api/v1/shell/wait",
            json={
                "id": session_id,
                "seconds": seconds
            }
        )
        return ToolResult(**response.json())

    async def write_to_process(self, session_id: str, input_text: str, press_enter: bool = True) -> ToolResult:
        response = await self.client.post(
            f"{self.base_url}/api/v1/shell/write",
            json={
                "id": session_id,
                "input": input_text,
                "press_enter": press_enter
            }
        )
        return ToolResult(**response.json())

    async def kill_process(self, session_id: str) -> ToolResult:
        response = await self.client.post(
            f"{self.base_url}/api/v1/shell/kill",
            json={"id": session_id}
        )
        return ToolResult(**response.json())

    async def file_write(self, file: str, content: str, append: bool = False, 
                        leading_newline: bool = False, trailing_newline: bool = False, 
                        sudo: bool = False) -> ToolResult:
        """Write content to file
        
        Args:
            file: File path
            content: Content to write
            append: Whether to append content
            leading_newline: Whether to add newline before content
            trailing_newline: Whether to add newline after content
            sudo: Whether to use sudo privileges
            
        Returns:
            Result of write operation
        """
        response = await self.client.post(
            f"{self.base_url}/api/v1/file/write",
            json={
                "file": file,
                "content": content,
                "append": append,
                "leading_newline": leading_newline,
                "trailing_newline": trailing_newline,
                "sudo": sudo
            }
        )
        return ToolResult(**response.json())

    async def file_read(self, file: str, start_line: int = None, 
                        end_line: int = None, sudo: bool = False) -> ToolResult:
        """Read file content
        
        Args:
            file: File path
            start_line: Start line number
            end_line: End line number
            sudo: Whether to use sudo privileges
            
        Returns:
            File content
        """
        response = await self.client.post(
            f"{self.base_url}/api/v1/file/read",
            json={
                "file": file,
                "start_line": start_line,
                "end_line": end_line,
                "sudo": sudo
            }
        )
        return ToolResult(**response.json())
        
    async def file_exists(self, path: str) -> ToolResult:
        """Check if file exists
        
        Args:
            path: File path
            
        Returns:
            Whether file exists
        """
        response = await self.client.post(
            f"{self.base_url}/api/v1/file/exists",
            json={"path": path}
        )
        return ToolResult(**response.json())
        
    async def file_delete(self, path: str) -> ToolResult:
        """Delete file
        
        Args:
            path: File path
            
        Returns:
            Result of delete operation
        """
        response = await self.client.post(
            f"{self.base_url}/api/v1/file/delete",
            json={"path": path}
        )
        return ToolResult(**response.json())
        
    async def file_list(self, path: str) -> ToolResult:
        """List directory contents
        
        Args:
            path: Directory path
            
        Returns:
            List of directory contents
        """
        response = await self.client.post(
            f"{self.base_url}/api/v1/file/list",
            json={"path": path}
        )
        return ToolResult(**response.json())

    async def file_replace(self, file: str, old_str: str, new_str: str, sudo: bool = False) -> ToolResult:
        """Replace string in file
        
        Args:
            file: File path
            old_str: String to replace
            new_str: String to replace with
            sudo: Whether to use sudo privileges
            
        Returns:
            Result of replace operation
        """
        response = await self.client.post(
            f"{self.base_url}/api/v1/file/replace",
            json={
                "file": file,
                "old_str": old_str,
                "new_str": new_str,
                "sudo": sudo
            }
        )
        return ToolResult(**response.json())

    async def file_search(self, file: str, regex: str, sudo: bool = False) -> ToolResult:
        """Search in file content
        
        Args:
            file: File path
            regex: Regular expression
            sudo: Whether to use sudo privileges
            
        Returns:
            Search results
        """
        response = await self.client.post(
            f"{self.base_url}/api/v1/file/search",
            json={
                "file": file,
                "regex": regex,
                "sudo": sudo
            }
        )
        return ToolResult(**response.json())

    async def file_find(self, path: str, glob_pattern: str) -> ToolResult:
        """Find files by name pattern
        
        Args:
            path: Search directory path
            glob_pattern: Glob match pattern
            
        Returns:
            List of found files
        """
        response = await self.client.post(
            f"{self.base_url}/api/v1/file/find",
            json={
                "path": path,
                "glob": glob_pattern
            }
        )
        return ToolResult(**response.json())

    async def file_upload(self, file_data: BinaryIO, path: str, filename: str = None) -> ToolResult:
        """Upload file to sandbox
        
        Args:
            file_data: File content as binary stream
            path: Target file path in sandbox
            filename: Original filename (optional)
            
        Returns:
            Upload operation result
        """
        # Prepare form data for upload
        files = {"file": (filename or "upload", file_data, "application/octet-stream")}
        data = {"path": path}
        
        response = await self.client.post(
            f"{self.base_url}/api/v1/file/upload",
            files=files,
            data=data
        )
        return ToolResult(**response.json())

    async def file_download(self, path: str) -> BinaryIO:
        """Download file from sandbox
        
        Args:
            path: File path in sandbox
            
        Returns:
            File content as binary stream
        """
        response = await self.client.get(
            f"{self.base_url}/api/v1/file/download",
            params={"path": path}
        )
        response.raise_for_status()
        
        # Return the response content as a BinaryIO stream
        # TODO: change to real stream
        return io.BytesIO(response.content)
    
    @staticmethod
    @alru_cache(maxsize=128, typed=True)
    async def _resolve_hostname_to_ip(hostname: str) -> str:
        """Resolve hostname to IP address
        
        Args:
            hostname: Hostname to resolve
            
        Returns:
            Resolved IP address, or None if resolution fails
            
        Note:
            This method is cached using LRU cache with a maximum size of 128 entries.
            The cache helps reduce repeated DNS lookups for the same hostname.
        """
        try:
            # First check if hostname is already in IP address format
            try:
                socket.inet_pton(socket.AF_INET, hostname)
                # If successfully parsed, it's an IPv4 address format, return directly
                return hostname
            except OSError:
                # Not a valid IP address format, proceed with DNS resolution
                pass
                
            # Use socket.getaddrinfo for DNS resolution
            addr_info = socket.getaddrinfo(hostname, None, family=socket.AF_INET)
            # Return the first IPv4 address found
            if addr_info and len(addr_info) > 0:
                return addr_info[0][4][0]  # Return sockaddr[0] from (family, type, proto, canonname, sockaddr), which is the IP address
            return None
        except Exception as e:
            # Log error and return None on failure
            logger.error(f"Failed to resolve hostname {hostname}: {str(e)}")
            return None
    
    async def destroy(self) -> bool:
        """Destroy Docker sandbox"""
        try:
            if self.client:
                await self.client.aclose()
            if self.container_name:
                docker_client = docker.from_env()
                docker_client.containers.get(self.container_name).remove(force=True)
            return True
        except Exception as e:
            logger.error(f"Failed to destroy Docker sandbox: {str(e)}")
            return False
    
    async def get_browser(self) -> Browser:
        """Get browser instance
        
        Args:
            llm: LLM instance used for browser automation
            
        Returns:
            Browser: Returns a configured PlaywrightBrowser instance
                    connected using the sandbox's CDP URL
        """
        return PlaywrightBrowser(self.cdp_url)

    @staticmethod
    @alru_cache(maxsize=128, typed=True)
    async def _resolve_hostname_to_ip(hostname: str) -> str:
        """Resolve hostname to IP address
        
        Args:
            hostname: Hostname to resolve
            
        Returns:
            Resolved IP address, or None if resolution fails
            
        Note:
            This method is cached using LRU cache with a maximum size of 128 entries.
            The cache helps reduce repeated DNS lookups for the same hostname.
        """
        try:
            # First check if hostname is already in IP address format
            try:
                socket.inet_pton(socket.AF_INET, hostname)
                # If successfully parsed, it's an IPv4 address format, return directly
                return hostname
            except OSError:
                # Not a valid IP address format, proceed with DNS resolution
                pass
                
            # Use socket.getaddrinfo for DNS resolution
            addr_info = socket.getaddrinfo(hostname, None, family=socket.AF_INET)
            # Return the first IPv4 address found
            if addr_info and len(addr_info) > 0:
                return addr_info[0][4][0]  # Return sockaddr[0] from (family, type, proto, canonname, sockaddr), which is the IP address
            return None
        except Exception as e:
            # Log error and return None on failure
            logger.error(f"Failed to resolve hostname {hostname}: {str(e)}")
            return None

    @classmethod
    async def create(cls) -> Sandbox:
        """Create a new sandbox instance
        
        Returns:
            New sandbox instance
        """
        settings = get_settings()

        if settings.sandbox_address:
            # Chrome CDP needs IP address
            ip = await cls._resolve_hostname_to_ip(settings.sandbox_address)
            return DockerSandbox(ip=ip)
    
        return await asyncio.to_thread(DockerSandbox._create_task)
    
    @classmethod
    @alru_cache(maxsize=128, typed=True)
    async def get(cls, id: str) -> Sandbox:
        """Get sandbox by ID
        
        Args:
            id: Sandbox ID
            
        Returns:
            Sandbox instance
        """
        settings = get_settings()
        if settings.sandbox_address:
            ip = await cls._resolve_hostname_to_ip(settings.sandbox_address)
            return DockerSandbox(ip=ip, container_name=id)

        docker_client = docker.from_env()
        container = docker_client.containers.get(id)
        container.reload()
        
        ip_address = cls._get_container_ip(container)
        logger.info(f"IP address: {ip_address}")
        return DockerSandbox(ip=ip_address, container_name=id)
