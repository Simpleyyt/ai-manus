from typing import Any, Mapping, Optional

from pydantic import BaseModel


class ConsoleRecordDto(BaseModel):
    ps1: str
    command: str
    output: str = ""


class ShellViewDto(BaseModel):
    """Application output for the shell-view use case."""

    output: str
    session_id: str
    console: Optional[list[ConsoleRecordDto]] = None

    @classmethod
    def from_tool_data(cls, data: Optional[Mapping[str, Any]]) -> "ShellViewDto":
        """Build the DTO from a sandbox ToolResult payload.

        Field names mirror the sandbox shell-view result, so Pydantic
        validation handles the mapping (including the nested console
        records) directly.
        """
        if not data:
            raise ValueError("shell view result is empty")
        return cls.model_validate(data)


class FileViewDto(BaseModel):
    """Application output for the file-view use case."""

    content: str
    file: str

    @classmethod
    def from_tool_data(cls, data: Optional[Mapping[str, Any]]) -> "FileViewDto":
        """Build the DTO from a sandbox ToolResult payload."""
        if not data:
            raise ValueError("file view result is empty")
        return cls.model_validate(data)
