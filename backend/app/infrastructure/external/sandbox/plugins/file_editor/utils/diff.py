from difflib import SequenceMatcher

from pydantic import BaseModel
from rich.text import Text


class EditGroup(BaseModel):
    before_edits: list[str]
    after_edits: list[str]


def get_edit_groups(
    old_content: str | None, new_content: str | None, n_context_lines: int = 2
) -> list[EditGroup]:
    """Get the edit groups showing changes between old and new content.

    Args:
        n_context_lines: Number of context lines to show around each change.

    Returns:
        A list of edit groups, where each group contains before/after edits.
    """
    if old_content is None or new_content is None:
        return []
    old_lines = old_content.split("\n")
    new_lines = new_content.split("\n")
    # Borrowed from difflib.unified_diff to directly parse into structured format
    edit_groups: list[EditGroup] = []
    for group in SequenceMatcher(None, old_lines, new_lines).get_grouped_opcodes(
        n_context_lines
    ):
        # Take the max line number in the group
        _indent_pad_size = len(str(group[-1][3])) + 1  # +1 for "*" prefix
        cur_group: EditGroup = EditGroup(
            before_edits=[],
            after_edits=[],
        )
        for tag, i1, i2, j1, j2 in group:
            if tag == "equal":
                for idx, line in enumerate(old_lines[i1:i2]):
                    line_num = i1 + idx + 1
                    cur_group.before_edits.append(
                        f"{line_num:>{_indent_pad_size}}|{line}"
                    )
                for idx, line in enumerate(new_lines[j1:j2]):
                    line_num = j1 + idx + 1
                    cur_group.after_edits.append(
                        f"{line_num:>{_indent_pad_size}}|{line}"
                    )
                continue
            if tag in {"replace", "delete"}:
                for idx, line in enumerate(old_lines[i1:i2]):
                    line_num = i1 + idx + 1
                    cur_group.before_edits.append(
                        f"-{line_num:>{_indent_pad_size - 1}}|{line}"
                    )
            if tag in {"replace", "insert"}:
                for idx, line in enumerate(new_lines[j1:j2]):
                    line_num = j1 + idx + 1
                    cur_group.after_edits.append(
                        f"+{line_num:>{_indent_pad_size - 1}}|{line}"
                    )
        edit_groups.append(cur_group)
    return edit_groups


def visualize_diff(
    path: str,
    old_content: str | None,
    new_content: str | None,
    n_context_lines: int = 2,
    change_applied: bool = True,
) -> Text:
    """Visualize the diff of the string replacement edit.

    Instead of showing the diff line by line, this function shows each hunk
    of changes as a separate entity.

    Args:
        n_context_lines: Number of context lines to show before/after changes.
        change_applied: Whether changes are applied. If false, shows as
            attempted edit.

    Returns:
        A string containing the formatted diff visualization.
    """
    content = Text()
    # Check if there are any changes
    if change_applied and old_content == new_content:
        msg = "(no changes detected. Please make sure your edits change "
        msg += "the content of the existing file.)\n"
        content.append(msg, style="bold red")
        return content

    if old_content is None:
        # creation of a new file
        old_content = ""
    assert new_content is not None, "new_content cannot be None"
    edit_groups = get_edit_groups(
        old_content, new_content, n_context_lines=n_context_lines
    )

    if change_applied:
        header = f"[File {path} edited with "
        header += f"{len(edit_groups)} changes.]\n"
    else:
        header = f"[Changes are NOT applied to {path} - Here's how "
        header += "the file looks like if changes are applied.]\n"

    content.append(header, style="bold" if change_applied else "bold yellow")

    op_type = "edit" if change_applied else "ATTEMPTED edit"
    for i, cur_edit_group in enumerate(edit_groups):
        if i != 0:
            content.append("\n-------------------------\n")
        content.append(f"[begin of {op_type} {i + 1} / {len(edit_groups)}]\n")
        content.append(f"(content before {op_type})\n")
        for line in cur_edit_group.before_edits:
            content.append(line + "\n", style="red")
        content.append(f"(content after {op_type})\n")
        for line in cur_edit_group.after_edits:
            content.append(line + "\n", style="green")
        content.append(f"[end of {op_type} {i + 1} / {len(edit_groups)}]", style="bold")
    return content
