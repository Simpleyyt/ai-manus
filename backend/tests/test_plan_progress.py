from app.domain.models.plan import Plan, Step, ExecutionStatus
from app.domain.models.event import PlanEvent, PlanStatus, StepEvent, StepStatus
from app.domain.models.agent_output import PlanReportOutput, PlanStepStatusUpdate
from app.domain.services.plan_progress import (
    mark_first_step_running,
    apply_plan_report,
    complete_plan,
)


def test_mark_first_step_running():
    plan = Plan(steps=[
        Step(id="1", description="A"),
        Step(id="2", description="B"),
    ])
    out = mark_first_step_running(plan)
    assert out.steps[0].status == ExecutionStatus.RUNNING
    assert out.steps[1].status == ExecutionStatus.PENDING


def test_apply_plan_report_updates_and_emits_step_events():
    plan = Plan(
        title="T",
        goal="G",
        steps=[
            Step(id="1", description="A", status=ExecutionStatus.RUNNING),
            Step(id="2", description="B", status=ExecutionStatus.PENDING),
        ],
    )
    report = PlanReportOutput(
        steps=[
            PlanStepStatusUpdate(id="1", status=ExecutionStatus.COMPLETED),
            PlanStepStatusUpdate(id="2", status=ExecutionStatus.RUNNING),
        ],
        reflection="Finished research",
    )
    events = apply_plan_report(plan, report)
    assert plan.steps[0].status == ExecutionStatus.COMPLETED
    assert plan.steps[0].success is True
    assert plan.steps[1].status == ExecutionStatus.RUNNING
    assert any(isinstance(e, PlanEvent) and e.status == PlanStatus.UPDATED for e in events)
    assert any(isinstance(e, StepEvent) and e.status == StepStatus.COMPLETED for e in events)
    assert any(isinstance(e, StepEvent) and e.status == StepStatus.STARTED for e in events)


def test_apply_plan_report_enforces_single_running():
    plan = Plan(steps=[
        Step(id="1", description="A", status=ExecutionStatus.PENDING),
        Step(id="2", description="B", status=ExecutionStatus.PENDING),
    ])
    report = PlanReportOutput(steps=[
        PlanStepStatusUpdate(id="1", status=ExecutionStatus.RUNNING),
        PlanStepStatusUpdate(id="2", status=ExecutionStatus.RUNNING),
    ])
    apply_plan_report(plan, report)
    running = [s for s in plan.steps if s.status == ExecutionStatus.RUNNING]
    assert len(running) == 1
    assert running[0].id == "2"  # last RUNNING in report wins


def test_apply_plan_report_replaces_existing_unreported_running_step():
    plan = Plan(steps=[
        Step(id="1", description="A", status=ExecutionStatus.RUNNING),
        Step(id="2", description="B", status=ExecutionStatus.PENDING),
    ])
    report = PlanReportOutput(steps=[
        PlanStepStatusUpdate(id="2", status=ExecutionStatus.RUNNING),
    ])

    apply_plan_report(plan, report)

    assert plan.steps[0].status == ExecutionStatus.PENDING
    assert plan.steps[1].status == ExecutionStatus.RUNNING


def test_complete_plan_marks_open_steps_done():
    plan = Plan(steps=[
        Step(id="1", description="A", status=ExecutionStatus.COMPLETED, success=True),
        Step(id="2", description="B", status=ExecutionStatus.RUNNING),
    ])
    out = complete_plan(plan)
    assert out.steps[1].status == ExecutionStatus.COMPLETED
    assert out.steps[1].success is True
    assert out.status == ExecutionStatus.COMPLETED
