import logging
from typing import AsyncGenerator, Optional
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
        # Initialize base tools
        base_tools = [
            ShellTool(sandbox),
            BrowserTool(browser),
            FileTool(sandbox),
            MessageTool()
        ]
        
        # Add search tool when search_engine is not None
        if search_engine:
            base_tools.append(SearchTool(search_engine))
        
        super().__init__(
            agent_id=agent_id,
            agent_repository=agent_repository,
            llm=llm,
            json_parser=json_parser,
            tools=base_tools
        )
        
        # Initialize MCP tool eagerly to avoid tool_call issues
        self._mcp_tool = None
        self._mcp_tool_loaded = False
        # Schedule MCP tool loading in the background
        import asyncio
        asyncio.create_task(self._ensure_mcp_tool_loaded())
    
    async def _ensure_mcp_tool_loaded(self):
        """Ensure MCP tool is loaded and available"""
        if not self._mcp_tool_loaded:
            try:
                from app.infrastructure.services.mcp_initializer import mcp_initializer
                self._mcp_tool = await mcp_initializer.get_mcp_tool()
                if self._mcp_tool and self._mcp_tool not in self.tools:
                    self.tools.append(self._mcp_tool)
                    # Clear tools cache to force regeneration with new MCP tools
                    self._tools_cache = None
                self._mcp_tool_loaded = True
                if self._mcp_tool:
                    logger.info(f"ExecutionAgent {self._agent_id}: MCP HTTP tool loaded successfully")
                else:
                    logger.warning(f"ExecutionAgent {self._agent_id}: MCP HTTP tool not available")
            except Exception as e:
                logger.error(f"ExecutionAgent {self._agent_id}: Failed to load MCP HTTP tool: {e}")
                self._mcp_tool_loaded = True  # Mark as loaded to avoid repeated attempts
    
    async def execute_step(self, plan: Plan, step: Step) -> AsyncGenerator[BaseEvent, None]:
        # Ensure MCP tool is loaded before executing
        await self._ensure_mcp_tool_loaded()
        
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
        

    async def cleanup(self):
        """Clean up agent resources"""
        # MCP tool cleanup is handled globally by mcp_initializer
        # Individual agent instances don't need to clean up MCP connections
        logger.debug(f"ExecutionAgent {self._agent_id}: cleanup completed")

