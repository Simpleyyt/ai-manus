"""Authentication related domain models"""

from pydantic import BaseModel
from typing import Optional
from app.domain.models.user import User


class AuthToken(BaseModel):
    """Authentication token model for login and refresh operations"""
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None
    user: Optional[User] = None