from typing import AsyncGenerator, Optional

from app.domain.external.browser import Browser
from app.domain.external.llm import LLM
from app.domain.external.sandbox import Sandbox
from app.domain.external.search import SearchEngine
from app.domain.models.event import (
    BaseEvent,
    DoneEvent,
    PlanEvent,
    PlanStatus,
    WaitEvent,
)
from app.domain.models.message import Message
from app.domain.models.plan import ExecutionStatus, Plan
from app.domain.models.session import SessionStatus
from app.domain.models.todo import TodoItem, TodoStatus
from app.domain.repositories.agent_repository import AgentRepository
from app.domain.repositories.project_repository import ProjectRepository
from app.domain.repositories.session_repository import SessionRepository
from app.domain.services.agents.manus import ManusAgent
from app.domain.services.flows.base import BaseFlow
from app.domain.services.todo_projection import todos_to_plan
from app.domain.services.tools.browser import BrowserToolkit
from app.domain.services.tools.file import FileToolkit
from app.domain.services.tools.mcp import MCPToolkit
from app.domain.services.tools.message import MessageToolkit
from app.domain.services.tools.search import SearchToolkit
from app.domain.services.tools.shell import ShellToolkit
from app.domain.services.tools.todo import TodoToolkit


class AgentLoopFlow(BaseFlow):
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
        self._session_id = session_id
        self._session_repository = session_repository
        self._project_repository = project_repository
        self._done = False

        tools = [
            ShellToolkit(sandbox),
            BrowserToolkit(browser),
            FileToolkit(sandbox),
            MessageToolkit(),
            TodoToolkit(),
            mcp_tool,
        ]
        if search_engine:
            tools.append(SearchToolkit(search_engine))

        self.agent = ManusAgent(
            agent_id=agent_id,
            agent_repository=agent_repository,
            llm=llm,
            tools=tools,
        )

    async def _apply_project_instruction(self, project_id: Optional[str]) -> None:
        instruction: Optional[str] = None
        if project_id and self._project_repository:
            project = await self._project_repository.find_by_id(project_id)
            if project and project.instruction:
                instruction = project.instruction
        self.agent.set_project_instruction(instruction)
        await self.agent.sync_system_prompt()

    @staticmethod
    def _todos_from_plan(plan: Plan) -> list[TodoItem]:
        status_map = {
            ExecutionStatus.PENDING: TodoStatus.PENDING,
            ExecutionStatus.RUNNING: TodoStatus.IN_PROGRESS,
            ExecutionStatus.COMPLETED: TodoStatus.COMPLETED,
            ExecutionStatus.FAILED: TodoStatus.CANCELLED,
        }
        return [
            TodoItem(
                id=step.id,
                content=step.description,
                status=status_map[step.status],
            )
            for step in plan.steps
        ]

    async def run(self, message: Message) -> AsyncGenerator[BaseEvent, None]:
        self._done = False
        session = await self._session_repository.find_by_id(self._session_id)
        if not session:
            raise ValueError(f"Session {self._session_id} not found")

        await self._apply_project_instruction(session.project_id)
        initial_status = session.status
        if initial_status != SessionStatus.PENDING:
            await self.agent.roll_back(message)

        await self._session_repository.update_status(
            self._session_id,
            SessionStatus.RUNNING,
        )

        last_plan = session.get_last_plan()
        if initial_status == SessionStatus.WAITING and last_plan:
            self.agent._todo_items = self._todos_from_plan(last_plan)

        waited = False
        events = (
            self.agent.resume()
            if initial_status == SessionStatus.WAITING
            else self.agent.run(message)
        )
        async for event in events:
            if isinstance(event, WaitEvent):
                waited = True
            yield event

        if not waited:
            final_todos = self.agent._todo_items
            if not final_todos and last_plan:
                final_todos = self._todos_from_plan(last_plan)
            if final_todos:
                yield PlanEvent(
                    status=PlanStatus.COMPLETED,
                    plan=todos_to_plan(
                        final_todos,
                        title=last_plan.title if last_plan else "",
                        goal=last_plan.goal if last_plan else "",
                    ),
                )
            self._done = True
            yield DoneEvent()

    def is_done(self) -> bool:
        return self._done
