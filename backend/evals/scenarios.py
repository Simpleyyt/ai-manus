"""Eval scenarios: scripted LLM turns + behavioral checks.

A scenario is a deterministic regression eval for one harness behavior:
the scripted responses replace the LLM, everything else (flow, agents,
toolkits, memory, event stream) is the real implementation.
"""

from dataclasses import dataclass, field
from typing import Callable, List

from app.domain.models.event import (
    DoneEvent,
    MessageEvent,
    PlanEvent,
    PlanStatus,
    StepEvent,
    StepStatus,
    WaitEvent,
)
from app.domain.models.message import LLMMessage, ToolCall

from evals.metrics import ScenarioResult


Check = Callable[[ScenarioResult], bool]


@dataclass
class Scenario:
    name: str
    description: str
    user_message: str
    responses: List[LLMMessage]
    checks: List[tuple[str, Check]] = field(default_factory=list)


def _create_plan(steps: List[dict], call_id: str = "plan-1") -> LLMMessage:
    return LLMMessage.assistant(tool_calls=[
        ToolCall(
            id=call_id,
            name="create_plan",
            args={
                "message": "Working on it.",
                "language": "en",
                "title": "Eval Task",
                "goal": "Finish the eval task",
                "steps": steps,
            },
        ),
    ])


def _file_write(call_id: str) -> LLMMessage:
    return LLMMessage.assistant(tool_calls=[
        ToolCall(
            id=call_id,
            name="file_write",
            args={"file": "/home/ubuntu/out.txt", "content": "work"},
        ),
    ])


def _complete_step(call_id: str, success: bool = True, result: str = "done") -> LLMMessage:
    return LLMMessage.assistant(tool_calls=[
        ToolCall(
            id=call_id,
            name="complete_step",
            args={"success": success, "result": result, "attachments": []},
        ),
    ])


def _deliver(call_id: str, message: str) -> LLMMessage:
    return LLMMessage.assistant(tool_calls=[
        ToolCall(
            id=call_id,
            name="deliver_result",
            args={"message": message, "attachments": []},
        ),
    ])


def _has_final_message(text: str) -> Check:
    return lambda r: any(
        isinstance(e, MessageEvent) and e.message == text for e in r.events
    )


def _done(r: ScenarioResult) -> bool:
    return any(isinstance(e, DoneEvent) for e in r.events)


def _plan_completed(r: ScenarioResult) -> bool:
    return any(
        isinstance(e, PlanEvent) and e.status == PlanStatus.COMPLETED for e in r.events
    )


def _no_error_events(r: ScenarioResult) -> bool:
    return r.error_events == 0


def _script_fully_consumed(r: ScenarioResult) -> bool:
    return r.remaining_responses == 0


BASE_CHECKS: List[tuple[str, Check]] = [
    ("script_fully_consumed", _script_fully_consumed),
    ("no_error_events", _no_error_events),
]


SCENARIOS: List[Scenario] = [
    Scenario(
        name="single_step_success",
        description="One successful step: no planner round-trip, summarize delivers.",
        user_message="Do the work",
        responses=[
            _create_plan([{"id": "1", "description": "Do the work"}]),
            _file_write("w1"),
            _complete_step("c1"),
            _deliver("d1", "All done"),
        ],
        checks=BASE_CHECKS + [
            ("done", _done),
            ("plan_completed", _plan_completed),
            ("final_message", _has_final_message("All done")),
            ("no_replan", lambda r: r.update_plan_calls == 0),
            ("llm_call_budget", lambda r: r.llm_calls == 4),
        ],
    ),
    Scenario(
        name="failed_step_triggers_replan",
        description="A failed step must route through Planner.update_plan.",
        user_message="Try it",
        responses=[
            _create_plan([
                {"id": "1", "description": "May fail"},
                {"id": "2", "description": "Later"},
            ]),
            _complete_step("c1", success=False, result="Blocked"),
            LLMMessage.assistant(tool_calls=[
                ToolCall(id="u1", name="update_plan", args={"steps": []}),
            ]),
            _deliver("d1", "Stopped after failure"),
        ],
        checks=BASE_CHECKS + [
            ("done", _done),
            ("replan_happened", lambda r: r.update_plan_calls >= 1),
            ("final_message", _has_final_message("Stopped after failure")),
        ],
    ),
    Scenario(
        name="ask_user_waits",
        description="message_ask_user must yield WaitEvent and suppress DoneEvent.",
        user_message="Help me choose",
        responses=[
            _create_plan([{"id": "1", "description": "Ask the user"}]),
            LLMMessage.assistant(tool_calls=[
                ToolCall(id="a1", name="message_ask_user", args={"text": "Which?"}),
            ]),
        ],
        checks=BASE_CHECKS + [
            ("wait_event", lambda r: any(isinstance(e, WaitEvent) for e in r.events)),
            ("no_done", lambda r: not _done(r)),
        ],
    ),
    Scenario(
        name="invalid_output_self_repair",
        description="Invalid complete_step args are fed back; the model repairs.",
        user_message="Do it carefully",
        responses=[
            _create_plan([{"id": "1", "description": "Do the work"}]),
            _file_write("w1"),
            # Missing required "result" field — must trigger self-repair.
            LLMMessage.assistant(tool_calls=[
                ToolCall(id="bad", name="complete_step", args={"success": True}),
            ]),
            _complete_step("c1", result="repaired"),
            _deliver("d1", "Recovered"),
        ],
        checks=BASE_CHECKS + [
            ("done", _done),
            ("self_repair_feedback", lambda r: r.invalid_output_feedback >= 1),
            ("final_message", _has_final_message("Recovered")),
        ],
    ),
    Scenario(
        name="premature_complete_rejected",
        description="complete_step(success=true) with no work tools is rejected.",
        user_message="Build it",
        responses=[
            _create_plan([{"id": "1", "description": "Build it"}]),
            _complete_step("early", result="pretend done"),
            _file_write("w1"),
            _complete_step("c1", result="really done"),
            _deliver("d1", "Shipped"),
        ],
        checks=BASE_CHECKS + [
            ("done", _done),
            ("rejection_feedback", lambda r: r.rejected_complete_step >= 1),
            (
                "step_result_is_real",
                lambda r: any(
                    isinstance(e, StepEvent)
                    and e.status == StepStatus.COMPLETED
                    and e.step.result == "really done"
                    for e in r.events
                ),
            ),
            ("final_message", _has_final_message("Shipped")),
        ],
    ),
]
