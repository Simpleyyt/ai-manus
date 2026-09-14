"""Plan-Act state machine (scheme C) smoke tests."""

from typing import Optional

import pytest

from app.domain.models.event import (
    DoneEvent,
    MessageEvent,
    PlanEvent,
    PlanStatus,
    StepEvent,
    StepStatus,
    WaitEvent,
)
from app.domain.models.message import LLMMessage, Message, ToolCall
from app.domain.services.flows.plan_act import PlanActFlow

from tests.harness import FakeSession, ScriptedLLM, build_plan_act_flow


def _flow(llm: ScriptedLLM, session: Optional[FakeSession] = None) -> PlanActFlow:
    return build_plan_act_flow(llm, session=session)


def _has_update_plan_call(llm: ScriptedLLM) -> bool:
    return any("update_plan" in names for names in llm.asked_tool_names)


def _file_write(call_id: str = "write-1") -> ToolCall:
    return ToolCall(
        id=call_id,
        name="file_write",
        args={"file": "/home/ubuntu/out.txt", "content": "work"},
    )


@pytest.mark.asyncio
async def test_plan_act_one_step_then_summarize():
    """Successful step still runs deliver_result summarize (no skip)."""
    llm = ScriptedLLM([
        LLMMessage.assistant(tool_calls=[
            ToolCall(
                id="plan-1",
                name="create_plan",
                args={
                    "message": "I will do the work.",
                    "language": "en",
                    "title": "Do the work",
                    "goal": "Finish",
                    "steps": [{"id": "1", "description": "Do the work"}],
                },
            ),
        ]),
        LLMMessage.assistant(tool_calls=[_file_write("w1")]),
        LLMMessage.assistant(tool_calls=[
            ToolCall(
                id="done-1",
                name="complete_step",
                args={
                    "success": True,
                    "result": "Step finished",
                    "attachments": ["/home/ubuntu/out.txt"],
                },
            ),
        ]),
        LLMMessage.assistant(tool_calls=[
            ToolCall(
                id="sum-1",
                name="deliver_result",
                args={"message": "All done", "attachments": ["/home/ubuntu/out.txt"]},
            ),
        ]),
    ])
    flow = _flow(llm)
    events = [event async for event in flow.run(Message(message="Do it"))]

    assert any(
        isinstance(e, MessageEvent) and e.message == "All done" for e in events
    )
    assert any(
        isinstance(e, PlanEvent) and e.status == PlanStatus.COMPLETED for e in events
    )
    assert isinstance(events[-1], DoneEvent)
    assert flow.is_done()
    assert llm.responses == []
    assert any("deliver_result" in names for names in llm.asked_tool_names)
    assert _has_update_plan_call(llm) is False


@pytest.mark.asyncio
async def test_plan_act_rejects_success_complete_step_without_work_tools():
    """complete_step(success=true) with no work tools is rejected; step continues."""
    llm = ScriptedLLM([
        LLMMessage.assistant(tool_calls=[
            ToolCall(
                id="plan-1",
                name="create_plan",
                args={
                    "message": "Working.",
                    "language": "en",
                    "title": "Work",
                    "goal": "Ship",
                    "steps": [{"id": "1", "description": "Build it"}],
                },
            ),
        ]),
        # Premature complete — should be rejected
        LLMMessage.assistant(tool_calls=[
            ToolCall(
                id="early",
                name="complete_step",
                args={"success": True, "result": "pretend done", "attachments": []},
            ),
        ]),
        LLMMessage.assistant(tool_calls=[_file_write("w1")]),
        LLMMessage.assistant(tool_calls=[
            ToolCall(
                id="done-1",
                name="complete_step",
                args={"success": True, "result": "really done", "attachments": []},
            ),
        ]),
        LLMMessage.assistant(tool_calls=[
            ToolCall(
                id="sum-1",
                name="deliver_result",
                args={"message": "Shipped", "attachments": []},
            ),
        ]),
    ])
    flow = _flow(llm)
    events = [event async for event in flow.run(Message(message="Build"))]

    assert any(
        isinstance(e, MessageEvent) and e.message == "Shipped" for e in events
    )
    assert not any(
        isinstance(e, MessageEvent) and e.message == "really done" for e in events
    )
    assert not any(
        isinstance(e, MessageEvent) and e.message == "pretend done" for e in events
    )
    step_done = next(
        e for e in events
        if isinstance(e, StepEvent) and e.status == StepStatus.COMPLETED
    )
    assert step_done.step.result == "really done"
    assert isinstance(events[-1], DoneEvent)
    assert llm.responses == []


