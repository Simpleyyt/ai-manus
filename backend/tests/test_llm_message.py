"""Unit tests for domain-native message types.

The domain ``LLMMessage`` model is framework-agnostic and only understands its
own native shape. Adapting historical persisted formats is the infrastructure
layer's job and is tested separately in ``test_memory_serialization.py``.
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

    def test_toolcall_native_shape(self):
        tc = ToolCall(id="1", name="t", args={"a": 1})
        assert tc.args == {"a": 1} and tc.name == "t" and tc.id == "1"


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

    def test_compact_elides_old_tool_output(self):
        m = self._memory()
        m.compact(keep_recent=0)
        tool_msg = m.messages[-1]
        assert "huge page content" not in tool_msg.content
        assert "elided" in tool_msg.content

    def test_compact_keeps_recent_tool_output(self):
        m = self._memory()
        m.compact()  # default keep_recent window covers all 4 messages
        assert m.messages[-1].content == "huge page content"
