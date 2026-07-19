from pydantic import BaseModel, Field
from typing import Optional

class ShellExecRequest(BaseModel):
    """Shell command execution request model"""
    id: Optional[str] = Field(None, description="Unique identifier of the target shell session, if not provided, one will be automatically created")
    exec_dir: Optional[str] = Field(None, description="Working directory for command execution (must use absolute path)")
    command: str = Field(..., description="Shell command to execute")


class ShellViewRequest(BaseModel):
    """Shell session content view request model"""
    id: str = Field(..., description="Unique identifier of the target shell session")
    console: Optional[bool] = Field(False, description="Whether to return console records")
    max_length: Optional[int] = Field(10000, description="Maximum length of the output to return, the most recent part is kept")


class ShellWaitRequest(BaseModel):
    """Shell process wait request model"""
    id: str = Field(..., description="Unique identifier of the target shell session")
    seconds: Optional[int] = Field(None, description="Wait time (seconds)")


class ShellWriteToProcessRequest(BaseModel):
    """Request model for writing input to a running process"""
    id: str = Field(..., description="Unique identifier of the target shell session")
    input: str = Field(..., description="Input content to write to the process")
    press_enter: bool = Field(..., description="Whether to press enter key after input")


class ShellKillProcessRequest(BaseModel):
    """Request model for terminating a running process"""
    id: str = Field(..., description="Unique identifier of the target shell session")
