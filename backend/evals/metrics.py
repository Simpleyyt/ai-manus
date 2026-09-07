"""Metrics extracted from one eval scenario run."""

from dataclasses import dataclass, field
from typing import List

from app.domain.models.event import BaseEvent, ErrorEvent, ToolEvent, ToolStatus
from app.domain.models.memory import Memory
from app.domain.models.message import Role


@dataclass
class ScenarioResult:
    events: List[BaseEvent]
    llm_calls: int
    update_plan_calls: int
    remaining_responses: int
    tool_calls: int = 0
    error_events: int = 0
    invalid_output_feedback: int = 0
    rejected_complete_step: int = 0
    unknown_tool_responses: int = 0
    check_failures: List[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.check_failures


def build_result(
    events: List[BaseEvent],
    llm,
    memories: dict[str, Memory],
) -> ScenarioResult:
    tool_calls = sum(
        1
        for e in events
        if isinstance(e, ToolEvent) and e.status == ToolStatus.CALLED
    )
    error_events = sum(1 for e in events if isinstance(e, ErrorEvent))

    invalid_feedback = 0
    rejected = 0
    unknown = 0
    for memory in memories.values():
        for message in memory.get_messages():
            if message.role != Role.TOOL:
                continue
            content = message.content or ""
            if content.startswith("Invalid arguments"):
                invalid_feedback += 1
            elif content.startswith("Rejected:"):
                rejected += 1
            elif content.startswith("Unknown tool"):
                unknown += 1

    update_plan_calls = sum(
        1 for names in llm.asked_tool_names if "update_plan" in names.split(",")
    )

    return ScenarioResult(
        events=events,
        llm_calls=len(llm.requests),
        update_plan_calls=update_plan_calls,
        remaining_responses=len(llm.responses),
        tool_calls=tool_calls,
        error_events=error_events,
        invalid_output_feedback=invalid_feedback,
        rejected_complete_step=rejected,
        unknown_tool_responses=unknown,
    )
