import pytest

from app.application.data.official_skill_packages import (
    official_package_dir,
    read_official_skill_md,
)
from app.domain.models.skill import Skill, SkillOwnerType, SkillSource
from app.domain.skills.body import resolve_skill_body
from app.domain.skills.skill_md import parse_skill_md


@pytest.mark.parametrize(
    ("name", "description"),
    [
        ("skill-creator", "Build a reusable skill together with Manus"),
        (
            "market-research",
            "Research markets and competitors into a structured brief",
        ),
        ("slides", "Turn an outline into presentation slides"),
        (
            "web-research",
            "Search the web and synthesize findings with citations",
        ),
        ("summarize", "Summarize long documents into concise takeaways"),
    ],
)
def test_official_packages_expose_index_metadata(name, description):
    path = official_package_dir(name)
    assert path is not None
    assert (path / "SKILL.md").is_file()

    content = read_official_skill_md(name)
    assert content is not None
    parsed = parse_skill_md(content)
    assert parsed.name == name
    assert parsed.description == description
    assert parsed.body


def test_unknown_official_package_is_not_resolved():
    assert official_package_dir("unknown") is None
    assert read_official_skill_md("unknown") is None


def test_resolve_body_from_official_package():
    skill = Skill(
        id="skill_slides",
        name="slides",
        description="Turn an outline into presentation slides",
        owner_type=SkillOwnerType.OFFICIAL,
        source=SkillSource.CATALOG,
    )

    body = resolve_skill_body(skill)

    assert "Export a slide deck" in body
