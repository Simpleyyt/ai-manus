from typing import Dict, Any, List, AsyncGenerator, Optional
import json
import logging
from app.domain.models.plan import Plan, Step
from app.domain.models.message import Message
from app.domain.services.agents.base import BaseAgent
from app.domain.models.memory import Memory
from app.domain.external.llm import LLM
from app.domain.services.prompts.system import SYSTEM_PROMPT
from app.domain.services.prompts.planner import (
    CREATE_PLAN_PROMPT, 
    UPDATE_PLAN_PROMPT,
    REFLECT_ON_FAILURE_PROMPT,
    PLANNER_SYSTEM_PROMPT
)
from app.domain.models.event import (
    BaseEvent,
    PlanEvent,
    PlanStatus,
    ErrorEvent,
    MessageEvent,
    DoneEvent,
)
from app.domain.external.sandbox import Sandbox
from app.domain.services.tools.base import BaseTool
from app.domain.services.tools.file import FileTool
from app.domain.services.tools.shell import ShellTool
from app.domain.repositories.agent_repository import AgentRepository
from app.domain.utils.json_parser import JsonParser

logger = logging.getLogger(__name__)

class PlannerAgent(BaseAgent):
    """
    Planner agent class, defining the basic behavior of planning
    """

    name: str = "planner"
    system_prompt: str = SYSTEM_PROMPT + PLANNER_SYSTEM_PROMPT
    format: Optional[str] = "json_object"
    tool_choice: Optional[str] = "none"

    def __init__(
        self,
        agent_id: str,
        agent_repository: AgentRepository,
        llm: LLM,
        tools: List[BaseTool],
        json_parser: JsonParser,
    ):
        super().__init__(
            agent_id=agent_id,
            agent_repository=agent_repository,
            llm=llm,
            json_parser=json_parser,
            tools=tools,
        )


    async def create_plan(self, message: Message) -> AsyncGenerator[BaseEvent, None]:
        message = CREATE_PLAN_PROMPT.format(
            message=message.message,
            attachments="\n".join(message.attachments)
        )
        async for event in self.execute(message):
            if isinstance(event, MessageEvent):
                logger.info(event.message)
                parsed_response = await self.json_parser.parse(event.message)
                plan = Plan.model_validate(parsed_response)
                yield PlanEvent(status=PlanStatus.CREATED, plan=plan)
            else:
                yield event

    async def update_plan(self, plan: Plan, step: Step) -> AsyncGenerator[BaseEvent, None]:
        """
        Dynamic next-step planning: Generate the NEXT SINGLE STEP based on current execution context.
        This replaces the traditional multi-step planning with an adaptive, reflexion-based approach.
        """
        message = UPDATE_PLAN_PROMPT.format(plan=plan.dump_json(), step=step.model_dump_json())
        async for event in self.execute(message):
            if isinstance(event, MessageEvent):
                logger.debug(f"Planner agent dynamic next-step planning: {event.message}")
                parsed_response = await self.json_parser.parse(event.message)
                updated_plan = Plan.model_validate(parsed_response)
                new_steps = [Step.model_validate(step) for step in updated_plan.steps]
                
                # Dynamic Planning: Remove all pending steps and add only the new next step(s)
                # Keep only completed steps
                completed_steps = [s for s in plan.steps if s.is_done()]
                
                # If new steps are provided, add them (should be at most 1 in dynamic planning)
                if new_steps:
                    logger.info(f"Generated {len(new_steps)} new step(s) dynamically")
                    # Ensure step IDs continue numbering from completed steps
                    next_id = len(completed_steps) + 1
                    for i, new_step in enumerate(new_steps):
                        new_step.id = str(next_id + i)
                    completed_steps.extend(new_steps)
                else:
                    logger.info("No new steps generated - goal likely achieved")
                
                # Update plan with new steps
                plan.steps = completed_steps
                
                yield PlanEvent(status=PlanStatus.UPDATED, plan=plan)
            else:
                yield event

    async def reflect_on_failure(
        self, 
        goal: str, 
        step: Step, 
        previous_reflections: Optional[List[str]] = None
    ) -> AsyncGenerator[BaseEvent, None]:
        """
        Perform self-reflection on a failed or problematic step.
        
        Args:
            goal: The overall goal being pursued
            step: The step that failed or produced unexpected results
            previous_reflections: List of previous reflection messages to avoid repeating mistakes
            
        Yields:
            Events including the reflection analysis
        """
        previous_reflection_text = ""
        if previous_reflections:
            previous_reflection_text = "\n".join([f"- {r}" for r in previous_reflections[-3:]])  # Last 3 reflections
        else:
            previous_reflection_text = "None"
        
        message = REFLECT_ON_FAILURE_PROMPT.format(
            goal=goal,
            step_description=step.description,
            step_result=step.result or "No result",
            error_message=step.error or "No specific error",
            previous_reflection=previous_reflection_text
        )
        
        async for event in self.execute(message):
            if isinstance(event, MessageEvent):
                logger.info(f"Planner agent reflection: {event.message}")
                try:
                    parsed_response = await self.json_parser.parse(event.message)
                    analysis = parsed_response.get("analysis", "")
                    correction_suggestions = parsed_response.get("correction_suggestions", "")
                    approach_viable = parsed_response.get("approach_viable", True)
                    
                    # Store reflection in the step
                    step.reflection = f"Analysis: {analysis}\nSuggestions: {correction_suggestions}"
                    
                    # Yield reflection as a message event
                    reflection_message = f"🤔 Self-Reflection:\n{analysis}\n\n💡 Suggestions: {correction_suggestions}"
                    yield MessageEvent(message=reflection_message)
                    
                    # If approach is not viable, we might want to signal this
                    if not approach_viable:
                        logger.warning(f"Reflection indicates current approach is not viable for goal: {goal}")
                        
                except Exception as e:
                    logger.error(f"Failed to parse reflection response: {e}")
                    step.reflection = f"Reflection parsing failed: {str(e)}"
                    
            else:
                yield event