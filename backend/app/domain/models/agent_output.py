"""Structured output contracts between agents and the LLM.

Each model backs an :class:`app.domain.services.tools.base.OutputTool` that
the model calls through native function calling to submit structured results
(plans, step reports, final deliveries). Schemas are derived from these
Pydantic models, and arguments are validated against them with self-repair on
failure — no JSON format instructions live in prompts anymore.
"""
from typing import List

from pydantic import BaseModel, Field


class PlanStepDraft(BaseModel):
    """A single step proposed by the planner."""

    id: str = Field(description="Short sequential step identifier, e.g. '1', '2'")
    description: str = Field(
        description="Atomic, self-contained step description the executor can act on"
    )


class PlanOutput(BaseModel):
    """Arguments of the ``create_plan`` output tool."""

    message: str = Field(
        description=(
            "Reply to the user acknowledging the task and how you will approach"
            " it, written in the user's language"
        )
    )
    language: str = Field(
        description="Working language inferred from the user's message, e.g. 'en', 'zh'"
    )
    title: str = Field(description="Short title for this task")
    goal: str = Field(
        description="Overall goal of the plan; empty string if the task is infeasible"
    )
    steps: List[PlanStepDraft] = Field(
        description=(
            "Ordered atomic steps to accomplish the goal; empty list if the"
            " task is infeasible or needs no tool work"
        )
    )


class PlanUpdateOutput(BaseModel):
    """Arguments of the ``update_plan`` output tool."""

    steps: List[PlanStepDraft] = Field(
        description=(
            "The remaining (not yet completed) steps after re-planning, starting"
            " from the first uncompleted step; empty list if nothing is left to do"
        )
    )


class StepReport(BaseModel):
    """Arguments of the ``complete_step`` output tool."""

    success: bool = Field(description="Whether the step was completed successfully")
    result: str = Field(
        description=(
            "Concrete outcome of the step: what was done and what was produced,"
            " in the working language"
        )
    )
    attachments: List[str] = Field(
        default_factory=list,
        description="Absolute sandbox paths of files produced in this step",
    )


class FinalResult(BaseModel):
    """Arguments of the ``deliver_result`` output tool."""

    message: str = Field(
        description=(
            "Final answer delivered to the user, detailed and in the user's"
            " language; reference produced files where relevant"
        )
    )
    attachments: List[str] = Field(
        default_factory=list,
        description="Absolute sandbox paths of files to deliver to the user",
    )
