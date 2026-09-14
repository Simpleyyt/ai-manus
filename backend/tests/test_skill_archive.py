import io
import zipfile
import pytest
from app.domain.skills.archive import (
    MAX_SKILL_PACKAGE_BYTES,
    SkillArchiveError,
    ensure_package_size,
    wrap_markdown_as_zip,
    read_skill_md_from_package,
    iter_package_files,
    normalize_package_bytes,
)

def _zip_bytes(mapping: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for path, text in mapping.items():
            zf.writestr(path, text)
    return buf.getvalue()

def test_read_skill_md_at_root():
    data = _zip_bytes({"SKILL.md": "---\nname: demo\ndescription: d\n---\n\n# Hi\n"})
    assert "name: demo" in read_skill_md_from_package(data)

def test_read_skill_md_single_top_folder():
    data = _zip_bytes({"demo-skill/SKILL.md": "---\nname: demo-skill\ndescription: d\n---\n\nBody\n"})
    assert "demo-skill" in read_skill_md_from_package(data)

def test_iter_package_files_strips_top_folder_and_includes_scripts():
    data = _zip_bytes({
        "demo-skill/SKILL.md": "---\nname: demo-skill\ndescription: d\n---\n\nBody\n",
        "demo-skill/scripts/run.py": "print(1)\n",
    })
    files = dict(iter_package_files(data))
    assert "SKILL.md" in files
    assert files["scripts/run.py"] == b"print(1)\n"

def test_zip_slip_rejected():
    data = _zip_bytes({"../evil.md": "x"})
    with pytest.raises(SkillArchiveError):
        iter_package_files(data)

def test_zip_slip_rejected_directory_member():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("../evil/", "")
    data = buf.getvalue()
    with pytest.raises(SkillArchiveError):
        iter_package_files(data)

def test_unique_nested_skill_md_accepted():
    data = _zip_bytes({
        "foo/bar/SKILL.md": "---\nname: nested\ndescription: d\n---\n\nBody\n",
        "foo/bar/scripts/run.py": "print(1)\n",
        "README.md": "# repo\n",
    })
    assert "name: nested" in read_skill_md_from_package(data)
    files = dict(iter_package_files(data))
    assert "SKILL.md" in files
    assert files["scripts/run.py"] == b"print(1)\n"
    assert "README.md" not in files


def test_macos_metadata_ignored_when_resolving_root():
    data = _zip_bytes({
        "skill-creator/SKILL.md": "---\nname: skill-creator\ndescription: d\n---\n\nBody\n",
        "skill-creator/scripts/init.py": "print(1)\n",
        "__MACOSX/skill-creator/._SKILL.md": "junk",
        "__MACOSX/skill-creator/scripts/._init.py": "junk",
        "skill-creator/.DS_Store": "junk",
    })
    assert "skill-creator" in read_skill_md_from_package(data)
    files = dict(iter_package_files(data))
    assert set(files) == {"SKILL.md", "scripts/init.py"}


def test_multiple_skill_md_rejected():
    data = _zip_bytes({
        "a/SKILL.md": "---\nname: a\ndescription: d\n---\n\nA\n",
        "b/SKILL.md": "---\nname: b\ndescription: d\n---\n\nB\n",
    })
    with pytest.raises(SkillArchiveError, match="Multiple SKILL.md"):
        read_skill_md_from_package(data)

def test_size_cap():
    with pytest.raises(SkillArchiveError):
        ensure_package_size(b"x" * (MAX_SKILL_PACKAGE_BYTES + 1))

def test_uncompressed_package_size_cap_applies_to_reads():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("SKILL.md", b"x" * (MAX_SKILL_PACKAGE_BYTES + 1))
    package = buf.getvalue()
    assert len(package) < MAX_SKILL_PACKAGE_BYTES

    with pytest.raises(SkillArchiveError, match="uncompressed"):
        read_skill_md_from_package(package)
    with pytest.raises(SkillArchiveError, match="uncompressed"):
        iter_package_files(package)

def test_uncompressed_package_size_cap_is_aggregate():
    half_cap = MAX_SKILL_PACKAGE_BYTES // 2
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "SKILL.md",
            b"---\nname: demo\ndescription: d\n---\n\nBody\n",
        )
        zf.writestr("script.py", b"x" * (MAX_SKILL_PACKAGE_BYTES + 1))

    with pytest.raises(SkillArchiveError, match="uncompressed"):
        read_skill_md_from_package(buf.getvalue())
    with pytest.raises(SkillArchiveError, match="uncompressed"):
        iter_package_files(buf.getvalue())

def test_normalize_md_to_zip():
    raw = b"---\nname: alone\ndescription: d\n---\n\nOnly md\n"
    pkg = normalize_package_bytes(raw, "alone.md")
    assert read_skill_md_from_package(pkg).startswith("---")
