"""Unit tests for the framework-agnostic tool abstraction.

Verifies that the ``@tool`` decorator derives OpenAI-compatible function
schemas from signatures + Google-style docstrings, and that toolkits expose
lookup / invocation without depending on LangChain.
"""
from typing import Optional

import pytest

from app.domain.models.tool_result import ToolResult
from app.domain.services.tools.base import BaseToolkit, tool


class SampleToolkit(BaseToolkit):
    name = "sample"

    def __init__(self, backend):
        super().__init__()
        self.backend = backend

    @tool(parse_docstring=True)
    async def do_thing(self, id: str, count: Optional[int] = None) -> ToolResult:
        """Do a thing with an id. Use for testing.

        Args:
            id: The unique identifier
            count: (Optional) How many times
        """
        return await self.backend(id, count)


class _FakeBackend:
    def __init__(self):
        self.calls = []

    async def __call__(self, id, count):
        self.calls.append((id, count))
        return ToolResult(success=True, data=f"{id}:{count}")


class TestToolSchema:
    def setup_method(self):
        self.tk = SampleToolkit(backend=_FakeBackend())

    def test_toolkit_collects_tools(self):
        names = [t.name for t in self.tk.get_tools()]
        assert names == ["do_thing"]

    def test_openai_schema_shape(self):
        schema = self.tk.get_tool_schemas()[0]
        assert schema["type"] == "function"
        fn = schema["function"]
        assert fn["name"] == "do_thing"
        # summary line becomes the description (Args section stripped out)
        assert "Do a thing with an id" in fn["description"]
        assert "Args:" not in fn["description"]

    def test_parameter_descriptions_from_docstring(self):
        params = self.tk.get_tool_schemas()[0]["function"]["parameters"]
        assert params["type"] == "object"
        assert params["properties"]["id"]["description"] == "The unique identifier"
        assert "How many times" in params["properties"]["count"]["description"]

    def test_required_vs_optional(self):
        params = self.tk.get_tool_schemas()[0]["function"]["parameters"]
        assert "id" in params["required"]
        # count has a default -> not required
        assert "count" not in params["required"]

    def test_no_pydantic_title_leakage(self):
        params = self.tk.get_tool_schemas()[0]["function"]["parameters"]
        assert "title" not in params
        assert all("title" not in p for p in params["properties"].values())


class TestToolLookupAndInvoke:
    def setup_method(self):
        self.backend = _FakeBackend()
        self.tk = SampleToolkit(backend=self.backend)

    def test_get_tool(self):
        assert self.tk.get_tool("do_thing").name == "do_thing"
        assert self.tk.get_tool("missing") is None

    async def test_invoke_binds_toolkit_and_returns_result(self):
        tool_obj = self.tk.get_tool("do_thing")
        result = await tool_obj.invoke({"id": "abc", "count": 3})
        assert isinstance(result, ToolResult)
        assert result.data == "abc:3"
        assert self.backend.calls == [("abc", 3)]

    def test_tool_carries_toolkit_reference(self):
        assert self.tk.get_tool("do_thing").toolkit is self.tk
