from app.domain.models.skill import Skill, SkillOwnerType, SkillSource


def test_skill_accepts_package_fields():
    s = Skill(
        id="skill_x",
        name="x",
        description="d",
        owner_type=SkillOwnerType.PERSONAL,
        source=SkillSource.UPLOAD,
        package_file_id="abc123",
        package_sha256="deadbeef",
    )
    assert s.package_file_id == "abc123"
    assert s.package_sha256 == "deadbeef"
