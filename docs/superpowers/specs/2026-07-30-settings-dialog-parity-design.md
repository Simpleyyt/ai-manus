# Settings Dialog Manus Parity (方案 C)

Date: 2026-07-30  
Status: approved for planning  
Surface: logged-in manus.im `#settings` → local `SettingsDialog`

## Goal

直接抄 official Settings dialog chrome and personal-facing tabs into ai-manus. Match mined DOM / `className` tokens; omit product surfaces without local backend. Do not invent cards, fake billing, or connectors.

## Scope (C)

**In:**

1. Dialog shell + left nav (user card, search, grouped items, close X)
2. General（通用）
3. Account（账户）
4. Shortcuts（快捷键）— read-only table
5. Personalization（个性化）— nickname only
6. Get help（获取帮助）— external link(s)

**Out (omit entire nav entries, no placeholders):**

- Usage & Billing
- Connectors / Skills / Mail Manus / My Computer
- Data management / Integrations / Developer / Cloud browser
- Communication rows that need Manus marketing/email backend
- Account rows: credits/plan, change email, manage login methods, delete account
- Personalization: occupation, about you, knowledge, import memory, custom instructions

## Official reference (mined)

Capture: Chrome CDP on `https://manus.im/app#settings` (2026-07-30). Screenshots under `tmp/screenshots/official-settings-*.png` (gitignored).

### Dialog shell

```
@container/dialog max-h-[95%] outline-none rounded-[16px]
bg-[var(--background-gray-main)] shadow-menu pointer-events-auto m-auto
w-[380px] max-w-[98%] md:w-[80vw] md:min-w-[720px] md:max-w-[1440px]
min-h-[400px] overflow-hidden
```

Close control: absolute top-end X (`lucide-x size-5 text-[var(--icon-tertiary)]`).

### Sidebar

```
md:w-[221px] … md:border-r border-[var(--border-main)] … flex flex-col
```

- User card: avatar + fullname + 「个人」/ Personal; chevron may be visual-only (no multi-account)
- Search input: filters visible nav labels only
- Group labels: `hidden md:block text-[var(--text-tertiary)] text-[13px] leading-[18px] pt-3 pr-3 pl-3.5 pb-1`
- Nav row (active): `md:h-8 md:gap-2 md:self-stretch md:px-4 md:rounded-lg` + `md:bg-[var(--fill-tsp-white-main)]`

### Local nav map (after omit)

| Group | Item id | Label (en key) |
|---|---|---|
| Settings | `general` | General |
| Settings | `account` | Account |
| Settings | `shortcuts` | Shortcuts |
| Features | `personalization` | Personalization |
| (footer) | `help` | Get help |

Remove current Manus logo block from settings sidebar.

## Tab designs

### General

Sections pasted from official:

1. **Appearance**
   - Language: existing `useLocale` (zh / en)
   - Theme: Light / Dark / Auto cards (`w-[110px] min-h-[32px] rounded-[10px] …`). Selected = black outline.
2. **Communication preferences** (subset)
   - Browser notifications — request/revoke `Notification` permission; toggle reflects permission + enabled flag
   - Sound reminder — play existing/local completion sound when enabled (wire to whatever completion path exists; if none yet, toggle persists preference for future hook)
   - Omit: product updates email, queued-task email, Manus ads

**Theme persistence:** apply `document.documentElement.classList` `dark` for Dark; remove for Light; Auto listens to `prefers-color-scheme`. Persist preference with the same approach as other UI chrome (composable + one key). This is chrome preference, not product data synced like favorites — allowed under replicate-manus-ui rule 7 exception for UI chrome. Do **not** invent a preferences Mongo API in this workstream unless already required elsewhere.

### Account

Row layout from official Account tab; wire:

| Row | Behavior |
|---|---|
| Full name | Inline edit → `POST /auth/change-fullname` (reuse Profile logic) |
| Email | Read-only display |
| User ID | `currentUser.id` + Copy |
| Log out | Existing logout (keep; needed locally) |

Omit plan/credits, change-email button, manage login methods, delete account.

Drop nested `ProfileSettings` sub-page navigation; fullname editing lives on Account (and nickname on Personalization can call the same API).

### Shortcuts

Read-only list UI matching official keyboard chips. Seed from real local bindings where they exist:

| Action | Binding today | Show |
|---|---|---|
| New task | ⌘/Ctrl+K (`SessionSidebar`) | yes, wired label |
| Search tasks | if present | yes if wired |
| Toggle sidebar | if present | yes if wired |
| Plan mode / Voice input | none | omit rows |

No custom rebinding, no “Reset to default” action this round (omit control or leave disabled + not claimed as working). Copy may still say shortcuts are shown for reference.

### Personalization

Header copy aligned with official (“Manage your identity…”). Only:

- Nickname field → same as fullname API

Omit occupation, about, knowledge, import memory, custom instructions blocks entirely (no empty fake forms).

### Get help

Single content panel with link(s) to project docs / GitHub issues (pick existing URLs from README). No ticket system.

## File mapping

| Piece | Primary files |
|---|---|
| Dialog open state | `useSettingsDialog.ts` — tab ids: `general` \| `account` \| `shortcuts` \| `personalization` \| `help` |
| Shell | `SettingsDialog.vue` — dialog width classes |
| Nav + layout | `SettingsTabs.vue` — rewrite to grouped nav + user card + search |
| General | `GeneralSettings.vue` — language + theme + notification/sound |
| Account | `AccountSettings.vue` — rewrite rows; absorb name edit |
| Shortcuts | new `ShortcutsSettings.vue` |
| Personalization | new `PersonalizationSettings.vue` (or slim rename of Profile) |
| Help | new `HelpSettings.vue` |
| Theme | new `useTheme.ts` (or similar) |
| i18n | `en.ts` / `zh.ts` — English source strings as keys |
| Entry | `UserMenu.vue` — Account → `account`, Settings → `general` |

`ProfileSettings.vue` / sub-page config: remove from dialog flow after Account absorbs name edit; delete or leave unused only if nothing else imports it.

## Product / skill constraints

- 直接抄 class trees from CDP dumps / JS; no Library/Project chrome transplant
- Product skips = **removals only**
- No new `localStorage` for server-synced product prefs; theme/sound/notification toggles are UI chrome / device permission
- No Collaborate / Share invent
- Bilingual i18n required
- Do not commit `tmp/` screenshots

## Verification

1. Side-by-side: Vue class strings vs `tmp/screenshots/official-settings-*.png` + DOM notes
2. Nav shows only in-scope items; omitted product tabs absent
3. Theme Light/Dark/Auto toggles `.dark` correctly; Auto follows OS
4. Language still switches i18n
5. Account: rename + copy user id + logout work
6. `cd frontend && npm run type-check && npm run lint`

## Non-goals

- Backend preference / billing / connectors APIs
- Customizable shortcut recording
- Multi-account switcher
- Hash-route parity beyond optional `#settings` open (nice-to-have, not required for first land)
