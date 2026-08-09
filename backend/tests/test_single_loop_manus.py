from typing import Any, List, Optional

import pytest

from app.domain.models.agent_output import FinalResult
from app.domain.models.event import (
    DoneEvent,
    MessageEvent,
    PlanEvent,
    PlanStatus,
    TitleEvent,
    ToolEvent,
    WaitEvent,
)
from app.domain.models.memory import Memory
from app.domain.models.message import LLMMessage, Message, Role, ToolCall
from app.domain.models.plan import ExecutionStatus, Plan, Step
from app.domain.models.session import SessionStatus
from app.domain.models.tool_result import ToolResult
from app.domain.services.agents.manus import ManusAgent
from app.domain.services.agents.base import BaseAgent, StructuredOutputEvent
from app.domain.services.flows.agent_loop import AgentLoopFlow
from app.domain.services.tools.base import OutputTool
from app.domain.services.tools.file import FileToolkit
from app.domain.services.tools.message import MessageToolkit
from app.domain.services.tools.plan import PlanToolkit


class FakeAgentRepository:
    def __init__(self) -> None:
        self.memories: dict[str, Memory] = {}

    @staticmethod
    def _key(agent_id: str, name: str) -> str:
        return f"{agent_id}:{name}"

    async def get_memory(self, agent_id: str, name: str) -> Memory:
        return self.memories.setdefault(self._key(agent_id, name), Memory())

    async def save_memory(self, agent_id: str, name: str, memory: Memory) -> None:
        self.memories[self._key(agent_id, name)] = memory


class ScriptedLLM:
    def __init__(self, responses: List[LLMMessage]) -> None:
        self.responses = list(responses)
        self.calls: list[list[LLMMessage]] = []

    async def ask(self, messages, tools=None, response_format=None, tool_choice=None):
        self.calls.append(list(messages))
        return self.responses.pop(0)

    async def parse_json(self, text: str):
        raise AssertionError("parse_json must not be used by the agent loop")


class FakeSandbox:
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
    def __init__(self, session: FakeSession) -> None:
        self.session = session
        self.status_updates: list[SessionStatus] = []

    async def find_by_id(self, session_id: str):
        return self.session

    async def update_status(self, session_id: str, status: SessionStatus) -> None:
        self.status_updates.append(status)


class TestAgent(BaseAgent):
    name = "test"

    def build_system_prompt(self) -> str:
        return "test system prompt"


DELIVER_RESULT = OutputTool(
    name="deliver_result",
    description="Deliver the final result.",
    schema=FinalResult,
)

def _flow(
    llm: ScriptedLLM,
    *,
    session: Optional[FakeSession] = None,
    agent_repository: Optional[FakeAgentRepository] = None,
) -> AgentLoopFlow:
    return AgentLoopFlow(
        agent_id="agent-1",
        agent_repository=agent_repository or FakeAgentRepository(),
        session_id="session-1",
        session_repository=FakeSessionRepository(session or FakeSession()),
        sandbox=FakeSandbox(),
        browser=object(),
        mcp_tool=MessageToolkit(),
        llm=llm,
    )


