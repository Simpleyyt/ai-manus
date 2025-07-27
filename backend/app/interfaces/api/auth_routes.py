from fastapi import APIRouter, Depends, Request
import logging

from app.application.services.auth_service import AuthService
from app.application.services.token_service import TokenService
from app.application.services.file_service import FileService
from app.application.services.agent_service import AgentService
from app.application.errors.exceptions import (
    UnauthorizedError, NotFoundError, BadRequestError
)
from app.interfaces.dependencies import get_auth_service, get_current_user, get_file_service, get_agent_service, get_token_service
from app.interfaces.schemas.response import APIResponse, ResourceAccessTokenResponse
from app.interfaces.schemas.auth import (
    LoginRequest, RegisterRequest, ChangePasswordRequest, RefreshTokenRequest,
    LoginResponse, RegisterResponse, AuthStatusResponse, RefreshTokenResponse,
    UserResponse
)
from app.interfaces.schemas.request import AccessTokenRequest
from app.core.config import get_settings
from app.domain.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])



@router.post("/login", response_model=APIResponse[LoginResponse])
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> APIResponse[LoginResponse]:
    """User login endpoint"""
    # Authenticate user and get tokens
    auth_result = await auth_service.login_with_tokens(request.email, request.password)
    
    # Return success response with tokens
    return APIResponse.success(LoginResponse(
        user=UserResponse.from_user(auth_result.user),
        access_token=auth_result.access_token,
        refresh_token=auth_result.refresh_token,
        token_type=auth_result.token_type
    ))


@router.post("/register", response_model=APIResponse[RegisterResponse])
async def register(
    request: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> APIResponse[RegisterResponse]:
    """User registration endpoint"""
    # Register user
    user = await auth_service.register_user(
        fullname=request.fullname,
        password=request.password,
        email=request.email
    )
    
    # Generate tokens for the new user
    access_token = auth_service.token_service.create_access_token(user)
    refresh_token = auth_service.token_service.create_refresh_token(user)
    
    # Return success response with tokens
    return APIResponse.success(RegisterResponse(
        user=UserResponse.from_user(user),
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    ))


@router.get("/status", response_model=APIResponse[AuthStatusResponse])
async def get_auth_status(
    auth_service: AuthService = Depends(get_auth_service)
) -> APIResponse[AuthStatusResponse]:
    """Get authentication status and configuration"""
    settings = get_settings()
    
    return APIResponse.success(AuthStatusResponse(
        auth_provider=settings.auth_provider
    ))


@router.post("/change-password", response_model=APIResponse[dict])
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> APIResponse[dict]:
    """Change user password endpoint"""
    # Change password for current user
    await auth_service.change_password(current_user.id, request.old_password, request.new_password)
    
    return APIResponse.success({})


@router.get("/me", response_model=APIResponse[UserResponse])
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> APIResponse[UserResponse]:
    """Get current user information"""
    return APIResponse.success(UserResponse.from_user(current_user))


@router.get("/user/{user_id}", response_model=APIResponse[UserResponse])
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> APIResponse[UserResponse]:
    """Get user information by ID (admin only)"""
    # Check if current user is admin
    if current_user.role != "admin":
        raise UnauthorizedError("Admin access required")
    
    user = await auth_service.get_user_by_id(user_id)
    
    if not user:
        raise NotFoundError("User not found")
    
    return APIResponse.success(UserResponse.from_user(user))


@router.post("/user/{user_id}/deactivate", response_model=APIResponse[dict])
async def deactivate_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> APIResponse[dict]:
    """Deactivate user account (admin only)"""
    # Check if current user is admin
    if current_user.role != "admin":
        raise UnauthorizedError("Admin access required")
    
    # Prevent self-deactivation
    if current_user.id == user_id:
        raise BadRequestError("Cannot deactivate your own account")
    
    await auth_service.deactivate_user(user_id)
    return APIResponse.success({})


@router.post("/user/{user_id}/activate", response_model=APIResponse[dict])
async def activate_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> APIResponse[dict]:
    """Activate user account (admin only)"""
    # Check if current user is admin
    if current_user.role != "admin":
        raise UnauthorizedError("Admin access required")
    
    await auth_service.activate_user(user_id)
    return APIResponse.success({})


@router.post("/refresh", response_model=APIResponse[RefreshTokenResponse])
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> APIResponse[RefreshTokenResponse]:
    """Refresh access token endpoint"""
    # Refresh access token
    token_result = await auth_service.refresh_access_token(request.refresh_token)
    
    return APIResponse.success(RefreshTokenResponse(
        access_token=token_result.access_token,
        token_type=token_result.token_type
    ))


@router.post("/logout", response_model=APIResponse[dict])
async def logout(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
) -> APIResponse[dict]:
    """User logout endpoint"""
    # Extract token from Authorization header
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise UnauthorizedError("Authentication required")
    
    token = auth_header.split(" ")[1]
    
    # Revoke token
    await auth_service.logout(token)
    
    return APIResponse.success({})
 