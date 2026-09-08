from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest

from app.application.errors.exceptions import BadRequestError
from app.application.services.skill_github import (
    fetch_github_skill_zipball,
    parse_github_repo_url,
)
from app.application.services.skill_service import SkillService
from app.domain.models.skill import SkillSource
from app.domain.skills.archive import MAX_SKILL_PACKAGE_BYTES


def test_parse_github_repo_url():
    assert parse_github_repo_url("https://github.com/acme/my-skill") == (
        "acme",
        "my-skill",
    )
    assert parse_github_repo_url("https://github.com/acme/my-skill.git/") == (
        "acme",
        "my-skill",
    )


@pytest.mark.parametrize(
    "url",
    [
        "http://github.com/acme/my-skill",
        "https://gitlab.com/acme/my-skill",
        "https://github.com/acme",
        "https://github.com/acme/my-skill/tree/main",
        "https://github.com:not-a-port/acme/my-skill",
    ],
)
def test_parse_rejects_non_repository_github_urls(url):
    with pytest.raises(BadRequestError):
        parse_github_repo_url(url)


def test_parse_wraps_malformed_url_error():
    with pytest.raises(BadRequestError, match="Invalid GitHub URL"):
        parse_github_repo_url("https://[github.com/acme/my-skill")


@pytest.mark.asyncio
async def test_fetch_tries_main_then_master():
    client = SimpleNamespace(
        get=AsyncMock(
            side_effect=[
                SimpleNamespace(status_code=404, content=b""),
                SimpleNamespace(status_code=200, content=b"master zip"),
            ]
        )
    )

    archive = await fetch_github_skill_zipball("acme", "my-skill", client=client)

    assert archive == b"master zip"
    assert client.get.await_args_list[0].args == (
        "https://codeload.github.com/acme/my-skill/zip/refs/heads/main",
    )
    assert client.get.await_args_list[1].args == (
        "https://codeload.github.com/acme/my-skill/zip/refs/heads/master",
    )


@pytest.mark.asyncio
async def test_fetch_rejects_when_main_and_master_are_unavailable():
    client = SimpleNamespace(
        get=AsyncMock(
            side_effect=[
                SimpleNamespace(status_code=404, content=b""),
                SimpleNamespace(status_code=500, content=b""),
            ]
        )
    )

    with pytest.raises(
        BadRequestError, match="Could not download repository archive"
    ):
        await fetch_github_skill_zipball("acme", "my-skill", client=client)


@pytest.mark.asyncio
async def test_fetch_tries_master_after_main_http_error():
    client = SimpleNamespace(
        get=AsyncMock(
            side_effect=[
                httpx.ConnectError("main connection failed"),
                SimpleNamespace(status_code=200, content=b"master zip"),
            ]
        )
    )

    archive = await fetch_github_skill_zipball("acme", "my-skill", client=client)

    assert archive == b"master zip"


@pytest.mark.asyncio
async def test_fetch_rejects_when_both_branches_raise_http_error():
    client = SimpleNamespace(
        get=AsyncMock(
            side_effect=[
                httpx.ConnectError("main connection failed"),
                httpx.ConnectError("master connection failed"),
            ]
        )
    )

    with pytest.raises(
        BadRequestError, match="Could not download repository archive"
    ):
        await fetch_github_skill_zipball("acme", "my-skill", client=client)


class _StreamingResponse:
    def __init__(self, status_code, chunks):
        self.status_code = status_code
        self._chunks = chunks

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def aiter_bytes(self):
        for chunk in self._chunks:
            yield chunk


class _StreamingClient:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.urls = []

    def stream(self, method, url):
        self.urls.append((method, url))
        return next(self.responses)


@pytest.mark.asyncio
async def test_fetch_aborts_stream_over_package_size_cap():
    client = _StreamingClient(
        [
            _StreamingResponse(
                200,
                [b"x" * MAX_SKILL_PACKAGE_BYTES, b"x"],
            )
        ]
    )

    with pytest.raises(BadRequestError, match="exceeds"):
        await fetch_github_skill_zipball("acme", "my-skill", client=client)


@pytest.mark.asyncio
async def test_import_from_github_fetches_then_ingests(monkeypatch):
    archive = b"github zipball"
    imported_skill = object()
    fetch = AsyncMock(return_value=archive)
    monkeypatch.setattr(
        "app.application.services.skill_service.fetch_github_skill_zipball",
        fetch,
    )
    service = SkillService(None, None, None)
    service.ingest_skill_package = AsyncMock(return_value=imported_skill)
    url = "https://github.com/acme/my-skill"

    result = await service.import_from_github("user-1", url)

    assert result is imported_skill
    fetch.assert_awaited_once_with("acme", "my-skill")
    service.ingest_skill_package.assert_awaited_once_with(
        "user-1",
        archive,
        source=SkillSource.GITHUB,
        source_url=url,
    )
