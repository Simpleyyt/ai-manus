# Skills

## Introduction

Skills are reusable workflow packages: each skill has a name, a description, and a full `SKILL.md` instruction body (optionally with scripts and asset files). The format follows [Agent Skills](https://agentskills.io/what-are-skills).

In AI Manus you can:

- Manage skills under **Settings → Features → Skills**, add from the **official catalog**, **upload a ZIP / `.skill`**, or import a **public GitHub** repo
- Insert a skill chip with **`/`** in the composer, or via **`+` → Use skills**
- Persist `required_skills` on send; history renders chips with hover tooltips (Official badge for catalog skills)
- Let the Agent call **`load_skill`** for full instructions and sync skill files into the sandbox

> Skills are not the same as [MCP](mcp.md): MCP connects external tool servers; Skills are specialized workflow instructions for the model (and optional sandbox files).

## How to use

### 1. Manage skills in Settings

Open **Settings → Features → Skills** (panel title: **Added skills**):

| Action | Description |
|--------|-------------|
| **Added list** | Search and browse; toggle **enable / disable** (disable ≠ unsubscribe) |
| **Browse Skills** | Dialog with **Official / Team / Personal** tabs (Team is an empty placeholder for now) |
| **Create ▾** | **Create Skill with Manus**, **Upload a Skill**, **Import Skill from GitHub**, **Add from official** |

On first load, all official skills are auto-subscribed and enabled (`skill-creator`, `web-research`, `summarize`, `slides`, `market-research`), plus a personal seed example `data-viz`.

### 2. Add custom skills

**Upload**

- Supports `.zip` / `.skill` packages (the backend can also wrap a parseable bare `SKILL.md`)
- Package must include a parseable `SKILL.md` (YAML frontmatter: `name`, `description` + Markdown body)
- `name` must match lowercase alphanumerics with `-` segments (e.g. `my-skill`)
- Max package size: **20MB**

**Import from GitHub**

- Public repos only (`github.com` http/https URLs)
- Paste the repo root or a subdirectory link: `…/tree/<branch>/path/to/skill`, `…/blob/<branch>/…/SKILL.md`
- Zipball fetch prefers the branch in the URL, then `main`, then `master`
- With a subdirectory: that folder must contain `SKILL.md`. Without one: the archive must contain exactly one `SKILL.md`

Successful upload/import auto-adds the skill as enabled.

**Create Skill with Manus**

- Ensures `skill-creator` is added, then prefills the home composer with that skill chip so you can author a skill in chat.

### 3. Invoke in chat

Any of:

1. Type **`/`** in the composer and pick an **enabled** skill from the Skills section (inserts a skill chip)
2. Open **`+` → Use skills**: search and pick a skill; the panel also supports **Add skills** (upload / GitHub / official) and **Manage skills** (opens Settings)
3. Send raw text: `/skill-name` followed by your task

On send, the client attaches `required_skills: [{ id, name }, …]`; the backend also parses leading `/{name}` in the message text. Structured refs take precedence over slash parsing.

References to missing or disabled skills are **silently ignored** (treated as normal text).

**Chat history**

- Skill mentions render as chips (prefer persisted `required_skills`; older messages without that field fall back to a leading `/{name}` token)
- Hover a chip for name, description (≈3-line clamp), and an Official badge for catalog skills

**Agent mode (full capability)**

- **L1:** System prompt and the `load_skill` tool description list enabled skill names/descriptions (plus an `<available_skills>` catalog)
- **Soft L2:** After an explicit invocation, inject an `<active_skill>` activation marker (**no** `SKILL.md` body); the model must call `load_skill` first
- **Hard L2:** Full `SKILL.md` enters context only via the **`load_skill`** tool result
- **L3:** Enabled packages sync into the sandbox at `/home/ubuntu/skills/{name}/`
- **Plan first step:** The planner is instructed—and the host enforces—that the first step is `Load {name} skill` / 「加载 {name} 技能」 so the executor calls `load_skill` first

**Chat mode**

- No sandbox sync and no `load_skill`; only an activation note — weaker than Agent mode

## Bundled official skills

Shipped under `backend/app/application/data/official_skills/`:

| name | Summary |
|------|---------|
| `skill-creator` | Help create reusable skills |
| `web-research` | Web research workflows |
| `summarize` | Long-document summarization |
| `slides` | Presentation / slides |
| `market-research` | Market research |

## HTTP API

Prefix: `/api/v1` (authenticated).

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/skills` | Catalog + added list (with `enabled`); seeds defaults on first visit |
| `POST` | `/skills/added` | body `{ "skill_ids": [...] }` add / re-enable |
| `PATCH` | `/skills/added/{skill_id}` | body `{ "enabled": true/false }` |
| `POST` | `/skills/import/github` | body `{ "url": "https://github.com/owner/repo" }` (tree/blob subpaths supported) |
| `POST` | `/skills/import/upload` | multipart field `file` |

Invocation goes through WebSocket `/api/v1/ws/chat` (optional `required_skills: [{ "id", "name" }]`). There is no dedicated “run skill” REST endpoint.

There is currently **no** API to fully remove a subscription—only disable.

## Configuration

Skills have **no** dedicated environment variables; nothing to toggle in `.env`. Package size (20MB) and sandbox paths are code constants.

Developer entry points:

- Backend: `backend/app/application/services/skill_service.py`, `skill_runtime_service.py`
- Skill tool: `backend/app/domain/services/tools/skill.py` (`load_skill`)
- Plan first step: `backend/app/domain/services/skills/plan_steps.py`
- Official packages: `backend/app/application/data/official_skills/`
- Frontend: Settings Skills tab, composer `/` slash menu, `+` → Use skills panel, history skill chips / hover

## Notes

- The **Team** skills tab is an empty placeholder for now.
- GitHub import is public repos only. Paste the repo root or a subdirectory URL. Without a subdirectory, the archive must contain exactly one `SKILL.md`.
- Do not expect sandbox scripts or full `load_skill` behavior in Chat mode.
- Non-UTF-8 files inside a package may be skipped during sandbox sync.

## Further reading

- [Agent Skills specification](https://agentskills.io/what-are-skills)
- [MCP configuration](mcp.md) (external tools)
