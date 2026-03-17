import logging
import asyncio
from typing import TypedDict, Optional, AsyncGenerator, List

from langgraph.graph import StateGraph, START, END

from app.domain.services.flows.base import BaseFlow
from app.domain.models.message import Message
from app.domain.models.event import (
    BaseEvent,
    PlanEvent,
    PlanStatus,
    MessageEvent,
    DoneEvent,
    TitleEvent,
    ErrorEvent,
    WaitEvent,
)
from app.domain.models.plan import Plan, Step, ExecutionStatus
from app.domain.services.agents.planner import PlannerAgent
from app.domain.services.agents.execution import ExecutionAgent
from app.domain.external.sandbox import Sandbox
from app.domain.external.browser import Browser
from app.domain.external.search import SearchEngine
from app.domain.repositories.agent_repository import AgentRepository
from app.domain.repositories.session_repository import SessionRepository
from app.domain.models.session import SessionStatus
from app.domain.services.tools.mcp import MCPToolkit
from app.domain.services.tools.shell import ShellToolkit
from app.domain.services.tools.browser import BrowserToolkit
from app.domain.services.tools.file import FileToolkit
from app.domain.services.tools.message import MessageToolkit
from app.domain.services.tools.search import SearchToolkit

logger = logging.getLogger(__name__)


class PlanActState(TypedDict):
    """LangGraph state for the PlanAct flow."""
    message: Message
    plan: Optional[Plan]
    current_step: Optional[Step]
    should_wait: bool
    has_steps: bool


