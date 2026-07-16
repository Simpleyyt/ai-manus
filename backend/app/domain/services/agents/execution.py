from typing import AsyncGenerator, List
from app.domain.models.plan import Plan, Step, ExecutionStatus
from app.domain.models.file import FileInfo
from app.domain.models.message import Message
from app.domain.models.agent_output import StepReport, FinalResult
from app.domain.services.agents.base import BaseAgent, StructuredOutputEvent
from app.domain.repositories.agent_repository import AgentRepository
from app.domain.services.prompts.system import build_system_prompt
from app.domain.services.prompts.execution import EXECUTION_ROLE_PROMPT, EXECUTION_PROMPT, SUMMARIZE_PROMPT
from app.domain.models.event import (
    BaseEvent,
    StepEvent,
    StepStatus,
    ErrorEvent,
    MessageEvent,
    ToolEvent,
    ToolStatus,
    WaitEvent,
)
from app.domain.services.tools.base import BaseToolkit, OutputTool
from app.domain.external.llm import LLM
import logging

logger = logging.getLogger(__name__)

COMPLETE_STEP_TOOL = OutputTool(
    name="complete_step",
    description="Report the outcome of the current plan step when it is finished or cannot proceed.",
    schema=StepReport,
)

DELIVER_RESULT_TOOL = OutputTool(
    name="deliver_result",
    description="Deliver the final task result and its files to the user.",
    schema=FinalResult,
)


class ExecutionAgent(BaseAgent):
    """Execution agent: carries out plan steps with tools.

    Uses native tool calling end-to-end: work tools during the step, and the
    ``complete_step`` / ``deliver_result`` output tools to submit structured
    results — no JSON-in-prompt protocol.
    """

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
            tools=tools
        )

    def build_system_prompt(self) -> str:
        return build_system_prompt(
            toolkits=self.toolkits,
            role_prompt=EXECUTION_ROLE_PROMPT,
        )

    async def execute_step(self, plan: Plan, step: Step, message: Message) -> AsyncGenerator[BaseEvent, None]:
        request = EXECUTION_PROMPT.format(
            step=step.description,
            message=message.message,
            attachments="\n".join(message.attachments),
            language=plan.language
        )
        step.status = ExecutionStatus.RUNNING
        yield StepEvent(status=StepStatus.STARTED, step=step)
        async for event in self.execute(request, output_tool=COMPLETE_STEP_TOOL):
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
                yield StepEvent(status=StepStatus.COMPLETED, step=step)
                if step.result:
                    yield MessageEvent(message=step.result)
                continue
            elif isinstance(event, MessageEvent):
                # Plain assistant text without a step report: surface it but
                # keep the step lifecycle driven by complete_step.
                continue
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

    async def summarize(self) -> AsyncGenerator[BaseEvent, None]:
        async for event in self.execute(SUMMARIZE_PROMPT, output_tool=DELIVER_RESULT_TOOL):
            if isinstance(event, StructuredOutputEvent):
                result: FinalResult = event.output
                logger.debug(f"Execution agent summary: {result.message}")
                attachments = [FileInfo(file_path=file_path) for file_path in result.attachments]
                yield MessageEvent(message=result.message, attachments=attachments)
                continue
            if isinstance(event, MessageEvent):
                continue
            yield event
