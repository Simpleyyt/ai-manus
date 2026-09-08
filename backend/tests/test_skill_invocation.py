import pytest

from app.domain.services.skills.invocation import parse_skill_invocation
from app.domain.services.prompts.system import (
    build_system_prompt,
    format_skill_context,
    format_skill_planner_context,
)


def test_parse_skill_invocation_with_task():
    parsed = parse_skill_invocation("/market-research analyze competitors")
    assert parsed is not None
    assert parsed.name == "market-research"
    assert parsed.task == "analyze competitors"


def test_parse_skill_invocation_name_only():
    parsed = parse_skill_invocation("/slides")
    assert parsed is not None
    assert parsed.name == "slides"
    assert parsed.task == ""


def test_parse_skill_invocation_ignores_non_skill_text():
    assert parse_skill_invocation("hello /market-research") is None
    assert parse_skill_invocation("/") is None


def test_format_skill_context_requires_load_skill():
    section = format_skill_context(
        name="market-research",
        body="Research markets into a structured brief.",
        task="analyze competitors",
    )
    prompt = build_system_prompt(skill_context=section)
    assert "<active_skill>" in prompt
    assert "MUST call `load_skill`" in prompt
    assert "market-research" in prompt
    assert "<skill_instructions>" not in prompt
    assert "Research markets into a structured brief." not in prompt
    assert "analyze competitors" in prompt
    catalog = "<available_skills>\n- /x\n</available_skills>"
    ordered = build_system_prompt(skill_catalog=catalog, skill_context=section)
    assert ordered.index("<active_skill>") < ordered.index("<available_skills>")


def test_format_skill_planner_context_omits_body_requires_load_step():
    section = format_skill_planner_context(
        name="pdf",
        task="one page",
    )
    assert "<active_skill>" in section
    assert "<skill_instructions>" not in section
    assert "Use reportlab" not in section
    assert "first plan step MUST" in section
    assert "加载 pdf 技能" in section
    assert "Load pdf skill" in section
    assert "one page" in section
    prompt = build_system_prompt(skill_context=section)
    assert "<skill_instructions>" not in prompt
