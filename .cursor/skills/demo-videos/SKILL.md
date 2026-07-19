---
name: demo-videos
description: >-
  Record, upload, and sync README demo MP4s for ai-manus. Use when
  recording demos, updating demo videos, fixing README video embeds, working
  with docs/demos.yml, gh image, user-attachments, sync_demos.py, or local
  tmp/videos and tmp/screenshots (gitignored — never commit demo binaries).
  Publishing (upload / demos.yml / push) requires explicit user confirmation.
  Do not overwrite docs/demo.md scenario pages (takeover / file / MCP).
---

# Demo Videos

Keep README demos in sync via `docs/demos.yml`. On **github.com**, only
`https://github.com/user-attachments/assets/...` URLs render as inline MP4 players.

**Do not overwrite** `docs/demo.md` / `docs/en/demo.md` — those are hand-maintained
Docsify pages for **电脑接管 / 文件处理 / MCP** (picgo videos), separate from README demos.

## Hard rules

| Do | Don't |
|----|--------|
| Put `user-attachments` URLs in `docs/demos.yml` `url` for README players | Expect Release / `raw.githubusercontent.com` / in-repo paths to auto-play in README |
| Use `gh image` (browser `user_session`) to upload | Use `gh auth token` / PAT for Attachments — upload API rejects them |
| Run `.cursor/skills/update-docs/update_doc.sh` after editing `demos.yml` | Hand-edit `<!-- demos:... -->` blocks |
| Keep Release assets until new Attachment URLs are committed and verified | Delete a product Release while README still points at it |
| Prefer versioned product releases (`vX.Y.Z`) for shipping | Create `demo-videos-*` releases just to host README MP4s |

| Trim solid-white first frames before upload | Ship recordings that open on a blank white frame |
| Keep all local MP4 / WebM / poster JPG under `tmp/` | Commit videos, screenshots, or `docs/assets/demos/` into git |
| **Get explicit user confirmation before publishing** | Upload, change live demo URLs, or push demo doc updates unprompted |
| **Start every recording from a clean UI** (empty session list) | Record over leftover chats in the sidebar / All Tasks |

## Clean initial state (required before record)

Demos must open on a **fresh home screen**: no prior sessions in the left panel / All Tasks list.
Leftover chats make Basic Features (multi-session) and other clips look messy.

With `AUTH_PROVIDER=none` (dev default), wipe all sessions via API **before** launching Playwright:

```bash
python3 - <<'PY'
import json, urllib.request

base = "http://localhost:8000/api/v1"
sessions = json.load(urllib.request.urlopen(base + "/sessions"))["data"]["sessions"]
for s in sessions:
    sid = s["session_id"]
    req = urllib.request.Request(f"{base}/sessions/{sid}", method="DELETE")
    urllib.request.urlopen(req)
    print("deleted", sid)
left = json.load(urllib.request.urlopen(base + "/sessions"))["data"]["sessions"]
print("remaining", len(left))
assert len(left) == 0, left
PY
```

Then open `/` (not `/chat/<old-id>`). Expand the sidebar if the demo needs it
(`localStorage.manus-left-panel-state = true`). Confirm **All Tasks** is empty before typing the first prompt.

Fallback (wipes all DB sessions for the stack):

```bash
./dev.sh exec -T mongodb mongosh manus --quiet --eval 'db.sessions.deleteMany({})'
```

## Publish gate (confirmation required)

Recording, trimming, and local review under `tmp/` may proceed without asking.
**Publishing** must stop for explicit user OK first. “Publishing” means any of:

1. `gh image` / Release upload (creates public Attachment or Release assets)
2. Editing `docs/demos.yml` `url` (or related title/task that ships with a new video)
3. `.cursor/skills/update-docs/update_doc.sh` when it would rewrite README/docs demo blocks to new URLs
4. `git commit` / `git push` of those demo URL / synced markdown changes

**Before asking for confirmation**, show the user enough to decide:

- Which demo(s) (basic / browser / code)
- Local path(s) under `tmp/videos/`
- First-frame / key stills under `tmp/screenshots/` (or describe what the clip shows)
- Intended task text / language if changing

Only after the user clearly confirms (e.g. “确认发布”, “upload”, “可以更新”) continue with upload → `demos.yml` → `.cursor/skills/update-docs/update_doc.sh` → commit/push.

If confirmation is ambiguous or missing, **do not publish** — leave artifacts in `tmp/` and wait.

## Local media (`tmp/` — never commit)

