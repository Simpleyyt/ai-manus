---
name: release
description: >-
  Create GitHub version releases for ai-manus (vX.Y.Z) matching the v2.4.0 /
  v2.5.0 note format. Use when the user asks to cut a release, publish a
  version tag, write release notes, or delete mistaken demo-only releases.
---

# Release

Ship **versioned product releases** (`vX.Y.Z`) with bilingual notes. Do **not**
create ad-hoc `demo-videos-*` (or similar) releases for README MP4 mirrors —
demo clips live on GitHub Attachments; see `.cursor/skills/demo-videos/SKILL.md`.

## Hard rules

| Do | Don't |
|----|--------|
| Tag and release from current `origin/main` (or the commit the user names) | Release from a random feature branch unless asked |
| Follow the **v2.4.0 / v2.5.0 note template** (ZH + EN + Diff + Key Changes) | Invent a different release layout |
| Cover **all** changes since the previous version tag | Only list the last PR |
| Use `gh release create` / `gh release delete` | Attach demo MP4s as the primary release purpose |
| Ask for the version bump if unclear (`v2.5.0` → `v2.6.0` / `v2.5.1`) | Create `demo-videos-YYYYMMDD` style releases |

## Canonical note format

Copy this structure (see https://github.com/Simpleyyt/ai-manus/releases/tag/v2.5.0):

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

- 更新日志 / Changelog: thematic summary bullets (not every commit).
- 关键变更: one line per merged PR (title + `#number`), chronological or grouped by importance.
- Diff stats: `git diff --stat vPrev..origin/main | tail -1`.

## Workflow

```
Task Progress:
- [ ] 1. Confirm version + base commit (usually origin/main)
- [ ] 2. Collect changes since previous tag
- [ ] 3. Draft bilingual notes in the canonical format
- [ ] 4. Create annotated tag on that commit and push
- [ ] 5. gh release create (set --latest unless told otherwise)
- [ ] 6. Verify release URL and that demo-videos-* releases are absent
```

### 1. Confirm version and tip

```bash
git fetch origin main --tags
gh release list --limit 5
git log -1 --oneline origin/main
PREV=$(gh release list --limit 1 --exclude-drafts --exclude-pre-releases \
  | awk 'NR==1 {print $3}')   # or last stable tag, e.g. v2.5.0
# If PREV is the tag about to be superseded, use the previous Latest before create.
```

Ask the user for `vX.Y.Z` if they did not specify. Default next minor after Latest
unless they ask for patch / major.

### 2. Collect changes

```bash
PREV=v2.5.0   # previous release tag
git log "$PREV"..origin/main --oneline
git log "$PREV"..origin/main --pretty=format:'%s' | grep -oE '#[0-9]+' | sort -un
git diff --stat "$PREV"..origin/main | tail -1

# PR titles for Key Changes
for n in <pr numbers>; do
  gh pr view "$n" --json number,title --jq '"#\(.number) \(.title)"'
done
```

### 3. Draft notes

Fill the canonical template. Keep ZH and EN aligned. Prefer themes in 更新日志 /
Changelog; put the full PR list under 关键变更.

### 4–5. Tag and create

`gh release create` with `--target origin/main` may fail; prefer an annotated tag:

```bash
VERSION=v2.6.0
PREV=v2.5.0
MAIN=$(git rev-parse origin/main)

git tag -a "$VERSION" "$MAIN" -m "$VERSION"
git push origin "$VERSION"

gh release create "$VERSION" \
  --title "$VERSION" \
  --latest \
  --notes-file - <<'EOF'
…canonical body…
EOF
```

Omit binary assets unless the user explicitly asks to attach files.

### 6. Verify

```bash
gh release view "$VERSION"
gh release list --limit 5
# Expect no demo-videos-* entries
```

## Deleting bad releases

If a mistaken non-version release exists (e.g. `demo-videos-20260719`):

```bash
gh release delete demo-videos-20260719 --yes --cleanup-tag
git push origin :refs/tags/demo-videos-20260719 2>/dev/null || true
```

Then create the proper `vX.Y.Z` release if that was the intent.

## Related

- Demo MP4 upload / README players: `.cursor/skills/demo-videos/SKILL.md`
- Doc sync after demos.yml changes: `.cursor/skills/update-docs/SKILL.md`