@pytest.mark.asyncio
async def test_agent_loop_flow_create_plan_then_manus_deliver():
    llm = ScriptedLLM([
        LLMMessage.assistant(tool_calls=[
            ToolCall(
                id="plan-1",
                name="create_plan",
                args={
                    "message": "I will do the work.",
                    "language": "en",
                    "title": "Do the work",
                    "goal": "Finish the requested work",
                    "steps": [{"id": "1", "description": "Do the work"}],
                },
            ),
        ]),
        LLMMessage.assistant(tool_calls=[
            ToolCall(
                id="notify-1",
                name="message_notify_user",
                args={"text": "Starting now."},
            ),
        ]),
        LLMMessage.assistant(tool_calls=[
            ToolCall(
                id="report-1",
                name="plan_report",
                args={
                    "steps": [{
                        "id": "1",
                        "status": "completed",
                        "reflection": "Work finished",
                    }],
                    "reflection": "All work complete",
                },
            ),
        ]),
        LLMMessage.assistant(tool_calls=[
            ToolCall(
                id="result-1",
                name="deliver_result",
                args={"message": "Finished in one loop", "attachments": []},
            ),
        ]),
    ])
    flow = _flow(llm)

    events = []
    created_step_status = None
    async for event in flow.run(Message(message="Do it")):
        if isinstance(event, PlanEvent) and event.status == PlanStatus.CREATED:
            created_step_status = event.plan.steps[0].status
        events.append(event)

    plan_events = [event for event in events if isinstance(event, PlanEvent)]
    assert [event.status for event in plan_events] == [
        PlanStatus.CREATED,
        PlanStatus.UPDATED,
        PlanStatus.COMPLETED,
    ]
    assert created_step_status == ExecutionStatus.RUNNING
    assert plan_events[1].plan.steps[0].result == "Work finished"
    assert any(
        isinstance(event, TitleEvent) and event.title == "Do the work"
        for event in events
    )
    assert any(
        isinstance(event, MessageEvent)
        and event.message == "Finished in one loop"
        for event in events
    )
    assert not any(
        isinstance(event, ToolEvent)
        and event.function_name in {"plan_report", "replan"}
        for event in events
    )
    assert isinstance(events[-1], DoneEvent)
    assert flow.is_done()
    assert llm.responses == []


@pytest.mark.asyncio
async def test_agent_loop_flow_empty_plan_skips_manus():
    llm = ScriptedLLM([
        LLMMessage.assistant(tool_calls=[
            ToolCall(
                id="plan-1",
                name="create_plan",
                args={
                    "message": "This needs no tool work.",
                    "language": "en",
                    "title": "Direct answer",
                    "goal": "",
                    "steps": [],
                },
            ),
        ]),
    ])
    flow = _flow(llm)

    events = [event async for event in flow.run(Message(message="Answer it"))]

    assert any(
        isinstance(event, MessageEvent)
        and event.message == "This needs no tool work."
        for event in events
    )
    assert [event.status for event in events if isinstance(event, PlanEvent)] == [
        PlanStatus.CREATED,
        PlanStatus.COMPLETED,
    ]
    assert not any(isinstance(event, ToolEvent) for event in events)
    assert isinstance(events[-1], DoneEvent)
    assert llm.responses == []


@pytest.mark.asyncio
async def test_agent_loop_flow_replan_is_intercepted_and_uses_planner():
    llm = ScriptedLLM([
        LLMMessage.assistant(tool_calls=[
            ToolCall(
                id="plan-1",
                name="create_plan",
                args={
                    "message": "I will investigate.",
                    "language": "en",
                    "title": "Investigate",
                    "goal": "Resolve the issue",
                    "steps": [{"id": "1", "description": "Try the original route"}],
                },
            ),
        ]),
        LLMMessage.assistant(tool_calls=[
            ToolCall(
                id="notify-1",
                name="message_notify_user",
                args={"text": "Starting the investigation."},
            ),
        ]),
        LLMMessage.assistant(tool_calls=[
            ToolCall(
                id="replan-1",
                name="replan",
                args={"reason": "The original route is unavailable"},
            ),
        ]),
        LLMMessage.assistant(tool_calls=[
            ToolCall(
                id="update-1",
                name="update_plan",
                args={
                    "steps": [
                        {"id": "2", "description": "Use the fallback route"},
                    ],
                },
            ),
        ]),
        LLMMessage.assistant(tool_calls=[
            ToolCall(
                id="result-1",
                name="deliver_result",
                args={"message": "Resolved with fallback", "attachments": []},
            ),
        ]),
    ])
    flow = _flow(llm)

    events = [event async for event in flow.run(Message(message="Investigate"))]

    updated = next(
        event for event in events
        if isinstance(event, PlanEvent) and event.status == PlanStatus.UPDATED
    )
    assert updated.plan.steps[0].id == "2"
    assert not any(
        isinstance(event, ToolEvent) and event.function_name == "replan"
        for event in events
    )
    replan_tool_reply = next(
        message for message in llm.calls[-1]
        if message.role == Role.TOOL and message.name == "replan"
    )
    assert "Use the fallback route" in replan_tool_reply.content
    assert isinstance(events[-1], DoneEvent)
    assert llm.responses == []


