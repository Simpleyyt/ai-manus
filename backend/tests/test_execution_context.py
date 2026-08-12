"""Helpers for execution context + single-step summarize skip."""

from app.domain.models.plan import ExecutionStatus, Plan, Step
from app.domain.services.prompts.execution import (
    RESUME_PROMPT,
    build_execution_request,
    can_skip_summarize,
    format_prior_steps,
)
from app.domain.models.message import Message


def test_format_prior_steps_lists_finished_steps_only():
    plan = Plan(
        goal="Ship",
        language="en",
        steps=[
            Step(
                id="1",
                description="Research",
                status=ExecutionStatus.COMPLETED,
                success=True,
                result="Found A",
            ),
            Step(id="2", description="Write", status=ExecutionStatus.PENDING),
        ],
    )
    text = format_prior_steps(plan, plan.steps[1])
    assert "Research" in text
    assert "Found A" in text
    assert "Write" not in text


def test_format_prior_steps_empty_when_first():
    plan = Plan(steps=[Step(id="1", description="Only")])
    assert format_prior_steps(plan, plan.steps[0]) == "(none)"


def test_build_execution_request_includes_goal_and_prior():
    plan = Plan(
        goal="Build app",
        language="zh",
        steps=[
            Step(
                id="1",
                description="Scaffold",
                status=ExecutionStatus.COMPLETED,
                success=True,
                result="repo ready",
            ),
            Step(id="2", description="Implement"),
        ],
    )
    req = build_execution_request(
        plan, plan.steps[1], Message(message="make it", attachments=["a.txt"])
    )
    assert "Build app" in req
    assert "Scaffold" in req
    assert "repo ready" in req
    assert "Implement" in req
    assert "make it" in req
    assert "a.txt" in req
    assert "zh" in req


def test_can_skip_summarize_always_false():
    ok = Plan(
        steps=[
            Step(
                id="1",
                description="Do",
                status=ExecutionStatus.COMPLETED,
                success=True,
                result="Done detail",
            )
        ]
    )
    assert can_skip_summarize(ok) is False


def test_resume_prompt_mentions_continue_without_reasking():
    assert "re-ask" in RESUME_PROMPT.lower() or "again" in RESUME_PROMPT.lower()
    assert "{step}" in RESUME_PROMPT
    assert "{goal}" in RESUME_PROMPT
