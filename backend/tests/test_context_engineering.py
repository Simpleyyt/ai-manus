"""Unit tests for the redesigned context engineering.

Covers the composable system prompt, structured output via native function
calling (OutputTool + self-repair), token-aware memory compaction, tool
result truncation, and the dynamic MCP tool bridge. Pure unit tests — no
running backend required.
"""
import json
from typing import List, Optional

from pydantic import BaseModel

from app.domain.models.agent_output import PlanOutput, StepReport
from app.domain.models.memory import Memory, estimate_tokens
from app.domain.models.message import LLMMessage, Role, ToolCall
from app.domain.models.tool_result import ToolResult
from app.domain.services.agents.base import BaseAgent, StructuredOutputEvent
from app.domain.services.prompts.system import build_system_prompt
from app.domain.services.tools.base import (
    BaseToolkit,
    OutputTool,
    Tool,
    describe_toolkits,
    tool,
)


class EchoToolkit(BaseToolkit):
    name = "echo"
    instructions = "- Echo things back verbatim"

    @tool(parse_docstring=True)
    async def echo(self, text: str) -> ToolResult:
        """Echo the given text back.

        Args:
            text: Text to echo
        """
        return ToolResult(success=True, data=text)


class SilentToolkit(BaseToolkit):
    """Toolkit without instructions — must not add a prompt section."""

    name = "silent"

    @tool(parse_docstring=True)
    async def noop(self) -> ToolResult:
        """Do nothing."""
        return ToolResult(success=True)


class TestSystemPromptBuilder:
    def test_core_prompt_always_present(self):
        prompt = build_system_prompt()
        assert "You are Manus" in prompt
        assert "<sandbox_environment>" in prompt

    def test_bound_toolkit_contributes_section(self):
        prompt = build_system_prompt(toolkits=[EchoToolkit()])
        assert "<echo_rules>" in prompt
        assert "Echo things back verbatim" in prompt

    def test_toolkit_without_instructions_adds_no_section(self):
        prompt = build_system_prompt(toolkits=[SilentToolkit()])
        assert "<silent_rules>" not in prompt

    def test_role_prompt_appended(self):
        prompt = build_system_prompt(role_prompt="<role>planner</role>")
        assert prompt.endswith("<role>planner</role>")

    def test_describe_toolkits_compact_overview(self):
        overview = describe_toolkits([EchoToolkit(), SilentToolkit()])
        assert overview == "- echo: echo\n- silent: noop"


class TestOutputTool:
    def test_schema_shape(self):
        out = OutputTool("create_plan", "Submit the plan.", PlanOutput)
        schema = out.to_openai_schema()
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "create_plan"
        props = schema["function"]["parameters"]["properties"]
        assert set(props) == {"message", "language", "title", "goal", "steps"}

    def test_validate_success_and_failure(self):
        out = OutputTool("complete_step", "Report step.", StepReport)
        report = out.validate({"success": True, "result": "done"})
        assert report.success is True and report.attachments == []

        import pytest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            out.validate({"result": "missing success"})


