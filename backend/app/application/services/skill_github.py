from urllib.parse import urlsplit

import httpx

from app.application.errors.exceptions import BadRequestError
from app.domain.skills.archive import MAX_SKILL_PACKAGE_BYTES


def parse_github_repo_url(url: str) -> tuple[str, str]:
    try:
        parsed = urlsplit(url.strip())
    except ValueError as exc:
        raise BadRequestError("Invalid GitHub URL") from exc

    if (
        parsed.scheme != "https"
        or parsed.netloc.lower() != "github.com"
        or parsed.query
        or parsed.fragment
    ):
        raise BadRequestError("Invalid GitHub URL")

    parts = parsed.path.strip("/").split("/")
    if len(parts) != 2 or not all(parts):
        raise BadRequestError("Invalid GitHub URL")

    owner, repo = parts
    repo = repo.removesuffix(".git")
    if not repo:
        raise BadRequestError("Invalid GitHub URL")
    return owner, repo


async def fetch_github_skill_zipball(
    owner: str,
    repo: str,
    *,
    client=None,
) -> bytes:
    if client is None:
        async with httpx.AsyncClient() as owned_client:
            return await fetch_github_skill_zipball(
                owner,
                repo,
                client=owned_client,
            )

    for branch in ("main", "master"):
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
