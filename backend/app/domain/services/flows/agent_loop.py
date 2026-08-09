from typing import AsyncGenerator, Optional

from pydantic import ValidationError

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
    ToolEvent,
    ToolStatus,
    WaitEvent,
)
from app.domain.models.agent_output import PlanReportOutput, ReplanOutput
from app.domain.models.message import Message
from app.domain.models.plan import ExecutionStatus, Plan
from app.domain.models.session import SessionStatus
from app.domain.repositories.agent_repository import AgentRepository
from app.domain.repositories.project_repository import ProjectRepository
from app.domain.repositories.session_repository import SessionRepository
from app.domain.services.agents.manus import ManusAgent
from app.domain.services.agents.planner import PlannerAgent
from app.domain.services.flows.base import BaseFlow
from app.domain.services.plan_progress import (
    apply_plan_report,
    complete_plan,
    mark_first_step_running,
)
from app.domain.services.tools.browser import BrowserToolkit
from app.domain.services.tools.file import FileToolkit
from app.domain.services.tools.mcp import MCPToolkit
from app.domain.services.tools.message import MessageToolkit
from app.domain.services.tools.plan import PlanToolkit
from app.domain.services.tools.search import SearchToolkit
from app.domain.services.tools.shell import ShellToolkit


def format_plan_for_manus(plan: Plan) -> str:
    lines = [
        "<authoritative_plan>",
        f"title: {plan.title}",
        f"goal: {plan.goal}",
        "steps:",
    ]
    lines.extend(
        f"- [{step.status.value}] id={step.id}: {step.description}"
        for step in plan.steps
    )
    lines.extend([
        "</authoritative_plan>",
        (
            "Update the Plan panel only via plan_report / replan. Optionally keep "
            "todo.md in sync for your own attention; never rely on todo.md for the UI."
        ),
    ])
    return "\n".join(lines)


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
            mcp_tool,
        ]
        if search_engine:
            tools.append(SearchToolkit(search_engine))

        self.planner = PlannerAgent(
            agent_id=agent_id,
            agent_repository=agent_repository,
            llm=llm,
            capability_toolkits=tools,
        )
        self.agent = ManusAgent(
            agent_id=agent_id,
            agent_repository=agent_repository,
            llm=llm,
            tools=[*tools, PlanToolkit()],
        )
        self.plan: Plan | None = None

    async def _apply_project_instruction(self, project_id: Optional[str]) -> None:
        instruction: Optional[str] = None
        if project_id and self._project_repository:
            project = await self._project_repository.find_by_id(project_id)
            if project and project.instruction:
                instruction = project.instruction
        for agent in (self.planner, self.agent):
            agent.set_project_instruction(instruction)
            await agent.sync_system_prompt()

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
        if initial_status != SessionStatus.WAITING:
            async for event in self.planner.create_plan(message):
                if isinstance(event, PlanEvent) and event.status == PlanStatus.CREATED:
                    self.plan = (
                        mark_first_step_running(event.plan)
                        if event.plan.steps
                        else event.plan
                    )
                    self.agent._plan_title = self.plan.title
                    self.agent._plan_goal = self.plan.goal
                    event = PlanEvent(status=PlanStatus.CREATED, plan=self.plan)
                    if self.plan.title:
                        self.agent._title_emitted = True
                        yield TitleEvent(title=self.plan.title)
                    if self.plan.message and self.plan.message.strip():
                        yield MessageEvent(message=self.plan.message.strip())
                yield event

            if not self.plan or not self.plan.steps:
                if self.plan:
                    yield PlanEvent(
                        status=PlanStatus.COMPLETED,
                        plan=complete_plan(self.plan),
                    )
                self._done = True
                yield DoneEvent()
                return

            manus_message = Message(
                message=f"{message.message}\n\n{format_plan_for_manus(self.plan)}",
                attachments=message.attachments,
            )
        else:
            self.plan = last_plan
            if self.plan:
                self.agent._plan_title = self.plan.title
                self.agent._plan_goal = self.plan.goal
            # Prior turn already spoke to the user; do not re-block work tools.
            self.agent._user_notified = True
            manus_message = message

        waited = False
        events = (
            self.agent.resume()
            if initial_status == SessionStatus.WAITING
            else self.agent.run(manus_message)
        )
        async for event in events:
            if isinstance(event, ToolEvent) and event.function_name == "plan_report":
                if event.status == ToolStatus.CALLED and self.plan:
                    result = event.function_result
                    if (
                        not result
                        or not getattr(result, "success", False)
                        or getattr(result, "data", None) is None
                    ):
                        continue
                    try:
                        report = PlanReportOutput.model_validate(result.data)
                    except ValidationError:
                        continue
                    for plan_event in apply_plan_report(self.plan, report):
                        yield plan_event
                continue

            if isinstance(event, ToolEvent) and event.function_name == "replan":
                if event.status == ToolStatus.CALLED and self.plan:
                    result = event.function_result
                    if (
                        not result
                        or not getattr(result, "success", False)
                        or getattr(result, "data", None) is None
                    ):
                        continue
                    try:
                        reason = ReplanOutput.model_validate(result.data).reason
                    except ValidationError:
                        continue
                    step = self.plan.get_next_step()
                    if step is None and self.plan.steps:
                        step = self.plan.steps[-1]
                    if step is not None:
                        finished_step = step.model_copy(update={
                            "result": reason,
                            "status": ExecutionStatus.COMPLETED,
                            "success": True,
                        })
                        async for plan_event in self.planner.update_plan(
                            self.plan,
                            finished_step,
                        ):
                            if (
                                isinstance(plan_event, PlanEvent)
                                and plan_event.status == PlanStatus.UPDATED
                            ):
                                self.plan = plan_event.plan
                                self.agent._injected_plan_text = (
                                    format_plan_for_manus(self.plan)
                                )
                            yield plan_event
                continue

            if isinstance(event, WaitEvent):
                waited = True
            yield event

        if not waited and self.plan:
            yield PlanEvent(
                status=PlanStatus.COMPLETED,
                plan=complete_plan(self.plan),
            )
        self._done = not waited
        if not waited:
            yield DoneEvent()

    def is_done(self) -> bool:
        return self._done
