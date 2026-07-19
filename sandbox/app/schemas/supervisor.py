"""
Supervisor request models
"""
from pydantic import BaseModel, Field
from typing import Optional


class TimeoutRequest(BaseModel):
    """Timeout activation/extension request"""
    minutes: Optional[int] = Field(None, description="Timeout duration in minutes, system default is used if not provided")
