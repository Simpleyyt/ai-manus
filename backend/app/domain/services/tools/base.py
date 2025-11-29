from typing import List, Callable
import inspect
import copy

from langchain_core.tools.structured import StructuredTool
from langchain.tools import BaseTool
from langchain.messages import ToolMessage
from langchain.messages import ToolCall
from langchain_core.tools.base import BaseToolkit as LangchainBaseToolkit, ArgsSchema
from typing import Any, Optional
from pydantic import BaseModel, create_model, ConfigDict


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
