from typing import Optional
from fastapi import APIRouter, Depends, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

from app.application.services.auth_service import AuthService
from app.application.services.email_service import EmailService
from app.application.errors.exceptions import (
    UnauthorizedError, NotFoundError, BadRequestError
)
from app.interfaces.dependencies import get_auth_service, get_current_user, get_email_service
from app.interfaces.schemas.base import APIResponse
from app.interfaces.schemas.auth import (
    LoginRequest, RegisterRequest, ChangePasswordRequest, ChangeFullnameRequest, RefreshTokenRequest,
    SendVerificationCodeRequest, ResetPasswordRequest,
    LoginResponse, RegisterResponse, AuthStatusResponse, RefreshTokenResponse,
    UserResponse
)
from app.core.config import get_settings
from app.domain.models.user import User
from app.domain.models.auth_session import AuthClientType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_session_cookie(response: Response, session_id: str, client: AuthClientType) -> None:
    settings = get_settings()
    if client in (AuthClientType.IOS, AuthClientType.ANDROID):
        max_age = settings.session_app_ttl_days * 24 * 3600
    else:
        max_age = settings.session_web_ttl_days * 24 * 3600
    response.set_cookie(
        key=settings.session_cookie_name,
        value=session_id,
        max_age=max_age,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite,
        path="/",
    )


