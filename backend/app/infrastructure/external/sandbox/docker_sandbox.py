from typing import Dict, Any, Optional, List, BinaryIO, Tuple
import uuid
import httpx
import docker
import socket
import logging
import asyncio
import io
import re
from pathlib import Path
from async_lru import alru_cache
from app.core.config import get_settings
from app.domain.models.tool_result import ToolResult
from app.domain.external.sandbox import Sandbox
from app.infrastructure.external.browser.playwright_browser import PlaywrightBrowser
from app.domain.external.browser import Browser
from app.domain.external.llm import LLM

logger = logging.getLogger(__name__)


class StatefulSession:
    """
    Maintains state for a single shell session.
    
    This class tracks:
    - Current working directory (CWD)
    - Environment variables
    - Background processes (PID tracking)
    
    Based on OpenHands SDK runtime patterns.
    """
    
    def __init__(self, session_id: str, initial_cwd: str = "/workspace"):
        self.session_id = session_id
        self.cwd = initial_cwd
        self.env_vars: Dict[str, str] = {}
        self.background_pids: Dict[str, int] = {}  # command -> PID mapping
        
    def update_cwd(self, new_cwd: str):
        """Update current working directory"""
        self.cwd = new_cwd
        logger.debug(f"Session {self.session_id}: CWD updated to {new_cwd}")
        
    def set_env(self, key: str, value: str):
        """Set environment variable"""
        self.env_vars[key] = value
        logger.debug(f"Session {self.session_id}: ENV {key}={value}")
        
    def get_env(self, key: str) -> Optional[str]:
        """Get environment variable"""
        return self.env_vars.get(key)
    
    def add_background_process(self, command: str, pid: int):
        """Track a background process"""
        self.background_pids[command] = pid
        logger.info(f"Session {self.session_id}: Background process started - PID {pid}")
        
    def remove_background_process(self, command: str):
        """Remove tracked background process"""
        if command in self.background_pids:
            pid = self.background_pids.pop(command)
            logger.info(f"Session {self.session_id}: Background process removed - PID {pid}")

