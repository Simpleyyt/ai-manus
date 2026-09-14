from types import SimpleNamespace
from unittest.mock import AsyncMock
import io
import zipfile

import httpx
import pytest

from app.application.errors.exceptions import BadRequestError
from app.application.services.skill_github import (
    ParsedGithubSkillUrl,
    extract_subdir_from_github_zip,
    fetch_github_skill_zipball,
    parse_github_repo_url,
)
from app.application.services.skill_service import SkillService
from app.domain.models.skill import SkillSource
from app.domain.skills.archive import MAX_SKILL_PACKAGE_BYTES


def test_parse_github_repo_url():
    assert parse_github_repo_url("https://github.com/acme/my-skill") == ParsedGithubSkillUrl(
        "acme", "my-skill"
    )
    assert parse_github_repo_url("https://github.com/acme/my-skill.git/") == ParsedGithubSkillUrl(
        "acme", "my-skill"
    )
    assert parse_github_repo_url("http://github.com/acme/my-skill") == ParsedGithubSkillUrl(
        "acme", "my-skill"
    )
    assert parse_github_repo_url("https://www.github.com/acme/my-skill") == ParsedGithubSkillUrl(
        "acme", "my-skill"
    )
    assert parse_github_repo_url("https://github.com/acme/my-skill/tree/main") == ParsedGithubSkillUrl(
        "acme", "my-skill", ref="main"
    )
    assert parse_github_repo_url(
        "https://github.com/acme/my-skill/blob/main/SKILL.md"
    ) == ParsedGithubSkillUrl("acme", "my-skill", ref="main")
    assert parse_github_repo_url(
        "https://github.com/obra/superpowers/tree/main/skills/brainstorming"
    ) == ParsedGithubSkillUrl(
        "obra", "superpowers", ref="main", subpath="skills/brainstorming"
    )
    assert parse_github_repo_url(
        "https://github.com/obra/superpowers/blob/main/skills/brainstorming/SKILL.md"
    ) == ParsedGithubSkillUrl(
        "obra", "superpowers", ref="main", subpath="skills/brainstorming"
    )


@pytest.mark.parametrize(
    "url",
    [
        "https://gitlab.com/acme/my-skill",
        "https://github.com/acme",
        "https://github.com:not-a-port/acme/my-skill",
        "ftp://github.com/acme/my-skill",
    ],
)
def test_parse_rejects_non_repository_github_urls(url):
    with pytest.raises(BadRequestError):
        parse_github_repo_url(url)


def test_parse_wraps_malformed_url_error():
    with pytest.raises(BadRequestError, match="Invalid GitHub URL"):
        parse_github_repo_url("https://[github.com/acme/my-skill")


def _zip_bytes(mapping: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for path, text in mapping.items():
            zf.writestr(path, text)
    return buf.getvalue()


def test_extract_subdir_from_github_zip():
    archive = _zip_bytes({
        "superpowers-main/README.md": "# root\n",
        "superpowers-main/skills/brainstorming/SKILL.md": (
            "---\nname: brainstorming\ndescription: d\n---\n\nBody\n"
        ),
        "superpowers-main/skills/brainstorming/helper.md": "h\n",
        "superpowers-main/skills/other/SKILL.md": (
            "---\nname: other\ndescription: d\n---\n\nOther\n"
        ),
    })
    sliced = extract_subdir_from_github_zip(archive, "skills/brainstorming")
    with zipfile.ZipFile(io.BytesIO(sliced)) as zf:
        names = set(zf.namelist())
    assert names == {"SKILL.md", "helper.md"}


def test_extract_subdir_requires_skill_md():
    archive = _zip_bytes({
        "repo-main/skills/empty/README.md": "x\n",
    })
    with pytest.raises(BadRequestError, match="SKILL.md not found"):
        extract_subdir_from_github_zip(archive, "skills/empty")


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
    fetch.assert_awaited_once_with("acme", "my-skill", ref=None)
    service.ingest_skill_package.assert_awaited_once_with(
        "user-1",
        archive,
        source=SkillSource.GITHUB,
        source_url=url,
    )


@pytest.mark.asyncio
async def test_import_from_github_slices_subdirectory(monkeypatch):
    archive = b"full zipball"
    sliced = b"sliced zip"
    imported_skill = object()
    fetch = AsyncMock(return_value=archive)
    monkeypatch.setattr(
        "app.application.services.skill_service.fetch_github_skill_zipball",
        fetch,
    )
    monkeypatch.setattr(
        "app.application.services.skill_service.extract_subdir_from_github_zip",
        lambda data, subpath: (
            sliced
            if data is archive and subpath == "skills/brainstorming"
            else b""
        ),
    )
    service = SkillService(None, None, None)
    service.ingest_skill_package = AsyncMock(return_value=imported_skill)
    url = "https://github.com/obra/superpowers/tree/main/skills/brainstorming"

    result = await service.import_from_github("user-1", url)

    assert result is imported_skill
    fetch.assert_awaited_once_with("obra", "superpowers", ref="main")
    service.ingest_skill_package.assert_awaited_once_with(
        "user-1",
        sliced,
        source=SkillSource.GITHUB,
        source_url=url,
    )
