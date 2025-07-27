from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Optional
import logging

from app.application.services.auth_service import AuthService
from app.application.errors.exceptions import UnauthorizedError, ValidationError
from app.interfaces.dependencies import get_auth_service, get_current_user
from app.interfaces.schemas.response import APIResponse
from app.interfaces.schemas.auth import (
    LoginRequest, RegisterRequest, ChangePasswordRequest, RefreshTokenRequest,
    LoginResponse, RegisterResponse, AuthStatusResponse, RefreshTokenResponse,
    UserResponse
)
from app.core.config import get_settings
from app.domain.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_to_response(user) -> UserResponse:
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


@router.post("/login", response_model=APIResponse[LoginResponse])
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> APIResponse[LoginResponse]:
    """User login endpoint"""
    try:
        # Authenticate user and get tokens
        auth_result = await auth_service.login_with_tokens(request.email, request.password)
        
        # Return success response with tokens
        return APIResponse.success(LoginResponse(
            user=_user_to_response(auth_result["user"]),
            access_token=auth_result["access_token"],
            refresh_token=auth_result["refresh_token"],
            token_type=auth_result["token_type"],
            message="Login successful"
        ))
        
    except ValidationError as e:
        logger.warning(f"Login validation error: {e}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except UnauthorizedError as e:
        logger.warning(f"Login unauthorized: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login failed")


@router.post("/register", response_model=APIResponse[RegisterResponse])
async def register(
    request: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> APIResponse[RegisterResponse]:
    """User registration endpoint"""
    try:
        # Register user
        user = await auth_service.register_user(
            fullname=request.fullname,
            password=request.password,
            email=request.email
        )
        
        # Generate tokens for the new user
        access_token = auth_service.jwt_manager.create_access_token(user)
        refresh_token = auth_service.jwt_manager.create_refresh_token(user)
        
        # Return success response with tokens
        return APIResponse.success(RegisterResponse(
            user=_user_to_response(user),
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            message="User registered successfully"
        ))
        
    except ValidationError as e:
        logger.warning(f"Registration validation error: {e}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Registration failed")


@router.get("/status", response_model=APIResponse[AuthStatusResponse])
async def get_auth_status(
    auth_service: AuthService = Depends(get_auth_service)
) -> APIResponse[AuthStatusResponse]:
    """Get authentication status and configuration"""
    settings = get_settings()
    
    return APIResponse.success(AuthStatusResponse(
        authenticated=False,  # This would be determined by middleware in real app
        user=None,
        auth_provider=settings.auth_provider,
        message=f"Authentication provider: {settings.auth_provider}"
    ))


@router.post("/change-password", response_model=APIResponse[dict])
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> APIResponse[dict]:
    """Change user password endpoint"""
    try:
        # Change password for current user
        await auth_service.change_password(current_user.id, request.old_password, request.new_password)
        
        return APIResponse.success({"message": "Password changed successfully"})
        
    except ValidationError as e:
        logger.warning(f"Password change validation error: {e}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except UnauthorizedError as e:
        logger.warning(f"Password change unauthorized: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        logger.error(f"Password change error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Password change failed")


@router.get("/me", response_model=APIResponse[UserResponse])
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> APIResponse[UserResponse]:
    """Get current user information"""
    return APIResponse.success(_user_to_response(current_user))


@router.get("/user/{user_id}", response_model=APIResponse[UserResponse])
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> APIResponse[UserResponse]:
    """Get user information by ID (admin only)"""
    try:
        # Check if current user is admin
        if current_user.role != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
        
        user = await auth_service.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        return APIResponse.success(_user_to_response(user))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get user")


@router.post("/user/{user_id}/deactivate", response_model=APIResponse[dict])
async def deactivate_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> APIResponse[dict]:
    """Deactivate user account (admin only)"""
    try:
        # Check if current user is admin
        if current_user.role != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
        
        # Prevent self-deactivation
        if current_user.id == user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot deactivate your own account")
        
        await auth_service.deactivate_user(user_id)
        return APIResponse.success({"message": "User deactivated successfully"})
        
    except HTTPException:
        raise
    except ValidationError as e:
        logger.warning(f"User deactivation validation error: {e}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        logger.error(f"User deactivation error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User deactivation failed")


@router.post("/user/{user_id}/activate", response_model=APIResponse[dict])
async def activate_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> APIResponse[dict]:
    """Activate user account (admin only)"""
    try:
        # Check if current user is admin
        if current_user.role != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
        
        await auth_service.activate_user(user_id)
        return APIResponse.success({"message": "User activated successfully"})
        
    except HTTPException:
        raise
    except ValidationError as e:
        logger.warning(f"User activation validation error: {e}")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        logger.error(f"User activation error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User activation failed")


@router.post("/refresh", response_model=APIResponse[RefreshTokenResponse])
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> APIResponse[RefreshTokenResponse]:
    """Refresh access token endpoint"""
    try:
        # Refresh access token
        token_result = await auth_service.refresh_access_token(request.refresh_token)
        
        return APIResponse.success(RefreshTokenResponse(
            access_token=token_result["access_token"],
            token_type=token_result["token_type"],
            message="Token refreshed successfully"
        ))
        
    except UnauthorizedError as e:
        logger.warning(f"Token refresh unauthorized: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Token refresh failed")


@router.post("/logout", response_model=APIResponse[dict])
async def logout(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
) -> APIResponse[dict]:
    """User logout endpoint"""
    try:
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
        
        token = auth_header.split(" ")[1]
        
        # Revoke token
        await auth_service.logout(token)
        
        return APIResponse.success({"message": "Logout successful"})
        
    except HTTPException:
        # Re-raise HTTPException to preserve status code
        raise
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Logout failed") 