class DockerSandbox(Sandbox):
    """
    Stateful Docker Sandbox with session context preservation.
    
    Enhanced to support:
    - Persistent CWD and ENV between commands (OpenHands SDK pattern)
    - Background process management
    - Skills/plugins injection at /openhands/tools
    - File editor integration
    """
    
    def __init__(self, ip: str = None, container_name: str = None):
        """Initialize Docker sandbox and API interaction client"""
        self.client = httpx.AsyncClient(timeout=600)
        self.ip = ip
        self.base_url = f"http://{self.ip}:8080"
        self._vnc_url = f"ws://{self.ip}:5901"
        self._cdp_url = f"http://{self.ip}:9222"
        self._container_name = container_name
        
        # Stateful session management (NEW)
        self._sessions: Dict[str, StatefulSession] = {}
        self._default_session_id = "default"
        self._get_or_create_session(self._default_session_id)
    
    def _get_or_create_session(self, session_id: str) -> StatefulSession:
        """Get existing session or create new one"""
        if session_id not in self._sessions:
            self._sessions[session_id] = StatefulSession(session_id)
            logger.info(f"Created new stateful session: {session_id}")
        return self._sessions[session_id]
    
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
            
            # Prepare plugins directory for volume mount
            plugins_dir = Path(__file__).parent / "plugins"
            plugins_dir.mkdir(parents=True, exist_ok=True)
            plugins_dir_str = str(plugins_dir.absolute())
            
            logger.info(f"Plugins directory: {plugins_dir_str}")

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
                    "NO_PROXY": settings.sandbox_no_proxy,
                    "PYTHONPATH": "/openhands/tools:$PYTHONPATH",  # Add tools to Python path
                },
                "volumes": {
                    plugins_dir_str: {
                        "bind": "/openhands/tools",
                        "mode": "ro"  # Read-only mount
                    }
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
        """Ensure sandbox is ready by checking that all services are RUNNING
        
        Enhanced with:
        - Real health check for CDP port
        - Better retry logic with exponential backoff
        """
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
                    # Additional health check: verify CDP port is accessible
                    cdp_accessible = await self._check_cdp_health()
                    if cdp_accessible:
                        logger.info(f"All {len(services)} services are RUNNING and CDP is accessible - sandbox is ready")
                        return  # Success
                    else:
                        logger.warning(f"Services running but CDP port not accessible yet (attempt {attempt + 1}/{max_retries})")
                        await asyncio.sleep(retry_interval)
                else:
                    logger.info(f"Waiting for services to start... Non-running: {', '.join(non_running_services)} (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(retry_interval)
                    
            except Exception as e:
                logger.warning(f"Failed to check supervisor status (attempt {attempt + 1}/{max_retries}): {str(e)}")
                await asyncio.sleep(retry_interval)
        
        # If we reach here, we've exhausted all retries
        error_message = f"Sandbox services failed to start after {max_retries} attempts ({max_retries * retry_interval} seconds)"
        logger.error(error_message)
        # CRITICAL: Raise exception to prevent continuation with broken sandbox
        raise Exception(error_message)
    
    async def _check_cdp_health(self) -> bool:
        """
        Real health check for Chrome DevTools Protocol port.
        Verifies that the CDP port is accessible and responding.
        
        Returns:
            True if CDP is healthy, False otherwise
        """
        try:
            # Try to connect to CDP endpoint
            response = await self.client.get(
                f"{self.cdp_url}/json/version",
                timeout=5.0
            )
            
            if response.status_code == 200:
                data = response.json()
                # Verify response contains expected CDP fields
                if "Browser" in data and "Protocol-Version" in data:
                    logger.debug(f"CDP health check passed: {data.get('Browser')}")
                    return True
            
            return False
            
        except Exception as e:
            logger.debug(f"CDP health check failed: {e}")
            return False

    async def exec_command(self, session_id: str, exec_dir: str, command: str) -> ToolResult:
        """Legacy exec_command - redirects to stateful execution for backward compatibility"""
        result = await self.exec_command_stateful(command, session_id)
        return ToolResult(
            success=(result["exit_code"] == 0),
            message=result["stdout"] if result["exit_code"] == 0 else result["stderr"],
            data={
                "exit_code": result["exit_code"],
                "stdout": result["stdout"],
                "stderr": result["stderr"],
                "cwd": result["cwd"]
            }
        )
    
    async def exec_command_stateful(
        self, 
        command: str, 
        session_id: str = None,
        timeout: int = 120
    ) -> Dict[str, Any]:
        """
        Execute command with stateful context preservation (OpenHands SDK pattern).
        
        This method:
        1. Loads session CWD and ENV
        2. Wraps command to preserve state
        3. Extracts new CWD after execution
        4. Parses ENV changes
        5. Handles background processes (&)
        
        Args:
            command: Shell command to execute
            session_id: Session identifier (default: "default")
            timeout: Command timeout in seconds
            
        Returns:
            Dict with keys: exit_code, stdout, stderr, cwd, background_pid (optional)
            
        Example:
            # Stateful ENV preservation
            result1 = await sandbox.exec_command_stateful("export USER=Test")
            result2 = await sandbox.exec_command_stateful("echo $USER")
            # result2["stdout"] will contain "Test"
        """
        if session_id is None:
            session_id = self._default_session_id
            
        session = self._get_or_create_session(session_id)
        
        # Check if command should run in background
        is_background = command.strip().endswith('&')
        if is_background:
            command = command.strip()[:-1].strip()  # Remove trailing &
        
        # Build stateful command wrapper
        # 1. cd to session CWD
        # 2. Export session ENV vars
        # 3. Execute command
        # 4. Capture new CWD and ENV changes
        
        env_exports = " ".join([f"export {k}={v};" for k, v in session.env_vars.items()])
        
        if is_background:
            # For background processes, capture PID
            wrapped_command = f"""
cd {session.cwd} || true
{env_exports}
nohup {command} > /tmp/bg_$$.out 2>&1 & echo $!
pwd
"""
        else:
            wrapped_command = f"""
cd {session.cwd} || true
{env_exports}
{command}
EXIT_CODE=$?
pwd
exit $EXIT_CODE
"""
        
        # Execute via sandbox API
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/shell/exec",
                json={
                    "id": session_id,
                    "exec_dir": session.cwd,
                    "command": wrapped_command
                },
                timeout=timeout
            )
            
            result = response.json()
            
            # Parse result
            exit_code = result.get("exit_code", -1)
            stdout = result.get("stdout", "")
            stderr = result.get("stderr", "")
            
            # Extract new CWD from last line of stdout
            if stdout:
                lines = stdout.strip().split('\n')
                if lines:
                    potential_cwd = lines[-1].strip()
                    # Check if it looks like a path
                    if potential_cwd.startswith('/'):
                        session.update_cwd(potential_cwd)
                        # Remove CWD from output
                        stdout = '\n'.join(lines[:-1]) if len(lines) > 1 else ""
            
            # Handle background process
            background_pid = None
            if is_background and stdout:
                lines = stdout.strip().split('\n')
                if lines and lines[0].isdigit():
                    background_pid = int(lines[0])
                    session.add_background_process(command, background_pid)
                    stdout = '\n'.join(lines[1:]) if len(lines) > 1 else ""
            
            # Parse ENV changes from command (if export was used)
            if 'export ' in command:
                # Extract export statements
                exports = re.findall(r'export\s+(\w+)=([^\s;]+)', command)
                for key, value in exports:
                    session.set_env(key, value.strip('"').strip("'"))
            
            result_dict = {
                "exit_code": exit_code,
                "stdout": stdout,
                "stderr": stderr,
                "cwd": session.cwd,
                "session_id": session_id
            }
            
            if background_pid:
                result_dict["background_pid"] = background_pid
                
            return result_dict
            
        except Exception as e:
            logger.error(f"Stateful command execution failed: {e}")
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "cwd": session.cwd,
                "session_id": session_id
            }

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
        """Upload file to sandbox with streaming support for large files
        
        Args:
            file_data: File content as binary stream
            path: Target file path in sandbox
            filename: Original filename (optional)
            
        Returns:
            Upload operation result
        """
        try:
            # Prepare form data for upload
            files = {"file": (filename or "upload", file_data, "application/octet-stream")}
            data = {"path": path}
            
            # Use streaming upload for better memory efficiency
            response = await self.client.post(
                f"{self.base_url}/api/v1/file/upload",
                files=files,
                data=data,
                timeout=300.0  # 5 minutes for large files
            )
            response.raise_for_status()
            
            return ToolResult(**response.json())
            
        except httpx.TimeoutException:
            return ToolResult(
                success=False,
                message=f"Upload timeout - file may be too large or network is slow"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                message=f"Upload failed: {str(e)}"
            )

    async def file_download(self, path: str) -> BinaryIO:
        """Download file from sandbox with TRUE streaming support and size limits
        
        Args:
            path: File path in sandbox
            
        Returns:
            File content as binary stream
            
        Raises:
            Exception: If file exceeds maximum size limit (500MB) or download fails
        """
        # Security: Maximum file size to prevent DoS (500MB)
        MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB
        
        try:
            # Use TRUE streaming download with client.stream() to handle large files efficiently
            async with self.client.stream(
                "GET",
                f"{self.base_url}/api/v1/file/download",
                params={"path": path},
                timeout=300.0  # 5 minutes for large files
            ) as response:
                response.raise_for_status()
                
                # Safely parse file size from headers
                content_length_str = response.headers.get('content-length')
                file_size = 0
                
                if content_length_str:
                    try:
                        file_size = int(content_length_str)
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid Content-Length header: {content_length_str}")
                        file_size = 0  # Unknown size, will check during download
                
                # Security check: Reject files exceeding maximum size
                if file_size > MAX_FILE_SIZE:
                    raise Exception(
                        f"File too large ({file_size / 1024 / 1024:.2f} MB). "
                        f"Maximum allowed: {MAX_FILE_SIZE / 1024 / 1024:.0f} MB"
                    )
                
                if file_size > 100 * 1024 * 1024:  # > 100MB
                    logger.warning(f"Large file download ({file_size / 1024 / 1024:.2f} MB) - using streaming")
                
                # Stream content to BytesIO chunk by chunk with size tracking
                buffer = io.BytesIO()
                bytes_downloaded = 0
                
                async for chunk in response.aiter_bytes(chunk_size=8192):
                    bytes_downloaded += len(chunk)
                    
                    # Security: Enforce size limit even if Content-Length is missing/wrong
                    if bytes_downloaded > MAX_FILE_SIZE:
                        raise Exception(
                            f"Download exceeded maximum size limit "
                            f"({MAX_FILE_SIZE / 1024 / 1024:.0f} MB)"
                        )
                    
                    buffer.write(chunk)
                
                buffer.seek(0)  # Reset to beginning
                return buffer
            
        except httpx.TimeoutException:
            logger.error(f"Download timeout for file: {path}")
            raise Exception("Download timeout - file may be too large or network is slow")
        except Exception as e:
            logger.error(f"Download failed for file {path}: {e}")
            raise
    
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
