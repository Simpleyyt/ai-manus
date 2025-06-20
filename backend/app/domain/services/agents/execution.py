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
    ToolEvent,
    ToolStatus,
    WaitEvent,
)
from app.domain.services.tools.shell import ShellTool
from app.domain.services.tools.browser import BrowserTool
from app.domain.services.tools.search import SearchTool
from app.domain.services.tools.file import FileTool
from app.domain.services.tools.message import MessageTool
from app.domain.services.tools.mcp import MCPTool
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
        # Create MCP tool instance
        self.mcp_tool = MCPTool()
        
        super().__init__(
            agent_id=agent_id,
            agent_repository=agent_repository,
            llm=llm,
            json_parser=json_parser,
            tools=[
                ShellTool(sandbox),
                BrowserTool(browser),
                FileTool(sandbox),
                MessageTool(),
                self.mcp_tool
            ]
        )
        
        # Only add search tool when search_engine is not None
        if search_engine:
            self.tools.append(SearchTool(search_engine))
    
    async def initialize(self):
        """Initialize the agent and all its tools"""
        # Ensure MCP tool is initialized at agent startup
        await self.mcp_tool._ensure_initialized()
        logger.info("ExecutionAgent initialized successfully with MCP tools")
    
    async def get_available_tools_async(self):
        """Override to ensure MCP tool is initialized before getting tools"""
        # Ensure MCP tool is initialized
        if hasattr(self.mcp_tool, '_ensure_initialized'):
            await self.mcp_tool._ensure_initialized()
        
        # Call parent method to get all tools
        return await super().get_available_tools_async()
    
    async def execute_step(self, plan: Plan, step: Step, message: str = "") -> AsyncGenerator[BaseEvent, None]:
        message = EXECUTION_PROMPT.format(goal=plan.goal, step=step.description, message=message)
        step.status = ExecutionStatus.RUNNING
        yield StepEvent(status=StepStatus.STARTED, step=step)
        async for event in self.execute(message):
            if isinstance(event, ErrorEvent):
                step.status = ExecutionStatus.FAILED
                step.error = event.error
                yield StepEvent(status=StepStatus.FAILED, step=step)
            elif isinstance(event, MessageEvent):
                step.status = ExecutionStatus.COMPLETED
                step.result = event.message
                yield StepEvent(status=StepStatus.COMPLETED, step=step)
            elif isinstance(event, ToolEvent):
                if event.function_name == "message_ask_user":
                    if event.status == ToolStatus.CALLING:
                        yield MessageEvent(message=event.function_args["text"], role="assistant")
                    elif event.status == ToolStatus.CALLED:
                        yield WaitEvent()
                        return
                    continue
            yield event
        step.status = ExecutionStatus.COMPLETED
    
    async def cleanup(self):
        """清理资源"""
        for tool in self.tools:
            if hasattr(tool, 'cleanup'):
                try:
                    await tool.cleanup()
                except Exception as e:
                    logger.error(f"清理工具 {tool.name} 失败: {e}")
