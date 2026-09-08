# Skill Package Storage & Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Store full skill packages (upload + GitHub snapshot + repo-bundled official), and sync entire trees to `/home/ubuntu/skills/{name}/` on sandbox ensure — aligned with official Manus / Agent Skills.

**Architecture:** Shared `ingest_skill_package` writes package bytes to GridFS and parses `SKILL.md` into Skill metadata. Official skills live as directories under `backend/app/application/data/official_skills/{name}/`. L3 sync extracts GridFS zips or copies official dirs into the sandbox with zip-slip protection. Prompt L1/L2 behavior stays (no keyword auto-match; active skill points at `SKILL.md`).

**Tech Stack:** Python 3.12, FastAPI, Beanie/Mongo, GridFS (`FileStorage`), httpx for GitHub codeload, pytest.

**Spec:** `docs/superpowers/specs/2026-09-01-skill-package-storage-design.md`

## Global Constraints

- Package size cap: **20 MiB**
- GitHub: HTTPS + `github.com` only; public repos; `SKILL.md` at package root after zipball normalization (no subpath, no PAT)
- Zip: reject `..` / absolute paths; allow root `SKILL.md` or single top-level folder containing `SKILL.md`
- `.md` upload: re-zip as a single-file archive so L3 has one code path
- Official catalog: repo-bundled packages only (no remote Manus CDN)
- Do **not** commit unless the user explicitly asks
- Verify: `cd backend && uv run pytest tests/test_skill_*.py -q` (and any new files named in tasks)
- Out of scope: private GH, live pull-to-update, auto safety-review chat, in-product skill file editor

---

## File structure

| File | Responsibility |
|---|---|
| `backend/app/domain/skills/archive.py` | Zip normalize, member list, safe extract to path map, md→zip, size check |
| `backend/app/domain/skills/skill_md.py` | Keep parse helpers; archive.py may call `extract_skill_md_from_bytes` or replace zip open with archive helpers |
| `backend/app/domain/skills/package.py` | Paths + `build_skill_md_file`; add helpers to list official package files / write map to sandbox |
| `backend/app/domain/models/skill.py` | Add `package_file_id`, `package_sha256` |
| `backend/app/infrastructure/models/documents.py` | Persist new Skill fields on `SkillDocument` |
| `backend/app/application/data/official_skills.py` | Index only (ids, names, descriptions, defaults); bodies from packages |
| `backend/app/application/data/official_skills/{name}/SKILL.md` (+ optional scripts) | Official package trees |
| `backend/app/application/data/official_skill_packages.py` | Resolve package root path for an official skill name |
| `backend/app/application/services/skill_service.py` | `ingest_skill_package`, upgrade upload/github; inject `FileStorage` |
| `backend/app/application/services/skill_github.py` | Parse URL + fetch codeload zipball (`main` then `master`) |
| `backend/app/application/services/skill_runtime_service.py` | Full-package L3 sync |
| `backend/app/domain/skills/body.py` | Prefer official package SKILL.md body when present |
| `backend/app/interfaces/dependencies.py` | Pass `get_file_storage()` into `SkillService` |
| `backend/tests/test_skill_archive.py` | Archive unit tests |
| `backend/tests/test_skill_github.py` | URL + fetch (mocked) |
| `backend/tests/test_skill_package_ingest.py` | Ingest + GridFS fake |
| `backend/tests/test_skill_sandbox_sync.py` | Extend for scripts/ tree sync |
| `backend/tests/test_skill_official_packages.py` | Official dir resolution + body |

---

### Task 1: Skill archive helpers

**Files:**
- Create: `backend/app/domain/skills/archive.py`
- Test: `backend/tests/test_skill_archive.py`

**Interfaces:**
- Consumes: stdlib `zipfile`, `io`, `hashlib`
- Produces:
  - `MAX_SKILL_PACKAGE_BYTES = 20 * 1024 * 1024`
  - `class SkillArchiveError(ValueError)`
  - `def ensure_package_size(data: bytes) -> None`
  - `def wrap_markdown_as_zip(skill_md: str) -> bytes`
  - `def normalize_package_bytes(data: bytes, filename: str = "") -> bytes`  
    (`.md` → zip; zip/skill pass through after size check)
  - `def read_skill_md_from_package(package_bytes: bytes) -> str`
  - `def iter_package_files(package_bytes: bytes) -> list[tuple[str, bytes]]`  
    (relative posix paths under package root, no dirs-only entries; zip-slip safe)
  - `def package_sha256(package_bytes: bytes) -> str`

