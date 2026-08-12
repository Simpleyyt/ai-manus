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
from app.domain.models.message import LLMMessage, Message, Role, ToolCall
from app.domain.models.todo import TodoItem
from app.domain.models.tool_result import ToolResult
from app.domain.repositories.agent_repository import AgentRepository
from app.domain.services.agents.base import BaseAgent, StructuredOutputEvent
from app.domain.services.prompts.manus import MANUS_ROLE_PROMPT
from app.domain.services.prompts.system import build_system_prompt
from app.domain.services.tools.base import BaseToolkit, OutputTool


DELIVER_RESULT_TOOL = OutputTool(
    name="deliver_result",
    description="Deliver the final task result and its files to the user.",
    schema=FinalResult,
)

# Chat / wait surface — may run before other work.
# plan_report / replan stay outside this set so notify-before-work applies;
# AgentLoopFlow intercepts their ToolEvents after Manus yields them.
_CONTROL_TOOLS = frozenset({
    "message_notify_user",
    "message_ask_user",
})

# Allowed after every plan step is done (until deliver_result / replan adds work).
_AFTER_PLAN_DONE_TOOLS = frozenset({
    "message_notify_user",
    "message_ask_user",
    "plan_report",
    "replan",
})

_NOTIFY_REQUIRED_BEFORE_WORK = (
    "Blocked: call message_notify_user first with a brief acknowledgment "
    "in the user's language, then retry this work tool."
)

_PLAN_FINISHED_BLOCK = (
    "Blocked: all authoritative plan steps are already completed or failed. "
    "Call deliver_result now with the final answer (and attachments). "
    "Call replan only if new remaining work is genuinely required."
)


def suggest_title(user_message: str) -> str:
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
        # Kept for AgentLoopFlow wait-resume / plan completion (session plan).
        self._todo_items: List[TodoItem] = []
        self._plan_title: str | None = None
        self._plan_goal: str | None = None
        self._title_emitted = False
        self._user_notified = False
        self._user_message = ""
        self._injected_plan_text: str | None = None
        self._injected_plan_complete_hint: str | None = None
        self._plan_finished = False

    def build_system_prompt(self) -> str:
        return build_system_prompt(
            toolkits=self.toolkits,
            role_prompt=MANUS_ROLE_PROMPT,
            project_instruction=self._project_instruction,
        )

    async def invoke_tool(self, tool, tool_call: ToolCall) -> LLMMessage:
        """Require a brief notify before shell/browser/file/search/mcp."""
        name = tool_call.name
        if name not in _CONTROL_TOOLS and not self._user_notified:
            result = ToolResult(
                success=False,
                message=_NOTIFY_REQUIRED_BEFORE_WORK,
            )
            return LLMMessage.tool(
                tool_call_id=tool_call.id,
                name=name,
                content=result.model_dump_json(),
                artifact=result,
            )
        if (
            self._plan_finished
            and name not in _AFTER_PLAN_DONE_TOOLS
        ):
            result = ToolResult(
                success=False,
                message=_PLAN_FINISHED_BLOCK,
            )
            return LLMMessage.tool(
                tool_call_id=tool_call.id,
                name=name,
                content=result.model_dump_json(),
                artifact=result,
            )
        return await super().invoke_tool(tool, tool_call)

    async def ask_with_messages(self, messages: List[LLMMessage]) -> LLMMessage:
        if self._injected_plan_text:
            for message in reversed(messages):
                if message.role == Role.TOOL and message.name == "replan":
                    message.content += f"\n\n{self._injected_plan_text}"
                    self._injected_plan_text = None
                    break
        if self._injected_plan_complete_hint:
            for message in reversed(messages):
                if message.role == Role.TOOL and message.name == "plan_report":
                    message.content += f"\n\n{self._injected_plan_complete_hint}"
                    self._injected_plan_complete_hint = None
                    break
        return await super().ask_with_messages(messages)

    async def _fan_out(
        self,
        events: AsyncIterable[BaseEvent],
    ) -> AsyncGenerator[BaseEvent, None]:
        async for event in events:
            if isinstance(event, ToolEvent):
                # Hide gated work-tool attempts (before notify) from the timeline.
                if (
                    event.function_name not in _CONTROL_TOOLS
                    and not self._user_notified
                ):
                    continue

                # Hide work tools blocked after the plan is fully finished.
                if (
                    self._plan_finished
                    and event.function_name not in _AFTER_PLAN_DONE_TOOLS
                ):
                    continue

                if event.function_name == "message_notify_user":
                    if event.status == ToolStatus.CALLING:
                        text = (event.function_args or {}).get("text", "")
                        if isinstance(text, str) and text.strip():
                            self._user_notified = True
                            yield MessageEvent(message=text.strip())
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
                if not self._title_emitted:
                    title = self._plan_title or suggest_title(self._user_message)
                    if title:
                        self._plan_title = title
                        self._title_emitted = True
                        yield TitleEvent(title=title)
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