class PlanActFlow(BaseFlow):
    def __init__(
        self,
        agent_id: str,
        agent_repository: AgentRepository,
        session_id: str,
        session_repository: SessionRepository,
        sandbox: Sandbox,
        browser: Browser,
        mcp_tool: MCPToolkit,
        search_engine: Optional[SearchEngine] = None,
    ):
        self._agent_id = agent_id
        self._repository = agent_repository
        self._session_id = session_id
        self._session_repository = session_repository
        self.plan = None
        self._start_from_execute = False
        self._event_queue: asyncio.Queue = asyncio.Queue()

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
            tools=tools,
        )
        logger.debug(f"Created planner agent for Agent {self._agent_id}")

        self.executor = ExecutionAgent(
            agent_id=self._agent_id,
            agent_repository=self._repository,
            tools=tools,
        )
        logger.debug(f"Created execution agent for Agent {self._agent_id}")

        self._graph = self._build_graph()

    # ------------------------------------------------------------------
    # Graph construction
    # ------------------------------------------------------------------

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(PlanActState)

        graph.add_node("plan", self._plan_node)
        graph.add_node("execute", self._execute_node)
        graph.add_node("update", self._update_node)
        graph.add_node("summarize", self._summarize_node)
        graph.add_node("complete", self._complete_node)

        graph.add_conditional_edges(START, self._route_entry)
        graph.add_conditional_edges("plan", self._after_plan)
        graph.add_conditional_edges("execute", self._after_execute)
        graph.add_edge("update", "execute")
        graph.add_edge("summarize", "complete")
        graph.add_edge("complete", END)

        return graph.compile()

    # ------------------------------------------------------------------
    # Routing functions
    # ------------------------------------------------------------------

    def _route_entry(self, state: PlanActState) -> str:
        if self._start_from_execute:
            return "execute"
        return "plan"

    def _after_plan(self, state: PlanActState) -> str:
        if not state.get("has_steps", True):
            return "complete"
        return "execute"

    def _after_execute(self, state: PlanActState) -> str:
        if state.get("should_wait"):
            return END
        if state.get("current_step") is None:
            return "summarize"
        return "update"

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------

    async def _emit(self, event: BaseEvent) -> None:
        await self._event_queue.put(event)

    # ------------------------------------------------------------------
    # Graph nodes
    # ------------------------------------------------------------------

    async def _plan_node(self, state: PlanActState) -> dict:
        logger.info(f"Agent {self._agent_id} entering plan node")
        message = state["message"]
        plan = None

        async for event in self.planner.create_plan(message):
            if isinstance(event, PlanEvent) and event.status == PlanStatus.CREATED:
                plan = event.plan
                self.plan = plan
                logger.info(
                    f"Agent {self._agent_id} created plan with "
                    f"{len(plan.steps)} steps"
                )
                await self._emit(TitleEvent(title=plan.title))
                await self._emit(
                    MessageEvent(role="assistant", message=plan.message)
                )
            await self._emit(event)

        has_steps = plan is not None and len(plan.steps) > 0
        if not has_steps:
            logger.info(f"Agent {self._agent_id} created plan with no steps")

        return {"plan": plan, "has_steps": has_steps}

    async def _execute_node(self, state: PlanActState) -> dict:
        plan = state.get("plan") or self.plan
        if plan is None:
            logger.warning(f"Agent {self._agent_id} execute node has no plan")
            return {"current_step": None, "should_wait": False, "plan": plan}

        plan.status = ExecutionStatus.RUNNING
        step = plan.get_next_step()

        if not step:
            logger.info(
                f"Agent {self._agent_id} has no more steps to execute"
            )
            return {"current_step": None, "should_wait": False, "plan": plan}

        logger.info(
            f"Agent {self._agent_id} executing step {step.id}: "
            f"{step.description[:50]}..."
        )

        async for event in self.executor.execute_step(plan, step, state["message"]):
            await self._emit(event)
            if isinstance(event, WaitEvent):
                logger.info(f"Agent {self._agent_id} waiting for user input")
                return {
                    "current_step": step,
                    "should_wait": True,
                    "plan": plan,
                }

        await self.executor.compact_memory()
        logger.info(f"Agent {self._agent_id} completed step {step.id}")
        return {"current_step": step, "should_wait": False, "plan": plan}

    async def _update_node(self, state: PlanActState) -> dict:
        plan = state["plan"]
        step = state["current_step"]
        logger.info(f"Agent {self._agent_id} updating plan after step {step.id}")

        async for event in self.planner.update_plan(plan, step):
            await self._emit(event)

        logger.info(f"Agent {self._agent_id} plan update completed")
        return {"plan": plan}

    async def _summarize_node(self, state: PlanActState) -> dict:
        logger.info(f"Agent {self._agent_id} summarizing")

        async for event in self.executor.summarize():
            await self._emit(event)

        logger.info(f"Agent {self._agent_id} summarizing completed")
        return {}

    async def _complete_node(self, state: PlanActState) -> dict:
        plan = state.get("plan") or self.plan
        if plan:
            plan.status = ExecutionStatus.COMPLETED
            logger.info(f"Agent {self._agent_id} plan has been completed")
            await self._emit(
                PlanEvent(status=PlanStatus.COMPLETED, plan=plan)
            )
        await self._emit(DoneEvent())
        logger.info(f"Agent {self._agent_id} message processing completed")
        return {}

    # ------------------------------------------------------------------
    # Public interface (keeps BaseFlow contract)
    # ------------------------------------------------------------------

    async def run(self, message: Message) -> AsyncGenerator[BaseEvent, None]:
        session = await self._session_repository.find_by_id(self._session_id)
        if not session:
            raise ValueError(f"Session {self._session_id} not found")

        self._start_from_execute = False

        if session.status != SessionStatus.PENDING:
            logger.debug(
                f"Session {self._session_id} is not PENDING, rolling back"
            )
            await self.executor.roll_back(message)
            await self.planner.roll_back(message)

        if session.status == SessionStatus.RUNNING:
            logger.debug(f"Session {self._session_id} is RUNNING")

        if session.status == SessionStatus.WAITING:
            logger.debug(f"Session {self._session_id} is WAITING, resuming execution")
            self._start_from_execute = True

        await self._session_repository.update_status(
            self._session_id, SessionStatus.RUNNING
        )
        self.plan = session.get_last_plan()

        logger.info(
            f"Agent {self._agent_id} started processing message: "
            f"{message.message[:50]}..."
        )

        initial_state: PlanActState = {
            "message": message,
            "plan": self.plan,
            "current_step": None,
            "should_wait": False,
            "has_steps": True,
        }

        self._event_queue = asyncio.Queue()

        async def _run_graph():
            try:
                await self._graph.ainvoke(initial_state)
            except Exception as e:
                logger.exception(f"Agent {self._agent_id} graph execution error: {e}")
                await self._event_queue.put(
                    ErrorEvent(error=f"Graph execution error: {str(e)}")
                )
            finally:
                await self._event_queue.put(None)

        graph_task = asyncio.create_task(_run_graph())

        try:
            while True:
                event = await self._event_queue.get()
                if event is None:
                    break
                yield event
        finally:
            if not graph_task.done():
                graph_task.cancel()
                try:
                    await graph_task
                except asyncio.CancelledError:
                    pass

    def is_done(self) -> bool:
        return self._event_queue.empty()
