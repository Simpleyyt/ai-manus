"""String replace editor tool implementation."""

from collections.abc import Sequence
from typing import TYPE_CHECKING, Literal

from pydantic import Field, PrivateAttr


if TYPE_CHECKING:
    from openhands.sdk.conversation.state import ConversationState

from rich.text import Text

from openhands.sdk.tool import (
    Action,
    Observation,
    ToolAnnotations,
    ToolDefinition,
    register_tool,
)
from openhands.tools.file_editor.utils.diff import visualize_diff


CommandLiteral = Literal["view", "create", "str_replace", "insert", "undo_edit"]


class FileEditorAction(Action):
    """Schema for file editor operations."""

    command: CommandLiteral = Field(
        description="The commands to run. Allowed options are: `view`, `create`, "
        "`str_replace`, `insert`, `undo_edit`."
    )
    path: str = Field(description="Absolute path to file or directory.")
    file_text: str | None = Field(
        default=None,
        description="Required parameter of `create` command, with the content of "
        "the file to be created.",
    )
    old_str: str | None = Field(
        default=None,
        description="Required parameter of `str_replace` command containing the "
        "string in `path` to replace.",
    )
    new_str: str | None = Field(
        default=None,
        description="Optional parameter of `str_replace` command containing the "
        "new string (if not given, no string will be added). Required parameter "
        "of `insert` command containing the string to insert.",
    )
    insert_line: int | None = Field(
        default=None,
        ge=0,
        description="Required parameter of `insert` command. The `new_str` will "
        "be inserted AFTER the line `insert_line` of `path`.",
    )
    view_range: list[int] | None = Field(
        default=None,
        description="Optional parameter of `view` command when `path` points to a "
        "file. If none is given, the full file is shown. If provided, the file "
        "will be shown in the indicated line number range, e.g. [11, 12] will "
        "show lines 11 and 12. Indexing at 1 to start. Setting `[start_line, "
        "-1]` shows all lines from `start_line` to the end of the file.",
    )


class FileEditorObservation(Observation):
    """A ToolResult that can be rendered as a CLI output."""

    command: CommandLiteral = Field(
        description=(
            "The command that was run: `view`, `create`, `str_replace`, "
            "`insert`, or `undo_edit`."
        )
    )

    path: str | None = Field(default=None, description="The file path that was edited.")
    prev_exist: bool = Field(
        default=True,
        description="Indicates if the file previously existed. If not, it was created.",
    )
    old_content: str | None = Field(
        default=None, description="The content of the file before the edit."
    )
    new_content: str | None = Field(
        default=None, description="The content of the file after the edit."
    )

    _diff_cache: Text | None = PrivateAttr(default=None)

    @property
    def visualize(self) -> Text:
        """Return Rich Text representation of this observation.

        Shows diff visualization for meaningful changes (file creation, successful
        edits), otherwise falls back to agent observation.
        """
        text = Text()

        if self.is_error:
            text.append("❌ ", style="red bold")
            text.append(self.ERROR_MESSAGE_HEADER, style="bold red")

        if not self._has_meaningful_diff:
            return super().visualize

        assert self.path is not None, "path should be set for meaningful diff"
        # Generate and cache diff visualization
        if not self._diff_cache:
            change_applied = self.command != "view" and not self.is_error
            self._diff_cache = visualize_diff(
                self.path,
                self.old_content,
                self.new_content,
                n_context_lines=2,
                change_applied=change_applied,
            )

        # Combine error prefix with diff visualization
        text.append(self._diff_cache)
        return text

    @property
    def _has_meaningful_diff(self) -> bool:
        """Check if there's a meaningful diff to display."""
        if self.is_error:
            return False

        if not self.path:
            return False

        if self.command not in ("create", "str_replace", "insert", "undo_edit"):
            return False

        # File creation case
        if self.command == "create" and self.new_content and not self.prev_exist:
            return True

        # File modification cases (str_replace, insert, undo_edit)
        if self.command in ("str_replace", "insert", "undo_edit"):
            # Need both old and new content to show meaningful diff
            if self.old_content is not None and self.new_content is not None:
                # Only show diff if content actually changed
                return self.old_content != self.new_content

        return False


