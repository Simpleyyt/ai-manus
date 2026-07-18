---
name: update-docs
description: >-
  Sync source files and README demo catalog into markdown via the update_doc.sh
  in this skill. Use when updating docs, README, quick_start, configuration,
  .env.example, docker-compose-example.yml, docs/demos.yml, adding sync tags,
  or when the user mentions update_doc.sh, doc sync, or documentation updates.
---

# Update Documentation

Script: **`.cursor/skills/update-docs/update_doc.sh`**  
Compat: repo-root `./update_doc.sh` forwards to the skill script.

After editing synced sources, run either:

```bash
./update_doc.sh
# or
.cursor/skills/update-docs/update_doc.sh
```

It does two jobs:

1. **File embeds** — replace `<!-- filename -->` … `<!-- /filename -->` blocks with live file content
2. **README demos** — run `scripts/sync_demos.py` from `docs/demos.yml` into `<!-- demos:readme:… -->` blocks

## Hard rules

| Do | Don't |
|----|--------|
| Edit the **source** (`.env.example`, compose example, `demos.yml`), then run the script | Hand-edit content inside sync tags |
| Update **both** Chinese and English docs for prose changes | Change only one language |
| Keep `docs/demo.md` / `docs/en/demo.md` hand-edited | Overwrite those pages from `demos.yml` (they are takeover / file / MCP scenarios) |
| Point demo **video** work to `.cursor/skills/demo-videos/SKILL.md` | Treat this skill as the recording/upload guide |

## Key files

| File | Role |
|------|------|
| `.cursor/skills/update-docs/update_doc.sh` | Sync driver; `FILES_TO_SYNC` lists embed sources; then calls `sync_demos.py` |
| `update_doc.sh` (repo root) | Thin wrapper → skill script |
| `docker-compose-example.yml` | Minimal compose snippet in quick start |
| `.env.example` | Env var reference in configuration / quick start |
| `docs/demos.yml` | README demo titles / tasks / Attachment URLs only |
| `scripts/sync_demos.py` | Fills `<!-- demos:readme:en\|zh -->` in `README.md` / `README_zh.md` |
| `docs/demo.md` / `docs/en/demo.md` | Scenario demos — **not** synced |

## Workflow

```
Task Progress:
- [ ] 1. Edit source file(s)
- [ ] 2. Register new embeds in FILES_TO_SYNC (if needed)
- [ ] 3. Add <!-- filename --> tags in target .md (if needed)
- [ ] 4. Run update_doc.sh (root wrapper or skill path)
- [ ] 5. Verify both ZH and EN outputs
```

### 1. Edit the source

Examples: `docker-compose-example.yml`, `.env.example`, `docs/demos.yml`.

For **new README demo videos** (record / `gh image` / confirm publish), follow **demo-videos** skill first, then edit `docs/demos.yml` and run this script.

### 2. Register embeds (new files only)

In `.cursor/skills/update-docs/update_doc.sh`:

```bash
FILES_TO_SYNC=(
    "docker-compose-example.yml:yaml"
    ".env.example:ini"
)
```

Format: `"path:code_type"`. If `code_type` is omitted, it is inferred from the extension.

Supported types: `yaml`, `json`, `javascript`, `typescript`, `python`, `bash`, `css`, `html`, `xml`, `sql`, `markdown`, `ini`, `env`, `dockerfile`, `nginx`, `text`.

### 3. Add sync tags (new embeds only)

Tag name must match `FILES_TO_SYNC` exactly:

```markdown
<!-- docker-compose-example.yml -->
```yaml
services:
  frontend:
    image: simpleyyt/manus-frontend
    ports:
      - "5173:80"
    depends_on:
      - backend
    restart: unless-stopped
    networks:
      - manus-network
    environment:
      - BACKEND_URL=http://backend:8000

  backend:
    image: simpleyyt/manus-backend
    depends_on:
      - sandbox
      - claw
    restart: unless-stopped
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      #- ./mcp.json:/etc/mcp.json # Mount MCP servers directory
    networks:
      - manus-network
    env_file:
      # All configuration is loaded from the .env file, see .env.example
      # More configuration options: https://docs.ai-manus.com/#/configuration
      - .env

  sandbox:
    image: simpleyyt/manus-sandbox
    command: /bin/sh -c "exit 0"  # prevent sandbox from starting, ensure image is pulled
    restart: "no"
    networks:
      - manus-network

  claw:
    image: simpleyyt/manus-claw
    entrypoint: /bin/sh -c "exit 0"  # prevent claw from starting, ensure image is pulled
    restart: "no"
    networks:
      - manus-network

  mongodb:
    image: mongo:7.0
    volumes:
      - mongodb_data:/data/db
    restart: unless-stopped
    #ports:
    #  - "27017:27017"
    networks:
      - manus-network

  redis:
    image: redis:7.0
    restart: unless-stopped
    networks:
      - manus-network

volumes:
  mongodb_data:
    name: manus-mongodb-data

networks:
  manus-network:
    name: manus-network
    driver: bridge
```
<!-- /docker-compose-example.yml -->
```

README demo blocks (managed by `sync_demos.py`):

```markdown
<!-- demos:readme:en -->
…
<!-- /demos:readme:en -->
```

```markdown
<!-- demos:readme:zh -->
…
<!-- /demos:readme:zh -->
```

Do **not** put `demos:docsify` tags in `docs/demo.md`.

### 4. Run sync

```bash
./update_doc.sh
```

Scans repo `.md` files (skips `.venv`, `.git`, `node_modules`), refreshes embed blocks, then syncs README demos.

### 5. Verify

- Spot-check that fenced blocks match the sources
- Confirm README Demos match `docs/demos.yml`
- Confirm `docs/demo.md` still shows 电脑接管 / 文件处理 / MCP (unchanged by sync)

## Bilingual map

| Chinese | English |
|---------|---------|
| `README_zh.md` | `README.md` |
| `docs/quick_start.md` | `docs/en/quick_start.md` |
| `docs/configuration.md` | `docs/en/configuration.md` |
| `docs/*.md` | `docs/en/*.md` |

## Pitfalls

- Tag text must exactly match the registered filename
- Both open and close tags are required
- Forgetting to run the script before commit leaves docs stale
- Mixing README demos with `docs/demo.md` scenario pages

## Related

- Demo recording / upload / publish confirmation: `.cursor/skills/demo-videos/SKILL.md`
