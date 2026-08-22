"""Unit tests for the framework-agnostic tool abstraction.

Verifies that ``@tool`` takes descriptions from either decorator arguments
or a Google-style docstring, and that toolkits expose lookup / invocation
without depending on LangChain.
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

    @tool
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

    def test_openai_schema_includes_brief(self):
        params = self.tk.get_tool_schemas()[0]["function"]["parameters"]
        assert "brief" in params["properties"]
        assert "user-facing" in params["properties"]["brief"]["description"]
        # Official timeline needs brief — require it on every executable tool
        assert "brief" in params.get("required", [])

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

    async def test_invoke_strips_brief_before_calling_impl(self):
        tool_obj = self.tk.get_tool("do_thing")
        result = await tool_obj.invoke({
            "id": "abc",
            "count": 1,
            "brief": "编写 Python 示例代码",
        })
        assert result.data == "abc:1"
        assert self.backend.calls == [("abc", 1)]

    def test_tool_carries_toolkit_reference(self):
        assert self.tk.get_tool("do_thing").toolkit is self.tk

    async def test_decorated_method_stays_callable(self):
        result = await self.tk.do_thing(id="abc", count=2)
        assert result.data == "abc:2"
        assert self.backend.calls == [("abc", 2)]


class ExplicitToolkit(BaseToolkit):
    name = "explicit"

    @tool(
        description="Do a thing with an id. Use for testing.",
        id="The unique identifier",
        count="(Optional) How many times",
    )
    async def do_thing(self, id: str, count: Optional[int] = None) -> ToolResult:
        """This docstring must be ignored in decorator mode.

        Args:
            id: WRONG id docs
            count: WRONG count docs
        """
        return ToolResult(success=True, data=f"{id}:{count}")

    @tool("Rename a file.", path="Absolute path of the file")
    async def rename(self, path: str) -> ToolResult:
        return ToolResult(success=True, data=path)


class SchemaToolkit(BaseToolkit):
    name = "schema"

    @tool(
        description="Look something up",
        parameters={
            "q": {"type": "string", "description": "Search query"},
        },
        required=["q"],
    )
    async def lookup(self, q: str) -> ToolResult:
        return ToolResult(success=True, data=q)


class TestDecoratorDocs:
    def test_parameter_descriptions_from_decorator(self):
        tk = ExplicitToolkit()
        params = tk.get_tool("do_thing").to_openai_schema()["function"]["parameters"]
        assert params["properties"]["id"]["description"] == "The unique identifier"
        assert "How many times" in params["properties"]["count"]["description"]
        assert "WRONG" not in params["properties"]["id"]["description"]

    def test_decorator_description_ignores_docstring(self):
        tk = ExplicitToolkit()
        fn = tk.get_tool("do_thing").to_openai_schema()["function"]
        assert fn["description"] == "Do a thing with an id. Use for testing."
        assert "ignored" not in fn["description"]

    def test_positional_description(self):
        tk = ExplicitToolkit()
        fn = tk.get_tool("rename").to_openai_schema()["function"]
        assert fn["description"] == "Rename a file."
        assert fn["parameters"]["properties"]["path"]["description"] == "Absolute path of the file"

    def test_explicit_parameters_schema(self):
        tk = SchemaToolkit()
        params = tk.get_tool("lookup").to_openai_schema()["function"]["parameters"]
        assert params["properties"]["q"]["description"] == "Search query"
        assert "q" in params["required"]

    def test_shell_toolkit_uses_decorator_docs(self):
        from types import SimpleNamespace

        from app.domain.services.tools.shell import ShellToolkit

        tk = ShellToolkit(SimpleNamespace())
        fn = tk.get_tool("shell_exec").to_openai_schema()["function"]
        assert "Execute commands in a specified shell session" in fn["description"]
        assert fn["parameters"]["properties"]["exec_dir"]["description"].startswith(
            "Working directory"
        )


class TestTakeBrief:
    def test_take_brief_splits_ui_label(self):
        from app.domain.services.tools.base import take_brief

        brief, args = take_brief({
            "file": "/home/ubuntu/a.py",
            "brief": "  编写 Python 示例代码  ",
        })
        assert brief == "编写 Python 示例代码"
        assert args == {"file": "/home/ubuntu/a.py"}

    def test_take_brief_missing(self):
        from app.domain.services.tools.base import take_brief

        brief, args = take_brief({"file": "a.py"})
        assert brief is None
        assert args == {"file": "a.py"}
