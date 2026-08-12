from app.domain.models.todo import TodoItem, TodoStatus
from app.domain.models.event import PlanEvent, PlanStatus, StepEvent, StepStatus
from app.domain.models.plan import ExecutionStatus
from app.domain.services.todo_projection import todos_to_plan, project_todo_write


def test_todos_to_plan_maps_statuses():
    plan = todos_to_plan([
        TodoItem(id="1", content="A", status=TodoStatus.COMPLETED),
        TodoItem(id="2", content="B", status=TodoStatus.IN_PROGRESS),
        TodoItem(id="3", content="C", status=TodoStatus.PENDING),
    ], title="T", goal="G")
    assert plan.title == "T"
    assert plan.goal == "G"
    assert plan.steps[0].status == ExecutionStatus.COMPLETED
    assert plan.steps[0].success is True
    assert plan.steps[1].status == ExecutionStatus.RUNNING
    assert plan.steps[2].status == ExecutionStatus.PENDING


def test_first_todo_write_emits_created_plan():
    items = [TodoItem(id="1", content="Research", status=TodoStatus.IN_PROGRESS)]
    events = project_todo_write(items, previous_items=None, title="Research task")
    assert len(events) >= 1
    assert isinstance(events[0], PlanEvent)
    assert events[0].status == PlanStatus.CREATED
    assert events[0].plan.steps[0].description == "Research"


def test_subsequent_todo_write_emits_updated_and_step_transitions():
    prev = [TodoItem(id="1", content="Research", status=TodoStatus.IN_PROGRESS)]
    curr = [TodoItem(id="1", content="Research", status=TodoStatus.COMPLETED)]
    events = project_todo_write(curr, previous_items=prev, title="Research task")
    assert any(isinstance(e, PlanEvent) and e.status == PlanStatus.UPDATED for e in events)
    assert any(isinstance(e, StepEvent) and e.status == StepStatus.COMPLETED for e in events)
