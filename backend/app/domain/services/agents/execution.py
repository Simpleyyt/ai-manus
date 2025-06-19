from typing import AsyncGenerator, Optional
import logging
from app.domain.models.plan import Plan, Step, ExecutionStatus
from app.domain.services.agents.base import BaseAgent
from app.domain.external.llm import LLM
from app.domain.external.sandbox import Sandbox
from app.domain.external.browser import Browser
from app.domain.external.search import SearchEngine
from app.domain.repositories.agent_repository import AgentRepository
from app.domain.services.prompts.execution import EXECUTION_SYSTEM_PROMPT, EXECUTION_PROMPT
from app.domain.events.agent_events import (
    BaseEvent,
    StepEvent,
    StepStatus,
    ErrorEvent,
    MessageEvent,
    DoneEvent,
)
from app.domain.services.tools.shell import ShellTool
from app.domain.services.tools.browser import BrowserTool
from app.domain.services.tools.search import SearchTool
from app.domain.services.tools.file import FileTool
from app.domain.services.tools.message import MessageTool
from app.domain.utils.json_parser import JsonParser
from app.domain.models.compression import AgentType

logger = logging.getLogger(__name__)


class ExecutionAgent(BaseAgent):
    """
    Execution agent class, defining the basic behavior of execution
    """

    name: str = "execution"
    system_prompt: str = EXECUTION_SYSTEM_PROMPT

    def __init__(
        self,
        agent_id: str,
        agent_repository: AgentRepository,
        llm: LLM,
        sandbox: Sandbox,
        browser: Browser,
        json_parser: JsonParser,
        search_engine: Optional[SearchEngine] = None,
    ):
        super().__init__(
            agent_id=agent_id,
            agent_repository=agent_repository,
            llm=llm,
            json_parser=json_parser,
            tools=[
                ShellTool(sandbox),
                BrowserTool(browser),
                FileTool(sandbox),
                MessageTool()
            ]
        )
        
        # Only add search tool when search_engine is not None
        if search_engine:
            self.tools.append(SearchTool(search_engine))
    
    async def execute_step(self, plan: Plan, step: Step) -> AsyncGenerator[BaseEvent, None]:
        # 在执行步骤前检查是否需要进行记忆管理
        if self.memory and self._memory_manager.should_compress_by_count(self.memory):
            logger.info("Execution agent memory size threshold reached, performing automatic cleanup before step execution")
            await self._memory_manager.auto_manage_memory(self.memory, AgentType.EXECUTION)
        
        message = EXECUTION_PROMPT.format(goal=plan.goal, step=step.description)
        step.status = ExecutionStatus.RUNNING
        yield StepEvent(status=StepStatus.STARTED, step=step)
        async for event in self.execute(message):
            if isinstance(event, ErrorEvent):
                step.status = ExecutionStatus.FAILED
                step.error = event.error
                yield StepEvent(status=StepStatus.FAILED, step=step)
            
            if isinstance(event, MessageEvent):
                step.status = ExecutionStatus.COMPLETED
                step.result = event.message
                yield StepEvent(status=StepStatus.COMPLETED, step=step)
            yield event
        step.status = ExecutionStatus.COMPLETED