@pytest.mark.asyncio
async def test_agent_loop_flow_invalid_plan_report_allows_model_repair():
    llm = ScriptedLLM([
        LLMMessage.assistant(tool_calls=[
            ToolCall(
                id="plan-1",
                name="create_plan",
                args={
                    "message": "I will do the work.",
                    "language": "en",
                    "title": "Repair report",
                    "goal": "Finish safely",
                    "steps": [{"id": "1", "description": "Do the work"}],
                },
            ),
        ]),
        LLMMessage.assistant(tool_calls=[
            ToolCall(
                id="notify-1",
                name="message_notify_user",
                args={"text": "Starting."},
            ),
        ]),
        LLMMessage.assistant(tool_calls=[
            ToolCall(
                id="bad-report",
                name="plan_report",
                args={"steps": [{"id": "1", "status": "not-a-status"}]},
            ),
        ]),
        LLMMessage.assistant(tool_calls=[
            ToolCall(
                id="good-report",
                name="plan_report",
                args={"steps": [{"id": "1", "status": "completed"}]},
            ),
        ]),
        LLMMessage.assistant(tool_calls=[
            ToolCall(
                id="result-1",
                name="deliver_result",
                args={"message": "Recovered", "attachments": []},
            ),
        ]),
    ])
    flow = _flow(llm)
    flow.agent.max_retries = 0

    events = [event async for event in flow.run(Message(message="Do it"))]

    assert any(
        isinstance(event, PlanEvent) and event.status == PlanStatus.UPDATED
        for event in events
    )
    assert isinstance(events[-1], DoneEvent)
    assert llm.responses == []


@pytest.mark.asyncio
async def test_agent_loop_flow_invalid_replan_allows_model_repair():
    llm = ScriptedLLM([
        LLMMessage.assistant(tool_calls=[
            ToolCall(
                id="plan-1",
                name="create_plan",
                args={
                    "message": "I will do the work.",
                    "language": "en",
                    "title": "Repair replan",
                    "goal": "Finish safely",
                    "steps": [{"id": "1", "description": "Do the work"}],
                },
            ),
        ]),
        LLMMessage.assistant(tool_calls=[
            ToolCall(
                id="notify-1",
                name="message_notify_user",
                args={"text": "Starting."},
            ),
        ]),
        LLMMessage.assistant(tool_calls=[
            ToolCall(id="bad-replan", name="replan", args={"reason": ""}),
        ]),
        LLMMessage.assistant(tool_calls=[
            ToolCall(
                id="result-1",
                name="deliver_result",
                args={"message": "Recovered", "attachments": []},
            ),
        ]),
    ])
    flow = _flow(llm)
    flow.agent.max_retries = 0

    events = [event async for event in flow.run(Message(message="Do it"))]

    assert any(
        isinstance(event, MessageEvent) and event.message == "Recovered"
        for event in events
    )
    assert isinstance(events[-1], DoneEvent)
    assert llm.responses == []


@pytest.mark.asyncio
async def test_agent_loop_flow_replan_after_all_steps_completed_keeps_new_steps():
    llm = ScriptedLLM([
        LLMMessage.assistant(tool_calls=[
            ToolCall(
                id="plan-1",
                name="create_plan",
                args={
                    "message": "I will investigate.",
                    "language": "en",
                    "title": "Extend work",
                    "goal": "Complete all required work",
                    "steps": [{"id": "1", "description": "Initial check"}],
                },
            ),
        ]),
        LLMMessage.assistant(tool_calls=[
            ToolCall(
                id="notify-1",
                name="message_notify_user",
                args={"text": "Starting."},
            ),
        ]),
        LLMMessage.assistant(tool_calls=[
            ToolCall(
                id="report-1",
                name="plan_report",
                args={"steps": [{"id": "1", "status": "completed"}]},
            ),
        ]),
        LLMMessage.assistant(tool_calls=[
            ToolCall(
                id="replan-1",
                name="replan",
                args={"reason": "A follow-up is required"},
            ),
        ]),
        LLMMessage.assistant(tool_calls=[
            ToolCall(
                id="update-1",
                name="update_plan",
                args={"steps": [{"id": "2", "description": "Follow up"}]},
            ),
        ]),
        LLMMessage.assistant(tool_calls=[
            ToolCall(
                id="result-1",
                name="deliver_result",
                args={"message": "Follow-up complete", "attachments": []},
            ),
        ]),
    ])
    flow = _flow(llm)

    events = [event async for event in flow.run(Message(message="Investigate"))]

    replanned = [
        event for event in events
        if isinstance(event, PlanEvent) and event.status == PlanStatus.UPDATED
    ][-1]
    assert [step.id for step in replanned.plan.steps] == ["1", "2"]
    assert isinstance(events[-1], DoneEvent)


