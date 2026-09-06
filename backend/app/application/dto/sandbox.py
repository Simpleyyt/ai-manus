from typing import Optional

from pydantic import BaseModel

from app.domain.models.sandbox.file import FileReadResult
from app.domain.models.sandbox.shell import ShellViewResult


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
    def from_result(cls, result: ShellViewResult) -> "ShellViewDto":
        """Build the DTO from the strongly-typed sandbox shell-view result.

        The dict-to-model boundary lives in ``ShellViewResult`` (the domain
        anti-corruption layer for the sandbox wire format); this factory only
        projects that domain value object onto the application DTO.
        """
        return cls.model_validate(result, from_attributes=True)


class FileViewDto(BaseModel):
    """Application output for the file-view use case."""

    content: str
    file: str

    @classmethod
    def from_result(cls, result: FileReadResult) -> "FileViewDto":
        """Build the DTO from the strongly-typed sandbox file-read result."""
        return cls.model_validate(result, from_attributes=True)
