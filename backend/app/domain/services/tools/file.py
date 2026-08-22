from typing import Optional

from pydantic import BaseModel, Field

from app.domain.external.sandbox import Sandbox
from app.domain.models.tool_result import ToolResult
from app.domain.services.tools.base import BaseToolkit, Tool


class FileReadTool(Tool):
    name = "file_read"
    description = (
        "Read file content. Use for checking file contents, analyzing logs, "
        "or reading configuration files."
    )

    class Args(BaseModel):
        file: str = Field(description="Absolute path of the file to read")
        start_line: Optional[int] = Field(
            default=None,
            description="(Optional) Starting line to read from, 0-based. If not specified, starts from beginning",
        )
        end_line: Optional[int] = Field(
            default=None,
            description="(Optional) Ending line number (exclusive). If not specified, reads entire file",
        )
        sudo: Optional[bool] = Field(
            default=False,
            description="(Optional) Whether to use sudo privileges, defaults to false",
        )

    async def run(
        self,
        file: str,
        start_line: Optional[int] = None,
        end_line: Optional[int] = None,
        sudo: Optional[bool] = False,
    ) -> ToolResult:
        return await self.toolkit.sandbox.file_read(
            file=file,
            start_line=start_line,
            end_line=end_line,
            sudo=sudo,
        )


class FileWriteTool(Tool):
    name = "file_write"
    description = (
        "Overwrite or append content to a file. Use for creating new files, "
        "appending content, or modifying existing files."
    )

    class Args(BaseModel):
        file: str = Field(description="Absolute path of the file to write to")
        content: str = Field(description="Text content to write")
        append: Optional[bool] = Field(
            default=False, description="(Optional) Whether to use append mode"
        )
        leading_newline: Optional[bool] = Field(
            default=False, description="(Optional) Whether to add a leading newline"
        )
        trailing_newline: Optional[bool] = Field(
            default=False, description="(Optional) Whether to add a trailing newline"
        )
        sudo: Optional[bool] = Field(
            default=False, description="(Optional) Whether to use sudo privileges"
        )

    async def run(
        self,
        file: str,
        content: str,
        append: Optional[bool] = False,
        leading_newline: Optional[bool] = False,
        trailing_newline: Optional[bool] = False,
        sudo: Optional[bool] = False,
    ) -> ToolResult:
        final_content = content
        if leading_newline:
            final_content = "\n" + final_content
        if trailing_newline:
            final_content = final_content + "\n"

        return await self.toolkit.sandbox.file_write(
            file=file,
            content=final_content,
            append=append,
            leading_newline=False,
            trailing_newline=False,
            sudo=sudo,
        )


class FileStrReplaceTool(Tool):
    name = "file_str_replace"
    description = (
        "Replace specified string in a file. Use for updating specific content "
        "in files or fixing errors in code."
    )

    class Args(BaseModel):
        file: str = Field(description="Absolute path of the file to perform replacement on")
        old_str: str = Field(description="Original string to be replaced")
        new_str: str = Field(description="New string to replace with")
        sudo: Optional[bool] = Field(
            default=False, description="(Optional) Whether to use sudo privileges"
        )

    async def run(
        self,
        file: str,
        old_str: str,
        new_str: str,
        sudo: Optional[bool] = False,
    ) -> ToolResult:
        return await self.toolkit.sandbox.file_replace(
            file=file,
            old_str=old_str,
            new_str=new_str,
            sudo=sudo,
        )


class FileFindInContentTool(Tool):
    name = "file_find_in_content"
    description = (
        "Search for matching text within file content. Use for finding specific "
        "content or patterns in files."
    )

    class Args(BaseModel):
        file: str = Field(description="Absolute path of the file to search within")
        regex: str = Field(description="Regular expression pattern to match")
        sudo: Optional[bool] = Field(
            default=False, description="(Optional) Whether to use sudo privileges"
        )

    async def run(self, file: str, regex: str, sudo: Optional[bool] = False) -> ToolResult:
        return await self.toolkit.sandbox.file_search(
            file=file,
            regex=regex,
            sudo=sudo,
        )


class FileFindByNameTool(Tool):
    name = "file_find_by_name"
    description = (
        "Find files by name pattern in specified directory. Use for locating "
        "files with specific naming patterns."
    )

    class Args(BaseModel):
        path: str = Field(description="Absolute path of directory to search")
        glob: str = Field(description="Filename pattern using glob syntax wildcards")

    async def run(self, path: str, glob: str) -> ToolResult:
        return await self.toolkit.sandbox.file_find(
            path=path,
            glob_pattern=glob,
        )


class FileToolkit(BaseToolkit):
    """File tool class, providing file operation functions"""

    name: str = "file"
    instructions: str = """
- Prefer file tools over shell redirection to avoid escaping issues
- Actively save intermediate results; keep different kinds of reference material in separate files
- Optionally keep /home/ubuntu/todo.md as personal working notes; it does not drive the Plan UI
- Use append mode to concatenate content onto an existing file
- Only read text, code, or markdown files; never read binary files
- Use line range limits appropriately; when uncertain, start by reading the first 20 lines
- Be mindful of performance impact with large files
"""
    tool_types = [
        FileReadTool,
        FileWriteTool,
        FileStrReplaceTool,
        FileFindInContentTool,
        FileFindByNameTool,
    ]

    def __init__(self, sandbox: Sandbox):
        """Initialize file tool class

        Args:
            sandbox: Sandbox service
        """
        self.sandbox = sandbox
        super().__init__()
