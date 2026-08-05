from typing import AsyncGenerator, AsyncIterable, List

from app.domain.external.llm import LLM
from app.domain.models.agent_output import FinalResult
from app.domain.models.event import (
    BaseEvent,
    ErrorEvent,
    MessageEvent,
    TitleEvent,
    ToolEvent,
    ToolStatus,
    WaitEvent,
)
from app.domain.models.file import FileInfo
from app.domain.models.message import Message
from app.domain.models.todo import TodoItem
from app.domain.repositories.agent_repository import AgentRepository
from app.domain.services.agents.base import BaseAgent, StructuredOutputEvent
from app.domain.services.prompts.manus import MANUS_ROLE_PROMPT
from app.domain.services.prompts.system import build_system_prompt
from app.domain.services.todo_projection import project_todo_write
from app.domain.services.tools.base import BaseToolkit, OutputTool


DELIVER_RESULT_TOOL = OutputTool(
    name="deliver_result",
    description="Deliver the final task result and its files to the user.",
    schema=FinalResult,
)


def suggest_title(user_message: str, items: List[TodoItem]) -> str:
    if items:
        return items[0].content.strip()[:80] or "New task"
    text = (user_message or "").strip().replace("\n", " ")
    return text[:80] if text else "New task"


class ManusAgent(BaseAgent):
    name: str = "manus"

    def __init__(
        self,
        agent_id: str,
        agent_repository: AgentRepository,
        llm: LLM,
        tools: List[BaseToolkit],
    ):
        super().__init__(
            agent_id=agent_id,
            agent_repository=agent_repository,
            llm=llm,
            tools=tools,
        )
        self._todo_items: List[TodoItem] = []
        self._title_emitted = False
        self._user_message = ""

    def build_system_prompt(self) -> str:
        return build_system_prompt(
            toolkits=self.toolkits,
            role_prompt=MANUS_ROLE_PROMPT,
            project_instruction=self._project_instruction,
        )

    async def _fan_out(
        self,
        events: AsyncIterable[BaseEvent],
    ) -> AsyncGenerator[BaseEvent, None]:
        async for event in events:
            if isinstance(event, ToolEvent):
                if (
                    event.function_name == "todo_write"
                    and event.status == ToolStatus.CALLED
                ):
                    items = [
                        TodoItem.model_validate(item)
                        for item in event.function_args.get("items", [])
                    ]
                    created_plan = not self._todo_items and bool(items)
                    title = suggest_title(self._user_message, items)
                    projected = project_todo_write(
                        items,
                        previous_items=self._todo_items,
                        title=title,
                    )
                    self._todo_items = items
                    for projected_event in projected:
                        yield projected_event
                    if created_plan and not self._title_emitted and title:
                        self._title_emitted = True
                        yield TitleEvent(title=title)
                    continue

                if event.function_name == "message_ask_user":
                    if event.status == ToolStatus.CALLING:
                        yield MessageEvent(
                            message=event.function_args.get("text", "")
                        )
                    elif event.status == ToolStatus.CALLED:
                        yield WaitEvent()
                        return
                    continue

                yield event
                continue

            if isinstance(event, StructuredOutputEvent):
                result: FinalResult = event.output
                attachments = [
                    FileInfo(file_path=file_path)
                    for file_path in result.attachments
                ]
                yield MessageEvent(
                    message=result.message,
                    attachments=attachments,
                )
                return

            if isinstance(event, MessageEvent):
                continue

            if isinstance(event, ErrorEvent):
                yield event
                continue

            yield event

    async def run(self, message: Message) -> AsyncGenerator[BaseEvent, None]:
        self._user_message = message.message
        request = message.message
        if message.attachments:
            request += "\n\nAttachments:\n" + "\n".join(message.attachments)
        async for event in self._fan_out(
            self.execute(request, output_tool=DELIVER_RESULT_TOOL)
        ):
            yield event

    async def resume(self) -> AsyncGenerator[BaseEvent, None]:
        async for event in self._fan_out(
            self.continue_execute(output_tool=DELIVER_RESULT_TOOL)
        ):
            yield event
