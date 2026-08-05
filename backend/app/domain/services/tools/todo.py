from typing import List

from app.domain.models.todo import TodoItem
from app.domain.models.tool_result import ToolResult
from app.domain.services.tools.base import BaseToolkit, tool


class TodoToolkit(BaseToolkit):
    name = "todo"
    instructions = """
- Maintain a short todo list for non-trivial tasks via todo_write
- Each call replaces the entire list; include every item every time
- Mark at most one item in_progress; update statuses as you finish work
- Prefer finishing todos before deliver_result
"""

    @tool(parse_docstring=True)
    async def todo_write(self, items: List[dict]) -> ToolResult:
        """Replace the current todo list with the provided full list.

        Args:
            items: Full list of todos. Each item needs id, content, and status
                (pending | in_progress | completed | cancelled).
        """
        parsed = [TodoItem.model_validate(i) for i in items]
        return ToolResult(
            success=True,
            message=f"Updated {len(parsed)} todos",
            data=[i.model_dump(mode="json") for i in parsed],
        )
