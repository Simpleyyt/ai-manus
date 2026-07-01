"""Unit tests for the AgentEngine seam.

These tests are self-contained (no running server, DB, or real LLM). They
verify:

1. The real LangChainAgentEngine tool-call loop (with the model call faked).
2. That PlanActFlow + planner/executor still drive the full plan-act cycle
   correctly against the framework-neutral AgentEngine port, using a scripted
   FakeAgentEngine.
3. That MCP tools are now invocable through the neutral ToolSpec path.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.domain.external.agent_engine import ResponseFormat
from app.domain.models.conversation import ChatMessage, Role, ToolCall
from app.domain.models.memory import Memory
from app.domain.models.message import Message
from app.domain.models.tool_result import ToolResult
from app.domain.models.tool_spec import ToolSpec
from app.domain.models.event import (
    MessageEvent,
    ToolEvent,
    ToolStatus,
    ErrorEvent,
    PlanEvent,
    PlanStatus,
    StepEvent,
    StepStatus,
)
from app.infrastructure.external.llm.langchain_agent_engine import LangChainAgentEngine


# --------------------------------------------------------------------------
# Fakes
# --------------------------------------------------------------------------

class FakeAgentRepository:
    """In-memory AgentRepository (only the memory methods are used)."""

    def __init__(self):
        self.memories = {}

    async def get_memory(self, agent_id, name):
        return self.memories.setdefault((agent_id, name), Memory(messages=[]))

    async def save_memory(self, agent_id, name, memory):
        self.memories[(agent_id, name)] = memory

    async def add_memory(self, agent_id, name, memory):
        self.memories[(agent_id, name)] = memory


class FakeSessionRepository:
    def __init__(self, session):
        self.session = session
        self.status_updates = []

    async def find_by_id(self, session_id):
        return self.session

    async def update_status(self, session_id, status):
        self.status_updates.append(status)
        self.session.status = status


class ScriptedFakeEngine:
    """An AgentEngine that returns pre-scripted assistant content per call.

    Mimics the seam contract: it appends the assistant message to the passed-in
    conversation and yields a final MessageEvent. It calls no LLM and no tool,
    which is exactly what lets us test the plan-act orchestration in isolation.
    """

    def __init__(self, scripted_contents):
        self._scripted = list(scripted_contents)
        self.inputs = []

    async def run(self, conversation, *, tools=(), response_format=ResponseFormat.TEXT, allow_tools=True):
        users = [m for m in conversation.get_messages() if m.role == Role.USER]
        self.inputs.append(users[-1].content if users else None)
        content = self._scripted.pop(0)
        conversation.add_message(ChatMessage(role=Role.ASSISTANT, content=content))
        yield MessageEvent(message=content)


# --------------------------------------------------------------------------
# 1. LangChainAgentEngine tool-call loop (real loop, faked model)
# --------------------------------------------------------------------------

def _make_engine_without_model():
    """Build a LangChainAgentEngine without constructing a real chat model."""
    engine = LangChainAgentEngine.__new__(LangChainAgentEngine)
    engine._model = None
    engine._max_iterations = 100
    engine._max_retries = 3
    engine._retry_interval = 0.0
    # Skip real tool binding; `_ask` is faked and ignores the chain.
    engine._bind = lambda tools, response_format, allow_tools: None
    return engine


def _scripted_ask(messages):
    """Return a fake `_ask` that pops neutral ChatMessages in order."""
    queue = list(messages)

    async def fake_ask(chain, conversation):
        return queue.pop(0)

    return fake_ask


def _conversation(*users):
    memory = Memory(messages=[ChatMessage(role=Role.SYSTEM, content="SYS")])
    for text in users:
        memory.add_message(ChatMessage(role=Role.USER, content=text))
    return memory


async def test_engine_runs_tool_then_finishes():
    engine = _make_engine_without_model()

    received_args = {}

    async def handler(args):
        received_args.update(args)
        return ToolResult(success=True, data={"echo": args})

    spec = ToolSpec(name="shell", description="run shell",
                    parameters={"type": "object", "properties": {}},
                    handler=handler, toolkit_name="shell")

    engine._ask = _scripted_ask([
        ChatMessage(role=Role.ASSISTANT, content="",
                    tool_calls=[ToolCall(id="c1", name="shell", arguments={"id": "s1"})]),
        ChatMessage(role=Role.ASSISTANT, content='{"done": true}'),
    ])

    conversation = _conversation("please run")
    events = [e async for e in engine.run(conversation, tools=[spec],
                                          response_format=ResponseFormat.JSON)]

    assert isinstance(events[0], ToolEvent) and events[0].status == ToolStatus.CALLING
    assert events[0].tool_name == "shell" and events[0].function_name == "shell"
    assert isinstance(events[1], ToolEvent) and events[1].status == ToolStatus.CALLED
    assert isinstance(events[1].function_result, ToolResult)
    assert isinstance(events[-1], MessageEvent) and events[-1].message == '{"done": true}'

    assert received_args == {"id": "s1"}

    roles = [m.role for m in conversation.get_messages()]
    assert roles == [Role.SYSTEM, Role.USER, Role.ASSISTANT, Role.TOOL, Role.ASSISTANT]
    assert conversation.messages[3].tool_call_id == "c1"


async def test_engine_unknown_tool_yields_error():
    engine = _make_engine_without_model()
    engine._ask = _scripted_ask([
        ChatMessage(role=Role.ASSISTANT, content="",
                    tool_calls=[ToolCall(id="c1", name="ghost", arguments={})]),
        ChatMessage(role=Role.ASSISTANT, content="final"),
    ])
    events = [e async for e in engine.run(_conversation("x"), tools=[])]
    assert any(isinstance(e, ErrorEvent) and "Unknown tool: ghost" in e.error for e in events)
    assert isinstance(events[-1], MessageEvent)


async def test_engine_max_iterations_yields_error():
    engine = _make_engine_without_model()
    engine._max_iterations = 1

    async def handler(args):
        return ToolResult(success=True, data="ok")

    spec = ToolSpec(name="shell", description="d", parameters={"type": "object", "properties": {}},
                    handler=handler, toolkit_name="shell")

    engine._ask = _scripted_ask([
        ChatMessage(role=Role.ASSISTANT, content="",
                    tool_calls=[ToolCall(id="c1", name="shell", arguments={})]),
        ChatMessage(role=Role.ASSISTANT, content="",
                    tool_calls=[ToolCall(id="c2", name="shell", arguments={})]),
    ])
    events = [e async for e in engine.run(_conversation("x"), tools=[spec])]
    assert any(isinstance(e, ErrorEvent) and "Maximum iteration" in e.error for e in events)


async def test_engine_tool_failure_returns_error_content():
    engine = _make_engine_without_model()
    engine._max_retries = 0

    async def handler(args):
        raise RuntimeError("boom")

    spec = ToolSpec(name="shell", description="d", parameters={"type": "object", "properties": {}},
                    handler=handler, toolkit_name="shell")

    engine._ask = _scripted_ask([
        ChatMessage(role=Role.ASSISTANT, content="",
                    tool_calls=[ToolCall(id="c1", name="shell", arguments={})]),
        ChatMessage(role=Role.ASSISTANT, content="done"),
    ])
    conversation = _conversation("x")
    events = [e async for e in engine.run(conversation, tools=[spec])]
    called = [e for e in events if isinstance(e, ToolEvent) and e.status == ToolStatus.CALLED]
    assert called and called[0].function_result is None
    tool_msgs = [m for m in conversation.get_messages() if m.role == Role.TOOL]
    assert tool_msgs and "boom" in tool_msgs[0].content


# --------------------------------------------------------------------------
# 2. PlanActFlow end-to-end against the AgentEngine port
# --------------------------------------------------------------------------

async def test_plan_act_flow_full_cycle_with_fake_engine():
    from app.domain.models.session import Session, SessionStatus
    from app.domain.services.flows.plan_act import PlanActFlow
    from app.domain.services.tools.mcp import MCPToolkit

    agent_id = "agent-1"
    session = Session(agent_id=agent_id, user_id="u1", status=SessionStatus.PENDING)

    agent_repo = FakeAgentRepository()
    session_repo = FakeSessionRepository(session)

    engine = ScriptedFakeEngine([
        # 1) planner.create_plan -> a plan with one pending step
        '{"title":"Demo","goal":"do X","language":"en","message":"here is the plan",'
        '"steps":[{"description":"step one"}]}',
        # 2) executor.execute_step -> step result
        '{"success":true,"result":"did step one","attachments":[]}',
        # 3) planner.update_plan -> plan echoed back (step now completed)
        '{"title":"Demo","goal":"do X","language":"en",'
        '"steps":[{"description":"step one","status":"completed","success":true}]}',
        # 4) executor.summarize -> final message
        '{"message":"all done","attachments":[]}',
    ])

    flow = PlanActFlow(
        agent_id=agent_id,
        agent_repository=agent_repo,
        session_id=session.id,
        session_repository=session_repo,
        sandbox=None,
        browser=None,
        mcp_tool=MCPToolkit(),
        engine=engine,
        search_engine=None,
    )

    events = [e async for e in flow.run(Message(message="do X"))]
    kinds = [type(e).__name__ for e in events]

    assert len(engine.inputs) == 4
    assert kinds == [
        "TitleEvent",
        "MessageEvent",   # plan.message
        "PlanEvent",      # CREATED
        "StepEvent",      # STARTED
        "StepEvent",      # COMPLETED
        "MessageEvent",   # step result
        "PlanEvent",      # UPDATED
        "MessageEvent",   # summary
        "PlanEvent",      # COMPLETED
        "DoneEvent",
    ]

    plan_events = [e for e in events if isinstance(e, PlanEvent)]
    assert plan_events[0].status == PlanStatus.CREATED
    assert plan_events[-1].status == PlanStatus.COMPLETED

    step_events = [e for e in events if isinstance(e, StepEvent)]
    assert step_events[0].status == StepStatus.STARTED
    assert step_events[1].status == StepStatus.COMPLETED

    assert SessionStatus.RUNNING in session_repo.status_updates

    planner_mem = agent_repo.memories[(agent_id, "planner")]
    exec_mem = agent_repo.memories[(agent_id, "execution")]
    assert all(isinstance(m, ChatMessage) for m in planner_mem.messages)
    assert all(isinstance(m, ChatMessage) for m in exec_mem.messages)


# --------------------------------------------------------------------------
# 3. MCP tools become invocable through the neutral ToolSpec path
# --------------------------------------------------------------------------

async def test_mcp_toolkit_produces_invocable_tool_specs():
    from app.domain.services.tools.mcp import MCPToolkit

    toolkit = MCPToolkit()
    toolkit._tools = [{
        "type": "function",
        "function": {
            "name": "mcp_echo",
            "description": "echo",
            "parameters": {"type": "object", "properties": {"text": {"type": "string"}}},
        },
    }]

    invoked = {}

    async def fake_invoke_function(function_name, **kwargs):
        invoked["name"] = function_name
        invoked["kwargs"] = kwargs
        return ToolResult(success=True, data=kwargs)

    toolkit.invoke_function = fake_invoke_function

    specs = toolkit.to_tool_specs()
    assert len(specs) == 1
    assert specs[0].name == "mcp_echo" and specs[0].toolkit_name == "mcp"

    result = await specs[0].handler({"text": "hi"})
    assert isinstance(result, ToolResult)
    assert invoked == {"name": "mcp_echo", "kwargs": {"text": "hi"}}
