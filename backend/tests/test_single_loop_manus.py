from typing import List

import pytest

from app.domain.models.agent_output import FinalResult
from app.domain.models.event import (
    DoneEvent,
    MessageEvent,
    PlanEvent,
    PlanStatus,
    TitleEvent,
    ToolEvent,
    ToolStatus,
    WaitEvent,
)
from app.domain.models.memory import Memory
from app.domain.models.message import LLMMessage, Message, Role, ToolCall
from app.domain.models.plan import ExecutionStatus, Plan, Step
from app.domain.models.session import SessionStatus
from app.domain.services.agents.manus import ManusAgent
from app.domain.services.agents.base import BaseAgent, StructuredOutputEvent
from app.domain.services.flows.agent_loop import AgentLoopFlow
from app.domain.services.tools.base import OutputTool
from app.domain.services.tools.message import MessageToolkit
from app.domain.services.tools.todo import TodoToolkit


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

    async def ask(self, messages, tools=None, response_format=None, tool_choice=None):
        return self.responses.pop(0)

    async def parse_json(self, text: str):
        raise AssertionError("parse_json must not be used by the agent loop")


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


@pytest.mark.asyncio
async def test_agent_loop_flow_fresh_message_runs_manus():
    agent_repository = FakeAgentRepository()
    session_repository = FakeSessionRepository(FakeSession())
    llm = ScriptedLLM([
        LLMMessage.assistant(
            tool_calls=[
                ToolCall(
                    id="result-1",
                    name="deliver_result",
                    args={"message": "Finished in one loop", "attachments": []},
                ),
            ]
        ),
    ])
    flow = AgentLoopFlow(
        agent_id="agent-1",
        agent_repository=agent_repository,
        session_id="session-1",
        session_repository=session_repository,
        sandbox=object(),
        browser=object(),
        mcp_tool=MessageToolkit(),
        llm=llm,
    )

    events = [event async for event in flow.run(Message(message="Do it"))]

    assert any(
        isinstance(event, MessageEvent)
        and event.message == "Finished in one loop"
        for event in events
    )
    assert isinstance(events[-1], DoneEvent)
    assert session_repository.status_updates == [SessionStatus.RUNNING]
    assert flow.is_done()


@pytest.mark.asyncio
async def test_agent_loop_flow_wait_does_not_emit_done():
    flow = AgentLoopFlow(
        agent_id="agent-1",
        agent_repository=FakeAgentRepository(),
        session_id="session-1",
        session_repository=FakeSessionRepository(FakeSession()),
        sandbox=object(),
        browser=object(),
        mcp_tool=MessageToolkit(),
        llm=ScriptedLLM([
            LLMMessage.assistant(
                tool_calls=[
                    ToolCall(
                        id="ask-1",
                        name="message_ask_user",
                        args={"text": "Which option?"},
                    ),
                ]
            ),
        ]),
    )

    events = [event async for event in flow.run(Message(message="Do it"))]

    assert any(isinstance(event, WaitEvent) for event in events)
    assert not any(isinstance(event, DoneEvent) for event in events)
    assert not flow.is_done()


