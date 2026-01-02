"""Expose tool for generating public URLs for local services using cloudflared"""
from typing import Dict, Optional
import uuid
import asyncio
import re
import random
import string
import json
import os
from datetime import datetime
from app.domain.services.tools.base import tool, BaseTool
from app.domain.models.tool_result import ToolResult

class ExposeTool(BaseTool):
    """Expose tool class, providing public URL generation for local services using cloudflared tunnels"""

    name: str = "expose"

    def __init__(self):
        """Initialize Expose tool class"""
        super().__init__()
        # Store active port mappings with process info
        self._port_mappings: Dict[int, Dict[str, any]] = {}
        # Check cloudflared availability
        self._cloudflared_available: Optional[bool] = None

    async def _check_cloudflared(self) -> bool:
        """Check if cloudflared is installed and available

        Returns:
            True if cloudflared is available, False otherwise
        """
        if self._cloudflared_available is not None:
            return self._cloudflared_available

        try:
            process = await asyncio.create_subprocess_exec(
                'which', 'cloudflared',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            self._cloudflared_available = process.returncode == 0
        except Exception:
            self._cloudflared_available = False

        return self._cloudflared_available

    async def _detect_container_ip(self, port: int) -> str:
        """Detect the Docker container IP for a service running on the specified port

        Args:
            port: Port number where the service is running

        Returns:
            Container IP address or "127.0.0.1" if not found
        """
        try:
            # Find containers with the port listening (sandbox containers)
            process = await asyncio.create_subprocess_exec(
                'docker', 'ps', '--format', '{{.Names}}',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()

            if process.returncode != 0:
                print(f"[ExposeTool] Failed to list Docker containers")
                return "127.0.0.1"

            # Look for sandbox containers
            containers = stdout.decode('utf-8').strip().split('\n')
            sandbox_containers = [c for c in containers if c.startswith('manus-sandbox-')]

            if not sandbox_containers:
                print(f"[ExposeTool] No sandbox containers found")
                return "127.0.0.1"

            # Check each sandbox container for the port
            for container in sandbox_containers:
                # Check if this container has the port listening
                check_process = await asyncio.create_subprocess_exec(
                    'docker', 'exec', container, 'sh', '-c',
                    f'netstat -tln 2>/dev/null | grep ":{port} " || ss -tln 2>/dev/null | grep ":{port} "',
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                check_stdout, _ = await check_process.communicate()

                if check_stdout:
                    # Found the container with the port, get its IP
                    ip_process = await asyncio.create_subprocess_exec(
                        'docker', 'inspect', '-f',
                        '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}',
                        container,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    ip_stdout, _ = await ip_process.communicate()

                    if ip_process.returncode == 0:
                        container_ip = ip_stdout.decode('utf-8').strip()
                        if container_ip:
                            print(f"[ExposeTool] Detected container {container} at {container_ip}:{port}")
                            return container_ip

            print(f"[ExposeTool] Could not find container IP for port {port}, using localhost")
            return "127.0.0.1"

        except Exception as e:
            print(f"[ExposeTool] Error detecting container IP: {e}")
            return "127.0.0.1"

    async def _create_cloudflare_dns_record(self, subdomain: str, target_ip: str) -> bool:
        """Create a Cloudflare DNS A record for the subdomain

        Args:
            subdomain: Subdomain to create (e.g., "8000-abc123")
            target_ip: Target IP address (VM external IP)

        Returns:
            True if DNS record created successfully, False otherwise
        """
        try:
            import aiohttp

            # Get Cloudflare credentials from environment
            api_token = os.getenv('CLOUDFLARE_API_TOKEN')
            zone_id = os.getenv('CLOUDFLARE_ZONE_ID')
            domain = os.getenv('CLOUDFLARE_DOMAIN', 'manus.expert')

            if not api_token or not zone_id:
                print("[ExposeTool] Missing Cloudflare credentials in environment")
                return False

            # Construct full domain name
            full_domain = f"{subdomain}.{domain}"

            # Create DNS record via Cloudflare API
            url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
            headers = {
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json"
            }
            data = {
                "type": "A",
                "name": subdomain,
                "content": target_ip,
                "ttl": 60,  # 1 minute TTL for quick updates
                "proxied": False  # Direct connection, no Cloudflare proxy
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    result = await response.json()

                    if response.status == 200 and result.get('success'):
                        print(f"[ExposeTool] Created DNS record: {full_domain} -> {target_ip}")
                        return True
                    else:
                        errors = result.get('errors', [])
                        # Check if record already exists (error code 81057)
                        if any(err.get('code') == 81057 for err in errors):
                            print(f"[ExposeTool] DNS record already exists: {full_domain}")
                            return True

                        print(f"[ExposeTool] Failed to create DNS record: {result}")
                        return False

        except Exception as e:
            print(f"[ExposeTool] Error creating Cloudflare DNS record: {e}")
            return False

    async def _create_cloudflared_tunnel(self, port: int) -> Optional[Dict[str, any]]:
        """Create a cloudflared tunnel for the specified port

        Args:
            port: Port number to expose

        Returns:
            Dictionary with tunnel info (url, process) or None if failed
        """
        try:
            # Start cloudflared tunnel process
            process = await asyncio.create_subprocess_exec(
                'cloudflared', 'tunnel', '--url', f'http://localhost:{port}',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Wait for tunnel URL to be generated (max 20 seconds)
            url_pattern = re.compile(r'https://[a-z0-9-]+\.trycloudflare\.com')
            timeout = 20

            async def read_from_stream(stream, stream_name):
                """Read from a stream until URL is found"""
                try:
                    while True:
                        line = await asyncio.wait_for(
                            stream.readline(),
                            timeout=1.0
                        )
                        if not line:
                            break

                        line_str = line.decode('utf-8')
                        # Log output for debugging
                        print(f"[cloudflared {stream_name}] {line_str.strip()}")

                        match = url_pattern.search(line_str)
                        if match:
                            return match.group(0)
                except asyncio.TimeoutError:
                    pass
                return None

            async def read_output():
                """Read from both stdout and stderr until URL is found"""
                # Read from both streams concurrently
                stdout_task = asyncio.create_task(read_from_stream(process.stdout, "stdout"))
                stderr_task = asyncio.create_task(read_from_stream(process.stderr, "stderr"))

                # Wait for either stream to find the URL
                done, pending = await asyncio.wait(
                    {stdout_task, stderr_task},
                    return_when=asyncio.FIRST_COMPLETED,
                    timeout=timeout
                )

                # Cancel pending tasks
                for task in pending:
                    task.cancel()

                # Check if we got a URL from any completed task
                for task in done:
                    url = task.result()
                    if url:
                        return url

                return None

            # Try to get URL with timeout
            try:
                url = await asyncio.wait_for(read_output(), timeout=timeout)
                if url:
                    print(f"[cloudflared] Successfully extracted URL: {url}")
                    return {
                        "url": url,
                        "process": process,
                        "method": "cloudflared"
                    }
                else:
                    print("[cloudflared] Failed to extract URL from output")
            except asyncio.TimeoutError:
                print("[cloudflared] Timeout waiting for tunnel URL")

            # If we couldn't get URL, terminate process
            process.terminate()
            await process.wait()

        except Exception as e:
            print(f"[cloudflared] Exception creating tunnel: {e}")

        return None

    @tool(
        name="expose_port",
        description=(
            "Generate a public URL for a service running on a specified port using cloudflared tunnels. "
            "The service must bind to 0.0.0.0 (not localhost) to be accessible. "
            "Returns a real public HTTPS URL (e.g., https://xyz.trycloudflare.com) if cloudflared is available, "
            "otherwise returns a mock URL for testing purposes."
        ),
        parameters={
            "port": {
                "type": "integer",
                "description": "Port number where the service is running (1024-65535)"
            },
            "description": {
                "type": "string",
                "description": "Optional description of the service being exposed"
            }
        },
        required=["port"]
    )
    async def expose_port(
        self,
        port: int,
        description: Optional[str] = None
    ) -> ToolResult:
        """Generate public URL for service running on specified port using cloudflared

        Args:
            port: Port number where the service is running (1024-65535)
            description: Optional description of the service

        Returns:
            ToolResult containing the public URL or error message
        """
        # Validate port number
        if not isinstance(port, int) or port < 1024 or port > 65535:
            return ToolResult(
                success=False,
                message="Port must be an integer between 1024 and 65535",
                data=None
            )

        # Check if port is already exposed
        if port in self._port_mappings:
            existing_mapping = self._port_mappings[port]
            return ToolResult(
                success=True,
                message=f"Port {port} is already exposed",
                data={
                    "url": existing_mapping["url"],
                    "port": port,
                    "method": existing_mapping.get("method", "mock"),
                    "description": existing_mapping.get("description"),
                    "status": "existing"
                }
            )

        # Try to use cloudflared if available
        cloudflared_available = await self._check_cloudflared()
        tunnel_info = None

        if cloudflared_available:
            tunnel_info = await self._create_cloudflared_tunnel(port)

        if tunnel_info:
            # Cloudflared tunnel created successfully
            public_url = tunnel_info["url"]
            method = "cloudflared"

            # Store the mapping with process info
            self._port_mappings[port] = {
                "url": public_url,
                "process": tunnel_info["process"],
                "method": method,
                "description": description or f"Service on port {port}",
                "port": str(port)
            }

            msg_parts = [
                f"✅ Successfully exposed port {port} using cloudflared",
                f"🌐 Public URL: {public_url}",
            ]

            if description:
                msg_parts.insert(1, f"📝 Service: {description}")

            msg_parts.extend([
                "",
                "⚠️  Important:",
                "  • Ensure your application binds to 0.0.0.0 (not localhost)",
                "  • The tunnel will remain active until explicitly stopped",
                "  • URL is temporary and will change if tunnel is restarted"
            ])

            return ToolResult(
                success=True,
                message="\n".join(msg_parts),
                data={
                    "url": public_url,
                    "port": port,
                    "method": method,
                    "description": description or f"Service on port {port}",
                    "status": "created",
                    "real_tunnel": True
                }
            )
        else:
            # Fallback to manus.expert reverse proxy URL (clean URL like real Manus)
            # Generate port-id pattern to match nginx config: {port}-{randomid}.manus.expert
            unique_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
            subdomain = f"{port}-{unique_id}"
            public_url = f"http://{subdomain}.manus.expert"
            method = "reverse_proxy"

            # Get VM external IP for DNS record
            vm_external_ip = os.getenv('VM_EXTERNAL_IP', '34.59.167.52')

            # Create Cloudflare DNS record for this subdomain
            dns_created = await self._create_cloudflare_dns_record(subdomain, vm_external_ip)

            # Detect container IP for the port
            container_ip = await self._detect_container_ip(port)

            # Store mapping in shared file for Nginx lookup
            mapping_file = "/tmp/manus_port_mappings.json"
            try:
                # Load existing mappings
                if os.path.exists(mapping_file):
                    with open(mapping_file, 'r') as f:
                        all_mappings = json.load(f)
                else:
                    all_mappings = {}

                # Add new mapping with container IP
                all_mappings[unique_id] = {
                    "port": port,
                    "created": datetime.now().isoformat(),
                    "description": description or f"Service on port {port}",
                    "container_ip": container_ip
                }

                # Save updated mappings
                with open(mapping_file, 'w') as f:
                    json.dump(all_mappings, f, indent=2)

                print(f"[ExposeTool] Saved mapping: {unique_id} -> {container_ip}:{port}")
            except Exception as e:
                print(f"[ExposeTool] Warning: Failed to save mapping file: {e}")

            # Store the mapping in memory
            self._port_mappings[port] = {
                "url": public_url,
                "unique_id": unique_id,
                "method": method,
                "description": description or f"Service on port {port}",
                "port": str(port)
            }

            warning = "⚠️  Cloudflared not available - using manus.expert reverse proxy"
            if not cloudflared_available:
                warning += "\n   Install cloudflared for reliable tunnels: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/"

            msg_parts = [
                f"✅ Exposed port {port} via manus.expert",
                f"🔗 Public URL: {public_url}",
                "",
            ]

            # Add DNS status
            if dns_created:
                msg_parts.append("✅ DNS record created successfully - URL is publicly accessible")
            else:
                msg_parts.append("⚠️  DNS record creation skipped - URL only works via /etc/hosts")

            msg_parts.extend([
                "",
                warning,
                "",
                "⚠️  Important:",
                "  • Ensure your application binds to 0.0.0.0 (not localhost)",
                "  • URL format: {port}-{random-12-char}.manus.expert",
                "  • Port routing handled by Nginx regex extraction"
            ])

            if description:
                msg_parts.insert(1, f"📝 Service: {description}")

            return ToolResult(
                success=True,
                message="\n".join(msg_parts),
                data={
                    "url": public_url,
                    "port": port,
                    "unique_id": unique_id,
                    "method": method,
                    "description": description or f"Service on port {port}",
                    "status": "created",
                    "real_tunnel": False
                }
            )

    @tool(
        name="list_exposed_ports",
        description="List all currently exposed ports and their public URLs",
        parameters={},
        required=[]
    )
    async def list_exposed_ports(self) -> ToolResult:
        """List all exposed ports and their public URLs

        Returns:
            ToolResult containing list of exposed ports
        """
        if not self._port_mappings:
            return ToolResult(
                success=True,
                message="No ports are currently exposed",
                data={"exposed_ports": []}
            )

        exposed_list = [
            {
                "port": int(mapping["port"]) if isinstance(mapping["port"], str) else mapping["port"],
                "url": mapping["url"],
                "description": mapping["description"],
                "unique_id": mapping["unique_id"]
            }
            for mapping in self._port_mappings.values()
        ]

        message_lines = ["Currently exposed ports:"]
        for item in exposed_list:
            message_lines.append(
                f"  - Port {item['port']}: {item['url']}"
            )
            if item['description']:
                message_lines.append(f"    Description: {item['description']}")

        return ToolResult(
            success=True,
            message="\n".join(message_lines),
            data={"exposed_ports": exposed_list}
        )

    @tool(
        name="unexpose_port",
        description="Remove public URL exposure for a specified port and stop any running cloudflared tunnel",
        parameters={
            "port": {
                "type": "integer",
                "description": "Port number to stop exposing"
            }
        },
        required=["port"]
    )
    async def unexpose_port(self, port: int) -> ToolResult:
        """Remove public URL exposure for specified port

        Args:
            port: Port number to stop exposing

        Returns:
            ToolResult indicating success or failure
        """
        if port not in self._port_mappings:
            return ToolResult(
                success=False,
                message=f"Port {port} is not currently exposed",
                data=None
            )

        mapping = self._port_mappings.pop(port)

        # Terminate cloudflared process if it exists
        if "process" in mapping:
            try:
                process = mapping["process"]
                process.terminate()
                await asyncio.wait_for(process.wait(), timeout=5.0)
                tunnel_stopped = "✅ Cloudflared tunnel stopped"
            except asyncio.TimeoutError:
                process.kill()
                tunnel_stopped = "⚠️  Cloudflared tunnel forcefully killed"
            except Exception:
                tunnel_stopped = "⚠️  Failed to stop cloudflared tunnel (may still be running)"
        else:
            tunnel_stopped = None

        msg_parts = [f"✅ Removed exposure for port {port}"]

        if tunnel_stopped:
            msg_parts.append(tunnel_stopped)

        msg_parts.append(f"🔗 URL no longer accessible: {mapping['url']}")

        return ToolResult(
            success=True,
            message="\n".join(msg_parts),
            data={
                "port": port,
                "url": mapping["url"],
                "method": mapping.get("method", "mock"),
                "status": "removed"
            }
        )
