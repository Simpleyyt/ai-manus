from typing import Optional

from pydantic import BaseModel, Field

from app.domain.external.sandbox import Sandbox
from app.domain.models.tool_result import ToolResult
from app.domain.services.tools.base import BaseToolkit, Tool


class ShellExecTool(Tool):
    name = "shell_exec"
    description = (
        "Execute commands in a specified shell session. "
        "Use for running code, installing packages, or managing files."
    )

    class Args(BaseModel):
        id: str = Field(description="Unique identifier of the target shell session")
        exec_dir: str = Field(
            description="Working directory for command execution (must use absolute path)"
        )
        command: str = Field(description="Shell command to execute")

    async def run(self, id: str, exec_dir: str, command: str) -> ToolResult:
        return await self.toolkit.sandbox.exec_command(id, exec_dir, command)


class ShellViewTool(Tool):
    name = "shell_view"
    description = (
        "View the content of a specified shell session. "
        "Use for checking command execution results or monitoring output."
    )

    class Args(BaseModel):
        id: str = Field(description="Unique identifier of the target shell session")

    async def run(self, id: str) -> ToolResult:
        return await self.toolkit.sandbox.view_shell(id)


class ShellWaitTool(Tool):
    name = "shell_wait"
    description = (
        "Wait for the running process in a specified shell session to return. "
        "Use after running commands that require longer runtime."
    )

    class Args(BaseModel):
        id: str = Field(description="Unique identifier of the target shell session")
        seconds: Optional[int] = Field(default=None, description="Wait duration in seconds")

    async def run(self, id: str, seconds: Optional[int] = None) -> ToolResult:
        return await self.toolkit.sandbox.wait_for_process(id, seconds)


class ShellWriteToProcessTool(Tool):
    name = "shell_write_to_process"
    description = (
        "Write input to a running process in a specified shell session. "
        "Use for responding to interactive command prompts."
    )

    class Args(BaseModel):
        id: str = Field(description="Unique identifier of the target shell session")
        input: str = Field(description="Input content to write to the process")
        press_enter: bool = Field(description="Whether to press Enter key after input")

    async def run(self, id: str, input: str, press_enter: bool) -> ToolResult:
        return await self.toolkit.sandbox.write_to_process(id, input, press_enter)


class ShellKillProcessTool(Tool):
    name = "shell_kill_process"
    description = (
        "Terminate a running process in a specified shell session. "
        "Use for stopping long-running processes or handling frozen commands."
    )

    class Args(BaseModel):
        id: str = Field(description="Unique identifier of the target shell session")

    async def run(self, id: str) -> ToolResult:
        return await self.toolkit.sandbox.kill_process(id)


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
    tool_types = [
        ShellExecTool,
        ShellViewTool,
        ShellWaitTool,
        ShellWriteToProcessTool,
        ShellKillProcessTool,
    ]

    def __init__(self, sandbox: Sandbox):
        """Initialize Shell tool class

        Args:
            sandbox: Sandbox service
        """
        self.sandbox = sandbox
        super().__init__()
