import logging
from app.domain.services.flows.base import BaseFlow
from app.domain.models.agent import Agent
from app.domain.models.message import Message
from typing import AsyncGenerator, Optional, List
from enum import Enum
from app.domain.models.event import (
    BaseEvent,
    PlanEvent,
    PlanStatus,
    MessageEvent,
    DoneEvent,
    TitleEvent,
)
from app.domain.models.plan import ExecutionStatus
from app.domain.services.agents.planner import PlannerAgent
from app.domain.services.agents.execution import ExecutionAgent
from app.domain.external.llm import LLM
from app.domain.external.sandbox import Sandbox
from app.domain.external.browser import Browser
from app.domain.external.search import SearchEngine
from app.domain.external.file import FileStorage
from app.domain.repositories.agent_repository import AgentRepository
from app.domain.utils.json_parser import JsonParser
from app.domain.repositories.session_repository import SessionRepository
from app.domain.models.session import SessionStatus
from app.domain.services.tools.mcp import MCPTool
from app.domain.services.tools.shell import ShellTool
from app.domain.services.tools.browser import BrowserTool
from app.domain.services.tools.file import FileTool
from app.domain.services.tools.message import MessageTool
from app.domain.services.tools.search import SearchTool

logger = logging.getLogger(__name__)

class AgentStatus(str, Enum):
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    REFLECTING = "reflecting"  # New state for self-reflection on failures
    SUMMARIZING = "summarizing"
    COMPLETED = "completed"
    UPDATING = "updating"

