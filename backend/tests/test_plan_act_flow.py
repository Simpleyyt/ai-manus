"""
Test the LangGraph-based PlanActFlow.

Uses mocks for all external dependencies (sandbox, repository, etc.)
to verify the graph orchestration logic works correctly.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any, Optional, AsyncGenerator

from app.domain.services.flows.plan_act import PlanActFlow, PlanActState
from app.domain.models.message import Message
from app.domain.models.plan import Plan, Step, ExecutionStatus
from app.domain.models.event import (
    BaseEvent,
    PlanEvent,
    PlanStatus,
    MessageEvent,
    DoneEvent,
    TitleEvent,
    StepEvent,
    StepStatus,
    ToolEvent,
    ToolStatus,
    ErrorEvent,
    WaitEvent,
)
from app.domain.models.session import Session, SessionStatus
from app.domain.models.memory import Memory


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def make_plan(num_steps: int = 2, title: str = "Test Plan") -> Plan:
    steps = [
        Step(id=str(i + 1), description=f"Step {i + 1}")
        for i in range(num_steps)
    ]
    return Plan(
        title=title,
        goal="Test goal",
        language="en",
        steps=steps,
        message="Let me work on this.",
    )


def make_session(status: SessionStatus = SessionStatus.PENDING, plan: Optional[Plan] = None) -> Session:
    session = MagicMock(spec=Session)
    session.id = "test-session"
    session.status = status
    session.get_last_plan.return_value = plan
    return session


def _make_flow():
    """Create a PlanActFlow with all dependencies mocked."""
    sandbox = AsyncMock()
    browser = AsyncMock()
    agent_repo = AsyncMock()
    agent_repo.get_memory = AsyncMock(return_value=Memory())
    agent_repo.save_memory = AsyncMock()
    session_repo = AsyncMock()
    mcp_tool = MagicMock()
    mcp_tool.get_tools = MagicMock(return_value=[])
    mcp_tool.has_function = MagicMock(return_value=False)

    with patch("app.domain.services.agents.base.init_chat_model") as mock_init, \
         patch("app.domain.services.agents.base.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(
            model_name="gpt-4o",
            model_provider="openai",
            temperature=0.7,
            max_tokens=2000,
            api_base=None,
        )
        mock_init.return_value = MagicMock()

        flow = PlanActFlow(
            agent_id="agent-1",
            agent_repository=agent_repo,
            session_id="session-1",
            session_repository=session_repo,
            sandbox=sandbox,
            browser=browser,
            mcp_tool=mcp_tool,
        )
    return flow, session_repo


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_plan_act_state_typedef():
    """PlanActState has the expected keys."""
    state: PlanActState = {
        "message": Message(message="hello"),
        "plan": None,
        "current_step": None,
        "should_wait": False,
        "has_steps": True,
    }
    assert state["message"].message == "hello"
    assert state["plan"] is None
    assert state["should_wait"] is False


@pytest.mark.asyncio
async def test_graph_structure():
    """The compiled graph has all expected nodes."""
    flow, _ = _make_flow()

    graph_repr = flow._graph.get_graph()
    node_ids = set(graph_repr.nodes)
    assert "plan" in node_ids
    assert "execute" in node_ids
    assert "update" in node_ids
    assert "summarize" in node_ids
    assert "complete" in node_ids


@pytest.mark.asyncio
async def test_route_entry_default_goes_to_plan():
    """By default, entry routes to plan node."""
    flow, _ = _make_flow()
    flow._start_from_execute = False
    result = flow._route_entry({"message": Message(), "plan": None, "current_step": None, "should_wait": False, "has_steps": True})
    assert result == "plan"


@pytest.mark.asyncio
async def test_route_entry_waiting_goes_to_execute():
    """When resuming from WAITING, entry routes to execute."""
    flow, _ = _make_flow()
    flow._start_from_execute = True
    result = flow._route_entry({"message": Message(), "plan": None, "current_step": None, "should_wait": False, "has_steps": True})
    assert result == "execute"


@pytest.mark.asyncio
async def test_after_plan_routing():
    """after_plan routes to execute when has_steps, else complete."""
    flow, _ = _make_flow()

    assert flow._after_plan({"has_steps": True, "plan": None, "message": Message(), "current_step": None, "should_wait": False}) == "execute"
    assert flow._after_plan({"has_steps": False, "plan": None, "message": Message(), "current_step": None, "should_wait": False}) == "complete"


@pytest.mark.asyncio
async def test_after_execute_routing():
    """after_execute routes correctly based on state."""
    flow, _ = _make_flow()
    from langgraph.graph import END

    assert flow._after_execute({"should_wait": True, "current_step": Step(), "plan": None, "message": Message(), "has_steps": True}) == END
    assert flow._after_execute({"should_wait": False, "current_step": None, "plan": None, "message": Message(), "has_steps": True}) == "summarize"
    assert flow._after_execute({"should_wait": False, "current_step": Step(), "plan": None, "message": Message(), "has_steps": True}) == "update"


@pytest.mark.asyncio
async def test_full_flow_with_mocked_agents():
    """
    End-to-end test: mock planner and executor to verify the full
    LangGraph flow produces the expected sequence of events.
    """
    flow, session_repo = _make_flow()
    plan = make_plan(num_steps=1)
    session = make_session(status=SessionStatus.PENDING, plan=None)
    session_repo.find_by_id = AsyncMock(return_value=session)
    session_repo.update_status = AsyncMock()

    async def mock_create_plan(message):
        yield PlanEvent(status=PlanStatus.CREATED, plan=plan)

    async def mock_update_plan(plan_obj, step):
        yield PlanEvent(status=PlanStatus.UPDATED, plan=plan_obj)

    async def mock_execute_step(plan_obj, step, message):
        step.status = ExecutionStatus.COMPLETED
        step.success = True
        step.result = "Done"
        yield StepEvent(status=StepStatus.STARTED, step=step)
        yield StepEvent(status=StepStatus.COMPLETED, step=step)

    async def mock_summarize():
        yield MessageEvent(message="All tasks completed.")

    flow.planner.create_plan = mock_create_plan
    flow.planner.update_plan = mock_update_plan
    flow.planner.roll_back = AsyncMock()
    flow.executor.execute_step = mock_execute_step
    flow.executor.summarize = mock_summarize
    flow.executor.compact_memory = AsyncMock()
    flow.executor.roll_back = AsyncMock()

    message = Message(message="Build a hello world app")
    events: List[BaseEvent] = []

    async for event in flow.run(message):
        events.append(event)

    event_types = [type(e).__name__ for e in events]
    print(f"Event sequence: {event_types}")

    assert any(isinstance(e, TitleEvent) for e in events), "Missing TitleEvent"
    assert any(isinstance(e, PlanEvent) and e.status == PlanStatus.CREATED for e in events), "Missing PlanEvent(CREATED)"
    assert any(isinstance(e, StepEvent) for e in events), "Missing StepEvent"
    assert any(isinstance(e, DoneEvent) for e in events), "Missing DoneEvent"
    assert any(isinstance(e, PlanEvent) and e.status == PlanStatus.COMPLETED for e in events), "Missing PlanEvent(COMPLETED)"


@pytest.mark.asyncio
async def test_empty_plan_goes_to_complete():
    """When planner produces a plan with no steps, flow goes directly to complete."""
    flow, session_repo = _make_flow()
    empty_plan = Plan(title="Empty", goal="nothing", steps=[], message="Nothing to do.")
    session = make_session(status=SessionStatus.PENDING)
    session_repo.find_by_id = AsyncMock(return_value=session)
    session_repo.update_status = AsyncMock()

    async def mock_create_plan(message):
        yield PlanEvent(status=PlanStatus.CREATED, plan=empty_plan)

    flow.planner.create_plan = mock_create_plan
    flow.planner.roll_back = AsyncMock()
    flow.executor.roll_back = AsyncMock()

    message = Message(message="Do nothing")
    events: List[BaseEvent] = []

    async for event in flow.run(message):
        events.append(event)

    event_types = [type(e).__name__ for e in events]
    print(f"Event sequence (empty plan): {event_types}")

    assert any(isinstance(e, DoneEvent) for e in events)
    assert any(isinstance(e, PlanEvent) and e.status == PlanStatus.COMPLETED for e in events)
    assert not any(isinstance(e, StepEvent) for e in events)


@pytest.mark.asyncio
async def test_wait_event_ends_graph():
    """When executor yields WaitEvent, the flow stops without DoneEvent."""
    flow, session_repo = _make_flow()
    plan = make_plan(num_steps=2)
    session = make_session(status=SessionStatus.PENDING)
    session_repo.find_by_id = AsyncMock(return_value=session)
    session_repo.update_status = AsyncMock()

    async def mock_create_plan(message):
        yield PlanEvent(status=PlanStatus.CREATED, plan=plan)

    async def mock_execute_step(plan_obj, step, message):
        yield StepEvent(status=StepStatus.STARTED, step=step)
        yield WaitEvent()

    flow.planner.create_plan = mock_create_plan
    flow.planner.roll_back = AsyncMock()
    flow.executor.execute_step = mock_execute_step
    flow.executor.compact_memory = AsyncMock()
    flow.executor.roll_back = AsyncMock()

    message = Message(message="Need user input")
    events: List[BaseEvent] = []

    async for event in flow.run(message):
        events.append(event)

    event_types = [type(e).__name__ for e in events]
    print(f"Event sequence (wait): {event_types}")

    assert any(isinstance(e, WaitEvent) for e in events)
    assert not any(isinstance(e, DoneEvent) for e in events)


if __name__ == "__main__":
    asyncio.run(pytest.main([__file__, "-v"]))
