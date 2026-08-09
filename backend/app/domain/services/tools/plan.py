from app.domain.models.agent_output import PlanReportOutput, ReplanOutput
from app.domain.models.tool_result import ToolResult
from app.domain.services.tools.base import BaseToolkit, tool


def _normalize_step_statuses(steps: list[dict]) -> list[dict]:
    normalized: list[dict] = []
    for step in steps:
        item = dict(step)
        status = item.get("status")
        if isinstance(status, str) and status == "in_progress":
            item["status"] = "running"
        normalized.append(item)
    return normalized


class PlanToolkit(BaseToolkit):
    name = "plan"
    instructions = """
- The product Plan panel is authoritative and separate from todo.md.
- After finishing or starting a planned step, call plan_report with a FULL
  status snapshot for every known step id (pending|running|completed|failed).
  Keep at most one step running.
- Call replan with a clear reason when remaining steps no longer fit reality;
  then rebuild /home/ubuntu/todo.md to match the new plan (attention only).
- Do not invent Plan UI updates by only editing todo.md.
"""

    @tool(parse_docstring=True)
    async def plan_report(self, steps: list[dict], reflection: str = "") -> ToolResult:
        """Update authoritative plan step statuses for the Plan panel.

        Args:
            steps: Full list of {id, status} (optional reflection per step).
            reflection: Optional short overall reflection.
        """
        parsed = PlanReportOutput.model_validate(
            {
                "steps": _normalize_step_statuses(steps),
                "reflection": reflection or "",
            }
        )
        return ToolResult(
            success=True,
            message="Plan progress recorded",
            data=parsed.model_dump(mode="json"),
        )

    @tool(parse_docstring=True)
    async def replan(self, reason: str) -> ToolResult:
        """Request Planner to rewrite remaining steps.

        Args:
            reason: Why the current remaining plan is wrong or incomplete.
        """
        parsed = ReplanOutput.model_validate({"reason": reason})
        return ToolResult(
            success=True,
            message="Replan requested",
            data=parsed.model_dump(mode="json"),
        )
