"""Unit tests for the OpenAI SDK LLM gateway.

Ensures the infrastructure gateway correctly converts between domain
:class:`LLMMessage` objects and OpenAI chat-completion payloads/responses in
both directions, plus its local JSON extraction/repair helpers. These tests
build the client without making any network calls.
"""
import json
from types import SimpleNamespace

import pytest

from app.core.config import Settings
from app.domain.models.message import LLMMessage, Role, ToolCall
from app.infrastructure.external.llm.openai_llm import (
    OpenAILLM,
    _ToolArgsParseError,
    _extract_json_object,
)


def _gateway() -> OpenAILLM:
    # Constructing AsyncOpenAI only builds the client; no network call is made.
    return OpenAILLM(settings=Settings(api_key="test", api_base=None))


def _resp(content=None, tool_calls=None):
    """Build a fake OpenAI response message object."""
    tcs = []
    for i, (name, args) in enumerate(tool_calls or []):
        tcs.append(
            SimpleNamespace(
                id=f"call_{i}",
                type="function",
                function=SimpleNamespace(name=name, arguments=args),
            )
        )
    return SimpleNamespace(content=content, tool_calls=tcs or None)


class TestToOpenAI:
    def test_all_roles_converted(self):
        gw = _gateway()
        msgs = [
            LLMMessage.system("sys"),
            LLMMessage.user("hi"),
            LLMMessage.assistant(
                "", tool_calls=[ToolCall(id="c1", name="shell_exec", args={"cmd": "ls"})]
            ),
            LLMMessage.tool(tool_call_id="c1", name="shell_exec", content="{}"),
        ]
        payload = gw._to_openai(msgs)

        assert payload[0] == {"role": "system", "content": "sys"}
        assert payload[1] == {"role": "user", "content": "hi"}

        assistant = payload[2]
        assert assistant["role"] == "assistant"
        assert assistant["content"] is None  # null content allowed with tool_calls
        tc = assistant["tool_calls"][0]
        assert tc["id"] == "c1"
        assert tc["type"] == "function"
        assert tc["function"]["name"] == "shell_exec"
        assert json.loads(tc["function"]["arguments"]) == {"cmd": "ls"}

        tool = payload[3]
        assert tool == {"role": "tool", "tool_call_id": "c1", "content": "{}"}


class TestFromOpenAI:
    def test_message_with_tool_calls(self):
        gw = _gateway()
        m = gw._from_openai(
            _resp(tool_calls=[("file_read", '{"file": "/a"}')])
        )
        assert m.role == Role.ASSISTANT
        assert m.tool_calls[0].name == "file_read"
        assert m.tool_calls[0].args == {"file": "/a"}
        assert m.tool_calls[0].id == "call_0"

    def test_plain_message(self):
        gw = _gateway()
        m = gw._from_openai(_resp(content="hello"))
        assert m.role == Role.ASSISTANT and m.content == "hello" and m.tool_calls == []

    def test_none_content_becomes_empty_string(self):
        gw = _gateway()
        m = gw._from_openai(_resp(content=None, tool_calls=[("f", "{}")]))
        assert m.content == ""

    def test_empty_arguments_become_empty_dict(self):
        gw = _gateway()
        m = gw._from_openai(_resp(tool_calls=[("noargs", "")]))
        assert m.tool_calls[0].args == {}

    def test_markdown_fenced_arguments_repaired(self):
        gw = _gateway()
        m = gw._from_openai(
            _resp(tool_calls=[("f", '```json\n{"x": 1}\n```')])
        )
        assert m.tool_calls[0].args == {"x": 1}

    def test_unparseable_arguments_raise(self):
        gw = _gateway()
        with pytest.raises(_ToolArgsParseError):
            gw._from_openai(_resp(tool_calls=[("f", "not json at all")]))


class TestRoundTrip:
    def test_domain_to_openai_to_domain_preserves_tool_calls(self):
        gw = _gateway()
        original = LLMMessage.assistant(
            "text",
            tool_calls=[ToolCall(id="c3", name="info_search_web", args={"query": "x"})],
        )
        payload = gw._to_openai([original])[0]
        rebuilt = _resp(
            content=payload["content"],
            tool_calls=[
                (tc["function"]["name"], tc["function"]["arguments"])
                for tc in payload["tool_calls"]
            ],
        )
        back = gw._from_openai(rebuilt)
        assert back.content == "text"
        assert back.tool_calls[0].name == "info_search_web"
        assert back.tool_calls[0].args == {"query": "x"}


class TestExtractJsonObject:
    def test_plain(self):
        assert _extract_json_object('{"a": 1}') == {"a": 1}

    def test_markdown_fence(self):
        assert _extract_json_object('```json\n{"a": 1}\n```') == {"a": 1}

    def test_surrounding_text(self):
        assert _extract_json_object('here you go: {"a": 1} thanks') == {"a": 1}

    def test_not_json(self):
        assert _extract_json_object("nope") is None

    def test_none(self):
        assert _extract_json_object(None) is None


class TestParseJsonLocal:
    async def test_local_extraction_no_network(self):
        gw = _gateway()
        assert await gw.parse_json('{"ok": true}') == {"ok": True}
