from typing import Optional
from app.domain.external.sandbox import Sandbox
from app.domain.services.tools.base import BaseToolkit, tool
from app.domain.models.tool_result import ToolResult

class ShellToolkit(BaseToolkit):
    """Shell tool class, providing Shell interaction related functions"""

    name: str = "shell"
    instructions: str = """
- Avoid commands requiring interactive confirmation; use -y or -f flags
- Avoid commands with excessive output; redirect to files when necessary
- Chain related commands with && to minimize round-trips
- Use non-interactive `bc` for simple math, Python for anything complex; never compute mentally
- Save code to files before execution; never pipe code inline into interpreters
"""
    
    def __init__(self, sandbox: Sandbox):
        """Initialize Shell tool class
        
        Args:
            sandbox: Sandbox service
        """
        super().__init__()
        self.sandbox = sandbox
        
    @tool(
        description="Execute commands in a specified shell session. Use for running code, installing packages, or managing files.",
        id="Unique identifier of the target shell session",
        exec_dir="Working directory for command execution (must use absolute path)",
        command="Shell command to execute",
    )
    async def shell_exec(
        self,
        id: str,
        exec_dir: str,
        command: str
    ) -> ToolResult:
        return await self.sandbox.exec_command(id, exec_dir, command)
    
    @tool(
        description="View the content of a specified shell session. Use for checking command execution results or monitoring output.",
        id="Unique identifier of the target shell session",
    )
    async def shell_view(self, id: str) -> ToolResult:
        return await self.sandbox.view_shell(id)
    
    @tool(
        description="Wait for the running process in a specified shell session to return. Use after running commands that require longer runtime.",
        id="Unique identifier of the target shell session",
        seconds="Wait duration in seconds",
    )
    async def shell_wait(
        self,
        id: str,
        seconds: Optional[int] = None
    ) -> ToolResult:
        return await self.sandbox.wait_for_process(id, seconds)
    
    @tool(
        description="Write input to a running process in a specified shell session. Use for responding to interactive command prompts.",
        id="Unique identifier of the target shell session",
        input="Input content to write to the process",
        press_enter="Whether to press Enter key after input",
    )
    async def shell_write_to_process(
        self,
        id: str,
        input: str,
        press_enter: bool
    ) -> ToolResult:
        return await self.sandbox.write_to_process(id, input, press_enter)
    
    @tool(
        description="Terminate a running process in a specified shell session. Use for stopping long-running processes or handling frozen commands.",
        id="Unique identifier of the target shell session",
    )
    async def shell_kill_process(self, id: str) -> ToolResult:
        return await self.sandbox.kill_process(id)