All recording intermediates and review frames live under the repo-local **`tmp/`** tree (listed in `.gitignore`). README/docs only store Attachment URLs in `docs/demos.yml`.

| Path | Contents |
|------|----------|
| `tmp/videos/` | Final and intermediate recordings (`.mp4`, `.webm`) |
| `tmp/screenshots/` | First-frame checks, posters, Playwright stills (`.jpg`, `.png`) |

Setup if missing:

```bash
mkdir -p tmp/videos tmp/screenshots
git check-ignore -v tmp/videos/x.mp4 tmp/screenshots/x.jpg
# Expect: .gitignore matches — these must NOT appear in git status as addable files
```

**Git rules:**

- `.gitignore` already covers `tmp/`.
- Never `git add` MP4/WebM/demo JPG. Never recreate tracked files under `docs/assets/demos/` or `recordings/`.
- What *does* get committed after a demo update: `docs/demos.yml`, regenerated README/docs via `.cursor/skills/update-docs/update_doc.sh`, and skill/docs text — **not** binaries.
- Old local takes (e.g. `ai-manus-*-demo.*`, `e2e-test-process.*`, `main-run-demo.*`) can stay or be deleted under `tmp/`; they are not part of the published catalog.

Preferred output names for the three README demos: `basic.mp4`, `browser-use.mp4`, `code-use.mp4` in `tmp/videos/`.

## Key files

| File | Role |
|------|------|
| `docs/demos.yml` | Source of truth for **README** demos only (titles, tasks, `url`) |
| `scripts/sync_demos.py` | Fills `<!-- demos:readme:en\|zh -->` in README.md / README_zh.md |
| `.cursor/skills/update-docs/update_doc.sh` | Doc embeds + runs `sync_demos.py` |
| `docs/demo.md` / `docs/en/demo.md` | Hand-maintained scenario demos (takeover / file / MCP) — **not** from demos.yml |
| `tmp/videos/` | Local recordings (gitignored) |
| `tmp/screenshots/` | Local frames / posters (gitignored) |
| `.gitignore` | Must ignore `tmp/` |

## First-frame white screen (must fix)

Playwright / browser recordings almost always start with **~1–2s of solid white** (blank tab / page load). GitHub’s README player and local players show that as the opening frame, so demos look broken.

**Before upload:**

1. Extract the first frame and later samples; pure white ≈ mean luma `255`, variance `~0`.
2. Find the first timestamp where the Manus UI is visible (not solid white).
3. Re-encode with `-ss <that time>` (often `1.5`) so frame 0 is real UI.
4. Re-check the new file’s first frame before `gh image`.

```bash
FFMPEG=$(python3 -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())')

# Inspect first frame (save under tmp/screenshots for review)
"$FFMPEG" -y -i tmp/videos/in.mp4 -vframes 1 tmp/screenshots/first.jpg

# Trim blank intro (adjust -ss after inspection)
"$FFMPEG" -y -i tmp/videos/in.mp4 -ss 1.5 -c:v libx264 -preset fast -crf 23 -an \
  -movflags +faststart tmp/videos/out.mp4

# Confirm new first frame is UI, not white
"$FFMPEG" -y -i tmp/videos/out.mp4 -vframes 1 tmp/screenshots/first-after.jpg
```

Optional scan (mean/var over time) to pick `-ss`:

```bash
python3 - <<'PY'
# prints t / mean / var; BLANK when mean>245 and var<30
import subprocess, sys
from pathlib import Path
try:
    from PIL import Image
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "pillow", "-q"])
    from PIL import Image
ff = subprocess.check_output(
    [sys.executable, "-c", "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())"],
    text=True,
).strip()
src = Path("in.mp4")  # change path
for t in [i / 2 for i in range(0, 21)]:
    jpg = Path(f"/tmp/scan-{t}.jpg")
    subprocess.run(
        [ff, "-y", "-ss", str(t), "-i", str(src), "-vframes", "1", str(jpg)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    im = Image.open(jpg).convert("L").resize((160, 90))
    px = list(im.getdata())
    mean = sum(px) / len(px)
    var = sum((p - mean) ** 2 for p in px) / len(px)
    blank = mean > 245 and var < 30
    print(f"t={t:4.1f} mean={mean:6.1f} var={var:7.1f} {'BLANK' if blank else 'ok'}")
PY
```

## Workflow

