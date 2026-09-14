from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass
from urllib.parse import urlsplit

import httpx

from app.application.errors.exceptions import BadRequestError
from app.domain.skills.archive import MAX_SKILL_PACKAGE_BYTES


def _normalize_posix(path: str) -> str:
    return path.replace("\\", "/")


def _is_junk_path(path: str) -> bool:
    posix = _normalize_posix(path)
    parts = [p for p in posix.split("/") if p]
    if "__MACOSX" in parts:
        return True
    base = parts[-1] if parts else ""
    if base in {".DS_Store", "Thumbs.db"}:
        return True
    if base.startswith("._"):
        return True
    return False


@dataclass(frozen=True)
class ParsedGithubSkillUrl:
    owner: str
    repo: str
    ref: str | None = None
    subpath: str = ""


def parse_github_repo_url(url: str) -> ParsedGithubSkillUrl:
    """Parse owner/repo[/ref/subpath] from common GitHub URL shapes.

    Accepts repo roots and subdirectory links such as::

        https://github.com/owner/repo
        https://github.com/owner/repo/tree/main/skills/foo
        https://github.com/owner/repo/blob/main/skills/foo/SKILL.md
    """
    try:
        parsed = urlsplit(url.strip())
    except ValueError as exc:
        raise BadRequestError("Invalid GitHub URL") from exc

    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]

    if parsed.scheme not in {"https", "http"} or host != "github.com":
        raise BadRequestError("Invalid GitHub URL")

    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) < 2:
        raise BadRequestError("Invalid GitHub URL")

    owner, repo = parts[0], parts[1]
    repo = repo.removesuffix(".git")
    if not owner or not repo:
        raise BadRequestError("Invalid GitHub URL")

    ref: str | None = None
    subpath = ""
    rest = parts[2:]
    if rest:
        if rest[0] in {"tree", "blob"} and len(rest) >= 2:
            ref = rest[1]
            path_parts = rest[2:]
            if rest[0] == "blob" and path_parts and path_parts[-1] == "SKILL.md":
                path_parts = path_parts[:-1]
            subpath = "/".join(path_parts).strip("/")
        # Deeper paths without tree/blob are not valid GitHub browse URLs.

    return ParsedGithubSkillUrl(owner=owner, repo=repo, ref=ref, subpath=subpath)


def extract_subdir_from_github_zip(archive: bytes, subpath: str) -> bytes:
    """Slice a GitHub zipball down to one skill directory (must contain SKILL.md)."""
    subpath = _normalize_posix(subpath).strip("/")
    if not subpath:
        return archive
    if ".." in subpath.split("/"):
        raise BadRequestError("Invalid GitHub subdirectory path")

    try:
        with zipfile.ZipFile(io.BytesIO(archive)) as zf:
            members = [
                info
                for info in zf.infolist()
                if not info.is_dir()
                and not info.filename.endswith("/")
                and not _is_junk_path(info.filename)
            ]
            if not members:
                raise BadRequestError("GitHub subdirectory not found in repository")

            roots = {
                _normalize_posix(info.filename).split("/", 1)[0]
                for info in members
                if _normalize_posix(info.filename)
            }
            if len(roots) != 1:
                raise BadRequestError("Unexpected GitHub archive layout")
            zip_root = next(iter(roots))
            prefix = f"{zip_root}/{subpath}/"

            selected: list[tuple[str, bytes]] = []
            for info in members:
                posix = _normalize_posix(info.filename)
                if not posix.startswith(prefix):
                    continue
                rel = posix[len(prefix) :]
                if not rel or ".." in rel.split("/"):
                    continue
                selected.append((rel, zf.read(info)))
    except zipfile.BadZipFile as exc:
        raise BadRequestError("Invalid GitHub archive") from exc

    if not selected:
        raise BadRequestError(
            f"GitHub subdirectory not found: {subpath}"
        )
    if not any(rel == "SKILL.md" for rel, _ in selected):
        raise BadRequestError(
            f"SKILL.md not found in subdirectory: {subpath}"
        )

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as out:
        for rel, content in selected:
            out.writestr(rel, content)
    return buf.getvalue()


async def fetch_github_skill_zipball(
    owner: str,
    repo: str,
    *,
    ref: str | None = None,
    client=None,
) -> bytes:
    if client is None:
        async with httpx.AsyncClient() as owned_client:
            return await fetch_github_skill_zipball(
                owner,
                repo,
                ref=ref,
                client=owned_client,
            )

    branches: list[str] = []
    if ref:
        branches.append(ref)
    for branch in ("main", "master"):
        if branch not in branches:
            branches.append(branch)

    for branch in branches:
        url = (
            f"https://codeload.github.com/{owner}/{repo}"
            f"/zip/refs/heads/{branch}"
        )
        try:
            if hasattr(client, "stream"):
                async with client.stream("GET", url) as response:
                    if response.status_code != 200:
                        continue
                    chunks: list[bytes] = []
                    downloaded_bytes = 0
                    async for chunk in response.aiter_bytes():
                        downloaded_bytes += len(chunk)
                        if downloaded_bytes > MAX_SKILL_PACKAGE_BYTES:
                            raise BadRequestError(
                                "Repository archive exceeds "
                                f"{MAX_SKILL_PACKAGE_BYTES} bytes"
                            )
                        chunks.append(chunk)
                    return b"".join(chunks)

            response = await client.get(url)
        except httpx.HTTPError:
            continue
        if response.status_code == 200:
            if len(response.content) > MAX_SKILL_PACKAGE_BYTES:
                raise BadRequestError(
                    f"Repository archive exceeds {MAX_SKILL_PACKAGE_BYTES} bytes"
                )
            return response.content

    raise BadRequestError("Could not download repository archive")
