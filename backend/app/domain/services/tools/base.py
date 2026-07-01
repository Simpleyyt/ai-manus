from typing import List, Callable
import inspect
import copy

from langchain_core.tools.structured import StructuredTool
from langchain.tools import BaseTool
from langchain.messages import ToolMessage
from langchain.messages import ToolCall
from langchain_core.tools.base import BaseToolkit as LangchainBaseToolkit, ArgsSchema
from typing import Any, Dict, Optional
from pydantic import BaseModel, create_model, ConfigDict

from app.domain.models.tool_spec import ToolSpec


def create_model_without_fields(model_class: type[BaseModel], exclude_fields: set[str]) -> type[BaseModel]:
    fields = {}
    for field_name, field_info in model_class.model_fields.items():
        if field_name not in exclude_fields:
            fields[field_name] = (field_info.annotation, field_info)
    return create_model(model_class.__name__, **fields)

class Tool(BaseTool):
    
    name: str = ""
    description: str = ""
    args_schema: ArgsSchema | None = None
    toolkit: 'BaseToolkit' = None

    def __init__(self, tool: StructuredTool, **kwargs: Any):
        super().__init__(**kwargs)
        self.name = tool.name
        self.description = tool.description
        self.args_schema = create_model_without_fields(tool.args_schema, {'self'})
        self._tool = tool

    def _run(self, **kwargs: Any) -> Any:
        return self._tool.func(self.toolkit, **kwargs)

    async def _arun(self, **kwargs: Any) -> Any:
        return await self._tool.coroutine(self.toolkit, **kwargs)

    async def ainvoke(self, input: Any, config: Any = None, **kwargs: Any) -> ToolMessage:
        """Invoke tool and return a ToolMessage with the raw result stored in artifact."""
        args = input.get("args", {}) if isinstance(input, dict) else {}
        tool_call_id = input.get("id", "") if isinstance(input, dict) else ""
        raw_result = await self._arun(**args)
        content = raw_result.model_dump_json() if hasattr(raw_result, "model_dump_json") else str(raw_result)
        return ToolMessage(tool_call_id=tool_call_id, name=self.name, content=content, artifact=raw_result)


class BaseToolkit(LangchainBaseToolkit):
    """Base toolset class, providing common tool calling methods"""

    name: str = ""
    tools: List[Tool] = []
    model_config = ConfigDict(ignored_types=(BaseTool,), extra='allow')

    def __init__(self):
        super().__init__()
        self.tools = []

        for _, tool in inspect.getmembers(self, lambda x: isinstance(x, BaseTool)):
            self.tools.append(Tool(tool, toolkit=self))
        
    

    def get_tools(self) -> List[Tool]:
        """Get all registered tools
        
        Returns:
            List of tools
        """
        return self.tools
    
    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """Get specified tool
        
        Args:
            tool_name: Tool name
            
        Returns:
            Tool
        """
        for tool in self.tools:
            if tool.name == tool_name:
                return tool
        return None

    def to_tool_specs(self) -> List[ToolSpec]:
        """Expose this toolkit's tools as framework-neutral ToolSpecs.

        The ``@tool`` decorator is used only to derive the JSON schema and the
        callable here; the resulting ToolSpec carries no framework type, so any
        engine adapter can bind it.
        """
        specs: List[ToolSpec] = []
        for tool in self.tools:
            specs.append(ToolSpec(
                name=tool.name,
                description=tool.description,
                parameters=self._schema_for(tool),
                handler=self._make_handler(tool),
                toolkit_name=self.name,
            ))
        return specs

    @staticmethod
    def _schema_for(tool: Tool) -> Dict[str, Any]:
        if tool.args_schema is not None:
            try:
                return tool.args_schema.model_json_schema()
            except Exception:
                pass
        return {"type": "object", "properties": {}}

    @staticmethod
    def _make_handler(tool: Tool) -> Callable:
        async def handler(args: Dict[str, Any]) -> Any:
            return await tool._arun(**args)
        return handler
