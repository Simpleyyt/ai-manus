"""Skill package archive helpers (zip ingest, zip-slip safety, size caps)."""

from __future__ import annotations

import hashlib
import io
import os
import zipfile

MAX_SKILL_PACKAGE_BYTES = 20 * 1024 * 1024


class SkillArchiveError(ValueError):
    """Invalid or unsafe skill package archive."""


def ensure_package_size(data: bytes) -> None:
    if len(data) > MAX_SKILL_PACKAGE_BYTES:
        raise SkillArchiveError(
            f"Skill package exceeds {MAX_SKILL_PACKAGE_BYTES} bytes"
        )


def wrap_markdown_as_zip(skill_md: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("SKILL.md", skill_md)
    return buf.getvalue()


def normalize_package_bytes(data: bytes, filename: str = "") -> bytes:
    ensure_package_size(data)
    if filename.lower().endswith(".md"):
        return wrap_markdown_as_zip(data.decode("utf-8"))
    return data


def read_skill_md_from_package(package_bytes: bytes) -> str:
    ensure_package_size(package_bytes)
    with zipfile.ZipFile(io.BytesIO(package_bytes)) as zf:
        _validate_all_member_paths(zf)
        _validate_uncompressed_size(zf)
        file_names = _file_member_names(zf)
        prefix = _resolve_root_prefix(file_names)
        skill_path = f"{prefix}SKILL.md" if prefix else "SKILL.md"
        info = zf.getinfo(skill_path)
        content, _ = _read_member_with_budget(zf, info, 0)
        return content.decode("utf-8")


def iter_package_files(package_bytes: bytes) -> list[tuple[str, bytes]]:
    ensure_package_size(package_bytes)
    with zipfile.ZipFile(io.BytesIO(package_bytes)) as zf:
        _validate_all_member_paths(zf)
        _validate_uncompressed_size(zf)
        entries = [
            (info.filename, info)
            for info in zf.infolist()
            if not info.is_dir() and not info.filename.endswith("/")
        ]
        file_names = [name for name, _ in entries]
        prefix = _resolve_root_prefix(file_names)

        result: list[tuple[str, bytes]] = []
        extracted_bytes = 0
        for name, info in entries:
            rel = _relative_path(name, prefix)
            _validate_relative_path(rel)
            content, extracted_bytes = _read_member_with_budget(
                zf,
                info,
                extracted_bytes,
            )
            result.append((rel, content))
        return result


def package_sha256(package_bytes: bytes) -> str:
    return hashlib.sha256(package_bytes).hexdigest()


def _read_member_with_budget(
    zf: zipfile.ZipFile,
    info: zipfile.ZipInfo,
    extracted_bytes: int,
) -> tuple[bytes, int]:
    if (
        info.file_size > MAX_SKILL_PACKAGE_BYTES
        or extracted_bytes + info.file_size > MAX_SKILL_PACKAGE_BYTES
    ):
        raise SkillArchiveError(
            f"Skill package uncompressed content exceeds {MAX_SKILL_PACKAGE_BYTES} bytes"
        )

    chunks: list[bytes] = []
    with zf.open(info) as member:
        while chunk := member.read(64 * 1024):
            extracted_bytes += len(chunk)
            if extracted_bytes > MAX_SKILL_PACKAGE_BYTES:
                raise SkillArchiveError(
                    "Skill package uncompressed content exceeds "
                    f"{MAX_SKILL_PACKAGE_BYTES} bytes"
                )
            chunks.append(chunk)
    return b"".join(chunks), extracted_bytes


def _validate_all_member_paths(zf: zipfile.ZipFile) -> None:
    for info in zf.infolist():
        _validate_member_path(info.filename)


def _validate_uncompressed_size(zf: zipfile.ZipFile) -> None:
    total_size = sum(
        info.file_size
        for info in zf.infolist()
        if not info.is_dir() and not info.filename.endswith("/")
    )
    if total_size > MAX_SKILL_PACKAGE_BYTES:
        raise SkillArchiveError(
            f"Skill package uncompressed content exceeds {MAX_SKILL_PACKAGE_BYTES} bytes"
        )


def _file_member_names(zf: zipfile.ZipFile) -> list[str]:
    return [
        info.filename
        for info in zf.infolist()
        if not info.is_dir() and not info.filename.endswith("/")
    ]


def _normalize_posix(path: str) -> str:
    return path.replace("\\", "/")


def _validate_member_path(path: str) -> None:
    posix = _normalize_posix(path)
    if posix.startswith("/"):
        raise SkillArchiveError(f"Unsafe absolute path: {path}")
    parts = posix.split("/")
    if ".." in parts:
        raise SkillArchiveError(f"Unsafe path traversal: {path}")


def _validate_relative_path(rel: str) -> None:
    normalized = os.path.normpath(rel)
    if normalized.startswith("..") or os.path.isabs(normalized):
        raise SkillArchiveError(f"Unsafe relative path: {rel}")


def _resolve_root_prefix(file_paths: list[str]) -> str:
    if not file_paths:
        raise SkillArchiveError("SKILL.md not found in package")

    normalized = [_normalize_posix(p) for p in file_paths]

    if "SKILL.md" in normalized:
        return ""

    direct_folder_skills = [
        path
        for path in normalized
        if path.endswith("/SKILL.md") and "/" not in path[: -len("/SKILL.md")]
    ]
    if len(direct_folder_skills) != 1:
        raise SkillArchiveError("SKILL.md not found at package root")

    folder = direct_folder_skills[0][: -len("/SKILL.md")]
    prefix = f"{folder}/"
    if not all(path.startswith(prefix) for path in normalized):
        raise SkillArchiveError("SKILL.md not found at package root")

    return prefix


def _relative_path(member: str, prefix: str) -> str:
    posix = _normalize_posix(member)
    if prefix:
        if not posix.startswith(prefix):
            raise SkillArchiveError(f"File outside package root: {member}")
        rel = posix[len(prefix) :]
    else:
        rel = posix
    return rel.lstrip("/")
