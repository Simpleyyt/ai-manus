"""Shared offline test harness for the agent framework.

Reusable fakes that satisfy the ``domain/external`` Protocols and the
repository interfaces, so flows and agents can be driven entirely offline
(no MongoDB / Redis / sandbox / LLM). Import these instead of redefining
them per test module:

    from tests.harness import (
        FakeAgentRepository, FakeSandbox, FakeSession, FakeSessionRepository,
        ScriptedLLM, StubAgent, build_agent_loop_flow, build_plan_act_flow,
        collect, create_plan_call,
    )

See ``.cursor/skills/harness/SKILL.md`` for the full harness-coding guide
(file map, invariants, extension recipes, testing pyramid).
"""

from typing import Any, List, Optional

from app.domain.models.memory import Memory
from app.domain.models.message import LLMMessage, ToolCall
from app.domain.models.plan import Plan
from app.domain.models.session import SessionStatus
from app.domain.models.tool_result import ToolResult
from app.domain.services.agents.base import BaseAgent
from app.domain.services.flows.agent_loop import AgentLoopFlow
from app.domain.services.flows.plan_act import PlanActFlow
from app.domain.services.tools.message import MessageToolkit


class ScriptedLLM:
    """LLM stub that returns scripted assistant messages in order.

    Records every request so tests can assert on what the model saw:

    - ``asked_tool_names``: comma-joined tool names offered per call
    - ``calls``: message list per call
    - ``requests``: full ``{"messages", "tools", "tool_choice"}`` per call
    """

    def __init__(self, responses: List[LLMMessage]) -> None:
        self.responses = list(responses)
        self.asked_tool_names: list[str] = []
        self.calls: list[list[LLMMessage]] = []
        self.requests: list[dict] = []

    async def ask(self, messages, tools=None, response_format=None, tool_choice=None):
        names: list[str] = []
        for tool in tools or []:
            fn = (tool.get("function") or {}) if isinstance(tool, dict) else {}
            name = fn.get("name") or tool.get("name")
            if name:
                names.append(name)
        self.asked_tool_names.append(",".join(names))
        self.calls.append(list(messages))
        self.requests.append({
            "messages": list(messages),
            "tools": tools,
            "tool_choice": tool_choice,
        })
        return self.responses.pop(0)

    async def parse_json(self, text: str):
        raise AssertionError("parse_json must not be used by the agent loop")


class FakeAgentRepository:
    """In-memory AgentRepository keyed by ``agent_id:name``."""

    def __init__(self) -> None:
        self.memories: dict[str, Memory] = {}

    @staticmethod
    def _key(agent_id: str, name: str) -> str:
        return f"{agent_id}:{name}"

    async def get_memory(self, agent_id: str, name: str) -> Memory:
        return self.memories.setdefault(self._key(agent_id, name), Memory())

    async def save_memory(self, agent_id: str, name: str, memory: Memory) -> None:
        self.memories[self._key(agent_id, name)] = memory


class FakeSandbox:
    """Sandbox stub: file ops succeed, shell ops succeed and are counted."""

    def __init__(self) -> None:
        self.shell_exec_calls = 0

    async def file_write(self, **kwargs: Any) -> ToolResult:
        return ToolResult(success=True, message="written")

    async def file_read(self, **kwargs: Any) -> ToolResult:
        return ToolResult(success=True, message="ok", data="")

    async def file_str_replace(self, **kwargs: Any) -> ToolResult:
        return ToolResult(success=True, message="replaced")

    async def file_find_in_content(self, **kwargs: Any) -> ToolResult:
        return ToolResult(success=True, data=[])

    async def file_find_by_name(self, **kwargs: Any) -> ToolResult:
        return ToolResult(success=True, data=[])

    async def exec_command(self, id: str, exec_dir: str, command: str) -> ToolResult:
        self.shell_exec_calls += 1
        return ToolResult(success=True, message="Command executed", data={})

    async def view_shell(self, id: str, console: bool = False) -> ToolResult:
        return ToolResult(success=True, data={"console": []})

    async def wait_for_process(self, id: str, seconds: int | None = None) -> ToolResult:
        return ToolResult(success=True, data={})

    async def write_to_process(
        self, id: str, input: str, press_enter: bool = True
    ) -> ToolResult:
        return ToolResult(success=True, data={})

    async def kill_process(self, id: str) -> ToolResult:
        return ToolResult(success=True, data={})


class FakeSession:
    def __init__(
        self,
        status: SessionStatus = SessionStatus.PENDING,
        plan: Plan | None = None,
    ) -> None:
        self.status = status
        self.project_id = None
        self.plan = plan

    def get_last_plan(self):
        return self.plan


class FakeSessionRepository:
    """SessionRepository stub: mutates the session and records every update."""

    def __init__(self, session: FakeSession) -> None:
        self.session = session
        self.status_updates: list[SessionStatus] = []

    async def find_by_id(self, session_id: str):
        return self.session

    async def update_status(self, session_id: str, status: SessionStatus) -> None:
        self.session.status = status
        self.status_updates.append(status)


class StubAgent(BaseAgent):
    """Minimal concrete BaseAgent for unit-testing the tool loop directly."""

    name = "test"

    def build_system_prompt(self) -> str:
        return "test system prompt"


def build_plan_act_flow(
    llm: ScriptedLLM,
    *,
    session: Optional[FakeSession] = None,
    agent_repository: Optional[FakeAgentRepository] = None,
    sandbox: Optional[FakeSandbox] = None,
) -> PlanActFlow:
    return PlanActFlow(
        agent_id="agent-1",
        agent_repository=agent_repository or FakeAgentRepository(),
        session_id="session-1",
        session_repository=FakeSessionRepository(session or FakeSession()),
        sandbox=sandbox or FakeSandbox(),
        browser=object(),
        mcp_tool=MessageToolkit(),
        llm=llm,
    )


def build_agent_loop_flow(
    llm: ScriptedLLM,
    *,
    session: Optional[FakeSession] = None,
    agent_repository: Optional[FakeAgentRepository] = None,
    sandbox: Optional[FakeSandbox] = None,
) -> AgentLoopFlow:
    return AgentLoopFlow(
        agent_id="agent-1",
        agent_repository=agent_repository or FakeAgentRepository(),
        session_id="session-1",
        session_repository=FakeSessionRepository(session or FakeSession()),
        sandbox=sandbox or FakeSandbox(),
        browser=object(),
        mcp_tool=MessageToolkit(),
        llm=llm,
    )


def create_plan_call(
    *,
    call_id: str = "plan-1",
    message: str = "I will do the work.",
    title: str = "Do the work",
    goal: str = "Finish",
    steps: Optional[List[dict]] = None,
) -> ToolCall:
    """Factory for the ``create_plan`` output-tool call Planner scripts start with."""
    return ToolCall(
        id=call_id,
        name="create_plan",
        args={
            "message": message,
            "language": "en",
            "title": title,
            "goal": goal,
            "steps": [{"id": "1", "description": "Do the work"}]
            if steps is None
            else steps,
        },
    )


async def collect(gen) -> list:
    """Drain an async event generator into a list."""
    return [event async for event in gen]