def _clear_session_cookie(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(
        key=settings.session_cookie_name,
        path="/",
    )


def _client_ip(request: Request) -> Optional[str]:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


@router.post("/login", response_model=APIResponse[LoginResponse])
async def login(
    request: LoginRequest,
    response: Response,
    http_request: Request,
    auth_service: AuthService = Depends(get_auth_service)
) -> APIResponse[LoginResponse]:
    """User login — creates Redis session + Set-Cookie."""
    client = auth_service.parse_client(request.client)
    auth_result = await auth_service.login_with_session(
        request.email,
        request.password,
        client=client,
        ip=_client_ip(http_request),
        user_agent=http_request.headers.get("user-agent"),
    )
    _set_session_cookie(response, auth_result.access_token, client)
    return APIResponse.success(LoginResponse(
        user=UserResponse.from_domain(auth_result.user),
        access_token=auth_result.access_token,
        refresh_token=auth_result.refresh_token or auth_result.access_token,
        token_type=auth_result.token_type
    ))


@router.post("/register", response_model=APIResponse[RegisterResponse])
async def register(
    request: RegisterRequest,
    response: Response,
    http_request: Request,
    auth_service: AuthService = Depends(get_auth_service)
) -> APIResponse[RegisterResponse]:
    """User registration — creates Redis session + Set-Cookie."""
    user = await auth_service.register_user(
        fullname=request.fullname,
        password=request.password,
        email=request.email
    )
    client = auth_service.parse_client(request.client)
    session = await auth_service.create_auth_session(
        user,
        client=client,
        ip=_client_ip(http_request),
        user_agent=http_request.headers.get("user-agent"),
    )
    _set_session_cookie(response, session.session_id, client)
    return APIResponse.success(RegisterResponse(
        user=UserResponse.from_domain(user),
        access_token=session.session_id,
        refresh_token=session.session_id,
        token_type="bearer"
    ))


@router.get("/status", response_model=APIResponse[AuthStatusResponse])
async def get_auth_status(
    auth_service: AuthService = Depends(get_auth_service)
) -> APIResponse[AuthStatusResponse]:
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
    await auth_service.change_password(current_user.id, request.old_password, request.new_password)
    return APIResponse.success({})


@router.post("/change-fullname", response_model=APIResponse[UserResponse])
async def change_fullname(
    request: ChangeFullnameRequest,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> APIResponse[UserResponse]:
    updated_user = await auth_service.change_fullname(current_user.id, request.fullname)
    return APIResponse.success(UserResponse.from_domain(updated_user))


@router.get("/me", response_model=APIResponse[UserResponse])
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> APIResponse[UserResponse]:
    return APIResponse.success(UserResponse.from_domain(current_user))


@router.get("/user/{user_id}", response_model=APIResponse[UserResponse])
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> APIResponse[UserResponse]:
    if current_user.role != "admin":
        raise UnauthorizedError("Admin access required")
    user = await auth_service.get_user_by_id(user_id)
    if not user:
        raise NotFoundError("User not found")
    return APIResponse.success(UserResponse.from_domain(user))


@router.post("/user/{user_id}/deactivate", response_model=APIResponse[dict])
async def deactivate_user(
    user_id: str,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> APIResponse[dict]:
    if current_user.role != "admin":
        raise UnauthorizedError("Admin access required")
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
    if current_user.role != "admin":
        raise UnauthorizedError("Admin access required")
    await auth_service.activate_user(user_id)
    return APIResponse.success({})


@router.post("/refresh", response_model=APIResponse[RefreshTokenResponse])
async def refresh_token(
    response: Response,
    http_request: Request,
    request: RefreshTokenRequest,
    bearer_credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    auth_service: AuthService = Depends(get_auth_service)
) -> APIResponse[RefreshTokenResponse]:
    """Slide auth session (body refresh_token, Bearer, or Cookie)."""
    settings = get_settings()
    body_token = request.refresh_token
    bearer = bearer_credentials.credentials if bearer_credentials else None
    cookie_id = http_request.cookies.get(settings.session_cookie_name)

    if cookie_id and not bearer and not body_token:
        if http_request.headers.get("X-Requested-With") != "XMLHttpRequest":
            raise UnauthorizedError("CSRF check failed")

    token_result = await auth_service.refresh_access_token(
        refresh_token=body_token or bearer,
        cookie_session_id=cookie_id,
        rotate=request.rotate,
    )
    _set_session_cookie(response, token_result.access_token, AuthClientType.UNKNOWN)
    return APIResponse.success(RefreshTokenResponse(
        access_token=token_result.access_token,
        refresh_token=token_result.refresh_token or token_result.access_token,
        token_type=token_result.token_type
    ))


@router.post("/logout", response_model=APIResponse[dict])
async def logout(
    response: Response,
    http_request: Request,
    current_user: User = Depends(get_current_user),
    bearer_credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    auth_service: AuthService = Depends(get_auth_service)
) -> APIResponse[dict]:
    if get_settings().auth_provider == "none":
        raise BadRequestError("Logout is not allowed")

    settings = get_settings()
    token = (
        bearer_credentials.credentials
        if bearer_credentials
        else http_request.cookies.get(settings.session_cookie_name)
    )
    if token:
        await auth_service.logout(token)
    _clear_session_cookie(response)
    return APIResponse.success({})


@router.post("/logout-all", response_model=APIResponse[dict])
async def logout_all(
    response: Response,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> APIResponse[dict]:
    if get_settings().auth_provider == "none":
        raise BadRequestError("Logout is not allowed")
    count = await auth_service.logout_all(current_user.id)
    _clear_session_cookie(response)
    return APIResponse.success({"revoked": count})


@router.post("/send-verification-code", response_model=APIResponse[dict])
async def send_verification_code(
    request: SendVerificationCodeRequest,
    auth_service: AuthService = Depends(get_auth_service),
    email_service: EmailService = Depends(get_email_service)
) -> APIResponse[dict]:
    if get_settings().auth_provider != "password":
        raise BadRequestError("Password reset is not available")
    user = await auth_service.user_repository.get_user_by_email(request.email)
    if not user:
        raise NotFoundError("User not found")
    if not user.is_active:
        raise BadRequestError("User account is inactive")
    await email_service.send_verification_code(request.email)
    return APIResponse.success({})


@router.post("/reset-password", response_model=APIResponse[dict])
async def reset_password(
    request: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
    email_service: EmailService = Depends(get_email_service)
) -> APIResponse[dict]:
    if get_settings().auth_provider != "password":
        raise BadRequestError("Password reset is not available")
    if not await email_service.verify_code(request.email, request.verification_code):
        raise UnauthorizedError("Invalid or expired verification code")
    await auth_service.reset_password(request.email, request.new_password)
    return APIResponse.success({})
