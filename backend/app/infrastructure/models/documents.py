from typing import Dict, Optional, List, Type, TypeVar, Generic, get_args, Self
from datetime import datetime, timezone, UTC
from beanie import Document
from pydantic import BaseModel
from app.domain.models.agent import Agent
from app.domain.models.memory import Memory
from app.domain.models.event import AgentEvent
from app.domain.models.session import Session, SessionStatus
from app.domain.models.file import FileInfo
from app.domain.models.user import User, UserRole
from pymongo import IndexModel, ASCENDING

T = TypeVar('T', bound=BaseModel)

class BaseDocument(Document, Generic[T]):
    def __init_subclass__(cls, id_field="id", domain_model_class: Type[T] = None, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._ID_FIELD = id_field
        cls._DOMAIN_MODEL_CLASS = domain_model_class
    
    def update_from_domain(self, domain_obj: T) -> None:
        """Update the document from domain model"""
        data = domain_obj.model_dump(exclude={'id', 'created_at'})
        data[self._ID_FIELD] = domain_obj.id
        if hasattr(self, 'updated_at'):
            data['updated_at'] = datetime.now(UTC)
        
        for field, value in data.items():
            setattr(self, field, value)
    
    def to_domain(self) -> T:
        """Convert MongoDB document to domain model"""
        # Convert to dict and map agent_id to id field
        data = self.model_dump(exclude={'id'})
        data['id'] = data.pop(self._ID_FIELD)
        return self._DOMAIN_MODEL_CLASS.model_validate(data)
    
    @classmethod
    def from_domain(cls, domain_obj: T) -> Self:
        """Create a new MongoDB agent from domain"""
        # Convert to dict and map id to agent_id field
        data = domain_obj.model_dump()
        data[cls._ID_FIELD] = data.pop('id')
        return cls.model_validate(data)

class UserDocument(BaseDocument[User], id_field="user_id", domain_model_class=User):
    """MongoDB document for User"""
    user_id: str
    fullname: str
    email: str  # Now required field for login
    password_hash: Optional[str] = None
    role: UserRole = UserRole.USER
    is_active: bool = True
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)
    last_login_at: Optional[datetime] = None

    class Settings:
        name = "users"
        indexes = [
            "user_id",
            "fullname",  # Keep fullname index but not unique
            IndexModel([("email", ASCENDING)], unique=True),  # Email as unique index
        ]

class AgentDocument(BaseDocument[Agent], id_field="agent_id", domain_model_class=Agent):
    """MongoDB document for Agent"""
    agent_id: str
    model_name: str
    temperature: float
    max_tokens: int
    memories: Dict[str, Memory] = {}
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)

    class Settings:
        name = "agents"
        indexes = [
            "agent_id",
        ]


class SessionDocument(BaseDocument[Session], id_field="session_id", domain_model_class=Session):
    """MongoDB model for Session"""
    session_id: str
    user_id: str  # User ID that owns this session
    sandbox_id: Optional[str] = None
    agent_id: str
    task_id: Optional[str] = None
    title: Optional[str] = None
    unread_message_count: int = 0
    latest_message: Optional[str] = None
    latest_message_at: Optional[datetime] = None
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)
    events: List[AgentEvent]
    status: SessionStatus
    files: List[FileInfo] = []
    is_shared: Optional[bool] = False
    class Settings:
        name = "sessions"
        indexes = [
            "session_id",
            "user_id",  # Add index for user_id for efficient queries
        ]