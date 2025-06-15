from typing import Optional, AsyncGenerator
import asyncio
import logging
from app.domain.events.agent_events import (
    BaseEvent,
    ErrorEvent,
    TitleEvent,
    MessageEvent,
    DoneEvent,
    ToolEvent,
    WaitEvent,
    FileToolContent,
    ShellToolContent,
    SearchToolContent,
    ToolStatus
)
from app.domain.services.flows.plan_act import PlanActFlow
from app.domain.external.sandbox import Sandbox
from app.domain.external.browser import Browser
from app.domain.external.search import SearchEngine
from app.domain.external.llm import LLM
from app.domain.repositories.agent_repository import AgentRepository
from app.domain.external.task import TaskRunner, Task
from app.domain.repositories.session_repository import SessionRepository
from app.domain.models.session import SessionStatus
from app.domain.utils.json_parser import JsonParser

logger = logging.getLogger(__name__)

class AgentTaskRunner(TaskRunner):
    """Agent task that can be cancelled"""
    def __init__(
        self,
        session_id: str,
        agent_id: str,
        llm: LLM,
        sandbox: Sandbox,
        browser: Browser,
        agent_repository: AgentRepository,
        session_repository: SessionRepository,
        json_parser: JsonParser,
        search_engine: Optional[SearchEngine] = None,
    ):
        self._session_id = session_id
        self._agent_id = agent_id
        self._llm = llm
        self._sandbox = sandbox
        self._browser = browser
        self._search_engine = search_engine
        self._repository = agent_repository
        self._session_repository = session_repository
        self._json_parser = json_parser
        self._flow = PlanActFlow(
            self._agent_id,
            self._repository,
            self._session_id,
            self._session_repository,
            self._llm,
            self._sandbox,
            self._browser,
            self._json_parser,
            self._search_engine,
        )

    async def _put_and_add_event(self, task: Task, event: BaseEvent) -> None:
        event_id = await task.output_stream.put(event.model_dump_json())
        event.id = event_id
        await self._session_repository.add_event(self._session_id, event)
    
    async def _handle_tool_event(self, task: Task, event: ToolEvent) -> None:
        """Handle tool event"""
        if event.status == ToolStatus.CALLED:
            if event.tool_name == "browser":
                pass
            elif event.tool_name == "search":
                event.tool_content = SearchToolContent(results=event.function_result.data.get("results", []))
            elif event.tool_name == "shell":
                if "id" in event.function_args:
                    shell_result = await self._sandbox.view_shell(event.function_args["id"])
                    event.tool_content = ShellToolContent(console=shell_result.data.get("console", []))
                else:
                    event.tool_content = ShellToolContent(console="(No Console)")
            elif event.tool_name == "file":
                if "file" in event.function_args:
                    file_read_result = await self._sandbox.file_read(event.function_args["file"])
                    event.tool_content = FileToolContent(content=file_read_result.data.get("content", ""))
                else:
                    event.tool_content = FileToolContent(content="(No Content)")
            else:
                logger.warning(f"Agent {self._agent_id} received unknown tool event: {event.tool_name}")

    async def run(self, task: Task) -> None:
        """Process agent's message queue and run the agent's flow"""
        try:
            logger.info(f"Agent {self._agent_id} message processing task started")
            while not await task.input_stream.is_empty():
                _, message = await task.input_stream.pop()
                if message is None:
                    logger.warning(f"Agent {self._agent_id} received empty message")
                    return
                    
                logger.info(f"Agent {self._agent_id} received new message: {message[:50]}...")
                
                async for event in self._run_flow(message):
                    if isinstance(event, ToolEvent):
                        # TODO: move to tool function
                        await self._handle_tool_event(task, event)
                    await self._put_and_add_event(task, event)
                    if isinstance(event, TitleEvent):
                        await self._session_repository.update_title(self._session_id, event.title)
                    elif isinstance(event, MessageEvent):
                        await self._session_repository.update_latest_message(self._session_id, event.message, event.timestamp)
                        await self._session_repository.increment_unread_message_count(self._session_id)
                    elif isinstance(event, WaitEvent):
                        await self._session_repository.update_status(self._session_id, SessionStatus.WAITING)
                        return
                    if not await task.input_stream.is_empty():
                        break

            await self._session_repository.update_status(self._session_id, SessionStatus.COMPLETED)
        except asyncio.CancelledError:
            logger.info(f"Agent {self._agent_id} task cancelled")
            await self._put_and_add_event(task, DoneEvent())
            await self._session_repository.update_status(self._session_id, SessionStatus.COMPLETED)
        except Exception as e:
            logger.exception(f"Agent {self._agent_id} task encountered exception: {str(e)}")
            await self._put_and_add_event(task, ErrorEvent(error=f"Task error: {str(e)}"))
            await self._session_repository.update_status(self._session_id, SessionStatus.COMPLETED)
    
    async def _run_flow(self, message: str) -> AsyncGenerator[BaseEvent, None]:
        """Process a single message through the agent's flow and yield events"""
        if not message:
            logger.warning(f"Agent {self._agent_id} received empty message")
            yield ErrorEvent(error="No message")
            return

        async for event in self._flow.run(message):
            yield event

        logger.info(f"Agent {self._agent_id} completed processing one message")

    
    async def on_done(self, task: Task) -> None:
        """Called when the task is done"""
        logger.info(f"Agent {self._agent_id} task done")


    async def destroy(self) -> None:
        """Destroy the task and release resources"""
        logger.info(f"Starting to destroy agent task")
        
        # Destroy sandbox environment
        if self._sandbox:
            logger.debug(f"Destroying Agent {self._agent_id}'s sandbox environment")
            await self._sandbox.destroy()
        
        logger.debug(f"Agent {self._agent_id} has been fully closed and resources cleared")
