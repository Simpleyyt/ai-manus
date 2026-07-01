from typing import Optional
from datetime import datetime, UTC
from app.domain.models.agent import Agent
from app.domain.models.conversation import Conversation
from app.domain.repositories.agent_repository import AgentRepository
from app.infrastructure.models.documents import AgentDocument
import logging


logger = logging.getLogger(__name__)

class MongoAgentRepository(AgentRepository):
    """MongoDB implementation of AgentRepository"""

    async def save(self, agent: Agent) -> None:
        """Save or update an agent"""
        mongo_agent = await AgentDocument.find_one(
            AgentDocument.agent_id == agent.id
        )
        
        if not mongo_agent:
            mongo_agent = AgentDocument.from_domain(agent)
            await mongo_agent.save()
            return
        
        # Update fields from agent domain model
        mongo_agent.update_from_domain(agent)
        await mongo_agent.save()

    async def find_by_id(self, agent_id: str) -> Optional[Agent]:
        """Find an agent by its ID"""
        mongo_agent = await AgentDocument.find_one(
            AgentDocument.agent_id == agent_id
        )
        return mongo_agent.to_domain() if mongo_agent else None

    async def get_conversation(self, agent_id: str, name: str) -> Conversation:
        """Get a named conversation for an agent, creating an empty one if absent"""
        mongo_agent = await AgentDocument.find_one(
            AgentDocument.agent_id == agent_id
        )
        if not mongo_agent:
            raise ValueError(f"Agent {agent_id} not found")
        return mongo_agent.conversations.get(name, Conversation(messages=[]))

    async def save_conversation(self, agent_id: str, name: str, conversation: Conversation) -> None:
        """Save a named conversation for an agent"""
        result = await AgentDocument.find_one(
            AgentDocument.agent_id == agent_id
        ).update(
            {"$set": {f"conversations.{name}": conversation, "updated_at": datetime.now(UTC)}}
        )
        if not result:
            raise ValueError(f"Agent {agent_id} not found")