@pytest.mark.asyncio
async def test_agent_loop_flow_wait_does_not_emit_done():
    flow = _flow(ScriptedLLM([
        LLMMessage.assistant(tool_calls=[
            ToolCall(
                id="plan-1",
                name="create_plan",
                args={
                    "message": "I need one choice.",
                    "language": "en",
                    "title": "Choose",
                    "goal": "Use the selected option",
                    "steps": [{"id": "1", "description": "Use the option"}],
                },
            ),
        ]),
        LLMMessage.assistant(
            tool_calls=[
                ToolCall(
                    id="ask-1",
                    name="message_ask_user",
                    args={"text": "Which option?"},
                ),
            ]
        ),
    ]))

    events = [event async for event in flow.run(Message(message="Do it"))]

    assert any(isinstance(event, WaitEvent) for event in events)
    assert not any(isinstance(event, DoneEvent) for event in events)
    assert not any(
        isinstance(event, PlanEvent) and event.status == PlanStatus.COMPLETED
        for event in events
    )
    assert not flow.is_done()


@pytest.mark.asyncio
async def test_agent_loop_waiting_resume_skips_create_plan():
    agent_repository = FakeAgentRepository()
    memory = Memory(messages=[
        LLMMessage.system("old system prompt"),
        LLMMessage.assistant(
            tool_calls=[
                ToolCall(
                    id="ask-1",
                    name="message_ask_user",
                    args={"text": "Which option?"},
                ),
            ]
        ),
    ])
    await agent_repository.save_memory("agent-1", ManusAgent.name, memory)
    plan = Plan(
        title="Choose an option",
        steps=[
            Step(
                id="choose",
                description="Choose the preferred option",
                status=ExecutionStatus.RUNNING,
            ),
        ],
    )
    llm = ScriptedLLM([
            LLMMessage.assistant(
                tool_calls=[
                    ToolCall(
                        id="result-1",
                        name="deliver_result",
                        args={"message": "Used option B", "attachments": []},
                    ),
                ]
            ),
        ])
    flow = _flow(
        llm,
        session=FakeSession(status=SessionStatus.WAITING, plan=plan),
        agent_repository=agent_repository,
    )

    events = [
        event async for event in flow.run(Message(message="Use option B"))
    ]

    assert any(
        isinstance(event, MessageEvent) and event.message == "Used option B"
        for event in events
    )
    completed_plan = next(
        event for event in events
        if isinstance(event, PlanEvent) and event.status == PlanStatus.COMPLETED
    )
    assert completed_plan.plan.steps[0].id == "choose"
    assert completed_plan.plan.steps[0].status == ExecutionStatus.COMPLETED
    assert not any(
        message.role == Role.USER
        for message in memory.get_messages()
    )
    assert any(
        message.role == Role.TOOL and message.content == "Use option B"
        for message in memory.get_messages()
    )
    assert isinstance(events[-1], DoneEvent)
    assert llm.responses == []
