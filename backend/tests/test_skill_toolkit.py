import pytest

from app.domain.models.tool_result import ToolResult
from app.domain.services.tools.skill import SkillToolkit
from app.domain.skills.package import skill_md_path


@pytest.mark.asyncio
async def test_load_skill_returns_body_and_file_path():
    toolkit = SkillToolkit(
        skills=[("pdf", "Make PDFs")],
        bodies={"pdf": "Use reportlab carefully.\n"},
    )
    result = await toolkit.get_tool("load_skill").invoke({"name": "pdf"})
    assert isinstance(result, ToolResult)
    assert result.success is True
    assert result.data["name"] == "pdf"
    assert result.data["file"] == skill_md_path("pdf")
    assert "reportlab" in result.data["content"]


@pytest.mark.asyncio
async def test_load_skill_rejects_unknown_name():
    toolkit = SkillToolkit(skills=[("pdf", "Make PDFs")], bodies={"pdf": "body"})
    result = await toolkit.get_tool("load_skill").invoke({"name": "nope"})
    assert result.success is False
    assert "nope" in (result.message or "").lower() or "unknown" in (result.message or "").lower()


def test_load_skill_schema_embeds_available_skills_catalog():
    toolkit = SkillToolkit(
        skills=[("pdf", "Make PDFs"), ("slides", "Make slides")],
        bodies={},
    )
    schemas = toolkit.get_tool_schemas()
    assert len(schemas) == 1
    desc = schemas[0]["function"]["description"]
    assert "<available_skills>" in desc
    assert "pdf" in desc
    assert "Make PDFs" in desc
    assert "load_skill" in schemas[0]["function"]["name"] or schemas[0]["function"]["name"] == "load_skill"
