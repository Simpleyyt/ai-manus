"""Unit tests for the framework-agnostic tool abstraction.

Verifies that Tool classes derive OpenAI-compatible function schemas from
Pydantic Args models, and that toolkits expose lookup / invocation without
depending on LangChain.
"""
from typing import Optional

from pydantic import BaseModel, Field

from app.domain.models.tool_result import ToolResult
from app.domain.services.tools.base import BaseToolkit, Tool
from app.domain.services.tools.message import MessageToolkit
from app.domain.services.tools.plan import PlanToolkit


class DoThingTool(Tool):
    name = "do_thing"
    description = "Do a thing with an id. Use for testing."

    class Args(BaseModel):
        id: str = Field(description="The unique identifier")
        count: Optional[int] = Field(default=None, description="(Optional) How many times")

    async def run(self, id: str, count: Optional[int] = None) -> ToolResult:
        return await self.toolkit.backend(id, count)


class SampleToolkit(BaseToolkit):
    name = "sample"
    tool_types = [DoThingTool]

    def __init__(self, backend):
        self.backend = backend
        super().__init__()


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
        assert "Do a thing with an id" in fn["description"]
        assert "Args:" not in fn["description"]

    def test_openai_schema_includes_brief(self):
        params = self.tk.get_tool_schemas()[0]["function"]["parameters"]
        assert "brief" in params["properties"]
        assert "user-facing" in params["properties"]["brief"]["description"]
        # Official timeline needs brief — require it on every executable tool
        assert "brief" in params.get("required", [])

    def test_parameter_descriptions_from_args_model(self):
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


class TestBuiltinToolkits:
    def test_message_toolkit_has_class_tools_without_brief(self):
        tk = MessageToolkit()
        assert [t.name for t in tk.get_tools()] == [
            "message_notify_user",
            "message_ask_user",
        ]
        schema = tk.get_tool("message_notify_user").to_openai_schema()
        assert "brief" not in schema["function"]["parameters"]["properties"]

    def test_plan_toolkit_has_class_tools(self):
        tk = PlanToolkit()
        assert [t.name for t in tk.get_tools()] == ["plan_report", "replan"]
        params = tk.get_tool("replan").to_openai_schema()["function"]["parameters"]
        assert "reason" in params["properties"]
        assert "brief" in params["properties"]