@pytest.mark.asyncio
async def test_agent_loop_flow_waiting_session_rolls_back_resumes_and_rehydrates_todos():
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
    flow = AgentLoopFlow(
        agent_id="agent-1",
        agent_repository=agent_repository,
        session_id="session-1",
        session_repository=FakeSessionRepository(
            FakeSession(status=SessionStatus.WAITING, plan=plan)
        ),
        sandbox=object(),
        browser=object(),
        mcp_tool=MessageToolkit(),
        llm=ScriptedLLM([
            LLMMessage.assistant(
                tool_calls=[
                    ToolCall(
                        id="result-1",
                        name="deliver_result",
                        args={"message": "Used option B", "attachments": []},
                    ),
                ]
            ),
        ]),
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
    assert flow.agent._todo_items[0].content == "Choose the preferred option"
    assert flow.agent._todo_items[0].status.value == "in_progress"
    assert not any(
        message.role == Role.USER
        for message in memory.get_messages()
    )
    assert any(
        message.role == Role.TOOL and message.content == "Use option B"
        for message in memory.get_messages()
    )
    assert isinstance(events[-1], DoneEvent)


def test_agent_loop_flow_rehydrates_unsuccessful_completed_step_as_cancelled():
    plan = Plan(
        steps=[
            Step(
                id="cancelled",
                description="Skipped work",
                status=ExecutionStatus.COMPLETED,
                success=False,
            ),
        ],
    )

    todos = AgentLoopFlow._todos_from_plan(plan)

    assert todos[0].status.value == "cancelled"


@pytest.mark.asyncio
async def test_agent_loop_flow_completes_the_last_plan_when_agent_has_no_todos():
    last_plan = Plan(
        title="Existing plan",
        steps=[Step(id="existing", description="Existing step")],
    )
    flow = AgentLoopFlow(
        agent_id="agent-1",
        agent_repository=FakeAgentRepository(),
        session_id="session-1",
        session_repository=FakeSessionRepository(
            FakeSession(status=SessionStatus.RUNNING, plan=last_plan)
        ),
        sandbox=object(),
        browser=object(),
        mcp_tool=MessageToolkit(),
        llm=ScriptedLLM([
            LLMMessage.assistant(
                tool_calls=[
                    ToolCall(
                        id="result-1",
                        name="deliver_result",
                        args={"message": "Done", "attachments": []},
                    ),
                ]
            ),
        ]),
    )

    events = [event async for event in flow.run(Message(message="Continue"))]

    completed_plan = next(
        event for event in events
        if isinstance(event, PlanEvent) and event.status == PlanStatus.COMPLETED
    )
    assert completed_plan.plan.steps[0].id == "existing"


@pytest.mark.asyncio
async def test_agent_loop_flow_completed_plan_keeps_latest_todo_title_and_goal():
    flow = AgentLoopFlow(
        agent_id="agent-1",
        agent_repository=FakeAgentRepository(),
        session_id="session-1",
        session_repository=FakeSessionRepository(FakeSession()),
        sandbox=object(),
        browser=object(),
        mcp_tool=MessageToolkit(),
        llm=ScriptedLLM([
            LLMMessage.assistant(
                tool_calls=[
                    ToolCall(
                        id="todo-1",
                        name="todo_write",
                        args={
                            "items": [
                                {
                                    "id": "preserve",
                                    "content": "Preserve plan metadata",
                                    "status": "pending",
                                },
                            ],
                        },
                    ),
                ],
            ),
            LLMMessage.assistant(
                tool_calls=[
                    ToolCall(
                        id="result-1",
                        name="deliver_result",
                        args={"message": "Done", "attachments": []},
                    ),
                ],
            ),
        ]),
    )

    events = [event async for event in flow.run(Message(message="Do it"))]

    completed_plan = next(
        event for event in events
        if isinstance(event, PlanEvent) and event.status == PlanStatus.COMPLETED
    )
    assert completed_plan.plan.title == "Preserve plan metadata"
    assert completed_plan.plan.goal == "Preserve plan metadata"


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
async def test_manus_run_todo_then_deliver_emits_plan_and_message():
    repository = FakeAgentRepository()
    llm = ScriptedLLM([
        LLMMessage.assistant(
            tool_calls=[
                ToolCall(
                    id="todo-1",
                    name="todo_write",
                    args={
                        "items": [
                            {
                                "id": "research",
                                "content": "Research the requested topic",
                                "status": "in_progress",
                            }
                        ]
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
        tools=[TodoToolkit(), MessageToolkit()],
    )

    events = [event async for event in agent.run(Message(message="Research this"))]

    plan_event = next(event for event in events if isinstance(event, PlanEvent))
    assert plan_event.status == PlanStatus.CREATED
    assert plan_event.plan.steps[0].description == "Research the requested topic"
    assert any(
        isinstance(event, TitleEvent)
        and event.title == "Research the requested topic"
        for event in events
    )
    assert any(
        isinstance(event, MessageEvent)
        and event.message == "Research complete"
        for event in events
    )


@pytest.mark.asyncio
async def test_manus_invalid_todo_args_yields_tool_event_and_continues():
    repository = FakeAgentRepository()
    llm = ScriptedLLM([
        LLMMessage.assistant(
            tool_calls=[
                ToolCall(
                    id="todo-invalid",
                    name="todo_write",
                    args={
                        "items": [
                            {
                                "id": "research",
                                "status": "in_progress",
                            }
                        ]
                    },
                ),
            ]
        ),
        LLMMessage.assistant(
            tool_calls=[
                ToolCall(
                    id="result-1",
                    name="deliver_result",
                    args={"message": "Recovered and completed", "attachments": []},
                ),
            ]
        ),
    ])
    agent = ManusAgent(
        agent_id="agent-1",
        agent_repository=repository,
        llm=llm,
        tools=[TodoToolkit(), MessageToolkit()],
    )
    agent.max_retries = 0

    events = [event async for event in agent.run(Message(message="Research this"))]

    assert any(
        isinstance(event, ToolEvent)
        and event.function_name == "todo_write"
        and event.status == ToolStatus.CALLED
        for event in events
    )
    assert not any(isinstance(event, PlanEvent) for event in events)
    assert any(
        isinstance(event, MessageEvent)
        and event.message == "Recovered and completed"
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
        tools=[TodoToolkit(), MessageToolkit()],
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
        tools=[TodoToolkit(), MessageToolkit()],
    )

    events = [event async for event in agent.run(Message(message="Quick task"))]

    assert any(
        isinstance(event, TitleEvent) and event.title == "Quick task"
        for event in events
    )
