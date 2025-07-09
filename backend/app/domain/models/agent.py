from typing import Optional, Dict
from datetime import datetime, UTC
from pydantic import BaseModel, Field, field_validator
from app.domain.models.memory import Memory
import uuid

class Agent(BaseModel):
    """
    Agent aggregate root that manages the lifecycle and state of an AI agent
    Including its execution context, memory, and current plan
    """
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:16])
    memories: Dict[str, Memory] = Field(default_factory=dict)
    model_name: str = Field(default="")
    temperature: float = Field(default=0.7)
    max_tokens: int = Field(default=4000)
    
    # Context related fields
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))  # Creation timestamp
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))  # Last update timestamp

    @field_validator("temperature")
    def validate_temperature(cls, v: float) -> float:
        """Validate temperature is between 0 and 1"""
        if not 0 <= v <= 1:
            raise ValueError("Temperature must be between 0 and 1")
        return v

    @field_validator("max_tokens")
    def validate_max_tokens(cls, v: Optional[int]) -> Optional[int]:
        """Validate max_tokens is positive if provided"""
        if v is not None and v <= 0:
            raise ValueError("Max tokens must be positive")
        return v

    class Config:
        arbitrary_types_allowed = True
