import pytest

from app.application.data.official_skill_packages import (
    official_package_dir,
    read_official_skill_md,
)
from app.application.data.official_skills import list_official_skills, official_skill_id
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
    assert official_package_dir("../slides") is None
    assert read_official_skill_md("unknown") is None


def test_shipped_catalog_ids_follow_directory_names():
    skills = list_official_skills()
    assert [skill.name for skill in skills] == [
        "market-research",
        "skill-creator",
        "slides",
        "summarize",
        "web-research",
    ]
    assert [skill.id for skill in skills] == [
        official_skill_id(name) for name in (
            "market-research",
            "skill-creator",
            "slides",
            "summarize",
            "web-research",
        )
    ]


def test_skills_directory_is_the_catalog(tmp_path, monkeypatch):
    notes = tmp_path / "notes"
    notes.mkdir()
    (notes / "README.txt").write_text("not a skill", encoding="utf-8")

    broken = tmp_path / "Bad Name"
    broken.mkdir()
    (broken / "SKILL.md").write_text("# no", encoding="utf-8")

    mismatch = tmp_path / "beta-skill"
    mismatch.mkdir()
    (mismatch / "SKILL.md").write_text(
        "---\nname: other-name\ndescription: nope\n---\n\n# Other\n",
        encoding="utf-8",
    )

    good = tmp_path / "alpha-skill"
    good.mkdir()
    (good / "SKILL.md").write_text(
        "---\nname: alpha-skill\ndescription: Alpha skill\n---\n\n# Alpha\n\nDo alpha.\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("SKILLS_PATH", str(tmp_path))

    skills = list_official_skills()
    assert [skill.name for skill in skills] == ["alpha-skill"]
    assert skills[0].id == "skill_alpha_skill"
    assert official_package_dir("alpha-skill") == good
    assert "Do alpha." in resolve_skill_body(skills[0])


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
