from typing import List

from app.domain.models.agent_output import PlanReportOutput
from app.domain.models.event import (
    BaseEvent,
    PlanEvent,
    PlanStatus,
    StepEvent,
    StepStatus,
)
from app.domain.models.plan import ExecutionStatus, Plan, Step


def mark_first_step_running(plan: Plan) -> Plan:
    for step in plan.steps:
        if step.status in (ExecutionStatus.PENDING, ExecutionStatus.RUNNING):
            step.status = ExecutionStatus.RUNNING
            break
    return plan


def _set_step_success(step: Step, status: ExecutionStatus) -> None:
    if status == ExecutionStatus.COMPLETED:
        step.success = True
    elif status == ExecutionStatus.FAILED:
        step.success = False


def _should_emit_started(prev: ExecutionStatus, curr: ExecutionStatus) -> bool:
    return curr == ExecutionStatus.RUNNING and prev == ExecutionStatus.PENDING


def _should_emit_completed(prev: ExecutionStatus, curr: ExecutionStatus) -> bool:
    return curr == ExecutionStatus.COMPLETED and prev != ExecutionStatus.COMPLETED


def apply_plan_report(plan: Plan, report: PlanReportOutput) -> List[BaseEvent]:
    step_by_id = {step.id: step for step in plan.steps}
    previous_status = {step.id: step.status for step in plan.steps}

    running_updates: List[str] = []
    last_touched: Step | None = None

    for update in report.steps:
        step = step_by_id.get(update.id)
        if step is None:
            continue
        step.status = update.status
        _set_step_success(step, update.status)
        if update.reflection is not None:
            step.result = update.reflection
        if update.status == ExecutionStatus.RUNNING:
            running_updates.append(update.id)
        last_touched = step

    running_steps = [
        step for step in plan.steps if step.status == ExecutionStatus.RUNNING
    ]
    preferred_running = next(
        (
            step_by_id[step_id]
            for step_id in reversed(running_updates)
            if step_by_id[step_id].status == ExecutionStatus.RUNNING
        ),
        running_steps[0] if running_steps else None,
    )
    for step in running_steps:
        if step is not preferred_running:
            step.status = ExecutionStatus.PENDING

    if report.reflection and last_touched is not None and not last_touched.result:
        last_touched.result = report.reflection

    events: List[BaseEvent] = [PlanEvent(status=PlanStatus.UPDATED, plan=plan)]

    for step in plan.steps:
        prev = previous_status[step.id]
        curr = step.status
        if _should_emit_started(prev, curr):
            events.append(StepEvent(status=StepStatus.STARTED, step=step))
        elif _should_emit_completed(prev, curr):
            events.append(StepEvent(status=StepStatus.COMPLETED, step=step))

    return events


def complete_plan(plan: Plan) -> Plan:
    for step in plan.steps:
        if step.status not in (ExecutionStatus.COMPLETED, ExecutionStatus.FAILED):
            step.status = ExecutionStatus.COMPLETED
            step.success = True
    plan.status = ExecutionStatus.COMPLETED
    return plan
