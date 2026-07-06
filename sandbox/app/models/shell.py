"""
Shell business model definitions
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class ConsoleRecord(BaseModel):
    """Shell command console record model"""
    ps1: str = Field(..., description="Command prompt")
    command: str = Field(..., description="Executed command")
    output: str = Field(default="", description="Command output")


class ShellExecResult(BaseModel):
    """Shell command execution result model"""
    session_id: str = Field(..., description="Shell session ID")
    command: str = Field(..., description="Executed command")
    status: str = Field(..., description="Command execution status")
    returncode: Optional[int] = Field(None, description="Process return code, only has value when status is completed")
    output: Optional[str] = Field(None, description="Command execution output, only has value when status is completed")


class ShellViewResult(BaseModel):
    """Shell session content view result model"""
    output: str = Field(..., description="Shell session output content")
    session_id: str = Field(..., description="Shell session ID")
    console: Optional[List[ConsoleRecord]] = Field(None, description="Console command records")


class ShellWaitResult(BaseModel):
    """Process wait result model"""
    returncode: int = Field(..., description="Process return code")


class ShellWriteResult(BaseModel):
    """Process input write result model"""
    status: str = Field(..., description="Write status")


class ShellKillResult(BaseModel):
    """Process termination result model"""
    status: str = Field(..., description="Process status")
    returncode: int = Field(..., description="Process return code") 