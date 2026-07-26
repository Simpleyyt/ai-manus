from typing import Optional, Union
import logging
from functools import lru_cache
from fastapi import Request, Header, HTTPException, status, Depends, Query
from starlette.websockets import WebSocket
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.infrastructure.external.file.gridfsfile import get_file_storage
from app.infrastructure.external.search import get_search_engine
from app.domain.models.user import User, UserRole
from app.domain.models.auth_session import CredentialSource
from app.application.errors.exceptions import UnauthorizedError
from app.core.config import get_settings

# Import all required services
from app.application.services.agent_service import AgentService
from app.application.services.file_service import FileService
from app.application.services.auth_service import AuthService
from app.application.services.token_service import TokenService
from app.application.services.email_service import EmailService
from app.infrastructure.external.cache import get_cache
from app.infrastructure.external.llm import get_llm
from app.infrastructure.external.session_auth import RedisSessionStore

# Import all required dependencies for agent service
from app.domain.external.task import Task
from app.domain.services.agent_task_runner import AgentTaskRunnerFactory
from app.infrastructure.external.sandbox.docker_sandbox import DockerSandbox
from app.infrastructure.external.task.redis_task import RedisStreamTask
from app.infrastructure.repositories.mongo_agent_repository import MongoAgentRepository
from app.infrastructure.repositories.mongo_session_repository import MongoSessionRepository
from app.infrastructure.repositories.file_mcp_repository import FileMCPRepository
from app.infrastructure.repositories.user_repository import MongoUserRepository
from app.infrastructure.repositories.claw_repository import ClawRepository as MongoClawRepository
from app.application.services.claw_service import ClawService
from app.domain.services.claw_domain_service import ClawDomainService
from app.application.services.project_service import ProjectService
from app.infrastructure.repositories.mongo_project_repository import MongoProjectRepository
from app.infrastructure.repositories.mongo_file_favorite_repository import MongoFileFavoriteRepository


# Configure logging
logger = logging.getLogger(__name__)

# Security scheme - Bearer Token only
security_bearer = HTTPBearer(auto_error=False)

def _get_task_cls() -> type[Task]:
    """Select the task backend implementation from the TASK_BACKEND setting."""
    settings = get_settings()
    backend = (settings.task_backend or "local").lower()
    if backend == "celery":
        from app.infrastructure.external.task.celery_task import CeleryTask
        logger.info("Using Celery task backend")
        return CeleryTask
    if backend != "local":
        logger.warning("Unknown TASK_BACKEND '%s', falling back to 'local'", backend)
    return RedisStreamTask


@lru_cache()
def get_agent_service() -> AgentService:
    """
    Get agent service instance with all required dependencies
    
    This function creates and returns an AgentService instance with all
    necessary dependencies. Uses lru_cache for singleton pattern.
    """
    logger.info("Creating AgentService instance")
    
    # Create all dependencies
    agent_repository = MongoAgentRepository()
    session_repository = MongoSessionRepository()
    sandbox_cls = DockerSandbox
    task_cls = _get_task_cls()
    file_storage = get_file_storage()
    search_engine = get_search_engine()
    mcp_repository = FileMCPRepository()
    llm = get_llm()
    
    # Register the factory used to rebuild task runners on the execution side.
    # For the local backend the runner is rebuilt in this process; for the
    # celery backend workers register their own factory (see app/worker.py).
    task_cls.set_runner_factory(AgentTaskRunnerFactory(
        agent_repository=agent_repository,
        session_repository=session_repository,
        sandbox_cls=sandbox_cls,
        file_storage=file_storage,
        mcp_repository=mcp_repository,
        llm=llm,
        search_engine=search_engine,
        project_repository=MongoProjectRepository(),
    ))
    
    # Create AgentService instance
    return AgentService(
        agent_repository=agent_repository,
        session_repository=session_repository,
        sandbox_cls=sandbox_cls,
        task_cls=task_cls,
        file_storage=file_storage,
        search_engine=search_engine,
        mcp_repository=mcp_repository,
        llm=llm,
        file_favorite_repository=MongoFileFavoriteRepository(),
    )


@lru_cache()
def get_file_service() -> FileService:
    """
    Get file service instance with required dependencies
    
    This function creates and returns a FileService instance with
    the necessary file storage and token service dependencies.
    """
    logger.info("Creating FileService instance")
    
    # Get dependencies
    file_storage = get_file_storage()
    token_service = get_token_service()
    
    return FileService(
        file_storage=file_storage,
        token_service=token_service,
    )


@lru_cache()
def get_project_service() -> ProjectService:
    """Get project service instance"""
    logger.info("Creating ProjectService instance")
    return ProjectService(
        project_repository=MongoProjectRepository(),
        session_repository=MongoSessionRepository(),
    )


@lru_cache()
def get_session_store() -> RedisSessionStore:
    """Get Redis-backed opaque auth session store."""
    return RedisSessionStore()


@lru_cache()
def get_auth_service() -> AuthService:
    """
    Get authentication service instance with required dependencies
    
    This function creates and returns an AuthService instance with
    the necessary user repository dependency.
    """
    logger.info("Creating AuthService instance")
    
    # Get user repository dependency
    user_repository = MongoUserRepository()
    
    return AuthService(
        user_repository=user_repository,
        token_service=get_token_service(),
        session_store=get_session_store(),
    )


_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"})


def _enforce_cookie_csrf(request: Request, source: CredentialSource) -> None:
    """Require X-Requested-With on cookie-authenticated mutating requests."""
    if source != CredentialSource.COOKIE:
        return
    if request.method.upper() in _SAFE_METHODS:
        return
    if request.headers.get("X-Requested-With") != "XMLHttpRequest":
        raise UnauthorizedError("CSRF check failed")


