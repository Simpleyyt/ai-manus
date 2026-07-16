"""Composable system prompt.

The system prompt is assembled at agent-construction time from:

* a core identity/policy section shared by all agents,
* one usage section per toolkit actually bound to the agent (taken from
  ``BaseToolkit.instructions``), so prompt guidance always matches the tools
  the model can really call,
* an optional role-specific section supplied by the concrete agent.

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


def build_system_prompt(
    toolkits: Optional[List[BaseToolkit]] = None,
    role_prompt: str = "",
) -> str:
    """Assemble the system prompt for an agent.

    Args:
        toolkits: Toolkits bound to the agent; each contributes its own usage
            section only when it defines ``instructions``.
        role_prompt: Role-specific guidance appended by the concrete agent.
    """
    sections = [CORE_PROMPT]
    for toolkit in toolkits or []:
        instructions = (toolkit.instructions or "").strip()
        if instructions:
            sections.append(
                f"<{toolkit.name}_rules>\n{instructions}\n</{toolkit.name}_rules>"
            )
    if role_prompt.strip():
        sections.append(role_prompt.strip())
    return "\n\n".join(sections)
