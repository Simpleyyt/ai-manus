from typing import Optional, Protocol
from app.domain.models.agent import Agent
from app.domain.models.conversation import Conversation

class AgentRepository(Protocol):
    """Repository interface for Agent aggregate"""
    
    async def save(self, agent: Agent) -> None:
        """Save or update an agent"""
        ...
    
    async def find_by_id(self, agent_id: str) -> Optional[Agent]:
        """Find an agent by its ID"""
        ...

    async def get_conversation(self, agent_id: str, name: str) -> Conversation:
        """Get a named conversation for an agent, creating an empty one if absent"""
        ...

    async def save_conversation(self, agent_id: str, name: str, conversation: Conversation) -> None:
        """Save a named conversation for an agent"""
        ...
