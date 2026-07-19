---
name: release
description: >-
  Cut ai-manus GitHub version releases (vX.Y.Z) with bilingual notes matching
  v2.4.0 / v2.5.0. Use when the user asks to release, tag a version, publish
  release notes, bump Latest, or delete mistaken demo-only / non-version
  releases. Do not use for README demo MP4 uploads (see demo-videos skill).
---

# Release (vX.Y.Z)

Dedicated skill for **product version releases**. Not for demo video hosting.

Reference release: https://github.com/Simpleyyt/ai-manus/releases/tag/v2.5.0

## Hard rules

| Do | Don't |
|----|--------|
| Create tags named `vX.Y.Z` (semver) | Create `demo-videos-*` or other ad-hoc release names |
| Tag `origin/main` (or the commit the user specifies) | Release from an unmerged feature branch unless asked |
| Use the canonical bilingual note template below | Invent a new release notes layout |
| Summarize **all** changes since the previous version tag | Only mention the latest PR |
| Confirm version with the user if unspecified | Attach README demo MP4s as the reason for a release |

Demo MP4s → GitHub Attachments via `.cursor/skills/demo-videos/SKILL.md`.  
Doc sync → `.cursor/skills/update-docs/SKILL.md`.

## Canonical note format

```markdown
## 更新日志
* **主题**：中文要点……（#N）。
* …

## Changelog
* **Theme**: English bullet…… (#N).
* …

## 与上一个版本的差异 / Diff from previous release
* Compare: https://github.com/Simpleyyt/ai-manus/compare/vA.B.C...vX.Y.Z
* Stats: N files changed, +X insertions(+), -Y deletions(-).

## 关键变更 / Key Changes
* <PR title> (#N)
* …

**Full Changelog**: https://github.com/Simpleyyt/ai-manus/compare/vA.B.C...vX.Y.Z
```

- **更新日志 / Changelog**: thematic bullets (features, fixes, docs) — not every commit.
- **关键变更**: one line per merged PR (`title (#N)`).
- **Stats**: `git diff --stat "$PREV"..origin/main | tail -1`.

## Workflow

```
Task Progress:
- [ ] 1. Confirm version + tip commit
- [ ] 2. Collect changes since previous tag
- [ ] 3. Draft notes (canonical format)
- [ ] 4. Annotated tag + push
- [ ] 5. gh release create --latest (unless told otherwise)
- [ ] 6. Verify URL; ensure no demo-videos-* leftovers
```

### 1. Confirm version and tip

```bash
git fetch origin main --tags
gh release list --limit 5
git log -1 --oneline origin/main
```

- Previous tag = current Latest (e.g. `v2.5.0`), unless the user names another base.
- New version: ask if unclear. Default **next minor** (`v2.5.0` → `v2.6.0`); use patch/major only when requested.

### 2. Collect changes

```bash
PREV=v2.5.0
git log "$PREV"..origin/main --oneline
git log "$PREV"..origin/main --pretty=format:'%s' | grep -oE '#[0-9]+' | sort -un
git diff --stat "$PREV"..origin/main | tail -1

for n in <pr numbers>; do
  gh pr view "$n" --json number,title --jq '"#\(.number) \(.title)"'
done
```

### 3. Draft notes

Fill the template. Keep ZH ↔ EN aligned. Themes up top; full PR list under 关键变更.

### 4–5. Tag and publish

`gh release create --target origin/main` may 422 — prefer annotated tag first:

```bash
VERSION=v2.6.0
MAIN=$(git rev-parse origin/main)

git tag -a "$VERSION" "$MAIN" -m "$VERSION"
git push origin "$VERSION"

gh release create "$VERSION" \
  --title "$VERSION" \
  --latest \
  --notes "$(cat <<'EOF'
…canonical body…
EOF
)"
```

Do not attach binaries unless the user explicitly asks.

### 6. Verify

```bash
gh release view "$VERSION"
gh release list --limit 5
```

Latest should be the new `vX.Y.Z`. There must be **no** `demo-videos-*` releases.

## Delete mistaken releases

```bash
gh release delete demo-videos-YYYYMMDD --yes --cleanup-tag
git push origin :refs/tags/demo-videos-YYYYMMDD 2>/dev/null || true
```

Then cut a proper `vX.Y.Z` if that was the real intent.

## Related skills

| Skill | Role |
|-------|------|
| `.cursor/skills/demo-videos/SKILL.md` | Record / upload README demos (Attachments) |
| `.cursor/skills/update-docs/SKILL.md` | Sync embeds + README demos from `demos.yml` |
