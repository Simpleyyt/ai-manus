from typing import Optional, Union
import logging
from functools import lru_cache
from fastapi import Request, Header, HTTPException, status, Depends, Query
from starlette.websockets import WebSocket
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.infrastructure.external.file.gridfsfile import get_file_storage
from app.infrastructure.external.search import get_search_engine
from app.domain.models.user import User, UserRole
from app.application.errors.exceptions import UnauthorizedError
from app.core.config import get_settings

# Import all required services
from app.application.services.agent_service import AgentService
from app.application.services.file_service import FileService
from app.application.services.auth_service import AuthService
from app.application.services.token_service import TokenService
from app.application.services.email_service import EmailService
from app.infrastructure.external.cache import get_cache

# Import all required dependencies for agent service
from app.infrastructure.external.llm.openai_llm import OpenAILLM
from app.infrastructure.external.sandbox.docker_sandbox import DockerSandbox
from app.infrastructure.external.task.redis_task import RedisStreamTask
from app.infrastructure.utils.llm_json_parser import LLMJsonParser
from app.infrastructure.repositories.mongo_agent_repository import MongoAgentRepository
from app.infrastructure.repositories.mongo_session_repository import MongoSessionRepository
from app.infrastructure.repositories.file_mcp_repository import FileMCPRepository
from app.infrastructure.repositories.user_repository import MongoUserRepository


# Configure logging
logger = logging.getLogger(__name__)

# Security scheme - Bearer Token only
security_bearer = HTTPBearer(auto_error=False)

@lru_cache()
def get_agent_service() -> AgentService:
    """
    Get agent service instance with all required dependencies
    
    This function creates and returns an AgentService instance with all
    necessary dependencies. Uses lru_cache for singleton pattern.
    """
    logger.info("Creating AgentService instance")
    
    # Create all dependencies
    llm = OpenAILLM()
    agent_repository = MongoAgentRepository()
    session_repository = MongoSessionRepository()
    sandbox_cls = DockerSandbox
    task_cls = RedisStreamTask
    json_parser = LLMJsonParser()
    file_storage = get_file_storage()
    search_engine = get_search_engine()
    mcp_repository = FileMCPRepository()
    
    # Create AgentService instance
    return AgentService(
        llm=llm,
        agent_repository=agent_repository,
        session_repository=session_repository,
        sandbox_cls=sandbox_cls,
        task_cls=task_cls,
        json_parser=json_parser,
        file_storage=file_storage,
        search_engine=search_engine,
        mcp_repository=mcp_repository,
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
    )


@lru_cache()
def get_token_service() -> TokenService:
    """Get token service instance"""
    logger.info("Creating TokenService instance")
    return TokenService()


@lru_cache()
def get_email_service() -> EmailService:
    """Get email service instance"""
    logger.info("Creating EmailService instance")
    cache = get_cache()
    return EmailService(cache=cache)


async def get_current_user(
    bearer_credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """
    Get current authenticated user (required)
    
    This dependency enforces authentication using Bearer Token.
    If authentication fails, it raises an UnauthorizedError.
    """
    settings = get_settings()
    
    # If auth_provider is 'none', return anonymous user
    if settings.auth_provider == "none":
        return User(
            id="anonymous",
            fullname="anonymous",
            email="anonymous@localhost",
            role=UserRole.USER,
            is_active=True
        )
    
    # Check if bearer token is provided
    if not bearer_credentials:
        raise UnauthorizedError("Authentication required")
    
    try:
        # Verify bearer token
        user = await auth_service.verify_token(bearer_credentials.credentials)
        
        if not user:
            raise UnauthorizedError("Invalid token")
            
        if not user.is_active:
            raise UnauthorizedError("User account is inactive")
            
        return user
        
    except Exception as e:
        logger.warning(f"Authentication failed: {e}")
        raise UnauthorizedError("Authentication failed")


async def get_optional_current_user(
    bearer_credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    auth_service: AuthService = Depends(get_auth_service)
) -> Optional[User]:
    """
    Get current authenticated user (optional)
    
    This dependency allows both authenticated and anonymous access.
    Returns None if authentication fails or is not provided.
    
    Uses Bearer Token authentication.
    """
    settings = get_settings()
    
    # If auth_provider is 'none', return anonymous user
    if settings.auth_provider == "none":
        return User(
            id="anonymous",
            fullname="anonymous",
            email="anonymous@localhost",
            role=UserRole.USER,
            is_active=True
        )
    
    # If no bearer token provided, return None
    if not bearer_credentials:
        return None
    
    try:
        # Try to verify bearer token
        user = await auth_service.verify_token(bearer_credentials.credentials)
        
        if user and user.is_active:
            return user
            
    except Exception as e:
        logger.warning(f"Optional authentication failed: {e}")
        
    return None

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