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

`recordings/` is gitignored (local only). Optional checked-in copies: `docs/assets/demos/*.mp4`.

## Key files

| File | Role |
|------|------|
| `docs/demos.yml` | Source of truth (titles, tasks, `url`, optional `path`) |
| `scripts/sync_demos.py` | Fills `<!-- demos:readme\|docsify:en\|zh -->` blocks |
| `./update_doc.sh` | Doc embeds + runs `sync_demos.py` |
| `docs/assets/demos/` | Optional MP4 backups / local paths |
| `recordings/` | Local recordings (not committed) |

## Workflow

```
Task Progress:
- [ ] 1. Record / convert MP4
- [ ] 2. Copy into docs/assets/demos/ (optional but recommended)
- [ ] 3. Upload with gh image → user-attachments URLs
- [ ] 4. Update docs/demos.yml
- [ ] 5. ./update_doc.sh
- [ ] 6. Verify players render
```

### 1. Record

Produce MP4s under `recordings/` (e.g. Playwright + ffmpeg). Prefer short, clear demos:
`basic.mp4`, `browser-use.mp4`, `code-use.mp4`.

**Trim blank intros:** recordings often start with ~1–2s of solid white (page load).
Before upload, cut until the first UI frame:

```bash
FFMPEG=$(python3 -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())')
# adjust -ss if needed after inspecting first frames
"$FFMPEG" -y -i in.mp4 -ss 1.5 -c:v libx264 -preset fast -crf 23 -an -movflags +faststart out.mp4
```

### 2. Stage under docs (optional)

```bash
mkdir -p docs/assets/demos
cp recordings/basic.mp4 docs/assets/demos/basic.mp4
# … browser-use, code-use
```

### 3. Upload for README players (`gh image`)

```bash
gh extension install drogers0/gh-image   # once
gh image check-token                    # must print GitHub username
gh image --repo Simpleyyt/ai-manus \
  docs/assets/demos/basic.mp4 \
  docs/assets/demos/browser-use.mp4 \
  docs/assets/demos/code-use.mp4
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
Optional: `path: docs/assets/demos/....mp4` as a repo backup.

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
| Poster JPG → in-repo MP4 link | Static frame; click opens blob player |
| Short GIF in repo | Inline motion, no real controls |

Docsify can still embed Release MP4s via `[](url ':include controls width="100%"')` even when README cannot.

## Optional: Release mirror

```bash
gh release create demo-videos-YYYYMMDD docs/assets/demos/*.mp4 \
  --title "Demo videos YYYY-MM-DD" --latest=false
```

Useful as CDN backup / Docsify source. **Do not delete** until `demos.yml` no longer references those download URLs.

## Related

- General doc sync (compose/env embeds): `.cursor/skills/update-docs/SKILL.md`
