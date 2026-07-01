"""Unit tests for domain-native message types and legacy-format compatibility.

These tests guard the anti-corruption layer that lets the framework-agnostic
``LLMMessage`` model read the two historical persisted shapes (LangChain
``model_dump`` and the older OpenAI chat shape) as well as its own shape.
"""
from app.domain.models.message import LLMMessage, Role, ToolCall
from app.domain.models.memory import Memory


class TestLLMMessageNative:
    def test_convenience_constructors(self):
        assert LLMMessage.system("s").role == Role.SYSTEM
        assert LLMMessage.user("u").role == Role.USER
        a = LLMMessage.assistant("a", tool_calls=[ToolCall(id="1", name="t", args={"x": 1})])
        assert a.role == Role.ASSISTANT
        assert a.tool_calls[0].name == "t"
        t = LLMMessage.tool(tool_call_id="1", name="t", content="c")
        assert t.role == Role.TOOL and t.tool_call_id == "1" and t.name == "t"

    def test_content_none_becomes_empty(self):
        m = LLMMessage.model_validate({"role": "assistant", "content": None})
        assert m.content == ""

    def test_artifact_excluded_from_dump(self):
        m = LLMMessage.tool(tool_call_id="x", name="t", content="c", artifact={"big": "obj"})
        assert m.artifact == {"big": "obj"}
        assert "artifact" not in m.model_dump()

    def test_toolcall_string_args_parsed(self):
        tc = ToolCall.model_validate({"id": "1", "name": "t", "args": '{"a": 1}'})
        assert tc.args == {"a": 1}

    def test_toolcall_invalid_string_args_defaults_empty(self):
        tc = ToolCall.model_validate({"name": "t", "args": "not json"})
        assert tc.args == {}


class TestLegacyOpenAIFormat:
    def test_openai_tool_call_and_tool_message(self):
        data = {
            "messages": [
                {"role": "system", "content": "sys"},
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": None,
                            "type": "function",
                            "function": {"name": "shell_exec", "arguments": '{"cmd": "ls"}'},
                        }
                    ],
                },
                {"role": "tool", "function_name": "shell_exec", "tool_call_id": "abc", "content": "{}"},
            ]
        }
        m = Memory.model_validate(data)
        assert [x.role for x in m.messages] == [Role.SYSTEM, Role.ASSISTANT, Role.TOOL]
        tc = m.messages[1].tool_calls[0]
        assert tc.name == "shell_exec" and tc.args == {"cmd": "ls"}
        # tool message name recovered from legacy "function_name"
        assert m.messages[2].name == "shell_exec"


class TestLegacyLangChainFormat:
    def test_langchain_type_discriminator_mapped_to_role(self):
        data = {
            "messages": [
                {"type": "system", "content": "sys", "name": None, "id": None},
                {
                    "type": "ai",
                    "content": "",
                    "tool_calls": [
                        {"name": "shell_exec", "args": {"cmd": "ls"}, "id": "call_1", "type": "tool_call"}
                    ],
                    "invalid_tool_calls": [],
                },
                {"type": "tool", "content": "{}", "name": "shell_exec", "tool_call_id": "call_1", "status": "success"},
            ]
        }
        m = Memory.model_validate(data)
        assert [x.role for x in m.messages] == [Role.SYSTEM, Role.ASSISTANT, Role.TOOL]
        tc = m.messages[1].tool_calls[0]
        assert tc.name == "shell_exec" and tc.args == {"cmd": "ls"} and tc.id == "call_1"
        # extra langchain-only fields (additional_kwargs, status, ...) are ignored
        assert m.messages[2].name == "shell_exec"

    def test_human_maps_to_user(self):
        m = LLMMessage.model_validate({"type": "human", "content": "hi"})
        assert m.role == Role.USER


class TestMemoryOperations:
    def _memory(self):
        m = Memory()
        m.add_message(LLMMessage.system("sys"))
        m.add_message(LLMMessage.user("hi"))
        m.add_message(LLMMessage.assistant("", tool_calls=[ToolCall(id="1", name="browser_view", args={})]))
        m.add_message(LLMMessage.tool(tool_call_id="1", name="browser_view", content="huge page content"))
        return m

    def test_empty(self):
        assert Memory().empty is True
        assert self._memory().empty is False

    def test_roll_back(self):
        m = self._memory()
        n = len(m.messages)
        m.roll_back()
        assert len(m.messages) == n - 1

    def test_compact_strips_browser_tool_output(self):
        m = self._memory()
        m.compact()
        tool_msg = m.messages[-1]
        assert "huge page content" not in tool_msg.content
        assert "(removed)" in tool_msg.content