Command = Literal[
    "view",
    "create",
    "str_replace",
    "insert",
    "undo_edit",
]


TOOL_DESCRIPTION = """Custom editing tool for viewing, creating and editing files in plain-text format
* State is persistent across command calls and discussions with the user
* If `path` is a text file, `view` displays the result of applying `cat -n`. If `path` is a directory, `view` lists non-hidden files and directories up to 2 levels deep
* The `create` command cannot be used if the specified `path` already exists as a file
* If a `command` generates a long output, it will be truncated and marked with `<response clipped>`
* The `undo_edit` command will revert the last edit made to the file at `path`
* This tool can be used for creating and editing files in plain-text format.


Before using this tool:
1. Use the view tool to understand the file's contents and context
2. Verify the directory path is correct (only applicable when creating new files):
   - Use the view tool to verify the parent directory exists and is the correct location

When making edits:
   - Ensure the edit results in idiomatic, correct code
   - Do not leave the code in a broken state
   - Always use absolute file paths (starting with /)

CRITICAL REQUIREMENTS FOR USING THIS TOOL:

1. EXACT MATCHING: The `old_str` parameter must match EXACTLY one or more consecutive lines from the file, including all whitespace and indentation. The tool will fail if `old_str` matches multiple locations or doesn't match exactly with the file content.

2. UNIQUENESS: The `old_str` must uniquely identify a single instance in the file:
   - Include sufficient context before and after the change point (3-5 lines recommended)
   - If not unique, the replacement will not be performed

3. REPLACEMENT: The `new_str` parameter should contain the edited lines that replace the `old_str`. Both strings must be different.

Remember: when making multiple file edits in a row to the same file, you should prefer to send all edits in a single message with multiple calls to this tool, rather than multiple messages with a single call each.
"""  # noqa: E501


class FileEditorTool(ToolDefinition[FileEditorAction, FileEditorObservation]):
    """A ToolDefinition subclass that automatically initializes a FileEditorExecutor."""

    @classmethod
    def create(
        cls,
        conv_state: "ConversationState",
    ) -> Sequence["FileEditorTool"]:
        """Initialize FileEditorTool with a FileEditorExecutor.

        Args:
            conv_state: Conversation state to get working directory from.
                         If provided, workspace_root will be taken from
                         conv_state.workspace
        """
        # Import here to avoid circular imports
        from openhands.tools.file_editor.impl import FileEditorExecutor

        # Initialize the executor
        executor = FileEditorExecutor(workspace_root=conv_state.workspace.working_dir)

        # Build the tool description with conditional image viewing support
        # Split TOOL_DESCRIPTION to insert image viewing line after the second bullet
        description_lines = TOOL_DESCRIPTION.split("\n")
        base_description = "\n".join(description_lines[:2])  # First two lines
        remaining_description = "\n".join(description_lines[2:])  # Rest of description

        # Add image viewing line if LLM supports vision
        if conv_state.agent.llm.vision_is_active():
            tool_description = (
                f"{base_description}\n"
                "* If `path` is an image file (.png, .jpg, .jpeg, .gif, .webp, "
                ".bmp), `view` displays the image content\n"
                f"{remaining_description}"
            )
        else:
            tool_description = TOOL_DESCRIPTION

        # Add working directory information to the tool description
        # to guide the agent to use the correct directory instead of root
        working_dir = conv_state.workspace.working_dir
        enhanced_description = (
            f"{tool_description}\n\n"
            f"Your current working directory is: {working_dir}\n"
            f"When exploring project structure, start with this directory "
            f"instead of the root filesystem."
        )

        # Initialize the parent Tool with the executor
        return [
            cls(
                action_type=FileEditorAction,
                observation_type=FileEditorObservation,
                description=enhanced_description,
                annotations=ToolAnnotations(
                    title="file_editor",
                    readOnlyHint=False,
                    destructiveHint=True,
                    idempotentHint=False,
                    openWorldHint=False,
                ),
                executor=executor,
            )
        ]


# Automatically register the tool when this module is imported
register_tool(FileEditorTool.name, FileEditorTool)