@pytest.mark.asyncio
async def test_continue_execute_does_not_append_user_message():
    """Continuing after a tool reply must not insert another user turn."""
    repository = FakeAgentRepository()
    memory = Memory(messages=[
        LLMMessage.system("test system prompt"),
        LLMMessage.user("original request"),
        LLMMessage.assistant(
            tool_calls=[
                ToolCall(id="ask-1", name="message_ask_user", args={"text": "Which?"}),
            ]
        ),
        LLMMessage.tool(
            tool_call_id="ask-1",
            name="message_ask_user",
            content="Use option B",
        ),
    ])
    await repository.save_memory("agent-1", TestAgent.name, memory)
    llm = ScriptedLLM([
        LLMMessage.assistant(
            tool_calls=[
                ToolCall(
                    id="result-1",
                    name="deliver_result",
                    args={"message": "Done with option B", "attachments": []},
                ),
            ]
        ),
    ])
    agent = TestAgent(
        agent_id="agent-1",
        agent_repository=repository,
        llm=llm,
    )
    user_messages_before = sum(
        message.role == Role.USER for message in memory.get_messages()
    )

    events = [
        event async for event in agent.continue_execute(output_tool=DELIVER_RESULT)
    ]

    user_messages_after = sum(
        message.role == Role.USER for message in memory.get_messages()
    )
    assert user_messages_after == user_messages_before
    assert any(isinstance(event, StructuredOutputEvent) for event in events)


@pytest.mark.asyncio
async def test_manus_run_todo_md_does_not_emit_plan():
    """todo.md is a normal file write — no checklist parsing / Plan projection."""
    repository = FakeAgentRepository()
    llm = ScriptedLLM([
        LLMMessage.assistant(
            tool_calls=[
                ToolCall(
                    id="n1",
                    name="message_notify_user",
                    args={"text": "I'll research this."},
                ),
                ToolCall(
                    id="todo-md",
                    name="file_write",
                    args={
                        "file": "/home/ubuntu/todo.md",
                        "content": "# Plan\n- [~] Research\n- [ ] Deliver\n",
                    },
                ),
            ]
        ),
        LLMMessage.assistant(
            tool_calls=[
                ToolCall(
                    id="result-1",
                    name="deliver_result",
                    args={"message": "Research complete", "attachments": []},
                ),
            ]
        ),
    ])
    agent = ManusAgent(
        agent_id="agent-1",
        agent_repository=repository,
        llm=llm,
        tools=[FileToolkit(FakeSandbox()), MessageToolkit()],
    )

    events = [event async for event in agent.run(Message(message="Research this"))]

    assert not any(isinstance(event, PlanEvent) for event in events)
    assert any(
        isinstance(event, TitleEvent) and event.title == "Research this"
        for event in events
    )
    assert any(
        isinstance(event, MessageEvent)
        and event.message == "Research complete"
        for event in events
    )
    assert any(
        isinstance(event, ToolEvent) and event.function_name == "file_write"
        for event in events
    )


@pytest.mark.asyncio
async def test_manus_ask_user_yields_wait_and_stops():
    repository = FakeAgentRepository()
    llm = ScriptedLLM([
        LLMMessage.assistant(
            tool_calls=[
                ToolCall(
                    id="ask-1",
                    name="message_ask_user",
                    args={"text": "Which option should I use?"},
                ),
            ]
        ),
    ])
    agent = ManusAgent(
        agent_id="agent-1",
        agent_repository=repository,
        llm=llm,
        tools=[MessageToolkit()],
    )

    events = [event async for event in agent.run(Message(message="Do the task"))]

    assert any(
        isinstance(event, MessageEvent)
        and event.message == "Which option should I use?"
        for event in events
    )
    assert any(isinstance(event, WaitEvent) for event in events)


@pytest.mark.asyncio
async def test_manus_emits_fallback_title_when_delivering_without_todos():
    repository = FakeAgentRepository()
    llm = ScriptedLLM([
        LLMMessage.assistant(
            tool_calls=[
                ToolCall(
                    id="result-1",
                    name="deliver_result",
                    args={"message": "Done", "attachments": []},
                ),
            ]
        ),
    ])
    agent = ManusAgent(
        agent_id="agent-1",
        agent_repository=repository,
        llm=llm,
        tools=[MessageToolkit()],
    )

    events = [event async for event in agent.run(Message(message="Quick task"))]

    assert any(
        isinstance(event, TitleEvent) and event.title == "Quick task"
        for event in events
    )


