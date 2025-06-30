from typing import AsyncGenerator, Optional, List
from datetime import datetime
import logging
from app.domain.models.plan import Plan, Step, ExecutionStatus
from app.domain.models.file import FileInfo
from app.domain.services.agents.base import BaseAgent
from app.domain.external.llm import LLM
from app.domain.external.sandbox import Sandbox
from app.domain.external.browser import Browser
from app.domain.external.search import SearchEngine
from app.domain.repositories.agent_repository import AgentRepository
from app.domain.services.prompts.execution_for_cybersecurity import EXECUTION_SYSTEM_PROMPT, EXECUTION_PROMPT, CONCLUSION_PROMPT
from app.domain.events.agent_events import (
    BaseEvent,
    StepEvent,
    StepStatus,
    ErrorEvent,
    MessageEvent,
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
from app.domain.models.compression import AgentType

from app.domain.external.mcp_config import MCPConfigProvider

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
        mcp_config_provider: Optional[MCPConfigProvider] = None,
    ):
        # Create MCP tool instance with config provider
        self.mcp_tool = MCPTool(mcp_config_provider)
        
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
    
    async def execute_step(self, plan: Plan, step: Step, message: str = "", attachments: List[str] = []) -> AsyncGenerator[BaseEvent, None]:
        # 在执行步骤前检查是否需要进行记忆管理
        if self.memory and self._memory_manager.should_compress_by_count(self.memory):
            logger.info("Execution agent memory size threshold reached, performing automatic cleanup before step execution")
            compressed = await self._memory_manager.auto_manage_memory(self.memory, AgentType.EXECUTION)
            # 🔧 修复：如果发生了压缩，立即保存
            if compressed:
                await self._repository.save_memory(self._agent_id, self.name, self.memory)
                logger.info("Execution agent memory compressed and saved")
        
        message = EXECUTION_PROMPT.format(goal=plan.goal, step=step.description,
                        message=message, date=datetime.now().strftime("%Y-%m-%d"), attachments=attachments)

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
                        yield MessageEvent(message=event.function_args.get("text", ""))
                    elif event.status == ToolStatus.CALLED:
                        yield WaitEvent()
                        return
                    continue
            yield event
        step.status = ExecutionStatus.COMPLETED

    async def conclusion(self) -> AsyncGenerator[BaseEvent, None]:
        message = CONCLUSION_PROMPT
        async for event in self.execute(message, format="json_object"):
            if isinstance(event, MessageEvent):
                logger.debug(f"Execution agent conclusion: {event.message}")
                parsed_response = await self.json_parser.parse(event.message)
                attachments = [FileInfo(file_path=file_path) for file_path in parsed_response.get("attachments", [])]
                yield MessageEvent(message=parsed_response.get("message", ""), attachments=attachments)
                continue
            yield event
    
    async def cleanup(self):
        """清理资源"""
        for tool in self.tools:
            if hasattr(tool, 'cleanup'):
                try:
                    await tool.cleanup()
                except Exception as e:
                    logger.error(f"清理工具 {tool.name} 失败: {e}")
