"""
Supervisor Service Implementation
"""
import threading
import xmlrpc.client
import socket
import http.client
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional

from app.core.config import settings
from app.core.exceptions import BadRequestException, ResourceNotFoundException
from app.models.supervisor import (
    ProcessInfo,
    SupervisorActionResult,
    SupervisorTimeout
)

SUPERVISOR_SOCKET_PATH = "/tmp/supervisor.sock"


class UnixStreamHTTPConnection(http.client.HTTPConnection):
    """HTTP connection over a Unix socket, for the supervisord XML-RPC API"""

    def __init__(self, host, socket_path, timeout=None):
        http.client.HTTPConnection.__init__(self, host, timeout=timeout)
        self.socket_path = socket_path

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(self.socket_path)


class UnixStreamTransport(xmlrpc.client.Transport):
    """xmlrpc transport that connects through a Unix socket"""

    def __init__(self, socket_path):
        xmlrpc.client.Transport.__init__(self)
        self.socket_path = socket_path

    def make_connection(self, host):
        return UnixStreamHTTPConnection(host, self.socket_path)


class SupervisorService:
    """
    Manages supervisord processes and the service auto-shutdown timeout.
    """

    def __init__(self):
        # ServerProxy connects lazily, on the first RPC call
        self.server = xmlrpc.client.ServerProxy(
            'http://localhost',
            transport=UnixStreamTransport(SUPERVISOR_SOCKET_PATH)
        )

        # Timeout management - enabled based on configuration
        self.timeout_active = settings.SERVICE_TIMEOUT_MINUTES is not None
        self.shutdown_task: Optional[asyncio.Task] = None
        self.shutdown_timer: Optional[threading.Timer] = None
        self.shutdown_time: Optional[datetime] = None
        # Auto-extend functionality - disabled when user explicitly controls timeout
        self._auto_extend_enabled = True

        if settings.SERVICE_TIMEOUT_MINUTES is not None:
            self.shutdown_time = datetime.now() + timedelta(minutes=settings.SERVICE_TIMEOUT_MINUTES)
            self._setup_timer(settings.SERVICE_TIMEOUT_MINUTES)

    @property
    def auto_extend_enabled(self) -> bool:
        """Whether the timeout is automatically extended on API requests"""
        return self._auto_extend_enabled

    def disable_auto_extend(self):
        """Disable auto-extend (called when user explicitly manages timeout)"""
        self._auto_extend_enabled = False

    def _cancel_timer(self):
        """Cancel any pending shutdown timer"""
        if self.shutdown_task:
            self.shutdown_task.cancel()
            self.shutdown_task = None
        if self.shutdown_timer:
            self.shutdown_timer.cancel()
            self.shutdown_timer = None

    def _setup_timer(self, minutes):
        """Schedule a shutdown after the given number of minutes"""
        self._cancel_timer()

        async def shutdown_after_timeout():
            await asyncio.sleep(minutes * 60)
            await self.shutdown()

        try:
            loop = asyncio.get_running_loop()
            self.shutdown_task = loop.create_task(shutdown_after_timeout())
        except RuntimeError:
            # No running event loop (e.g. during module import): use a thread timer
            self.shutdown_timer = threading.Timer(
                minutes * 60,
                lambda: asyncio.run(self.shutdown())
            )
            self.shutdown_timer.daemon = True
            self.shutdown_timer.start()

    async def _call_rpc(self, method, *args):
        """Execute RPC call asynchronously"""
        try:
            return await asyncio.to_thread(method, *args)
        except Exception as e:
            raise BadRequestException(f"RPC call failed: {str(e)}")

    async def get_all_processes(self) -> List[ProcessInfo]:
        """Get all process statuses"""
        try:
            processes = await self._call_rpc(self.server.supervisor.getAllProcessInfo)
            return [ProcessInfo(**process) for process in processes]
        except Exception as e:
            raise ResourceNotFoundException(f"Failed to get process status: {str(e)}")

    async def stop_all_services(self) -> SupervisorActionResult:
        """Stop all services"""
        try:
            result = await self._call_rpc(self.server.supervisor.stopAllProcesses)
            return SupervisorActionResult(status="stopped", result=result)
        except Exception as e:
            raise BadRequestException(f"Failed to stop all services: {str(e)}")

    async def shutdown(self) -> SupervisorActionResult:
        """Shut down the supervisord service itself, without stopping processes"""
        try:
            shutdown_result = await self._call_rpc(self.server.supervisor.shutdown)
            return SupervisorActionResult(status="shutdown", shutdown_result=shutdown_result)
        except Exception as e:
            raise BadRequestException(f"Failed to shut down supervisord service: {str(e)}")

    async def restart_all_services(self) -> SupervisorActionResult:
        """Restart all services"""
        try:
            stop_result = await self._call_rpc(self.server.supervisor.stopAllProcesses)
            start_result = await self._call_rpc(self.server.supervisor.startAllProcesses)
            return SupervisorActionResult(
                status="restarted",
                stop_result=stop_result,
                start_result=start_result
            )
        except Exception as e:
            raise BadRequestException(f"Failed to restart services: {str(e)}")

    def _schedule_shutdown(self, minutes: Optional[int], status: str) -> SupervisorTimeout:
        """
        (Re)schedule the automatic shutdown.

        Args:
            minutes: Timeout in minutes, falls back to the configured default
            status: Status string to report in the result
        """
        timeout_minutes = minutes or settings.SERVICE_TIMEOUT_MINUTES
        if timeout_minutes is None:
            raise BadRequestException("Timeout not specified, and system default is no timeout")

        self.timeout_active = True
        self.shutdown_time = datetime.now() + timedelta(minutes=timeout_minutes)
        self._setup_timer(timeout_minutes)

        return SupervisorTimeout(
            status=status,
            active=True,
            shutdown_time=self.shutdown_time.isoformat(),
            timeout_minutes=timeout_minutes
        )

    async def activate_timeout(self, minutes: Optional[int] = None) -> SupervisorTimeout:
        """
        Activate timeout functionality, automatically shutting down all services
        after the given time

        Args:
            minutes: Timeout in minutes, if None then use the configured default value
        """
        return self._schedule_shutdown(minutes, status="timeout_activated")

    async def extend_timeout(self, minutes: Optional[int] = None) -> SupervisorTimeout:
        """
        Extend the timeout

        Args:
            minutes: Number of minutes to extend, if None then use the configured default value
        """
        return self._schedule_shutdown(minutes, status="timeout_extended")

    async def cancel_timeout(self) -> SupervisorTimeout:
        """Cancel timeout functionality"""
        if not self.timeout_active:
            return SupervisorTimeout(status="no_timeout_active", active=False)

        self._cancel_timer()
        self.timeout_active = False
        self.shutdown_time = None
        # Re-enable auto-extend when timeout is cancelled
        self._auto_extend_enabled = True

        return SupervisorTimeout(status="timeout_cancelled", active=False)

    async def get_timeout_status(self) -> SupervisorTimeout:
        """Get current timeout status"""
        if not self.timeout_active:
            return SupervisorTimeout(active=False)

        remaining_seconds = 0
        if self.shutdown_time:
            remaining = self.shutdown_time - datetime.now()
            remaining_seconds = max(0, remaining.total_seconds())

        return SupervisorTimeout(
            active=self.timeout_active,
            shutdown_time=self.shutdown_time.isoformat() if self.shutdown_time else None,
            remaining_seconds=remaining_seconds
        )


supervisor_service = SupervisorService()
