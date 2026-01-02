"""
Comprehensive tests for AgentService initialization and functionality
"""
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch, PropertyMock
import logging

from app.application.services.agent_service import AgentService
from app.domain.external.llm import LLM
from app.domain.repositories.agent_repository import AgentRepository
from app.domain.repositories.session_repository import SessionRepository
from app.domain.external.sandbox import Sandbox
from app.domain.external.task import Task
from app.domain.utils.json_parser import JsonParser
from app.domain.external.file import FileStorage
from app.domain.repositories.mcp_repository import MCPRepository
from app.domain.external.search import SearchEngine
from app.domain.services.agent_domain_service import AgentDomainService

logger = logging.getLogger(__name__)


# Fixtures for mocking dependencies
@pytest.fixture
def mock_llm():
    """Create a mock LLM instance"""
    llm = Mock(spec=LLM)
    llm.model_name = "test-model"
    llm.temperature = 0.7
    llm.max_tokens = 2048
    return llm


@pytest.fixture
def mock_agent_repository():
    """Create a mock AgentRepository"""
    return Mock(spec=AgentRepository)


@pytest.fixture
def mock_session_repository():
    """Create a mock SessionRepository"""
    return Mock(spec=SessionRepository)


@pytest.fixture
def mock_sandbox_cls():
    """Create a mock Sandbox class"""
    sandbox_cls = Mock()
    sandbox_cls.__name__ = "MockSandbox"
    return sandbox_cls


@pytest.fixture
def mock_task_cls():
    """Create a mock Task class"""
    task_cls = Mock()
    task_cls.__name__ = "MockTask"
    return task_cls


@pytest.fixture
def mock_json_parser():
    """Create a mock JsonParser"""
    return Mock(spec=JsonParser)


@pytest.fixture
def mock_file_storage():
    """Create a mock FileStorage"""
    return Mock(spec=FileStorage)


@pytest.fixture
def mock_mcp_repository():
    """Create a mock MCPRepository"""
    return Mock(spec=MCPRepository)


@pytest.fixture
def mock_search_engine():
    """Create a mock SearchEngine"""
    return Mock(spec=SearchEngine)


