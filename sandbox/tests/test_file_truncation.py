"""Unit tests for file read truncation and replace/search full-file behavior."""
import asyncio
import os
import tempfile

import pytest

from app.services.file import FileService


@pytest.fixture
def file_service():
    return FileService()


def _write_temp(content: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".txt")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(content)
    return path


@pytest.mark.asyncio
async def test_read_file_returns_full_content_by_default(file_service):
    """Default read must not truncate large files (used by UI / tool views)."""
    body = "A" * 25000 + "TAIL_MARKER"
    path = _write_temp(body)
    try:
        result = await file_service.read_file(path)
        assert result.content == body
        assert "(truncated)" not in result.content
    finally:
        os.unlink(path)


@pytest.mark.asyncio
async def test_read_file_honors_explicit_max_length(file_service):
    body = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    path = _write_temp(body)
    try:
        result = await file_service.read_file(path, max_length=10)
        assert result.content == "ABCDEFGHIJ(truncated)"
    finally:
        os.unlink(path)


@pytest.mark.asyncio
async def test_str_replace_on_large_file_preserves_tail(file_service):
    """Replace must read the full file; truncating would wipe content past the cap."""
    prefix = "PREFIX_TOKEN"
    middle = "X" * 20000
    suffix = "SUFFIX_KEEP_ME"
    path = _write_temp(prefix + middle + suffix)
    try:
        result = await file_service.str_replace(path, "PREFIX_TOKEN", "REPLACED")
        assert result.replaced_count == 1

        after = await file_service.read_file(path)
        assert after.content.startswith("REPLACED")
        assert after.content.endswith("SUFFIX_KEEP_ME")
        assert "(truncated)" not in after.content
        assert len(after.content) == len("REPLACED" + middle + suffix)
    finally:
        os.unlink(path)


@pytest.mark.asyncio
async def test_find_in_content_matches_past_former_default_cap(file_service):
    """Search must scan the whole file, not only the first 10k chars."""
    path = _write_temp("Y" * 15000 + "NEEDLE_AT_END")
    try:
        result = await file_service.find_in_content(path, r"NEEDLE_AT_END")
        assert result.matches
        assert any("NEEDLE_AT_END" in m for m in result.matches)
    finally:
        os.unlink(path)
