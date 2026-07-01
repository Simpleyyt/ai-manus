"""Unit tests for the LangChain LLM gateway message translation.

Ensures the infrastructure gateway correctly converts between domain
:class:`LLMMessage` objects and LangChain message objects in both directions,
which is the boundary that keeps LangChain out of the domain.
"""
from langchain.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from app.domain.models.message import LLMMessage, Role, ToolCall
from app.infrastructure.external.llm.langchain_llm import LangchainLLM


def _gateway() -> LangchainLLM:
    # init_chat_model only constructs the client; no network call is made here.
    return LangchainLLM()


class TestToLangChain:
    def test_all_roles_converted(self):
        gw = _gateway()
        msgs = [
            LLMMessage.system("sys"),
            LLMMessage.user("hi"),
            LLMMessage.assistant("", tool_calls=[ToolCall(id="c1", name="shell_exec", args={"cmd": "ls"})]),
            LLMMessage.tool(tool_call_id="c1", name="shell_exec", content="{}"),
        ]
        lc = gw._to_langchain(msgs)
        assert isinstance(lc[0], SystemMessage)
        assert isinstance(lc[1], HumanMessage)
        assert isinstance(lc[2], AIMessage)
        assert lc[2].tool_calls[0]["name"] == "shell_exec"
        assert lc[2].tool_calls[0]["args"] == {"cmd": "ls"}
        assert isinstance(lc[3], ToolMessage)
        assert lc[3].tool_call_id == "c1"


class TestFromLangChain:
    def test_ai_message_with_tool_calls(self):
        gw = _gateway()
        ai = AIMessage(
            content="",
            tool_calls=[{"name": "file_read", "args": {"file": "/a"}, "id": "c2", "type": "tool_call"}],
        )
        m = gw._from_langchain(ai)
        assert m.role == Role.ASSISTANT
        assert m.tool_calls[0].name == "file_read"
        assert m.tool_calls[0].args == {"file": "/a"}
        assert m.tool_calls[0].id == "c2"

    def test_plain_ai_message(self):
        gw = _gateway()
        m = gw._from_langchain(AIMessage(content="hello"))
        assert m.role == Role.ASSISTANT and m.content == "hello" and m.tool_calls == []


class TestRoundTrip:
    def test_domain_to_lc_to_domain_preserves_tool_calls(self):
        gw = _gateway()
        original = LLMMessage.assistant(
            "text", tool_calls=[ToolCall(id="c3", name="info_search_web", args={"query": "x"})]
        )
        lc = gw._to_langchain([original])[0]
        back = gw._from_langchain(lc)
        assert back.content == "text"
        assert back.tool_calls[0].name == "info_search_web"
        assert back.tool_calls[0].args == {"query": "x"}
        assert back.tool_calls[0].id == "c3"
