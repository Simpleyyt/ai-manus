from typing import AsyncGenerator, List
import logging

from pydantic import ValidationError

from app.domain.external.llm import LLM
from app.domain.models.agent_output import FinalResult, StepReport
from app.domain.models.event import (
    BaseEvent,
    ErrorEvent,
    MessageEvent,
    StepEvent,
    StepStatus,
    ToolEvent,
    ToolStatus,
    WaitEvent,
)
from app.domain.models.file import FileInfo
from app.domain.models.message import LLMMessage, Message
from app.domain.models.plan import ExecutionStatus, Plan, Step
from app.domain.repositories.agent_repository import AgentRepository
from app.domain.services.agents.base import BaseAgent, StructuredOutputEvent
from app.domain.services.prompts.execution import (
    EXECUTION_ROLE_PROMPT,
    SUMMARIZE_PROMPT,
    build_execution_request,
    build_resume_request,
)
from app.domain.services.prompts.system import build_system_prompt
from app.domain.services.tools.base import BaseToolkit, OutputTool

logger = logging.getLogger(__name__)

COMPLETE_STEP_TOOL = OutputTool(
    name="complete_step",
    description=(
        "Report the outcome of the current plan step ONLY when its work is "
        "actually finished and verified (e.g. files saved and commands run). "
        "Do not call after partial scaffolding or with no tool work."
    ),
    schema=StepReport,
)

DELIVER_RESULT_TOOL = OutputTool(
    name="deliver_result",
    description="Deliver the final task result and its files to the user.",
    schema=FinalResult,
)

# Toolkits that count as real step work (not chat notify/ask).
_WORK_TOOLKITS = frozenset({"shell", "file", "browser", "search", "mcp"})


class ExecutionAgent(BaseAgent):
    """Execution agent: carries out one plan step with tools, then complete_step."""

    name: str = "execution"

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
        self._step_work_tool_calls = 0

    def build_system_prompt(self) -> str:
        return build_system_prompt(
            toolkits=self.toolkits,
            role_prompt=EXECUTION_ROLE_PROMPT,
            project_instruction=self._project_instruction,
        )

    def _reset_step_work_counter(self) -> None:
        self._step_work_tool_calls = 0

    async def invoke_tool(self, tool, tool_call):
        result = await super().invoke_tool(tool, tool_call)
        toolkit_name = getattr(getattr(tool, "toolkit", None), "name", None)
        if toolkit_name in _WORK_TOOLKITS:
            self._step_work_tool_calls += 1
        return result

    def _handle_output_call(self, tool_call):
        if not (
            self._output_tool
            and tool_call.name == self._output_tool.name
            and tool_call.name == "complete_step"
        ):
            return super()._handle_output_call(tool_call)

        try:
            output = self._output_tool.validate(tool_call.args)
        except ValidationError as e:
            logger.warning(
                "Structured output validation failed for %s: %s",
                tool_call.name,
                e,
            )
            return (
                LLMMessage.tool(
                    tool_call_id=tool_call.id,
                    name=tool_call.name,
                    content=(
                        f"Invalid arguments, please correct and call "
                        f"{tool_call.name} again: {e}"
                    ),
                ),
                None,
            )

        if getattr(output, "success", False) and self._step_work_tool_calls == 0:
            logger.info(
                "Rejecting complete_step(success=true) with no work tools yet"
            )
            return (
                LLMMessage.tool(
                    tool_call_id=tool_call.id,
                    name=tool_call.name,
                    content=(
                        "Rejected: you called complete_step(success=true) without "
                        "using any work tools (shell/file/browser/search/mcp) in "
                        "this step. Do the work and verify it, then call "
                        "complete_step again. If truly blocked, call "
                        "complete_step with success=false and explain why."
                    ),
                ),
                None,
            )

        return (
            LLMMessage.tool(
                tool_call_id=tool_call.id,
                name=tool_call.name,
                content='{"success": true}',
            ),
            output,
        )

    async def _fan_out_step(
        self,
        plan: Plan,
        step: Step,
        events,
    ) -> AsyncGenerator[BaseEvent, None]:
        async for event in events:
            if isinstance(event, ErrorEvent):
                step.status = ExecutionStatus.FAILED
                step.error = event.error
                yield StepEvent(status=StepStatus.FAILED, step=step)
            elif isinstance(event, StructuredOutputEvent):
                report: StepReport = event.output
                step.status = ExecutionStatus.COMPLETED
                step.success = report.success
                step.result = report.result
                step.attachments = report.attachments
                # Outcome stays on the StepEvent (chat timeline under StepGroup).
                # Do not also emit MessageEvent — that would break consecutive
                # stepGroup pb-0 connection in the UI.
                yield StepEvent(status=StepStatus.COMPLETED, step=step)
                continue
            elif isinstance(event, MessageEvent):
                continue
            elif isinstance(event, ToolEvent):
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

    async def execute_step(
        self, plan: Plan, step: Step, message: Message
    ) -> AsyncGenerator[BaseEvent, None]:
        self._reset_step_work_counter()
        request = build_execution_request(plan, step, message)
        step.status = ExecutionStatus.RUNNING
        yield StepEvent(status=StepStatus.STARTED, step=step)
        async for event in self._fan_out_step(
            plan,
            step,
            self.execute(request, output_tool=COMPLETE_STEP_TOOL),
        ):
            yield event

    async def resume_step(
        self, plan: Plan, step: Step
    ) -> AsyncGenerator[BaseEvent, None]:
        """Continue after message_ask_user with an explicit continue nudge."""
        # Keep prior work-tool count across wait/resume in the same step.
        request = build_resume_request(plan, step)
        step.status = ExecutionStatus.RUNNING
        async for event in self._fan_out_step(
            plan,
            step,
            self.execute(request, output_tool=COMPLETE_STEP_TOOL),
        ):
            yield event

    async def summarize(self) -> AsyncGenerator[BaseEvent, None]:
        async for event in self.execute(
            SUMMARIZE_PROMPT, output_tool=DELIVER_RESULT_TOOL
        ):
            if isinstance(event, StructuredOutputEvent):
                result: FinalResult = event.output
                attachments = [
                    FileInfo(file_path=file_path)
                    for file_path in result.attachments
                ]
                yield MessageEvent(message=result.message, attachments=attachments)
                continue
            if isinstance(event, MessageEvent):
                continue
            yield event
