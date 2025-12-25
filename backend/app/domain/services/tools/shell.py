from typing import Optional
from app.domain.external.sandbox import Sandbox
from app.domain.services.tools.base import tool, BaseTool
from app.domain.models.tool_result import ToolResult

class ShellTool(BaseTool):
    """
    Shell tool class with stateful session support (OpenHands SDK pattern).
    
    Features:
    - Persistent CWD and ENV between commands
    - Background process support (&)
    - Session-based command execution
    """

    name: str = "shell"
    
    def __init__(self, sandbox: Sandbox):
        """Initialize Shell tool class
        
        Args:
            sandbox: Sandbox service (must support stateful operations)
        """
        super().__init__()
        self.sandbox = sandbox
        
    @tool(
        name="shell_exec",
        description=(
            "Execute commands in a stateful shell session with persistent CWD and ENV. "
            "The session maintains state between commands (like export, cd). "
            "Supports background processes with & suffix (e.g., 'npm run dev &'). "
            "Use for running code, installing packages, managing files, or starting servers."
        ),
        parameters={
            "id": {
                "type": "string",
                "description": "Unique identifier of the target shell session (optional, defaults to 'default')"
            },
            "command": {
                "type": "string",
                "description": (
                    "Shell command to execute. "
                    "ENV vars set with 'export VAR=value' persist for this session. "
                    "Directory changes with 'cd' persist. "
                    "Append '&' to run in background (e.g., 'npm run dev &')."
                )
            }
        },
        required=["command"]
    )
    async def shell_exec(
        self,
        command: str,
        id: Optional[str] = None
    ) -> ToolResult:
        """
        Execute Shell command with stateful context preservation.
        
        Examples:
            # ENV persistence
            result1 = await shell_exec(command="export USER=Test")
            result2 = await shell_exec(command="echo $USER")  # outputs "Test"
            
            # CWD persistence
            result1 = await shell_exec(command="cd /tmp")
            result2 = await shell_exec(command="pwd")  # outputs "/tmp"
            
            # Background process
            result = await shell_exec(command="npm run dev &")
            # Returns immediately with PID
        
        Args:
            command: Shell command to execute
            id: Session identifier (optional, defaults to "default")
            
        Returns:
            Command execution result with exit_code, stdout, stderr, cwd
        """
        # Use stateful execution
        result = await self.sandbox.exec_command_stateful(command, id)
        
        # Format message
        if result["exit_code"] == 0:
            message = result["stdout"]
            if result.get("background_pid"):
                message += f"\n[Background process started with PID: {result['background_pid']}]"
        else:
            message = result["stderr"] or f"Command failed with exit code {result['exit_code']}"
        
        # Include CWD in data for agent awareness
        data = {
            "exit_code": result["exit_code"],
            "stdout": result["stdout"],
            "stderr": result["stderr"],
            "cwd": result["cwd"],
            "session_id": result["session_id"]
        }
        
        if result.get("background_pid"):
            data["background_pid"] = result["background_pid"]
        
        return ToolResult(
            success=(result["exit_code"] == 0),
            message=message,
            data=data
        )
    
    @tool(
        name="shell_view",
        description="View the content of a specified shell session. Use for checking command execution results or monitoring output.",
        parameters={
            "id": {
                "type": "string",
                "description": "Unique identifier of the target shell session"
            }
        },
        required=["id"]
    )
    async def shell_view(self, id: str) -> ToolResult:
        """View Shell session content
        
        Args:
            id: Unique identifier of the target Shell session
            
        Returns:
            Shell session content
        """
        return await self.sandbox.view_shell(id)
    
    @tool(
        name="shell_wait",
        description="Wait for the running process in a specified shell session to return. Use after running commands that require longer runtime.",
        parameters={
            "id": {
                "type": "string",
                "description": "Unique identifier of the target shell session"
            },
            "seconds": {
                "type": "integer",
                "description": "Wait duration in seconds"
            }
        },
        required=["id"]
    )
    async def shell_wait(
        self,
        id: str,
        seconds: Optional[int] = None
    ) -> ToolResult:
        """Wait for the running process in Shell session to return
        
        Args:
            id: Unique identifier of the target Shell session
            seconds: Wait time (seconds)
            
        Returns:
            Wait result
        """
        return await self.sandbox.wait_for_process(id, seconds)
    
    @tool(
        name="shell_write_to_process",
        description="Write input to a running process in a specified shell session. Use for responding to interactive command prompts.",
        parameters={
            "id": {
                "type": "string",
                "description": "Unique identifier of the target shell session"
            },
            "input": {
                "type": "string",
                "description": "Input content to write to the process"
            },
            "press_enter": {
                "type": "boolean",
                "description": "Whether to press Enter key after input"
            }
        },
        required=["id", "input", "press_enter"]
    )
    async def shell_write_to_process(
        self,
        id: str,
        input: str,
        press_enter: bool
    ) -> ToolResult:
        """Write input to the running process in Shell session
        
        Args:
            id: Unique identifier of the target Shell session
            input: Input content to write to the process
            press_enter: Whether to press Enter key after input
            
        Returns:
            Write result
        """
        return await self.sandbox.write_to_process(id, input, press_enter)
    
    @tool(
        name="shell_kill_process",
        description="Terminate a running process in a specified shell session. Use for stopping long-running processes or handling frozen commands.",
        parameters={
            "id": {
                "type": "string",
                "description": "Unique identifier of the target shell session"
            }
        },
        required=["id"]
    )
    async def shell_kill_process(self, id: str) -> ToolResult:
        """Terminate the running process in Shell session
        
        Args:
            id: Unique identifier of the target Shell session
            
        Returns:
            Termination result
        """
        return await self.sandbox.kill_process(id)