class PlanActFlow(BaseFlow):
    def __init__(
        self,
        agent_id: str,
        agent_repository: AgentRepository,
        session_id: str,
        session_repository: SessionRepository,
        llm: LLM,
        sandbox: Sandbox,
        browser: Browser,
        json_parser: JsonParser,
        mcp_tool: MCPTool,
        search_engine: Optional[SearchEngine] = None,
    ):
        self._agent_id = agent_id
        self._repository = agent_repository
        self._session_id = session_id
        self._session_repository = session_repository
        self.status = AgentStatus.IDLE
        self.plan = None

        tools = [
            ShellTool(sandbox),
            BrowserTool(browser),
            FileTool(sandbox),
            MessageTool(),
            mcp_tool
        ]
        
        # Only add search tool when search_engine is not None
        if search_engine:
            tools.append(SearchTool(search_engine))

        # Create planner and execution agents
        self.planner = PlannerAgent(
            agent_id=self._agent_id,
            agent_repository=self._repository,
            llm=llm,
            tools=tools,
            json_parser=json_parser,
        )
        logger.debug(f"Created planner agent for Agent {self._agent_id}")
            
        self.executor = ExecutionAgent(
            agent_id=self._agent_id,
            agent_repository=self._repository,
            llm=llm,
            tools=tools,
            json_parser=json_parser,
        )
        logger.debug(f"Created execution agent for Agent {self._agent_id}")

    async def run(self, message: Message) -> AsyncGenerator[BaseEvent, None]:

        # TODO: move to task runner
        session = await self._session_repository.find_by_id(self._session_id)
        if not session:
            raise ValueError(f"Session {self._session_id} not found")
        
        if session.status != SessionStatus.PENDING:
            logger.debug(f"Session {self._session_id} is not in PENDING status, rolling back")
            await self.executor.roll_back(message)
            await self.planner.roll_back(message)
        
        if session.status == SessionStatus.RUNNING:
            logger.debug(f"Session {self._session_id} is in RUNNING status")
            self.status = AgentStatus.PLANNING
        
        if session.status == SessionStatus.WAITING:
            logger.debug(f"Session {self._session_id} is in WAITING status")
            self.status = AgentStatus.EXECUTING

        await self._session_repository.update_status(self._session_id, SessionStatus.RUNNING)  
        self.plan = session.get_last_plan()

        logger.info(f"Agent {self._agent_id} started processing message: {message.message[:50]}...")
        step = None
        reflection_history = []  # Track reflections to avoid repeating mistakes
        
        while True:
            if self.status == AgentStatus.IDLE:
                logger.info(f"Agent {self._agent_id} state changed from {AgentStatus.IDLE} to {AgentStatus.PLANNING}")
                self.status = AgentStatus.PLANNING
                
            elif self.status == AgentStatus.PLANNING:
                # Create plan with goal and FIRST STEP ONLY (Dynamic Planning)
                logger.info(f"Agent {self._agent_id} started creating plan (goal + first step)")
                async for event in self.planner.create_plan(message):
                    if isinstance(event, PlanEvent) and event.status == PlanStatus.CREATED:
                        self.plan = event.plan
                        logger.info(f"Agent {self._agent_id} created plan with goal: {event.plan.goal}")
                        logger.info(f"Agent {self._agent_id} generated first step: {len(event.plan.steps)} step(s)")
                        yield TitleEvent(title=event.plan.title)
                        yield MessageEvent(role="assistant", message=event.plan.message)
                    yield event
                logger.info(f"Agent {self._agent_id} state changed from {AgentStatus.PLANNING} to {AgentStatus.EXECUTING}")
                self.status = AgentStatus.EXECUTING
                if len(event.plan.steps) == 0:
                    logger.info(f"Agent {self._agent_id} created plan successfully with no steps")
                    self.status = AgentStatus.COMPLETED
                    
            elif self.status == AgentStatus.EXECUTING:
                # Execute current step
                self.plan.status = ExecutionStatus.RUNNING
                step = self.plan.get_next_step()
                if not step:
                    logger.info(f"Agent {self._agent_id} has no more steps, state changed from {AgentStatus.EXECUTING} to {AgentStatus.COMPLETED}")
                    self.status = AgentStatus.SUMMARIZING
                    continue
                
                # Execute step
                logger.info(f"Agent {self._agent_id} started executing step {step.id}: {step.description[:50]}...")
                async for event in self.executor.execute_step(self.plan, step, message):
                    yield event
                logger.info(f"Agent {self._agent_id} completed step {step.id} with status: {step.status}")
                await self.executor.compact_memory()
                logger.debug(f"Agent {self._agent_id} compacted memory")
                
                # Evaluate execution result and decide next state
                # If step failed or had unexpected results, move to REFLECTING
                # Otherwise, move to UPDATING to generate next step
                if step.status == ExecutionStatus.FAILED or (not step.success and step.error):
                    logger.info(f"Agent {self._agent_id} detected failure/problem, state changed to {AgentStatus.REFLECTING}")
                    self.status = AgentStatus.REFLECTING
                else:
                    logger.info(f"Agent {self._agent_id} step succeeded, state changed to {AgentStatus.UPDATING}")
                    self.status = AgentStatus.UPDATING
                    
            elif self.status == AgentStatus.REFLECTING:
                # Perform self-reflection on the failed/problematic step
                logger.info(f"Agent {self._agent_id} started reflecting on step {step.id}")
                async for event in self.planner.reflect_on_failure(
                    goal=self.plan.goal,
                    step=step,
                    previous_reflections=reflection_history
                ):
                    yield event
                
                # Store reflection for future reference
                if step.reflection:
                    reflection_history.append(step.reflection)
                    logger.debug(f"Agent {self._agent_id} stored reflection: {step.reflection[:100]}...")
                
                # After reflection, move to UPDATING to generate corrective next step
                logger.info(f"Agent {self._agent_id} reflection completed, state changed to {AgentStatus.UPDATING}")
                self.status = AgentStatus.UPDATING
                
            elif self.status == AgentStatus.UPDATING:
                # Dynamic Next-Step Planning: Generate the NEXT SINGLE STEP based on current context
                logger.info(f"Agent {self._agent_id} started dynamic next-step planning")
                async for event in self.planner.update_plan(self.plan, step):
                    yield event
                
                logger.info(f"Agent {self._agent_id} plan update completed, state changed to {AgentStatus.EXECUTING}")
                self.status = AgentStatus.EXECUTING
                
            elif self.status == AgentStatus.SUMMARIZING:
                # Conclusion
                logger.info(f"Agent {self._agent_id} started summarizing")
                async for event in self.executor.summarize():
                    yield event
                logger.info(f"Agent {self._agent_id} summarizing completed, state changed to {AgentStatus.COMPLETED}")
                self.status = AgentStatus.COMPLETED
                
            elif self.status == AgentStatus.COMPLETED:
                self.plan.status = ExecutionStatus.COMPLETED
                logger.info(f"Agent {self._agent_id} plan has been completed")
                yield PlanEvent(status=PlanStatus.COMPLETED, plan=self.plan)
                self.status = AgentStatus.IDLE
                break
                
        yield DoneEvent()
        
        logger.info(f"Agent {self._agent_id} message processing completed")
    
    def is_done(self) -> bool:
        return self.status == AgentStatus.IDLE