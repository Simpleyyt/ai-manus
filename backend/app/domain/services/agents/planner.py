from typing import AsyncGenerator, Optional
import logging
from app.domain.models.plan import Plan, Step
from app.domain.models.message import Message
from app.domain.models.agent_output import PlanOutput, PlanUpdateOutput
from app.domain.services.agents.base import BaseAgent, StructuredOutputEvent
from app.domain.services.prompts.system import build_system_prompt
from app.domain.services.prompts.planner import (
    CREATE_PLAN_PROMPT,
    UPDATE_PLAN_PROMPT,
    PLANNER_ROLE_PROMPT,
)
from app.domain.models.event import (
    BaseEvent,
    PlanEvent,
    PlanStatus,
)
from app.domain.external.llm import LLM
from app.domain.services.tools.base import BaseToolkit, OutputTool, describe_toolkits
from app.domain.repositories.agent_repository import AgentRepository
from typing import List

logger = logging.getLogger(__name__)

CREATE_PLAN_TOOL = OutputTool(
    name="create_plan",
    description="Submit the plan for the user's request.",
    schema=PlanOutput,
)

UPDATE_PLAN_TOOL = OutputTool(
    name="update_plan",
    description="Submit the re-planned remaining steps.",
    schema=PlanUpdateOutput,
)


class PlannerAgent(BaseAgent):
    """Planner agent: creates and re-plans task plans.

    Submits plans through native function calling (``create_plan`` /
    ``update_plan`` output tools). It is not bound to any executor toolkits —
    it only receives a compact capability overview, which keeps full function
    schemas out of its context.
    """

    name: str = "planner"
    tool_choice: Optional[str] = "required"

    def __init__(
        self,
        agent_id: str,
        agent_repository: AgentRepository,
        llm: LLM,
        capability_toolkits: List[BaseToolkit] = [],
    ):
        super().__init__(
            agent_id=agent_id,
            agent_repository=agent_repository,
            llm=llm,
            tools=[],
        )
        # Kept as a reference so the overview is rendered lazily, after
        # runtime-discovered tools (e.g. MCP) have been initialized.
        self._capability_toolkits = capability_toolkits

    def build_system_prompt(self) -> str:
        return build_system_prompt(
            toolkits=[],
            role_prompt=PLANNER_ROLE_PROMPT.format(
                capabilities=describe_toolkits(self._capability_toolkits)
            ),
        )

    async def create_plan(self, message: Message) -> AsyncGenerator[BaseEvent, None]:
        request = CREATE_PLAN_PROMPT.format(
            message=message.message,
            attachments="\n".join(message.attachments)
        )
        async for event in self.execute(request, output_tool=CREATE_PLAN_TOOL):
            if isinstance(event, StructuredOutputEvent):
                output: PlanOutput = event.output
                logger.info(f"Planner created plan: {output.title}")
                plan = Plan.model_validate(output.model_dump())
                yield PlanEvent(status=PlanStatus.CREATED, plan=plan)
            else:
                yield event

    async def update_plan(self, plan: Plan, step: Step) -> AsyncGenerator[BaseEvent, None]:
        request = UPDATE_PLAN_PROMPT.format(plan=plan.dump_json(), step=step.model_dump_json())
        async for event in self.execute(request, output_tool=UPDATE_PLAN_TOOL):
            if isinstance(event, StructuredOutputEvent):
                output: PlanUpdateOutput = event.output
                logger.debug(f"Planner updated plan: {output}")
                new_steps = [Step.model_validate(s.model_dump()) for s in output.steps]

                # Find the index of the first pending step
                first_pending_index = None
                for i, existing_step in enumerate(plan.steps):
                    if not existing_step.is_done():
                        first_pending_index = i
                        break

                # If there are pending steps, replace all pending steps
                if first_pending_index is not None:
                    # Keep completed steps
                    updated_steps = plan.steps[:first_pending_index]
                    # Add new steps
                    updated_steps.extend(new_steps)
                    # Update steps in plan
                    plan.steps = updated_steps

                yield PlanEvent(status=PlanStatus.UPDATED, plan=plan)
            else:
                yield event
