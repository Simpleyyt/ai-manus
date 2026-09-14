"""Composable system prompt.

The system prompt is assembled at agent-construction time from:

* a core identity/policy section shared by all agents,
* one usage section per toolkit actually bound to the agent (taken from
  ``BaseToolkit.instructions``), so prompt guidance always matches the tools
  the model can really call,
* an optional role-specific section supplied by the concrete agent,
* an optional project-instructions section when the session belongs to a
  project that defines ``instruction``.

This replaces the previous monolithic hardcoded prompt, which shipped rules
for tools that were not always available and could drift out of sync with the
toolset.
"""
from typing import List, Optional

from app.domain.services.tools.base import BaseToolkit

CORE_PROMPT = """
You are Manus, a general-purpose AI agent created by the Manus team.

<capabilities>
You operate a Linux sandbox with internet access to complete user tasks
end-to-end: gathering and verifying information, processing and analyzing
data, writing documents and reports, coding, and any other work achievable
with a computer. You install what you need, run what you write, and verify
what you produce.
</capabilities>

<language>
- Default working language: English.
- If the user's message is in another language, use that language for all
  thinking, natural-language tool arguments, and responses.
</language>

<operating_principles>
- You execute the task yourself; never hand instructions back to the user to
  perform. Deliver final results, not plans or advice about how to do it.
- Work step by step; verify intermediate results before building on them.
- Prefer primary sources and cross-validate important facts.
- Save intermediate work to files so progress is never lost.
- When writing prose deliverables, cite sources with URLs when the content is
  based on references. Match the length and format to what the user asked
  for; be thorough for research and writing tasks.
- Code must be saved to a file before execution; never pipe code inline into
  interpreters.
</operating_principles>

<sandbox_environment>
- Ubuntu 22.04 (linux/amd64) with internet access
- User: `ubuntu` with sudo privileges; home directory: /home/ubuntu
- Python 3.10 (python3, pip3), Node.js 20 (node, npm), calculator (bc)
</sandbox_environment>
""".strip()


def format_project_instructions(instruction: Optional[str] = None) -> str:
    """Wrap a project instruction string for injection into a system prompt."""
    text = (instruction or "").strip()
    if not text:
        return ""
    return (
        "<project_instructions>\n"
        "Follow these project-specific instructions for every task in this "
        "project:\n\n"
        f"{text}\n"
        "</project_instructions>"
    )


def format_skill_catalog(skills: List[tuple[str, str]]) -> str:
    """L1 metadata catalog — name and description for enabled skills at session start."""
    if not skills:
        return ""
    lines = [
        "<available_skills>",
        "The user has enabled these skills (metadata only — not the full instructions).",
        "Each skill package lives in the sandbox at `/home/ubuntu/skills/{name}/`.",
        "When a skill is relevant (including after `/{name}` or a skill chip), call "
        "`load_skill` with that skill's name to load its SKILL.md instructions, then "
        "follow them (and any scripts/assets under that directory).",
        "Do not invent skill behavior from the short description alone.",
        "",
    ]
    for name, description in skills:
        desc = (description or "").strip().replace("\n", " ")
        lines.append(f"- `/{name}` → `/home/ubuntu/skills/{name}/SKILL.md`: {desc}")
    lines.append("</available_skills>")
    return "\n".join(lines)


def format_skill_planner_context(
    *,
    name: str,
    task: str = "",
) -> str:
    """Activation marker for the planner — no SKILL.md body inject.

    Planner has no executor tools; it must put a first step for the executor to
    call ``load_skill``, then plan remaining work around that skill workflow.
    """
    package_path = f"/home/ubuntu/skills/{name}"
    sections = [
        "<active_skill>",
        f"The user invoked skill `/{name}` for this turn.",
        "Do not invent skill behavior from the name alone — you do not have the "
        "full SKILL.md text.",
        "The first plan step MUST be a short load label in the working language "
        f"(zh: 加载 {name} 技能; en: Load {name} skill). The executor will call "
        "`load_skill` and follow the returned instructions.",
        "Subsequent steps must follow that skill's workflow, not an unrelated plan.",
        f"Package path: `{package_path}/`.",
    ]
    user_task = (task or "").strip()
    if user_task:
        sections.extend(["", "User task for this turn:", user_task])
    sections.append("</active_skill>")
    return "\n".join(sections)


def format_skill_context(
    *,
    name: str,
    task: str = "",
    body: str = "",
) -> str:
    """Soft L2 for the executor: require ``load_skill`` before other work.

    ``body`` is accepted for call-site compatibility but never injected here —
    full instructions enter context only via the ``load_skill`` tool result.
    """
    _ = body  # progressive disclosure: never inject body into the executor prompt
    package_path = f"/home/ubuntu/skills/{name}"
    sections = [
        "<active_skill>",
        f"The user invoked skill `/{name}` for this turn.",
        f"You MUST call `load_skill` with name `{name}` before other work, then "
        "follow the returned instructions (and any scripts/assets under the package).",
        "Do not invent skill behavior from the name or short description alone.",
        f"Package path: `{package_path}/`.",
    ]
    user_task = (task or "").strip()
    if user_task:
        sections.extend(["", "User task for this turn:", user_task])
    sections.append("</active_skill>")
    return "\n".join(sections)


def build_system_prompt(
    toolkits: Optional[List[BaseToolkit]] = None,
    role_prompt: str = "",
    project_instruction: Optional[str] = None,
    skill_catalog: Optional[str] = None,
    skill_context: Optional[str] = None,
) -> str:
    """Assemble the system prompt for an agent.

    Args:
        toolkits: Toolkits bound to the agent; each contributes its own usage
            section only when it defines ``instructions``.
        role_prompt: Role-specific guidance appended by the concrete agent.
        project_instruction: Optional per-project guidance from
            ``Project.instruction``.
    """
    sections = [CORE_PROMPT]
    # Active skill first after core so explicit invoke beats long toolkit/catalog text.
    skill_section = (skill_context or "").strip()
    if skill_section:
        sections.append(skill_section)
    for toolkit in toolkits or []:
        instructions = (toolkit.instructions or "").strip()
        if instructions:
            sections.append(
                f"<{toolkit.name}_rules>\n{instructions}\n</{toolkit.name}_rules>"
            )
    if role_prompt.strip():
        sections.append(role_prompt.strip())
    project_section = format_project_instructions(project_instruction)
    if project_section:
        sections.append(project_section)
    catalog_section = (skill_catalog or "").strip()
    if catalog_section:
        sections.append(catalog_section)
    return "\n\n".join(sections)
