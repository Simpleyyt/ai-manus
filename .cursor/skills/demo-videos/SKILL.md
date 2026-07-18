---
name: demo-videos
description: >-
  Record, upload, and sync README/Docsify demo MP4s for ai-manus. Use when
  recording demos, updating demo videos, fixing README video embeds, working
  with docs/demos.yml, gh image, user-attachments, or sync_demos.py.
---

# Demo Videos

Keep README + Docsify demos in sync via `docs/demos.yml`. On **github.com**, only
`https://github.com/user-attachments/assets/...` URLs render as inline MP4 players.

## Hard rules

| Do | Don't |
|----|--------|
| Put `user-attachments` URLs in `docs/demos.yml` `url` for README players | Expect Release / `raw.githubusercontent.com` / in-repo paths to auto-play in README |
| Use `gh image` (browser `user_session`) to upload | Use `gh auth token` / PAT for Attachments — upload API rejects them |
| Run `./update_doc.sh` after editing `demos.yml` | Hand-edit `<!-- demos:... -->` blocks |
| Keep Release assets until new Attachment URLs are committed and verified | Delete a Release while README still points at it |
| Trim solid-white first frames before upload | Ship recordings that open on a blank white frame |

`tmp/` is gitignored (local review only): `tmp/videos/` for recordings, `tmp/screenshots/` for frames.
`recordings/` is a symlink to `tmp/videos/` for older scripts. **Do not commit MP4s.**

## Key files

| File | Role |
|------|------|
| `docs/demos.yml` | Source of truth (titles, tasks, `url`) |
| `scripts/sync_demos.py` | Fills `<!-- demos:readme\|docsify:en\|zh -->` blocks |
| `./update_doc.sh` | Doc embeds + runs `sync_demos.py` |
| `tmp/videos/` | Local recordings (gitignored; `recordings/` → symlink) |
| `tmp/screenshots/` | Local frames / posters for review (gitignored) |
| `recordings/` | Symlink to `tmp/videos/` |

## First-frame white screen (must fix)

Playwright / browser recordings almost always start with **~1–2s of solid white** (blank tab / page load). GitHub’s README player and local players show that as the opening frame, so demos look broken.

**Before upload:**

1. Extract the first frame and later samples; pure white ≈ mean luma `255`, variance `~0`.
2. Find the first timestamp where the Manus UI is visible (not solid white).
3. Re-encode with `-ss <that time>` (often `1.5`) so frame 0 is real UI.
4. Re-check the new file’s first frame before `gh image`.

```bash
FFMPEG=$(python3 -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())')

# Inspect first frame
"$FFMPEG" -y -i in.mp4 -vframes 1 /tmp/first.jpg

# Trim blank intro (adjust -ss after inspection)
"$FFMPEG" -y -i in.mp4 -ss 1.5 -c:v libx264 -preset fast -crf 23 -an \
  -movflags +faststart out.mp4

# Confirm new first frame is UI, not white
"$FFMPEG" -y -i out.mp4 -vframes 1 /tmp/first-after.jpg
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
- [ ] 1. Record / convert MP4 under tmp/videos/
- [ ] 2. Trim first-frame white screen (see above)
- [ ] 3. Upload with gh image → user-attachments URLs
- [ ] 4. Update docs/demos.yml
- [ ] 5. ./update_doc.sh
- [ ] 6. Verify players render (and first frame is not white)
```

### 1. Record

Produce MP4s under `tmp/videos/` (or `recordings/` symlink). Prefer short, clear demos:
`basic.mp4`, `browser-use.mp4`, `code-use.mp4`.

**Basic Features** should show more than a single agent run: expand the left
sidebar (`localStorage.manus-left-panel-state = true`), run a short agent task,
click **New Task**, start a second session, then switch via **All Tasks**.

### 2. Trim first-frame white screen

Follow **First-frame white screen (must fix)** above. Do not upload until frame 0 is real UI.

### 3. Upload for README players (`gh image`)

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

### 4. Update `docs/demos.yml`

Set each demo’s `url` to the matching Attachment URL. Keep bilingual `title_*` / `task_*`.  
Same Attachment URLs can be reused under the `docsify:` section.

### 5. Sync

```bash
./update_doc.sh
```

Confirm `README.md`, `README_zh.md`, `docs/demo.md`, `docs/en/demo.md` updated.

### 6. Verify

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

```bash
gh release create demo-videos-YYYYMMDD tmp/videos/basic.mp4 tmp/videos/browser-use.mp4 tmp/videos/code-use.mp4 \
  --title "Demo videos YYYY-MM-DD" --latest=false
```

Useful as CDN backup / Docsify source. **Do not delete** until `demos.yml` no longer references those download URLs.

## Related

- General doc sync (compose/env embeds): `.cursor/skills/update-docs/SKILL.md`