# Tests for __init__ method
class TestAgentServiceInit:
    """Test suite for AgentService initialization"""

    def test_init_with_all_required_parameters(
        self,
        mock_llm,
        mock_agent_repository,
        mock_session_repository,
        mock_sandbox_cls,
        mock_task_cls,
        mock_json_parser,
        mock_file_storage,
        mock_mcp_repository,
    ):
        """Test initialization with all required parameters"""
        # Act
        service = AgentService(
            llm=mock_llm,
            agent_repository=mock_agent_repository,
            session_repository=mock_session_repository,
            sandbox_cls=mock_sandbox_cls,
            task_cls=mock_task_cls,
            json_parser=mock_json_parser,
            file_storage=mock_file_storage,
            mcp_repository=mock_mcp_repository,
        )

        # Assert - verify all attributes are set correctly
        assert service._agent_repository == mock_agent_repository
        assert service._session_repository == mock_session_repository
        assert service._file_storage == mock_file_storage
        assert service._llm == mock_llm
        assert service._search_engine is None
        assert service._sandbox_cls == mock_sandbox_cls
        assert isinstance(service._agent_domain_service, AgentDomainService)

    def test_init_with_search_engine(
        self,
        mock_llm,
        mock_agent_repository,
        mock_session_repository,
        mock_sandbox_cls,
        mock_task_cls,
        mock_json_parser,
        mock_file_storage,
        mock_mcp_repository,
        mock_search_engine,
    ):
        """Test initialization with optional search engine parameter"""
        # Act
        service = AgentService(
            llm=mock_llm,
            agent_repository=mock_agent_repository,
            session_repository=mock_session_repository,
            sandbox_cls=mock_sandbox_cls,
            task_cls=mock_task_cls,
            json_parser=mock_json_parser,
            file_storage=mock_file_storage,
            mcp_repository=mock_mcp_repository,
            search_engine=mock_search_engine,
        )

        # Assert
        assert service._search_engine == mock_search_engine
        assert isinstance(service._agent_domain_service, AgentDomainService)

    def test_init_without_search_engine(
        self,
        mock_llm,
        mock_agent_repository,
        mock_session_repository,
        mock_sandbox_cls,
        mock_task_cls,
        mock_json_parser,
        mock_file_storage,
        mock_mcp_repository,
    ):
        """Test initialization without optional search engine (defaults to None)"""
        # Act
        service = AgentService(
            llm=mock_llm,
            agent_repository=mock_agent_repository,
            session_repository=mock_session_repository,
            sandbox_cls=mock_sandbox_cls,
            task_cls=mock_task_cls,
            json_parser=mock_json_parser,
            file_storage=mock_file_storage,
            mcp_repository=mock_mcp_repository,
        )

        # Assert
        assert service._search_engine is None

    @patch('app.application.services.agent_service.AgentDomainService')
    def test_init_creates_agent_domain_service_with_correct_parameters(
        self,
        mock_agent_domain_service_cls,
        mock_llm,
        mock_agent_repository,
        mock_session_repository,
        mock_sandbox_cls,
        mock_task_cls,
        mock_json_parser,
        mock_file_storage,
        mock_mcp_repository,
        mock_search_engine,
    ):
        """Test that AgentDomainService is created with correct parameters"""
        # Act
        service = AgentService(
            llm=mock_llm,
            agent_repository=mock_agent_repository,
            session_repository=mock_session_repository,
            sandbox_cls=mock_sandbox_cls,
            task_cls=mock_task_cls,
            json_parser=mock_json_parser,
            file_storage=mock_file_storage,
            mcp_repository=mock_mcp_repository,
            search_engine=mock_search_engine,
        )

        # Assert - verify AgentDomainService was called with correct arguments
        mock_agent_domain_service_cls.assert_called_once_with(
            mock_agent_repository,
            mock_session_repository,
            mock_llm,
            mock_sandbox_cls,
            mock_task_cls,
            mock_json_parser,
            mock_file_storage,
            mock_mcp_repository,
            mock_search_engine,
        )

    @patch('app.application.services.agent_service.logger')
    def test_init_logs_initialization(
        self,
        mock_logger,
        mock_llm,
        mock_agent_repository,
        mock_session_repository,
        mock_sandbox_cls,
        mock_task_cls,
        mock_json_parser,
        mock_file_storage,
        mock_mcp_repository,
    ):
        """Test that initialization is properly logged"""
        # Act
        service = AgentService(
            llm=mock_llm,
            agent_repository=mock_agent_repository,
            session_repository=mock_session_repository,
            sandbox_cls=mock_sandbox_cls,
            task_cls=mock_task_cls,
            json_parser=mock_json_parser,
            file_storage=mock_file_storage,
            mcp_repository=mock_mcp_repository,
        )

        # Assert
        mock_logger.info.assert_called_with("Initializing AgentService")

    def test_init_with_missing_required_parameter_raises_error(
        self,
        mock_llm,
        mock_agent_repository,
        mock_session_repository,
        mock_sandbox_cls,
        mock_task_cls,
        mock_json_parser,
        mock_file_storage,
    ):
        """Test that initialization fails when missing required parameter"""
        # Act & Assert - expect TypeError when missing mcp_repository parameter
        with pytest.raises(TypeError):
            service = AgentService(
                llm=mock_llm,
                agent_repository=mock_agent_repository,
                session_repository=mock_session_repository,
                sandbox_cls=mock_sandbox_cls,
                task_cls=mock_task_cls,
                json_parser=mock_json_parser,
                file_storage=mock_file_storage,
                # mcp_repository deliberately omitted
            )

    def test_init_stores_all_dependencies_correctly(
        self,
        mock_llm,
        mock_agent_repository,
        mock_session_repository,
        mock_sandbox_cls,
        mock_task_cls,
        mock_json_parser,
        mock_file_storage,
        mock_mcp_repository,
    ):
        """Test that all dependencies are stored as instance variables"""
        # Act
        service = AgentService(
            llm=mock_llm,
            agent_repository=mock_agent_repository,
            session_repository=mock_session_repository,
            sandbox_cls=mock_sandbox_cls,
            task_cls=mock_task_cls,
            json_parser=mock_json_parser,
            file_storage=mock_file_storage,
            mcp_repository=mock_mcp_repository,
        )

        # Assert - check all private instance variables
        assert hasattr(service, '_agent_repository')
        assert hasattr(service, '_session_repository')
        assert hasattr(service, '_file_storage')
        assert hasattr(service, '_agent_domain_service')
        assert hasattr(service, '_llm')
        assert hasattr(service, '_search_engine')
        assert hasattr(service, '_sandbox_cls')

    def test_init_with_different_llm_configurations(
        self,
        mock_agent_repository,
        mock_session_repository,
        mock_sandbox_cls,
        mock_task_cls,
        mock_json_parser,
        mock_file_storage,
        mock_mcp_repository,
    ):
        """Test initialization with different LLM configurations"""
        # Arrange - create LLM with different settings
        llm1 = Mock(spec=LLM)
        llm1.model_name = "gpt-4"
        llm1.temperature = 0.9
        llm1.max_tokens = 4096

        llm2 = Mock(spec=LLM)
        llm2.model_name = "claude-3"
        llm2.temperature = 0.5
        llm2.max_tokens = 1024

        # Act - create services with different LLMs
        service1 = AgentService(
            llm=llm1,
            agent_repository=mock_agent_repository,
            session_repository=mock_session_repository,
            sandbox_cls=mock_sandbox_cls,
            task_cls=mock_task_cls,
            json_parser=mock_json_parser,
            file_storage=mock_file_storage,
            mcp_repository=mock_mcp_repository,
        )

        service2 = AgentService(
            llm=llm2,
            agent_repository=mock_agent_repository,
            session_repository=mock_session_repository,
            sandbox_cls=mock_sandbox_cls,
            task_cls=mock_task_cls,
            json_parser=mock_json_parser,
            file_storage=mock_file_storage,
            mcp_repository=mock_mcp_repository,
        )

        # Assert
        assert service1._llm == llm1
        assert service2._llm == llm2
        assert service1._llm.model_name == "gpt-4"
        assert service2._llm.model_name == "claude-3"

    def test_init_agent_domain_service_receives_all_dependencies(
        self,
        mock_llm,
        mock_agent_repository,
        mock_session_repository,
        mock_sandbox_cls,
        mock_task_cls,
        mock_json_parser,
        mock_file_storage,
        mock_mcp_repository,
        mock_search_engine,
    ):
        """Test that AgentDomainService is properly initialized with all dependencies"""
        # Act
        service = AgentService(
            llm=mock_llm,
            agent_repository=mock_agent_repository,
            session_repository=mock_session_repository,
            sandbox_cls=mock_sandbox_cls,
            task_cls=mock_task_cls,
            json_parser=mock_json_parser,
            file_storage=mock_file_storage,
            mcp_repository=mock_mcp_repository,
            search_engine=mock_search_engine,
        )

        # Assert - verify the domain service was created
        assert service._agent_domain_service is not None
        assert isinstance(service._agent_domain_service, AgentDomainService)
