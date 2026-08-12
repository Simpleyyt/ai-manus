import logging
from enum import Enum
from typing import AsyncGenerator, Optional

from app.domain.external.browser import Browser
from app.domain.external.llm import LLM
from app.domain.external.sandbox import Sandbox
from app.domain.external.search import SearchEngine
from app.domain.models.event import (
    BaseEvent,
    DoneEvent,
    MessageEvent,
    PlanEvent,
    PlanStatus,
    TitleEvent,
    WaitEvent,
)
from app.domain.models.message import Message
from app.domain.models.plan import ExecutionStatus, Step
from app.domain.models.session import SessionStatus
from app.domain.repositories.agent_repository import AgentRepository
from app.domain.repositories.project_repository import ProjectRepository
from app.domain.repositories.session_repository import SessionRepository
from app.domain.services.agents.execution import ExecutionAgent
from app.domain.services.agents.planner import PlannerAgent
from app.domain.services.flows.base import BaseFlow
from app.domain.services.plan_progress import mark_first_step_running
from app.domain.services.prompts.execution import can_skip_summarize
from app.domain.services.tools.browser import BrowserToolkit
from app.domain.services.tools.file import FileToolkit
from app.domain.services.tools.mcp import MCPToolkit
from app.domain.services.tools.message import MessageToolkit
from app.domain.services.tools.search import SearchToolkit
from app.domain.services.tools.shell import ShellToolkit

logger = logging.getLogger(__name__)


class AgentStatus(str, Enum):
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    SUMMARIZING = "summarizing"
    COMPLETED = "completed"
    UPDATING = "updating"


def step_needs_replan(step: Step) -> bool:
    """Only failed / unsuccessful steps ask Planner to rewrite remaining work."""
    if step.status == ExecutionStatus.FAILED:
        return True
    if step.status == ExecutionStatus.COMPLETED and step.success is False:
        return True
    return False


class PlanActFlow(BaseFlow):
    """Plan-Act state machine: Planner creates/updates plan; Executor runs one step at a time.

    Successful steps are marked locally (no Planner round-trip). Planner.update_plan
    runs only when the finished step failed or reported success=false.
    """

    def __init__(
        self,
        agent_id: str,
        agent_repository: AgentRepository,
        session_id: str,
        session_repository: SessionRepository,
        sandbox: Sandbox,
        browser: Browser,
        mcp_tool: MCPToolkit,
        llm: LLM,
        search_engine: Optional[SearchEngine] = None,
        project_repository: Optional[ProjectRepository] = None,
    ):
        self._agent_id = agent_id
        self._repository = agent_repository
        self._session_id = session_id
        self._session_repository = session_repository
        self._project_repository = project_repository
        self._llm = llm
        self.status = AgentStatus.IDLE
        self.plan = None
        self._done = False
        self._resume_waiting = False

        tools = [
            ShellToolkit(sandbox),
            BrowserToolkit(browser),
            FileToolkit(sandbox),
            MessageToolkit(),
            mcp_tool,
        ]
        if search_engine:
            tools.append(SearchToolkit(search_engine))

        self.planner = PlannerAgent(
            agent_id=self._agent_id,
            agent_repository=self._repository,
            llm=self._llm,
            capability_toolkits=tools,
        )
        self.executor = ExecutionAgent(
            agent_id=self._agent_id,
            agent_repository=self._repository,
            llm=self._llm,
            tools=tools,
        )

    async def _apply_project_instruction(self, project_id: Optional[str]) -> None:
        instruction: Optional[str] = None
        if project_id and self._project_repository:
            project = await self._project_repository.find_by_id(project_id)
            if project and project.instruction:
                instruction = project.instruction
        self.planner.set_project_instruction(instruction)
        self.executor.set_project_instruction(instruction)
        await self.planner.sync_system_prompt()
        await self.executor.sync_system_prompt()

    async def run(self, message: Message) -> AsyncGenerator[BaseEvent, None]:
        self._done = False
        session = await self._session_repository.find_by_id(self._session_id)
        if not session:
            raise ValueError(f"Session {self._session_id} not found")

        await self._apply_project_instruction(session.project_id)

        if session.status != SessionStatus.PENDING:
            await self.executor.roll_back(message)
            await self.planner.roll_back(message)

        self._resume_waiting = session.status == SessionStatus.WAITING
        if self._resume_waiting:
            self.status = AgentStatus.EXECUTING
        elif session.status == SessionStatus.RUNNING:
            self.status = AgentStatus.PLANNING
        else:
            self.status = AgentStatus.IDLE

        await self._session_repository.update_status(
            self._session_id, SessionStatus.RUNNING
        )
        self.plan = session.get_last_plan()

        step = None
        while True:
            if self.status == AgentStatus.IDLE:
                self.status = AgentStatus.PLANNING

            elif self.status == AgentStatus.PLANNING:
                async for event in self.planner.create_plan(message):
                    if isinstance(event, PlanEvent) and event.status == PlanStatus.CREATED:
                        self.plan = (
                            mark_first_step_running(event.plan)
                            if event.plan.steps
                            else event.plan
                        )
                        event = PlanEvent(status=PlanStatus.CREATED, plan=self.plan)
                        if self.plan.title and self.plan.title.strip():
                            yield TitleEvent(title=self.plan.title)
                        if self.plan.message and self.plan.message.strip():
                            yield MessageEvent(
                                role="assistant",
                                message=self.plan.message,
                            )
                    yield event

                if not self.plan or not self.plan.steps:
                    self.status = AgentStatus.COMPLETED
                else:
                    self.status = AgentStatus.EXECUTING

            elif self.status == AgentStatus.EXECUTING:
                if not self.plan:
                    self.status = AgentStatus.COMPLETED
                    continue

                self.plan.status = ExecutionStatus.RUNNING
                step = self.plan.get_next_step()
                if not step:
                    self.status = AgentStatus.SUMMARIZING
                    continue

                waited = False
                if self._resume_waiting:
                    self._resume_waiting = False
                    events = self.executor.resume_step(self.plan, step)
                else:
                    events = self.executor.execute_step(self.plan, step, message)

                async for event in events:
                    if isinstance(event, WaitEvent):
                        waited = True
                    yield event

                if waited:
                    self._done = False
                    return

                await self.executor.compact_memory()

                if step_needs_replan(step):
                    logger.info(
                        "Agent %s step %s needs replan (status=%s success=%s)",
                        self._agent_id,
                        step.id,
                        step.status,
                        step.success,
                    )
                    self.status = AgentStatus.UPDATING
                else:
                    # Local progress only — keep Plan panel in sync without Planner LLM.
                    yield PlanEvent(status=PlanStatus.UPDATED, plan=self.plan)
                    self.status = AgentStatus.EXECUTING

            elif self.status == AgentStatus.UPDATING:
                async for event in self.planner.update_plan(self.plan, step):
                    yield event
                self.status = AgentStatus.EXECUTING

            elif self.status == AgentStatus.SUMMARIZING:
                if can_skip_summarize(self.plan):
                    logger.info(
                        "Agent %s skipping summarize for single successful step",
                        self._agent_id,
                    )
                    self.status = AgentStatus.COMPLETED
                    continue
                async for event in self.executor.summarize():
                    yield event
                self.status = AgentStatus.COMPLETED

            elif self.status == AgentStatus.COMPLETED:
                if self.plan:
                    self.plan.status = ExecutionStatus.COMPLETED
                    yield PlanEvent(status=PlanStatus.COMPLETED, plan=self.plan)
                self.status = AgentStatus.IDLE
                break

        self._done = True
        yield DoneEvent()

    def is_done(self) -> bool:
        return self._done