- [ ] **Step 1: Write failing tests**

```python
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

def test_size_cap():
    with pytest.raises(SkillArchiveError):
        ensure_package_size(b"x" * (MAX_SKILL_PACKAGE_BYTES + 1))

def test_normalize_md_to_zip():
    raw = b"---\nname: alone\ndescription: d\n---\n\nOnly md\n"
    pkg = normalize_package_bytes(raw, "alone.md")
    assert read_skill_md_from_package(pkg).startswith("---")
```

- [ ] **Step 2: Run tests — expect FAIL (import / missing module)**

```bash
cd backend && uv run pytest tests/test_skill_archive.py -q
```

- [ ] **Step 3: Implement `archive.py`**

Implement the functions above. For zip-slip: after resolving package root prefix, join member paths and reject if `os.path.normpath` escapes root or member starts with `/` or contains `..`.

- [ ] **Step 4: Run tests — expect PASS**

```bash
cd backend && uv run pytest tests/test_skill_archive.py -q
```

- [ ] **Step 5: Commit** (only if user asked)

```bash
git add backend/app/domain/skills/archive.py backend/tests/test_skill_archive.py
git commit -m "feat(skills): add zip package archive helpers with zip-slip checks"
```

---

### Task 2: Extend Skill model + Mongo document

**Files:**
- Modify: `backend/app/domain/models/skill.py`
- Modify: `backend/app/infrastructure/models/documents.py` (`SkillDocument`)
- Test: `backend/tests/test_skill_model_package_fields.py` (lightweight construct/serialize)

**Interfaces:**
- Produces: `Skill.package_file_id: Optional[str] = None`, `Skill.package_sha256: Optional[str] = None`

- [ ] **Step 1: Failing test**

```python
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
```

- [ ] **Step 2: Run — FAIL until fields exist**

```bash
cd backend && uv run pytest tests/test_skill_model_package_fields.py -q
```

- [ ] **Step 3: Add fields to domain model + `SkillDocument`**

- [ ] **Step 4: PASS + commit if asked**

```bash
git add backend/app/domain/models/skill.py backend/app/infrastructure/models/documents.py backend/tests/test_skill_model_package_fields.py
git commit -m "feat(skills): persist package_file_id and package_sha256"
```

---

### Task 3: Official skill packages on disk

**Files:**
- Create: `backend/app/application/data/official_skills/market-research/SKILL.md`
- Create: `backend/app/application/data/official_skills/slides/SKILL.md`
- Create: `backend/app/application/data/official_skills/web-research/SKILL.md`
- Create: `backend/app/application/data/official_skills/summarize/SKILL.md`
- Create: `backend/app/application/data/official_skills/skill-creator/SKILL.md`
- Create: `backend/app/application/data/official_skill_packages.py`
- Modify: `backend/app/application/data/official_skills.py` (index; remove `OFFICIAL_SKILL_BODIES` or delegate)
- Modify: `backend/app/domain/skills/body.py`
- Test: `backend/tests/test_skill_official_packages.py`

**Interfaces:**
- Produces:
  - `def official_skills_data_root() -> Path`
  - `def official_package_dir(skill_name: str) -> Optional[Path]`
  - `def read_official_skill_md(skill_name: str) -> Optional[str]`
- `resolve_skill_body(skill)` reads official package `SKILL.md` body when `owner_type=official` and dir exists

- [ ] **Step 1: Move current `OFFICIAL_SKILL_BODIES` content into each `SKILL.md` with YAML frontmatter matching index name/description**

Example `slides/SKILL.md`:

```markdown
---
name: slides
description: Turn an outline into presentation slides
---

# Slides

Turn an outline into presentation slides.

1. Confirm audience, tone, and slide count.
2. Expand the outline into slide titles and bullet points.
3. Export a slide deck file the user can download.
```

Optionally add `slides/scripts/.gitkeep` or a tiny example script later — not required for this task.

- [ ] **Step 2: Failing test**

```python
from app.application.data.official_skill_packages import official_package_dir, read_official_skill_md
from app.domain.models.skill import Skill, SkillOwnerType, SkillSource
from app.domain.skills.body import resolve_skill_body

def test_official_package_dir_slides():
    path = official_package_dir("slides")
    assert path is not None
    assert (path / "SKILL.md").is_file()

def test_resolve_body_from_official_package():
    skill = Skill(
        id="skill_slides",
        name="slides",
        description="Turn an outline into presentation slides",
        owner_type=SkillOwnerType.OFFICIAL,
        source=SkillSource.CATALOG,
    )
    body = resolve_skill_body(skill)
    assert "Export a slide deck" in body or "presentation" in body.lower()
```

