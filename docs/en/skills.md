# Skills

## Introduction

Skills are reusable workflow packages: each skill has a name, a description, and a full `SKILL.md` instruction body (optionally with scripts and asset files). The format follows [Agent Skills](https://agentskills.io/what-are-skills).

In AI Manus you can:

- Add skills from the **official catalog**, upload a ZIP, or import a **public GitHub** repo
- Insert a skill chip with **`/`** in the composer, or send text starting with `/{name}`
- Let the Agent call **`load_skill`** for the full instructions and sync skill files into the sandbox

> Skills are not the same as [MCP](mcp.md): MCP connects external tool servers; Skills are specialized workflow instructions for the model (and optional sandbox files).

## How to use

### 1. Manage skills in Settings

Open **Settings → Skills**:

| Action | Description |
|--------|-------------|
| **Added list** | Search and browse; toggle **enable / disable** (disable ≠ unsubscribe) |
| **Browse Skills** | Add unsubscribed skills from Official / Personal catalogs |
| **Create ▾** | Add from official library, upload a package, import from GitHub, or “Create with Manus” (jump to chat) |

On first load, a default set is auto-subscribed and enabled (e.g. `skill-creator`, `web-research`, `summarize`, `slides`). Official entries such as `market-research` must be added manually.

### 2. Add custom skills

**Upload**

- Supports `.zip` / `.skill` packages (the backend can also wrap a parseable bare `SKILL.md`)
- Package must include a parseable `SKILL.md` (YAML frontmatter: `name`, `description` + Markdown body)
- `name` must match lowercase alphanumerics with `-` segments (e.g. `my-skill`)
- Max package size: **20MB**

**Import from GitHub**

- Public repos only: `https://github.com/{owner}/{repo}`
- Fetches the default-branch zipball (`main`, then `master`)
- `SKILL.md` must live at the repo root or under a single top-level folder

Successful upload/import auto-adds the skill as enabled.

### 3. Invoke in chat

1. Type **`/`** in the composer and pick an **enabled** skill (inserts a skill chip)
2. Or send: `/skill-name` followed by your task text
3. On send, the client may attach `required_skills`; the backend also parses leading `/{name}` in the message text

References to missing or disabled skills are **silently ignored** (treated as normal text).

**Agent mode (full capability)**

- System prompt lists skill names/descriptions only (L1)
- On explicit invocation, the model should call the **`load_skill`** tool for the full `SKILL.md` (L2)
- Enabled packages sync into the sandbox at `/home/ubuntu/skills/{name}/` (L3)

**Chat / Lite mode**

- No sandbox sync and no `load_skill`; skill support is weaker than Agent mode

## Bundled official skills

Shipped under `backend/app/application/data/official_skills/`:

| name | Summary |
|------|---------|
| `skill-creator` | Help create reusable skills |
| `web-research` | Web research workflows |
| `summarize` | Long-document summarization |
| `slides` | Presentation / slides |
| `market-research` | Market research (not auto-added; browse to add) |

## HTTP API

Prefix: `/api/v1` (authenticated).

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/skills` | Catalog + added list (with `enabled`) |
| `POST` | `/skills/added` | body `{ "skill_ids": [...] }` add / re-enable |
| `PATCH` | `/skills/added/{skill_id}` | body `{ "enabled": true/false }` |
| `POST` | `/skills/import/github` | body `{ "url": "https://github.com/owner/repo" }` |
| `POST` | `/skills/import/upload` | multipart field `file` |

Invocation goes through WebSocket `/api/v1/ws/chat` (optional `required_skills`). There is no dedicated “run skill” REST endpoint.

There is currently **no** API to fully remove a subscription—only disable.

## Configuration

Skills have **no** dedicated environment variables; nothing to toggle in `.env`. Package size limits and sandbox paths are code constants.

Developer entry points:

- Backend: `backend/app/application/services/skill_service.py`, `skill_runtime_service.py`
- Official packages: `backend/app/application/data/official_skills/`
- Frontend: Settings Skills tab, composer `/` slash menu and skill chips

## Notes

- The **Team** skills tab is an empty placeholder for now.
- GitHub import is public `owner/repo` only; private repos, non-`main`/`master` defaults, or nested package layouts may fail.
- Do not expect sandbox scripts or full `load_skill` behavior in Chat mode.
- Non-UTF-8 files inside a package may be skipped during sandbox sync.

## Further reading

- [Agent Skills specification](https://agentskills.io/what-are-skills)
- [MCP configuration](mcp.md) (external tools)