@pytest.mark.asyncio
async def test_manus_plan_report_yields_tool_event_after_notify():
    """Manus yields plan_report ToolEvents for Flow interception; does not swallow."""
    repository = FakeAgentRepository()
    llm = ScriptedLLM([
        LLMMessage.assistant(
            tool_calls=[
                ToolCall(
                    id="n1",
                    name="message_notify_user",
                    args={"text": "Starting the planned work."},
                ),
                ToolCall(
                    id="report-1",
                    name="plan_report",
                    args={
                        "steps": [{"id": "1", "status": "running"}],
                        "reflection": "",
                    },
                ),
            ]
        ),
        LLMMessage.assistant(
            tool_calls=[
                ToolCall(
                    id="result-1",
                    name="deliver_result",
                    args={"message": "Done", "attachments": []},
                ),
            ]
        ),
    ])
    agent = ManusAgent(
        agent_id="agent-1",
        agent_repository=repository,
        llm=llm,
        tools=[MessageToolkit(), PlanToolkit()],
    )

    events = [event async for event in agent.run(Message(message="Do the plan"))]

    plan_report_events = [
        event
        for event in events
        if isinstance(event, ToolEvent) and event.function_name == "plan_report"
    ]
    assert len(plan_report_events) >= 1
    assert not any(isinstance(event, PlanEvent) for event in events)


@pytest.mark.asyncio
async def test_manus_blocks_plan_report_until_notify():
    repository = FakeAgentRepository()
    plan_toolkit = PlanToolkit()
    agent = ManusAgent(
        agent_id="agent-1",
        agent_repository=repository,
        llm=ScriptedLLM([]),
        tools=[plan_toolkit],
    )

    blocked = await agent.invoke_tool(
        plan_toolkit.get_tool("plan_report"),
        ToolCall(
            id="report-1",
            name="plan_report",
            args={"steps": [{"id": "1", "status": "running"}]},
        ),
    )
    assert "message_notify_user" in blocked.content


@pytest.mark.asyncio
async def test_manus_blocks_work_tools_until_notify():
    repository = FakeAgentRepository()
    agent = ManusAgent(
        agent_id="agent-1",
        agent_repository=repository,
        llm=ScriptedLLM([]),
        tools=[FileToolkit(FakeSandbox())],
    )

    class StubWorkTool:
        name = "file_write"
        called = False

        async def invoke(self, args):
            self.called = True
            return ToolResult(success=True, message="written")

    work = StubWorkTool()
    blocked = await agent.invoke_tool(
        work,
        ToolCall(id="fw-1", name="file_write", args={"file": "/tmp/x", "content": "x"}),
    )
    assert work.called is False
    assert "message_notify_user" in blocked.content

    agent._user_notified = True
    allowed = await agent.invoke_tool(
        work,
        ToolCall(id="fw-2", name="file_write", args={"file": "/tmp/x", "content": "x"}),
    )
    assert work.called is True
    assert "written" in allowed.content


@pytest.mark.asyncio
async def test_manus_notify_surfaces_as_message_event():
    repository = FakeAgentRepository()
    llm = ScriptedLLM([
        LLMMessage.assistant(
            tool_calls=[
                ToolCall(
                    id="n1",
                    name="message_notify_user",
                    args={"text": "好的，我来写一个 Python 示例。"},
                ),
                ToolCall(
                    id="r1",
                    name="deliver_result",
                    args={"message": "完成", "attachments": []},
                ),
            ]
        ),
    ])
    agent = ManusAgent(
        agent_id="agent-1",
        agent_repository=repository,
        llm=llm,
        tools=[MessageToolkit()],
    )

    events = [event async for event in agent.run(Message(message="写一个 python 示例"))]

    assert any(
        isinstance(event, MessageEvent)
        and event.message == "好的，我来写一个 Python 示例。"
        for event in events
    )
    assert agent._user_notified is True
    assert not any(
        isinstance(event, ToolEvent) and event.function_name == "message_notify_user"
        for event in events
    )