class TestMemoryCompaction:
    def _memory_with_tool_results(self, n: int, size: int = 400) -> Memory:
        m = Memory()
        m.add_message(LLMMessage.system("sys"))
        for i in range(n):
            m.add_message(LLMMessage.assistant(
                "", tool_calls=[ToolCall(id=f"c{i}", name="echo", args={})]
            ))
            m.add_message(LLMMessage.tool(
                tool_call_id=f"c{i}", name="echo", content="x" * size
            ))
        return m

    def test_estimate_tokens_counts_content_and_calls(self):
        assert estimate_tokens("") == 0
        assert estimate_tokens("abcd" * 100) == 100
        m = self._memory_with_tool_results(2)
        assert m.estimate_tokens() > 0

    def test_unconditional_compact_elides_old_tool_results(self):
        m = self._memory_with_tool_results(10)
        m.compact(keep_recent=4)
        elided = [msg for msg in m.messages if "elided" in msg.content]
        assert elided, "old tool results should be elided"
        # The most recent messages are untouched.
        assert m.messages[-1].content == "x" * 400

    def test_budgeted_compact_stops_at_budget(self):
        m = self._memory_with_tool_results(10)
        before = m.estimate_tokens()
        m.compact(max_tokens=before + 1)  # already under budget: no-op
        assert all("elided" not in msg.content for msg in m.messages if msg.role == Role.TOOL)

        m.compact(max_tokens=before // 2, keep_recent=2)
        assert m.estimate_tokens() <= before // 2

    def test_compact_preserves_message_skeleton(self):
        m = self._memory_with_tool_results(5)
        count = len(m.messages)
        m.compact(keep_recent=0)
        assert len(m.messages) == count
        assert all(msg.role in (Role.SYSTEM, Role.ASSISTANT, Role.TOOL) for msg in m.messages)


class _FakeRepository:
    def __init__(self):
        self.memory = Memory()

    async def get_memory(self, agent_id: str, name: str) -> Memory:
        return self.memory

    async def save_memory(self, agent_id: str, name: str, memory: Memory) -> None:
        self.memory = memory


class _ScriptedLLM:
    """LLM stub returning scripted assistant messages in order."""

    def __init__(self, responses: List[LLMMessage]):
        self._responses = list(responses)
        self.requests = []

    async def ask(self, messages, tools=None, response_format=None, tool_choice=None):
        self.requests.append({"messages": list(messages), "tools": tools, "tool_choice": tool_choice})
        return self._responses.pop(0)

    async def parse_json(self, text: str):
        raise AssertionError("parse_json must not be used by the agent loop anymore")


class _TestAgent(BaseAgent):
    name = "test"

    def build_system_prompt(self) -> str:
        return "test system prompt"


def _agent(llm: _ScriptedLLM, toolkits: Optional[list] = None) -> _TestAgent:
    return _TestAgent(
        agent_id="a1",
        agent_repository=_FakeRepository(),
        llm=llm,
        tools=toolkits or [],
    )


REPORT_TOOL = OutputTool("complete_step", "Report the step outcome.", StepReport)


async def _collect(gen):
    return [event async for event in gen]


class TestAgentLoopStructuredOutput:
    async def test_output_tool_call_yields_structured_output(self):
        llm = _ScriptedLLM([
            LLMMessage.assistant("", tool_calls=[
                ToolCall(id="c1", name="complete_step",
                         args={"success": True, "result": "done", "attachments": []}),
            ]),
        ])
        agent = _agent(llm)
        events = await _collect(agent.execute("do it", output_tool=REPORT_TOOL))

        outputs = [e for e in events if isinstance(e, StructuredOutputEvent)]
        assert len(outputs) == 1
        assert outputs[0].output.result == "done"

        # Output tool schema was offered to the model.
        offered = [t["function"]["name"] for t in llm.requests[0]["tools"]]
        assert "complete_step" in offered

        # Memory stays consistent: the output call received a tool response.
        last = agent.memory.get_last_message()
        assert last.role == Role.TOOL and last.tool_call_id == "c1"

    async def test_invalid_output_args_trigger_self_repair(self):
        llm = _ScriptedLLM([
            # First attempt: missing required fields.
            LLMMessage.assistant("", tool_calls=[
                ToolCall(id="c1", name="complete_step", args={"success": True}),
            ]),
            # Second attempt: valid.
            LLMMessage.assistant("", tool_calls=[
                ToolCall(id="c2", name="complete_step",
                         args={"success": True, "result": "fixed"}),
            ]),
        ])
        agent = _agent(llm)
        events = await _collect(agent.execute("do it", output_tool=REPORT_TOOL))

        outputs = [e for e in events if isinstance(e, StructuredOutputEvent)]
        assert len(outputs) == 1 and outputs[0].output.result == "fixed"

        # The validation error was fed back as the tool response.
        error_feedback = [
            m for m in agent.memory.get_messages()
            if m.role == Role.TOOL and "Invalid arguments" in m.content
        ]
        assert len(error_feedback) == 1

    async def test_plain_message_is_nudged_to_output_tool(self):
        llm = _ScriptedLLM([
            LLMMessage.assistant("I think I'm done."),
            LLMMessage.assistant("", tool_calls=[
                ToolCall(id="c1", name="complete_step",
                         args={"success": True, "result": "ok"}),
            ]),
        ])
        agent = _agent(llm)
        events = await _collect(agent.execute("do it", output_tool=REPORT_TOOL))
        assert any(isinstance(e, StructuredOutputEvent) for e in events)
        # The nudge mentions the output tool by name.
        nudge = llm.requests[1]["messages"][-1]
        assert "complete_step" in nudge.content

    async def test_regular_tools_still_execute(self):
        llm = _ScriptedLLM([
            LLMMessage.assistant("", tool_calls=[
                ToolCall(id="c1", name="echo", args={"text": "hello"}),
            ]),
            LLMMessage.assistant("", tool_calls=[
                ToolCall(id="c2", name="complete_step",
                         args={"success": True, "result": "echoed"}),
            ]),
        ])
        agent = _agent(llm, toolkits=[EchoToolkit()])
        events = await _collect(agent.execute("echo hello", output_tool=REPORT_TOOL))
        assert any(isinstance(e, StructuredOutputEvent) for e in events)
        tool_msgs = [m for m in agent.memory.get_messages() if m.role == Role.TOOL and m.name == "echo"]
        assert len(tool_msgs) == 1
        assert json.loads(tool_msgs[0].content)["data"] == "hello"

    async def test_unknown_tool_gets_error_response(self):
        llm = _ScriptedLLM([
            LLMMessage.assistant("", tool_calls=[
                ToolCall(id="c1", name="not_a_tool", args={}),
            ]),
            LLMMessage.assistant("all done"),
        ])
        agent = _agent(llm)
        events = await _collect(agent.execute("do it"))
        # The dangling tool call was answered so the history stays valid.
        unknown = [
            m for m in agent.memory.get_messages()
            if m.role == Role.TOOL and "Unknown tool" in m.content
        ]
        assert len(unknown) == 1


class TestToolResultTruncation:
    async def test_oversized_tool_result_truncated(self):
        class BigToolkit(BaseToolkit):
            name = "big"

            @tool(parse_docstring=True)
            async def big(self) -> ToolResult:
                """Return something huge."""
                return ToolResult(success=True, data="y" * 100000)

        llm = _ScriptedLLM([
            LLMMessage.assistant("", tool_calls=[ToolCall(id="c1", name="big", args={})]),
            LLMMessage.assistant("done"),
        ])
        agent = _agent(llm, toolkits=[BigToolkit()])
        await _collect(agent.execute("go"))

        tool_msg = [m for m in agent.memory.get_messages() if m.role == Role.TOOL][0]
        assert len(tool_msg.content) <= agent.max_tool_result_chars + 100
        assert "truncated" in tool_msg.content


class TestDynamicMcpTools:
    def test_mcp_schemas_become_invocable_tools(self):
        from app.domain.services.tools.mcp import MCPToolkit

        toolkit = MCPToolkit()
        tools = toolkit._build_tools([
            {
                "type": "function",
                "function": {
                    "name": "mcp_server_lookup",
                    "description": "[server] Look something up",
                    "parameters": {"type": "object", "properties": {"q": {"type": "string"}}},
                },
            }
        ])
        toolkit.tools = tools
        found = toolkit.get_tool("mcp_server_lookup")
        assert isinstance(found, Tool)
        assert found.toolkit is toolkit
        assert toolkit.get_tool_schemas()[0]["function"]["name"] == "mcp_server_lookup"
