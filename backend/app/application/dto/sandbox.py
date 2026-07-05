from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ConsoleRecordDto(BaseModel):
    ps1: str
    command: str
    output: str = ""


class ShellViewDto(BaseModel):
    """Application output for the shell-view use case."""

    output: str
    session_id: str
    console: Optional[List[ConsoleRecordDto]] = None

    @classmethod
    def from_tool_data(cls, data: Dict[str, Any]) -> "ShellViewDto":
        console = data.get("console")
        console_dtos = None
        if console is not None:
            console_dtos = [
                ConsoleRecordDto(**record) if isinstance(record, dict) else record
                for record in console
            ]
        return cls(
            output=data["output"],
            session_id=data["session_id"],
            console=console_dtos,
        )


class FileViewDto(BaseModel):
    """Application output for the file-view use case."""

    content: str
    file: str

    @classmethod
    def from_tool_data(cls, data: Dict[str, Any]) -> "FileViewDto":
        return cls(content=data["content"], file=data["file"])
