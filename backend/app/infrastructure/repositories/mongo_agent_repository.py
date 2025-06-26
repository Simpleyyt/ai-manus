from typing import Optional, List
from datetime import datetime, UTC
from app.domain.models.agent import Agent
from app.domain.models.memory import Memory
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
            mongo_agent = self._to_mongo_agent(agent)
            await mongo_agent.save()
            return
        
        # Update fields from agent domain model
        agent_data = agent.model_dump(exclude={'id', 'created_at'})
        agent_data['agent_id'] = agent.id
        agent_data['updated_at'] = datetime.now(UTC)
        
        for field, value in agent_data.items():
            setattr(mongo_agent, field, value)
        await mongo_agent.save()

    async def find_by_id(self, agent_id: str) -> Optional[Agent]:
        """Find an agent by its ID"""
        mongo_agent = await AgentDocument.find_one(
            AgentDocument.agent_id == agent_id
        )
        return self._to_domain_agent(mongo_agent) if mongo_agent else None

    async def add_memory(self, agent_id: str,
                          name: str,
                          memory: Memory) -> None:
        """Add or update a memory for an agent"""
        result = await AgentDocument.find_one(
            AgentDocument.agent_id == agent_id
        ).update(
            {"$set": {f"memories.{name}": memory, "updated_at": datetime.now(UTC)}}
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
        return mongo_agent.memories.get(name, Memory(messages=[]))
    
    async def save_memory(self, agent_id: str, name: str, memory: Memory) -> None:
        """Update the messages of a memory"""
        result = await AgentDocument.find_one(
            AgentDocument.agent_id == agent_id
        ).update(
            {"$set": {f"memories.{name}": memory, "updated_at": datetime.now(UTC)}}
        )
        if not result:
            raise ValueError(f"Agent {agent_id} not found")

    def _to_domain_agent(self, mongo_agent: AgentDocument) -> Agent:
        """Convert MongoDB document to domain model"""
        # Convert to dict and map agent_id to id field
        agent_data = mongo_agent.model_dump(exclude={'id'})
        agent_data['id'] = agent_data.pop('agent_id')
        return Agent.model_validate(agent_data)
    

    def _to_mongo_agent(self, agent: Agent) -> AgentDocument:
        """Create a new MongoDB agent from domain agent"""
        # Convert to dict and map id to agent_id field
        agent_data = agent.model_dump()
        agent_data['agent_id'] = agent_data.pop('id')
        return AgentDocument.model_validate(agent_data)