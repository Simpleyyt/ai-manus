"""Unit tests for the infrastructure memory persistence adapter.

This is the anti-corruption layer that keeps historical wire-format knowledge
(LangChain ``type`` discriminated, and the older OpenAI ``role`` shape) out of
the domain, upgrading persisted blobs into native domain messages.
"""
from app.domain.models.message import LLMMessage, Role, ToolCall
from app.domain.models.memory import Memory
from app.infrastructure.models.memory_serialization import (
    deserialize_memory,
    serialize_memory,
)


class TestLegacyOpenAIFormat:
    def test_openai_tool_call_and_tool_message(self):
        raw = {
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
        m = deserialize_memory(raw)
        assert [x.role for x in m.messages] == [Role.SYSTEM, Role.ASSISTANT, Role.TOOL]
        tc = m.messages[1].tool_calls[0]
        assert tc.name == "shell_exec" and tc.args == {"cmd": "ls"}
        assert m.messages[1].content == ""  # None coerced
        # tool message name recovered from legacy "function_name"
        assert m.messages[2].name == "shell_exec"

    def test_invalid_string_args_default_empty(self):
        raw = {"messages": [
            {"role": "assistant", "tool_calls": [
                {"id": "1", "function": {"name": "t", "arguments": "not json"}}
            ]}
        ]}
        m = deserialize_memory(raw)
        assert m.messages[0].tool_calls[0].args == {}


class TestLegacyLangChainFormat:
    def test_type_discriminator_mapped_to_role(self):
        raw = {
            "messages": [
                {"type": "system", "content": "sys", "name": None, "id": None},
                {
                    "type": "ai",
                    "content": "",
                    "tool_calls": [
                        {"name": "shell_exec", "args": {"cmd": "ls"}, "id": "call_1", "type": "tool_call"}
                    ],
                    "invalid_tool_calls": [],
                    "additional_kwargs": {},
                    "response_metadata": {},
                },
                {"type": "tool", "content": "{}", "name": "shell_exec", "tool_call_id": "call_1", "status": "success"},
            ]
        }
        m = deserialize_memory(raw)
        assert [x.role for x in m.messages] == [Role.SYSTEM, Role.ASSISTANT, Role.TOOL]
        tc = m.messages[1].tool_calls[0]
        assert tc.name == "shell_exec" and tc.args == {"cmd": "ls"} and tc.id == "call_1"
        # framework-only extras (additional_kwargs, status, ...) are dropped
        assert m.messages[2].name == "shell_exec"

    def test_human_maps_to_user(self):
        m = deserialize_memory({"messages": [{"type": "human", "content": "hi"}]})
        assert m.messages[0].role == Role.USER


class TestNativeAndRoundTrip:
    def test_empty_and_none(self):
        assert deserialize_memory(None).messages == []
        assert deserialize_memory({}).messages == []

    def test_native_round_trip(self):
        mem = Memory(messages=[
            LLMMessage.system("sys"),
            LLMMessage.assistant("", tool_calls=[ToolCall(id="1", name="shell_exec", args={"cmd": "ls"})]),
            LLMMessage.tool(tool_call_id="1", name="shell_exec", content="{}", artifact={"drop": "me"}),
        ])
        blob = serialize_memory(mem)
        # artifact must never be persisted
        assert all("artifact" not in msg for msg in blob["messages"])
        restored = deserialize_memory(blob)
        assert [x.role for x in restored.messages] == [Role.SYSTEM, Role.ASSISTANT, Role.TOOL]
        assert restored.messages[1].tool_calls[0].args == {"cmd": "ls"}
        assert restored.messages[2].name == "shell_exec"
