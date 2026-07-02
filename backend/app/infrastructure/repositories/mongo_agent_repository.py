from typing import Optional, List
from datetime import datetime, UTC
from app.domain.models.agent import Agent
from app.domain.models.memory import Memory
from app.domain.repositories.agent_repository import AgentRepository
from app.infrastructure.models.documents import AgentDocument
from app.infrastructure.models.memory_serialization import deserialize_memory, serialize_memory
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

    async def add_memory(self, agent_id: str,
                          name: str,
                          memory: Memory) -> None:
        """Add or update a memory for an agent"""
        result = await AgentDocument.find_one(
            AgentDocument.agent_id == agent_id
        ).update(
            {"$set": {f"memories.{name}": serialize_memory(memory), "updated_at": datetime.now(UTC)}}
        )
        if not result:
            raise ValueError(f"Agent {agent_id} not found")

    async def get_memory(self, agent_id: str, name: str) -> Memory:
        """Get memory by name from agent, create if not exists"""
        mongo_agent = await AgentDocument.find_one(
            AgentDocument.agent_id == agent_id
        )
        if not mongo_agent:
            raise ValueError(f"Agent {agent_id} not found")
        return deserialize_memory(mongo_agent.memories.get(name))
    
    async def save_memory(self, agent_id: str, name: str, memory: Memory) -> None:
        """Update the messages of a memory"""
        result = await AgentDocument.find_one(
            AgentDocument.agent_id == agent_id
        ).update(
            {"$set": {f"memories.{name}": serialize_memory(memory), "updated_at": datetime.now(UTC)}}
        )
        if not result:
            raise ValueError(f"Agent {agent_id} not found")
