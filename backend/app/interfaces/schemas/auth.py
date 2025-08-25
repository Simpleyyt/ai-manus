from typing import Optional
from pydantic import BaseModel, field_validator
from datetime import datetime
from app.domain.models.user import UserRole


class LoginRequest(BaseModel):
    """Login request schema"""
    email: str
    password: str
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if not v or '@' not in v:
            raise ValueError("Valid email is required")
        return v.strip().lower()
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if not v or len(v) < 6:
            raise ValueError("Password must be at least 6 characters long")
        return v


class RegisterRequest(BaseModel):
    """Register request schema"""
    fullname: str
    email: str
    password: str
    
    @field_validator('fullname')
    @classmethod
    def validate_fullname(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError("Full name must be at least 2 characters long")
        return v.strip()
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if not v or '@' not in v:
            raise ValueError("Valid email is required")
        return v.strip().lower()
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if not v or len(v) < 6:
            raise ValueError("Password must be at least 6 characters long")
        return v


class ChangePasswordRequest(BaseModel):
    """Change password request schema"""
    old_password: str
    new_password: str
    
    @field_validator('old_password')
    @classmethod
    def validate_old_password(cls, v):
        if not v:
            raise ValueError("Old password is required")
        return v
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        if not v or len(v) < 6:
            raise ValueError("New password must be at least 6 characters long")
        return v


class ChangeFullnameRequest(BaseModel):
    """Change fullname request schema"""
    fullname: str
    
    @field_validator('fullname')
    @classmethod
    def validate_fullname(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError("Full name must be at least 2 characters long")
        return v.strip()


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""
    refresh_token: str
    
    @field_validator('refresh_token')
    @classmethod
    def validate_refresh_token(cls, v):
        if not v:
            raise ValueError("Refresh token is required")
        return v


class SendVerificationCodeRequest(BaseModel):
    """Send verification code request schema"""
    email: str
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if not v or '@' not in v:
            raise ValueError("Valid email is required")
        return v.strip().lower()


class ResetPasswordRequest(BaseModel):
    """Reset password request schema"""
    email: str
    verification_code: str
    new_password: str
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if not v or '@' not in v:
            raise ValueError("Valid email is required")
        return v.strip().lower()
    
    @field_validator('verification_code')
    @classmethod
    def validate_verification_code(cls, v):
        if not v:
            raise ValueError("Verification code is required")
        if not v.isdigit() or len(v) != 6:
            raise ValueError("Verification code must be 6 digits")
        return v
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        if not v or len(v) < 6:
            raise ValueError("New password must be at least 6 characters long")
        return v


class UserResponse(BaseModel):
    """User response schema"""
    id: str
    fullname: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None
    
    @staticmethod
    def from_user(user) -> 'UserResponse':
        """Convert user domain model to response schema"""
        return UserResponse(
            id=user.id,
            fullname=user.fullname,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login_at=user.last_login_at
        )


class LoginResponse(BaseModel):
    """Login response schema"""
    user: UserResponse
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RegisterResponse(BaseModel):
    """Register response schema"""
    user: UserResponse
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthStatusResponse(BaseModel):
    """Authentication status response schema"""
    auth_provider: str


class RefreshTokenResponse(BaseModel):
    """Refresh token response schema"""
    access_token: str
    token_type: str = "bearer" 