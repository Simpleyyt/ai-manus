from typing import Optional
import logging
from functools import lru_cache
from fastapi import Request
from app.infrastructure.external.file.gridfsfile import get_file_storage
from app.infrastructure.external.search import get_search_engine
from app.domain.models.user import User
from app.application.errors.exceptions import UnauthorizedError

# Import all required services
from app.application.services.agent_service import AgentService
from app.application.services.file_service import FileService
from app.application.services.auth_service import AuthService
from app.application.services.token_service import TokenService

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
    the necessary file storage dependency.
    """
    logger.info("Creating FileService instance")
    
    # Get file storage dependency
    file_storage = get_file_storage()
    
    return FileService(
        file_storage=file_storage,
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


def get_current_user(request: Request) -> User:
    """
    Get current authenticated user from request state
    
    This function extracts the current user from the request state
    that was set by the authentication middleware.
    """
    if not hasattr(request.state, 'user'):
        raise UnauthorizedError("Authentication required")
    
    user = request.state.user
    if not user:
        raise UnauthorizedError("Invalid user session")
    
    return user

def get_optional_current_user(request: Request) -> Optional[User]:
    """
    Get current authenticated user from request state, return None if not authenticated
    
    This function extracts the current user from the request state
    that was set by the authentication middleware. Returns None if no user.
    """
    if not hasattr(request.state, 'user'):
        return None
    
    return request.state.user