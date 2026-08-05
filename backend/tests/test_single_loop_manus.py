from typing import List

import pytest

from app.domain.models.agent_output import FinalResult
from app.domain.models.event import MessageEvent, PlanEvent, PlanStatus, TitleEvent, WaitEvent
from app.domain.models.memory import Memory
from app.domain.models.message import LLMMessage, Message, Role, ToolCall
from app.domain.services.agents.manus import ManusAgent
from app.domain.services.agents.base import BaseAgent, StructuredOutputEvent
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
async def test_manus_does_not_emit_title_without_a_created_plan():
    repository = FakeAgentRepository()
    llm = ScriptedLLM([
        LLMMessage.assistant(
            tool_calls=[
                ToolCall(
                    id="todo-1",
                    name="todo_write",
                    args={"items": []},
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
        tools=[TodoToolkit(), MessageToolkit()],
    )

    events = [event async for event in agent.run(Message(message="Quick task"))]

    assert not any(isinstance(event, TitleEvent) for event in events)