def _anonymous_user() -> User:
    return User(
        id="anonymous",
        fullname="anonymous",
        email="anonymous@localhost",
        role=UserRole.USER,
        is_active=True,
    )


@lru_cache()
def get_token_service() -> TokenService:
    """Get token service instance"""
    logger.info("Creating TokenService instance")
    return TokenService()


@lru_cache()
def get_claw_service() -> ClawService:
    """Get claw service instance"""
    logger.info("Creating ClawService instance")
    settings = get_settings()
    claw_repository = MongoClawRepository()

    if settings.claw_address:
        from app.infrastructure.external.claw.fixed_claw_runtime import FixedClawRuntime
        claw_runtime = FixedClawRuntime(address=settings.claw_address)
    else:
        from app.infrastructure.external.claw.docker_claw_runtime import DockerClawRuntime
        claw_runtime = DockerClawRuntime()

    from app.infrastructure.external.claw.http_claw_client import HttpClawClient
    claw_client = HttpClawClient()

    claw_domain_service = ClawDomainService(
        claw_repository=claw_repository,
        claw_runtime=claw_runtime,
        claw_client=claw_client,
    )

    return ClawService(claw_domain_service=claw_domain_service)


@lru_cache()
def get_email_service() -> EmailService:
    """Get email service instance"""
    logger.info("Creating EmailService instance")
    cache = get_cache()
    return EmailService(cache=cache)


async def get_current_user(
    request: Request,
    bearer_credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    """
    Get current authenticated user (required).

    Resolves Authorization Bearer (opaque session or JWT grace) or HttpOnly
    session cookie. Cookie-authenticated mutating requests require
    X-Requested-With: XMLHttpRequest.
    """
    settings = get_settings()

    if settings.auth_provider == "none":
        return _anonymous_user()

    bearer = bearer_credentials.credentials if bearer_credentials else None
    cookie_id = request.cookies.get(settings.session_cookie_name)

    try:
        resolved = await auth_service.resolve_credentials(
            bearer_token=bearer,
            cookie_session_id=cookie_id,
        )
        if not resolved:
            raise UnauthorizedError("Authentication required")

        _enforce_cookie_csrf(request, resolved.source)

        user = await auth_service.user_from_resolved(resolved)
        if not user:
            raise UnauthorizedError("Invalid token")
        if not user.is_active:
            raise UnauthorizedError("User account is inactive")
        return user
    except UnauthorizedError:
        raise
    except Exception as e:
        logger.warning(f"Authentication failed: {e}")
        raise UnauthorizedError("Authentication failed")


async def get_optional_current_user(
    request: Request,
    bearer_credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    auth_service: AuthService = Depends(get_auth_service),
) -> Optional[User]:
    """Get current authenticated user (optional)."""
    settings = get_settings()

    if settings.auth_provider == "none":
        return _anonymous_user()

    bearer = bearer_credentials.credentials if bearer_credentials else None
    cookie_id = request.cookies.get(settings.session_cookie_name)
    if not bearer and not cookie_id:
        return None

    try:
        resolved = await auth_service.resolve_credentials(
            bearer_token=bearer,
            cookie_session_id=cookie_id,
        )
        if not resolved:
            return None
        user = await auth_service.user_from_resolved(resolved)
        if user and user.is_active:
            return user
    except Exception as e:
        logger.warning(f"Optional authentication failed: {e}")

    return None


async def resolve_ws_user(
    websocket: WebSocket,
    auth_service: Optional[AuthService] = None,
) -> User:
    """
    Resolve user for WebSocket connections (B1).

    Browser: Cookie session_id.
    App: Authorization: Bearer <session_id>.
    Query ?token= is not accepted.
    """
    settings = get_settings()
    if settings.auth_provider == "none":
        return _anonymous_user()

    service = auth_service or get_auth_service()
    bearer = None
    auth_header = websocket.headers.get("authorization") or websocket.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        bearer = auth_header[7:].strip()

    cookie_id = websocket.cookies.get(settings.session_cookie_name)
    resolved = await service.resolve_credentials(
        bearer_token=bearer,
        cookie_session_id=cookie_id,
    )
    if not resolved:
        raise UnauthorizedError("Authentication required")
    user = await service.user_from_resolved(resolved)
    if not user or not user.is_active:
        raise UnauthorizedError("Invalid token")
    return user


async def verify_signature(
    request: Request,
    signature: Optional[str] = Query(None),
    token_service: TokenService = Depends(get_token_service)
) -> str:
    return await _verify_signature(request, signature, token_service)

async def verify_signature_websocket(
    request: WebSocket,
    signature: Optional[str] = Query(None),
    token_service: TokenService = Depends(get_token_service)
) -> str:
    return await _verify_signature(request, signature, token_service)

async def _verify_signature(
    request: Union[Request, WebSocket],
    signature: Optional[str] = Query(None),
    token_service: TokenService = Depends(get_token_service)
) -> str:
    """
    Verify signature for signed URL access
    
    This dependency validates the signature parameter in the request URL.
    If the signature is missing or invalid, it raises an HTTPException.
    
    This is designed to work with both regular HTTP endpoints and WebSocket endpoints.
    For WebSocket connections, the exception will be raised before the connection is accepted,
    preventing invalid connections from being established.
    
    Args:
        request: The incoming request
        signature: The signature query parameter
        token_service: Token service for signature verification
        
    Returns:
        The verified signature string
        
    Raises:
        HTTPException: If signature is missing or invalid (status code 401)
    """
    if not signature:
        logger.error(f"Missing signature: {request.url}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing signature"
        )
    
    if not token_service.verify_signed_url(str(request.url)):
        logger.error(f"Invalid signature: {request.url}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature"
        )
    
    return signature