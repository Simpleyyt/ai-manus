# Settings Dialog Manus Parity Implementation Plan

> **For agentic workers:** Execute task-by-task. Steps use checkbox syntax.

**Goal:** 直接抄 official Settings dialog (方案 C): shell/nav + General/Account/Shortcuts/Personalization/Help; omit product-only tabs.

**Architecture:** Rewrite `SettingsTabs` grouped nav; paste official classNames; composables `useTheme` + `useChromePrefs` for theme/sound/notification; tab panels as separate Vue SFCs.

**Tech Stack:** Vue 3 + TS, Vitest for composables, vue-i18n, lucide icons, existing Dialog/Select.

**Spec:** `docs/superpowers/specs/2026-07-30-settings-dialog-parity-design.md`

## Global Constraints

- Paste official tokens; product skips = omit only
- Theme/sound/notification = UI chrome prefs (localStorage OK like sidebar)
- No billing/connectors/skills fake UI
- i18n en + zh; English strings as keys
- Verify: `cd frontend && npm run type-check && npm run lint && npm run test`

---

### Task 1: Theme + chrome prefs composables

**Files:**
- Create: `frontend/src/composables/useTheme.ts`
- Create: `frontend/src/composables/useChromePrefs.ts`
- Create: `frontend/src/composables/__tests__/useTheme.spec.ts`

- [ ] Implement `ThemeMode = 'light' | 'dark' | 'auto'`, apply `.dark` on `document.documentElement`, persist `manus-theme-mode`
- [ ] Persist notification/sound booleans `manus-browser-notifications`, `manus-sound-reminder`
- [ ] Unit test theme apply light/dark/auto
- [ ] Commit when green (if user asked commits; else continue)

### Task 2: Settings shell + nav

**Files:**
- Modify: `SettingsDialog.vue`, `SettingsTabs.vue`, `useSettingsDialog.ts`, `UserMenu.vue`

- [ ] Dialog width: `md:w-[80vw] md:min-w-[720px] md:max-w-[1440px]`
- [ ] Body: `flex h-[min(580px,calc(100vh-82px))] flex-col md:h-[90vh] md:flex-row`
- [ ] Sidebar: user card + search + groups (general/account/shortcuts | personalization | help)
- [ ] Tab ids rename `settings` → `general`

### Task 3: Panel contents

**Files:**
- Modify: `GeneralSettings.vue`, `AccountSettings.vue`
- Create: `ShortcutsSettings.vue`, `PersonalizationSettings.vue`, `HelpSettings.vue`
- Remove flow for: `ProfileSettings.vue`

- [ ] General: Appearance + 2 communication toggles
- [ ] Account: fullname, email, user id+copy, logout
- [ ] Shortcuts: New task ⌘/Ctrl+K read-only
- [ ] Personalization: nickname → change-fullname
- [ ] Help: docs.ai-manus.com + GitHub issues

### Task 4: i18n + verify

- [ ] Add keys to `en.ts` / `zh.ts`
- [ ] `npm run test && npm run type-check && npm run lint`
