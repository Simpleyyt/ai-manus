from typing import List, Optional

from app.domain.models.event import (
    BaseEvent,
    PlanEvent,
    PlanStatus,
    StepEvent,
    StepStatus,
)
from app.domain.models.plan import ExecutionStatus, Plan, Step
from app.domain.models.todo import TodoItem, TodoStatus


def _todo_status_to_execution(todo_status: TodoStatus) -> tuple[ExecutionStatus, bool]:
    if todo_status == TodoStatus.PENDING:
        return ExecutionStatus.PENDING, False
    if todo_status == TodoStatus.IN_PROGRESS:
        return ExecutionStatus.RUNNING, False
    if todo_status == TodoStatus.COMPLETED:
        return ExecutionStatus.COMPLETED, True
    return ExecutionStatus.COMPLETED, False


def _todo_item_to_step(item: TodoItem) -> Step:
    status, success = _todo_status_to_execution(item.status)
    return Step(
        id=item.id,
        description=item.content,
        status=status,
        success=success,
    )


def todos_to_plan(items: List[TodoItem], *, title: str = "", goal: str = "") -> Plan:
    steps = [_todo_item_to_step(item) for item in items]
    resolved_goal = goal
    if not resolved_goal:
        for item in items:
            if item.status == TodoStatus.PENDING:
                resolved_goal = item.content
                break
    return Plan(title=title, goal=resolved_goal, steps=steps)


def _should_emit_started(prev: Optional[TodoItem], curr: TodoItem) -> bool:
    if curr.status != TodoStatus.IN_PROGRESS:
        return False
    if prev is None:
        return True
    return prev.status == TodoStatus.PENDING


def _should_emit_completed(prev: Optional[TodoItem], curr: TodoItem) -> bool:
    if curr.status not in (TodoStatus.COMPLETED, TodoStatus.CANCELLED):
        return False
    if prev is None:
        return True
    return prev.status != curr.status


def project_todo_write(
    items: List[TodoItem],
    *,
    previous_items: Optional[List[TodoItem]],
    title: str = "",
) -> List[BaseEvent]:
    """Return PlanEvent (+ optional StepEvents) for this todo_write."""
    plan = todos_to_plan(items, title=title)
    events: List[BaseEvent] = []

    if (previous_items is None or len(previous_items) == 0) and items:
        events.append(PlanEvent(status=PlanStatus.CREATED, plan=plan))
    else:
        events.append(PlanEvent(status=PlanStatus.UPDATED, plan=plan))

    prev_by_id = {item.id: item for item in (previous_items or [])}
    step_by_id = {step.id: step for step in plan.steps}

    for item in items:
        prev = prev_by_id.get(item.id)
        step = step_by_id[item.id]
        if _should_emit_started(prev, item):
            events.append(StepEvent(status=StepStatus.STARTED, step=step))
        elif _should_emit_completed(prev, item):
            events.append(StepEvent(status=StepStatus.COMPLETED, step=step))

    return events
