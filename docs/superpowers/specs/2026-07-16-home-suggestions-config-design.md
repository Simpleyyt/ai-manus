# Home Suggestion Chips — Backend Config Design

**Date:** 2026-07-16  
**Status:** Approved for implementation (pending final user review of this doc)  
**Approach:** JSON env var `HOME_SUGGESTIONS` exposed via existing `/api/v1/config/frontend`

## Goal

Homepage suggestion chips should:

1. Be driven by backend configuration (not hardcoded in the frontend).
2. Each chip map to a full **prompt** that is filled into the ChatBox on click (not auto-sent).
3. Remove the **「更多」 / More** expand control — show the configured list only.

## Non-goals

- Admin UI for editing suggestions
- Auto-submit / create session on chip click
- Per-locale i18n for chip labels (label text comes from config as-is)
- Database-backed configuration

## Data model

Environment variable: `HOME_SUGGESTIONS` (JSON array).

Each item:

| Field | Type | Required | Description |
|---|---|---|---|
| `label` | string | yes | Button display text (rendered as-is) |
| `prompt` | string | yes | Text filled into ChatBox on click |
| `icon` | string | yes | Lucide icon component name (e.g. `Presentation`, `Globe`) |

### Default value

Used when the env var is unset, empty, invalid JSON, or not an array:

```json
[
  {
    "label": "Create slides",
    "prompt": "Help me create a slide deck about …",
    "icon": "Presentation"
  },
  {
    "label": "Build website",
    "prompt": "Help me build a website for …",
    "icon": "Globe"
  },
  {
    "label": "Design",
    "prompt": "Help me design …",
    "icon": "Palette"
  },
  {
    "label": "Create games",
    "prompt": "Help me create a game about …",
    "icon": "Gamepad2"
  }
]
```

### Parsing rules

Align with existing `EXTRA_HEADERS` handling:

- Read raw string from `HOME_SUGGESTIONS`.
- If unset/empty → use defaults.
- If JSON parse fails or value is not a list → log warning, use defaults.
- Items missing required fields or with empty `label`/`prompt` → skip that item (log warning); if all items invalid → use defaults.
- `icon` may be any string; unknown icons are handled on the frontend with a fallback icon.

## Backend

### Settings (`backend/app/core/config.py`)

- Add `home_suggestions: list[dict] | None = None` (or a typed list after parse).
- Add `_parse_home_suggestions()` similar to `_parse_extra_headers()`, returning the default list on failure.
- Call parser inside `get_settings()` and assign to `settings.home_suggestions`.

### Schemas (`backend/app/interfaces/schemas/config.py`)

```python
class HomeSuggestion(BaseModel):
    label: str
    prompt: str
    icon: str

class ClientConfigResponse(BaseModel):
    # existing fields...
    home_suggestions: list[HomeSuggestion]
```

### API (`backend/app/interfaces/api/config_routes.py`)

Extend `GET /api/v1/config/frontend` to include `home_suggestions` from settings. No new route.

### Docs / env template

- Document `HOME_SUGGESTIONS` in `.env.example` and `docs/configuration.md` (+ English counterpart if present).

## Frontend

### API types (`frontend/src/api/config.ts`)

Extend `ClientConfigResponse`:

```ts
export interface HomeSuggestion {
  label: string
  prompt: string
  icon: string
}

// ClientConfigResponse.home_suggestions: HomeSuggestion[]
```

### HomePage (`frontend/src/pages/HomePage.vue`)

- Remove hardcoded `primarySuggestions`, `moreSuggestions`, `showMoreSuggestions`, and the More button.
- Load `home_suggestions` from `getCachedClientConfig()` (already fetched on mount).
- Render chips from that list.
- Map `icon` string → lucide-vue-next component via a small allowlist/map; unknown → `Sparkles` (or similar) fallback.
- Click handler: `message.value = suggestion.prompt`.
- If list is empty, hide the chips container.

### i18n cleanup

Remove locale keys that only served the old hardcoded chips / More button, e.g.:

- `Create slides`, `Build website`, `Design`, `Create games`
- `Deep research`, `Analyze data`, `Generate image`, `Write report`
- `More`

(Only remove keys that become unused after this change.)

## Error handling & edge cases

| Case | Behavior |
|---|---|
| Config fetch fails | Chips area hidden (or empty); ChatBox still works |
| Invalid env JSON | Backend logs warning, returns defaults |
| Unknown icon name | Frontend shows fallback icon |
| Empty valid list `[]` | No chips rendered (operator choice) |
| Very long prompt | Fill into textarea as-is; ChatBox existing UX handles overflow |

## Testing

- Backend: unit/integration check that `/config/frontend` includes `home_suggestions` with defaults when env unset; with custom JSON when set.
- Frontend: type-check / lint / build; manual check that click fills ChatBox with `prompt` and More is gone.
- Prefer a small Vitest/unit test for icon resolver if extracted; otherwise covered by type-check + manual GUI check.

## Out of scope follow-ups

- Localized labels via i18n keys in config
- Admin CRUD for suggestions
- Category / secondary chip rows
