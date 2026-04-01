---
name: update-docs
description: >-
  Sync source files into markdown documentation using update_doc.sh.
  Use when updating docs, README, quick_start, configuration files,
  adding new synced files, or when the user mentions documentation updates,
  update_doc.sh, or doc sync tags.
---

# Update Documentation

This project uses `update_doc.sh` to keep markdown documentation in sync with source files (e.g. `docker-compose-example.yml`, `.env.example`).

## How It Works

Source files are embedded into `.md` files via **sync tags**:

```markdown
<!-- filename -->
```code_type
(auto-replaced content)
```
<!-- /filename -->
```

Running `./update_doc.sh` scans all `.md` files, finds matching tag pairs, and replaces the content between them with the actual file content wrapped in a fenced code block.

## Key Files

| File | Purpose |
|------|---------|
| `update_doc.sh` | Sync script — `FILES_TO_SYNC` array at the top controls which files are synced |
| `docker-compose-example.yml` | Minimal compose example shown in quick start docs |
| `.env.example` | Full environment variable reference |
| `docs/quick_start.md` | Chinese quick start guide |
| `docs/en/quick_start.md` | English quick start guide |
| `docs/configuration.md` | Chinese configuration reference |
| `docs/en/configuration.md` | English configuration reference |
| `README.md` / `README_zh.md` | Project READMEs (also contain sync tags) |

## Workflow

### 1. Edit the Source File

Edit the source file directly (e.g. `docker-compose-example.yml` or `.env.example`).

### 2. Ensure the File Is Registered in `update_doc.sh`

Open `update_doc.sh` and check the `FILES_TO_SYNC` array:

```bash
FILES_TO_SYNC=(
    "docker-compose-example.yml:yaml"
    ".env.example:ini"
)
```

Format: `"filename:code_type"`. Supported code types: `yaml`, `json`, `javascript`, `typescript`, `python`, `bash`, `css`, `html`, `xml`, `sql`, `markdown`, `ini`, `env`, `dockerfile`, `nginx`, `text`. If omitted, code type is inferred from the file extension.

### 3. Add Sync Tags in Target Markdown (if new file)

In each `.md` file that should include the content, add a pair of HTML comment tags with an empty fenced code block between them:

```markdown
<!-- myfile.yml -->
```yaml
```
<!-- /myfile.yml -->
```

The tag name must match the filename in `FILES_TO_SYNC` exactly.

### 4. Run the Sync Script

```bash
./update_doc.sh
```

The script will replace the content between every matching tag pair across all `.md` files in the repo (excluding `.venv`, `.git`, `node_modules`).

### 5. Verify the Result

Read the updated `.md` files to confirm the synced content is correct.

## Adding a New Synced File — Checklist

1. Add the entry to `FILES_TO_SYNC` in `update_doc.sh`
2. Add `<!-- filename -->` / `<!-- /filename -->` tag pairs in every target `.md` file
3. Run `./update_doc.sh`
4. Verify the output

## Important: Always Update Both Languages

This project maintains **Chinese and English** versions of all documentation. When making any doc change, always update both:

| Chinese | English |
|---------|---------|
| `README_zh.md` | `README.md` |
| `docs/quick_start.md` | `docs/en/quick_start.md` |
| `docs/configuration.md` | `docs/en/configuration.md` |
| `docs/*.md` | `docs/en/*.md` |

## Common Pitfalls

- **Forgetting the other language**: Every doc change must be applied to both Chinese and English versions.
- **Tag name mismatch**: The text inside `<!-- ... -->` must exactly match the filename in `FILES_TO_SYNC` (including path separators if any).
- **Missing closing tag**: Both `<!-- filename -->` and `<!-- /filename -->` are required.
- **Forgetting to run the script**: After editing source files, always run `./update_doc.sh` before committing.