@pytest.mark.asyncio
async def test_plan_act_two_success_steps_skip_update_plan():
    llm = ScriptedLLM([
        LLMMessage.assistant(tool_calls=[
            ToolCall(
                id="plan-1",
                name="create_plan",
                args={
                    "message": "Two steps.",
                    "language": "en",
                    "title": "Two",
                    "goal": "Both",
                    "steps": [
                        {"id": "1", "description": "First"},
                        {"id": "2", "description": "Second"},
                    ],
                },
            ),
        ]),
        LLMMessage.assistant(tool_calls=[_file_write("w1")]),
        LLMMessage.assistant(tool_calls=[
            ToolCall(
                id="done-1",
                name="complete_step",
                args={"success": True, "result": "First done", "attachments": []},
            ),
        ]),
        LLMMessage.assistant(tool_calls=[_file_write("w2")]),
        LLMMessage.assistant(tool_calls=[
            ToolCall(
                id="done-2",
                name="complete_step",
                args={"success": True, "result": "Second done", "attachments": []},
            ),
        ]),
        LLMMessage.assistant(tool_calls=[
            ToolCall(
                id="sum-1",
                name="deliver_result",
                args={"message": "Both done", "attachments": []},
            ),
        ]),
    ])
    flow = _flow(llm)
    events = [event async for event in flow.run(Message(message="Do both"))]

    completed = [
        e for e in events
        if isinstance(e, StepEvent) and e.status == StepStatus.COMPLETED
    ]
    assert [e.step.id for e in completed] == ["1", "2"]
    assert _has_update_plan_call(llm) is False
    assert isinstance(events[-1], DoneEvent)
    assert llm.responses == []


@pytest.mark.asyncio
async def test_plan_act_failed_step_triggers_update_plan():
    llm = ScriptedLLM([
        LLMMessage.assistant(tool_calls=[
            ToolCall(
                id="plan-1",
                name="create_plan",
                args={
                    "message": "Will try.",
                    "language": "en",
                    "title": "Try",
                    "goal": "Recover",
                    "steps": [
                        {"id": "1", "description": "May fail"},
                        {"id": "2", "description": "Later"},
                    ],
                },
            ),
        ]),
        LLMMessage.assistant(tool_calls=[
            ToolCall(
                id="fail-1",
                name="complete_step",
                args={
                    "success": False,
                    "result": "Blocked",
                    "attachments": [],
                },
            ),
        ]),
        LLMMessage.assistant(tool_calls=[
            ToolCall(
                id="upd-1",
                name="update_plan",
                args={"steps": []},
            ),
        ]),
        LLMMessage.assistant(tool_calls=[
            ToolCall(
                id="sum-1",
                name="deliver_result",
                args={"message": "Stopped after failure", "attachments": []},
            ),
        ]),
    ])
    flow = _flow(llm)
    events = [event async for event in flow.run(Message(message="Try"))]

    assert _has_update_plan_call(llm) is True
    assert any(
        isinstance(e, PlanEvent) and e.status == PlanStatus.UPDATED for e in events
    )
    assert any(
        isinstance(e, MessageEvent) and e.message == "Stopped after failure"
        for e in events
    )
    assert isinstance(events[-1], DoneEvent)
    assert llm.responses == []


@pytest.mark.asyncio
async def test_plan_act_wait_does_not_emit_done():
    llm = ScriptedLLM([
        LLMMessage.assistant(tool_calls=[
            ToolCall(
                id="plan-1",
                name="create_plan",
                args={
                    "message": "Need a choice.",
                    "language": "en",
                    "title": "Choose",
                    "goal": "Pick",
                    "steps": [{"id": "1", "description": "Ask user"}],
                },
            ),
        ]),
        LLMMessage.assistant(tool_calls=[
            ToolCall(
                id="ask-1",
                name="message_ask_user",
                args={"text": "Which option?"},
            ),
        ]),
    ])
    flow = _flow(llm)
    events = [event async for event in flow.run(Message(message="Help"))]

    assert any(isinstance(e, WaitEvent) for e in events)
    assert not any(isinstance(e, DoneEvent) for e in events)
    assert flow.is_done() is False


def test_step_needs_replan_helper():
    from app.domain.models.plan import Step, ExecutionStatus
    from app.domain.services.flows.plan_act import step_needs_replan

    ok = Step(id="1", description="x", status=ExecutionStatus.COMPLETED, success=True)
    bad = Step(id="2", description="y", status=ExecutionStatus.COMPLETED, success=False)
    failed = Step(id="3", description="z", status=ExecutionStatus.FAILED, success=False)
    assert step_needs_replan(ok) is False
    assert step_needs_replan(bad) is True
    assert step_needs_replan(failed) is True
