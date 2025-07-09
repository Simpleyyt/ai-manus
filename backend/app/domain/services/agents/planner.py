from typing import Dict, Any, List, AsyncGenerator, Optional
import json
import logging
from app.domain.models.plan import Plan, Step
from app.domain.services.agents.base import BaseAgent
from app.domain.models.memory import Memory
from app.domain.external.llm import LLM
from app.domain.services.prompts.planner import (
    PLANNER_SYSTEM_PROMPT, 
    CREATE_PLAN_PROMPT, 
    UPDATE_PLAN_PROMPT
)
from app.domain.events.agent_events import (
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
    system_prompt: str = PLANNER_SYSTEM_PROMPT
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


    async def create_plan(self, message: Optional[str] = None, attachments: List[str] = []) -> AsyncGenerator[BaseEvent, None]:
        message = CREATE_PLAN_PROMPT.format(user_message=message, attachments=attachments) if message else None
        async for event in self.execute(message):
            if isinstance(event, MessageEvent):
                logger.info(event.message)
                parsed_response = await self.json_parser.parse(event.message)
                steps = [Step(id=step["id"], description=step["description"]) for step in parsed_response["steps"]]
                plan = Plan(id=f"plan_{len(steps)}", goal=parsed_response["goal"], title=parsed_response["title"], steps=steps, message=parsed_response["message"], todo=parsed_response.get("todo", ""))
                yield PlanEvent(status=PlanStatus.CREATED, plan=plan)
            else:
                yield event

    async def update_plan(self, plan: Plan) -> AsyncGenerator[BaseEvent, None]:
        message = UPDATE_PLAN_PROMPT.format(plan=plan.model_dump_json(include={"steps"}), goal=plan.goal)
        async for event in self.execute(message):
            if isinstance(event, MessageEvent):
                logger.debug(f"Planner agent update plan: {event.message}")
                parsed_response = await self.json_parser.parse(event.message)
                new_steps = [Step(id=step["id"], description=step["description"]) for step in parsed_response["steps"]]
                
                # Find the index of the first pending step
                first_pending_index = None
                for i, step in enumerate(plan.steps):
                    if not step.is_done():
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