- [ ] **Step 3: Implement loader + update `resolve_skill_body` + slim `official_skills.py`**

- [ ] **Step 4: Run official + existing skill body/runtime tests**

```bash
cd backend && uv run pytest tests/test_skill_official_packages.py tests/test_skill_runtime_service.py tests/test_skill_sandbox_sync.py -q
```

- [ ] **Step 5: Commit if asked**

---

### Task 4: `ingest_skill_package` + upgrade upload

**Files:**
- Modify: `backend/app/application/services/skill_service.py`
- Modify: `backend/app/interfaces/dependencies.py` (`get_skill_service` inject `file_storage=get_file_storage()`)
- Test: `backend/tests/test_skill_package_ingest.py`

**Interfaces:**
- Consumes: `FileStorage.upload_file`, archive helpers, `parse_skill_md`
- Produces:
  - `SkillService.__init__(..., file_storage: FileStorage)`
  - `async def ingest_skill_package(self, user_id: str, package_bytes: bytes, *, source: SkillSource, source_url: str) -> Skill`
  - `import_from_upload` → `normalize_package_bytes` then `ingest_skill_package(..., source=UPLOAD, source_url=filename)`

Ingest steps:

1. `ensure_package_size` / normalize
2. `read_skill_md_from_package` + `parse_skill_md` → name/description/body
3. `upload_file(BytesIO(package_bytes), filename=f"{name}.zip", user_id=user_id, content_type="application/zip", metadata={"kind": "skill_package"})`
4. Save personal Skill with `package_file_id`, `package_sha256`
5. Subscribe enabled

Fake storage for tests:

```python
class _FakeFileStorage:
    def __init__(self):
        self.files = {}
    async def upload_file(self, file_data, filename, user_id, content_type=None, metadata=None):
        data = file_data.read()
        fid = f"file_{len(self.files)+1}"
        self.files[fid] = data
        from app.domain.models.file import FileInfo
        return FileInfo(file_id=fid, filename=filename, size=len(data), upload_date=__import__("datetime").datetime.utcnow())
    async def download_file(self, file_id, user_id=None):
        import io
        from app.domain.models.file import FileInfo
        data = self.files[file_id]
        return io.BytesIO(data), FileInfo(file_id=file_id, filename="x.zip", size=len(data), upload_date=__import__("datetime").datetime.utcnow())
```

- [ ] **Step 1: Failing test — upload zip with script persists package_file_id and round-trips bytes**

```python
@pytest.mark.asyncio
async def test_ingest_stores_full_package():
    # build zip with SKILL.md + scripts/a.py using helpers from task 1
    # SkillService(fake_repos..., file_storage=_FakeFileStorage())
    # skill = await service.ingest_skill_package(user, bytes, source=SkillSource.UPLOAD, source_url="x.zip")
    # assert skill.package_file_id
    # downloaded, _ = await storage.download_file(skill.package_file_id)
    # assert b"scripts/a.py" in zip namelist of downloaded
```

- [ ] **Step 2: Implement ingest + wire upload + DI**

- [ ] **Step 3: PASS**

```bash
cd backend && uv run pytest tests/test_skill_package_ingest.py tests/test_skill_service.py -q
```

- [ ] **Step 4: Commit if asked**

---

### Task 5: GitHub zipball import

**Files:**
- Create: `backend/app/application/services/skill_github.py`
- Modify: `backend/app/application/services/skill_service.py` (`import_from_github`)
- Test: `backend/tests/test_skill_github.py`

**Interfaces:**
- Produces:
  - `def parse_github_repo_url(url: str) -> tuple[str, str]` → `(owner, repo)` or raise `BadRequestError`
  - `async def fetch_github_skill_zipball(owner: str, repo: str, *, client=None) -> bytes`  
    Try  
    `https://codeload.github.com/{owner}/{repo}/zip/refs/heads/main`  
    then `.../master`; non-200 both → `BadRequestError("Could not download repository archive")`

- [ ] **Step 1: Failing tests with httpx/respx or unittest.mock AsyncMock**