```
Task Progress:
- [ ] 1. Clear all sessions (empty All Tasks) — see Clean initial state
- [ ] 2. Record / convert MP4 under tmp/videos/
- [ ] 3. Trim first-frame white screen (see above)
- [ ] 4. Stop — get explicit user confirmation to publish (see Publish gate)
- [ ] 5. Upload with gh image → user-attachments URLs
- [ ] 6. Update docs/demos.yml
- [ ] 7. .cursor/skills/update-docs/update_doc.sh
- [ ] 8. Verify players render (and first frame is not white)
```

### 1. Clean initial state

Follow **Clean initial state** above. Do not start recording until the session list is empty.

### 2. Record

Produce MP4s under `tmp/videos/`. Prefer short, clear demos:
`basic.mp4`, `browser-use.mp4`, `code-use.mp4`.

**Basic Features** should showcase **multi-session switching**, not a single agent run:
clear the session list first (see Clean initial state), expand the sidebar
(`localStorage.manus-left-panel-state = true`), then create short sessions that
mirror the other demos (e.g. a Code Use–style prompt, then **New Task**, then a
Browser Use–style prompt such as “找一下最新新闻” / “Find latest news”), and
switch between them via **All Tasks**.

### 3. Trim first-frame white screen

Follow **First-frame white screen (must fix)** above. Do not upload until frame 0 is real UI.

### 4. Confirm with user (required)

Do **not** run `gh image`, edit live `url`s, sync demo docs, or push those changes until the user confirms. Present paths + stills (or a short summary of the clip) and wait.

### 5. Upload for README players (`gh image`)

```bash
gh extension install drogers0/gh-image   # once
gh image check-token                    # must print GitHub username
gh image --repo Simpleyyt/ai-manus \
  tmp/videos/basic.mp4 \
  tmp/videos/browser-use.mp4 \
  tmp/videos/code-use.mp4
```

Prints one bare URL per file (order = upload order), e.g.:

```text
https://github.com/user-attachments/assets/<uuid>
```

**Auth:** `gh image` reads the browser `user_session` cookie (Chrome/Firefox/…).  
It does **not** use `gh auth login` / OAuth. If `check-token` fails:

1. Open https://github.com in a supported browser — confirm avatar (logged in)
2. Retry `gh image check-token`
3. If still failing, Chrome may store cookies under an unusual profile path; ensure the active profile has `user_session` (not only `logged_in=no`)

### 6. Update `docs/demos.yml`

Set each demo’s `url` to the matching Attachment URL. Keep bilingual `title_*` / `task_*`.

### 7. Sync

```bash
.cursor/skills/update-docs/update_doc.sh
```

Confirm `README.md`, `README_zh.md` updated. Do **not** expect `docs/demo.md` to change.

### 8. Verify

```bash
# Expect camera-video / <video> for each Attachment URL
python3 - <<'PY'
import json, subprocess, urllib.request
from pathlib import Path
token = subprocess.check_output(["gh", "auth", "token"], text=True).strip()
md = Path("README.md").read_text().split("<!-- demos:readme:en -->")[1].split("<!-- /demos:readme:en -->")[0]
req = urllib.request.Request(
    "https://api.github.com/markdown",
    data=json.dumps({"text": md, "mode": "gfm", "context": "Simpleyyt/ai-manus"}).encode(),
    headers={
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
    },
)
html = urllib.request.urlopen(req).read().decode()
print("players:", html.count("camera-video"), "video tags:", html.count("<video"))
assert html.count("camera-video") >= 1 or html.count("<video") >= 1
PY
```

Then spot-check the PR/README preview on github.com.

## Fallback options (worse README UX)

Use only if Attachments are unavailable:

| Approach | README result |
|----------|----------------|
| Release `releases/download/.../*.mp4` bare URL | Text link only |
| HTML `<video src="release-or-raw">` | Stripped by GitHub sanitizer |
| Poster JPG → Attachment MP4 link | Static frame; click opens blob player |
| Short GIF in repo | Inline motion, no real controls |

Docsify can still embed Release MP4s via `[](url ':include controls width="100%"')` even when README cannot.

## Optional: Release mirror

Do **not** create `demo-videos-*` releases. Product shipping uses versioned
`vX.Y.Z` releases — see `.cursor/skills/release/SKILL.md`.

If Attachments are unavailable and you must host MP4s on a **version** release,
attach files to that `vX.Y.Z` release only with explicit user approval. Prefer
keeping README on `user-attachments` URLs.

## Related

- Version releases (`vX.Y.Z` notes format): `.cursor/skills/release/SKILL.md`
- General doc sync (compose/env embeds): `.cursor/skills/update-docs/SKILL.md`