```python
def test_parse_github_repo_url():
    assert parse_github_repo_url("https://github.com/acme/my-skill") == ("acme", "my-skill")

def test_parse_rejects_non_github():
    with pytest.raises(BadRequestError):
        parse_github_repo_url("https://gitlab.com/acme/my-skill")

@pytest.mark.asyncio
async def test_fetch_tries_main_then_master(monkeypatch):
    # first 404, second 200 with minimal zip bytes containing SKILL.md
    ...
```

- [ ] **Step 2: Implement fetch + `import_from_github` calls fetch then `ingest_skill_package(..., source=GITHUB, source_url=url)`**

- [ ] **Step 3: PASS**

```bash
cd backend && uv run pytest tests/test_skill_github.py tests/test_skill_package_ingest.py -q
```

- [ ] **Step 4: Commit if asked**

---

### Task 6: L3 full-package sandbox sync

**Files:**
- Modify: `backend/app/application/services/skill_runtime_service.py`
- Modify: `backend/app/domain/skills/package.py` (optional `async def write_files_to_sandbox(sandbox, skill_name, files: list[tuple[str, bytes]])`)
- Modify: `SkillRuntimeService` / DI to access `FileStorage` when downloading packages (pass via constructor from `get_skill_runtime_service` or download through `SkillService` method `async def load_package_bytes(skill) -> Optional[bytes]`)
- Test: extend `backend/tests/test_skill_sandbox_sync.py`

**Interfaces:**
- Prefer `SkillService.get_package_bytes(skill) -> Optional[bytes]` encapsulating GridFS download / official dir → zip-or-file map
- Sync algorithm per enabled skill:
  1. If official package dir → `iter` files from filesystem under dir
  2. Else if `package_file_id` → download zip → `iter_package_files`
  3. Else legacy → single `build_skill_md_file` write
  4. For each `(relpath, content)` → `sandbox.file_write(f"{skill_dir(name)}/{relpath}", content)` (text decode utf-8 where applicable; binary: if sandbox API is text-only, utf-8 scripts only for v1 — match existing `file_write` usage)

- [ ] **Step 1: Failing test with fake sandbox recording writes**

```python
@pytest.mark.asyncio
async def test_sync_writes_skill_md_and_script():
    # personal skill with package zip in fake storage including scripts/hello.py
    # await runtime.sync_enabled_skills_to_sandbox(user, fake_sandbox)
    # assert any path.endswith("/skills/demo/scripts/hello.py") for writes
```

```python
@pytest.mark.asyncio
async def test_sync_official_slides_writes_skill_md():
    # user with slides enabled; assert SKILL.md path written under /home/ubuntu/skills/slides/
```

- [ ] **Step 2: Implement sync**

- [ ] **Step 3: PASS full skill suite**

```bash
cd backend && uv run pytest tests/test_skill_archive.py tests/test_skill_model_package_fields.py tests/test_skill_official_packages.py tests/test_skill_package_ingest.py tests/test_skill_github.py tests/test_skill_sandbox_sync.py tests/test_skill_runtime_service.py tests/test_skill_service.py tests/test_skill_invocation.py tests/test_skill_loader.py -q
```

- [ ] **Step 4: Commit if asked**

---

### Task 7: Spec status + smoke notes

**Files:**
- Modify: `docs/superpowers/specs/2026-09-01-skill-package-storage-design.md` (ensure Status: Approved)
- Optional comment in `skill_routes.py` docstring that upload/github store full packages

- [ ] **Step 1: Confirm OpenAPI/routes still call upgraded service methods (no signature break for multipart upload)**
- [ ] **Step 2: Manual smoke (stack up):**
  1. Upload a tiny zip with `SKILL.md` + `scripts/x.py`
  2. Start agent session with that skill enabled / `/name`
  3. Confirm sandbox has both files (via tool events or sandbox API)
  4. Import a known public skill repo URL if network allows

- [ ] **Step 3: Commit docs only if user asked**

---

## Spec coverage checklist

| Spec item | Task |
|---|---|
| Zip normalize + zip-slip + 20MiB | Task 1 |
| `package_file_id` / sha256 | Task 2 |
| Official repo packages | Task 3 |
| Shared ingest + upload | Task 4 |
| GitHub codeload public root | Task 5 |
| L3 full tree sync + legacy fallback | Task 6 |
| Non-goals respected | Global Constraints |

## Placeholder scan

No TBD/TODO left in task steps; signatures named for cross-task use.

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-09-01-skill-package-storage.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — this session with executing-plans checkpoints  

Which approach?
