---
name: replicate-manus-ui
description: >-
  Replicate manus.im / manus.ai UI into ai-manus by mining official JS bundles
  and live DOM (Chrome CDP), then pasting className trees onto Vue — 直接抄,
  never approximate. Use when aligning SessionSidebar, Library, Project,
  Search, Computer, Chat header, Share, FilePreviewer, or any Manus UI parity;
  when the user says 对齐官方、复刻、直接抄、抄源码、manus.im, or asks what
  is still not aligned. Do **not** use this skill to re-document surfaces the
  user already marked done.
---

# Replicate Manus UI

Align ai-manus frontend with **logged-in manus.im** by **直接抄** official structure + Tailwind classNames from mined JS / live DOM.

**Not allowed:** screenshot vibes, “大概像 Library / 侧栏”, inventing pills/cards/headers, or adapting another page’s shell because it “felt close”. User feedback「整个样式不对，为啥不直接抄呢」= you approximated; stop and paste tokens.

Respond in **中文** unless the user writes in English.

## Hard rules

1. **直接抄 (paste, don't approximate)** — After mining, put the **exact** `className` strings and DOM tree into Vue first. Only then wire data / skip product-blocked pieces (Share, Collaborate). Token-level: `h-[56px]`, `gap-[12px]`, `rounded-[22px]`, `max-w-[1168px]`, copy strings like “Give Manus a task…”.
2. **Reuse local chrome that already matches** — If official uses the same chat composer (`gN`), **import `ChatBox`**; if the same session menu, extend `SessionItem` with a `variant` — do not rebuild a skinny textarea or sidebar row and call it done.
3. **One surface ≠ another** — Do not transplant Library title bar, sidebar `h-[36px]` rows, or Home hero onto Project / Computer / Search. Each surface has its own mined tree (`bF`/`AX`/`AJ`/`bz`, `e7`/`eR`/`eD`, …).
4. **Do not invent chrome** — Missing from mined Header/body → omit. Example: “选择要使用的应用” was a misread of **Use {product}'s computer**. Project: no fake「新建任务」pill; use `gN`/`ChatBox`.
5. **User visual beats stale JS** when they contradict. Note once, then follow the user.
6. **Product constraints** (unless user overrides): No Collaborate; no Manus 1.6 / Chat·Lite header switcher; i18n both `en.ts` + `zh.ts`.
7. **No `localStorage` for product data** — Favorites, pins, lists, and any user preference that official syncs to the server must use **backend APIs + Mongo** (e.g. session `is_favorite`, Library `file_favorites`). Do **not** ship a temporary `localStorage` stand-in “for now”. UI chrome prefs already in the app (sidebar expand) may stay as-is; **do not add new localStorage keys** for Manus-parity features.
8. **Do not commit** unless asked. Do not commit `tmp/` screenshots or scraped bundles.

## Workflow

```
Manus UI replicate:
- [ ] 1. Capture live DOM / screenshot (logged-in target page)
- [ ] 2. Locate official chunk + component names (e.g. bF, AX, AJ, bz)
- [ ] 3. Extract FULL className trees (paste into notes / gap table)
- [ ] 4. Map official node → local file; mark reuse (ChatBox) vs new
- [ ] 5. Implement by PASTING tokens: shell → chrome → content
- [ ] 6. Diff Vue classes vs mined snippet; delete anything not in source
```

### 直接抄 checklist (before claiming done)

- [ ] Outer shell classes match mined string (bg, flex, sticky heights)
- [ ] Grid / max-width / gaps are official numbers (map `@md:` → local `md:` only)
- [ ] Empty / hover / divider states copied (not “looks fine without”)
- [ ] No chrome borrowed from a different page
- [ ] Product skips are **removals** only (Share button gone), not redesigned layout

### 1. Capture live UI

Prefer a **logged-in** session (guest marketing pages lack Computer / sidebar).

```bash
# Chrome with sticky login profile
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-manus-debug \
  --profile-directory=Default \
  --no-first-run --no-default-browser-check \
  "https://manus.im/app/…"

# Drive tab: playwright-core connectOverCDP('http://127.0.0.1:9222')
# (local install often /tmp/pw)
```

Save under `tmp/screenshots/` (gitignored). 「截图发过来」→ personal skill **telegram-screenshots**.

**Capture gotchas (process, not a finished-page museum):**

- Prefer **element** screenshot for popovers; full-page makes menus unreadably small.
- If a portaled menu is “blank” in shots, check z-index vs overlays (e.g. center dialog `z-[1000]`) before blaming CSS tokens.
- Dump live `className` for disabled/hover — don’t invent from a washed-out crop.
- Click **exact** leaf text + `boundingBox`, not a huge grid parent.

**Dump quality (mandatory):**

- Do **not** implement from truncated HTML/class strings. Re-dump until chrome is complete (no mid-`<svg>` / mid-`text-[var(--`).
- Verify the **right node** (page title ≠ session group title).
- Pair every visual claim with a mined `className` / `e.s(["ComponentName"` snippet.

### 2. Mine official JS

Official app ships hashed chunks (e.g. under `/tmp/manus-js/` or project `tmp/`). Search exports:

```bash
rg -n 'e\.s\(\["ManusComputer' /tmp/manus-js/*.js
rg -n 'ManusComputerHeader|ManusComputerTimeline|ManusComputerPlanner' /tmp/manus-js/*.js
```

Extract by slicing around `className:"..."` / `e.s(["ComponentName"`. Prefer **exact Tailwind tokens** (`h-[56px]`, `ps-[16px]`, `var(--border-main)`, …).

Useful DOM ids from official:

| ID | Role |
|---|---|
| `manus-agent-workspace` | Computer shell root |
| `manus-chat-box` | Chat input region |
| `manus-home-page-session-content` | Session main column |

### 3. Gap list before coding

Produce a short table for the user:

| Official piece | Local file | Status |
|---|---|---|
| … | … | aligned / missing / wrong |

Implement only after the user confirms priority (or says「继续」).

### 4. Implement = paste then wire

1. **Paste shell** — copy outer `className` tree into the Vue root; fix only what Tailwind cannot express (`@md:` → `md:`, missing CSS vars via table below)
2. **Paste chrome** — header / composer / side cards / list rows with the same tokens; **reuse** `ChatBox` / existing icons when official reuses the same control
3. **Wire behavior** — APIs, i18n keys (English source strings as keys), navigation
4. **Content views last** — Browser / Terminal / File tool views

**Anti-pattern (Project page, fixed once):** first pass used Library-like `h-[56px]` title + invent「新建任务」button + sidebar `SessionItem`. Official is `bF` grid + `gN`/`ChatBox` + `AJ` (ChevronRight/Add) + `bz` rows. User:「为啥不直接抄」→ rewrite from mined trees.

Match **token-level** spacing from source (`gap-[8px]`, `h-[45px]` timeline). Map missing CSS vars:

| Official | Local fallback |
|---|---|
| `--text-blue` | add alias or use `--text-brand` |
| `--text-shining` | add for shimmer |
| `--icon-blue` | `--icon-brand` |

Shimmer pattern (streaming action line):

`animate-shimmer bg-[linear-gradient(110deg,var(--text-tertiary),35%,var(--text-shining),50%,var(--text-tertiary),75%,var(--text-tertiary))] bg-[length:200%_100%] bg-clip-text text-transparent`

### 5. Verify

- Re-read the mined snippet side-by-side with the Vue template (class strings, not vibes)
- Ask: any button/layout invented? any chrome copied from the wrong page?
- Type-check / lint if `node_modules` present: `cd frontend && npm run type-check && npm run lint`

## Computer panel (canonical)

Official `ManusComputer` children order:

**Header → Panel (`flex-1 min-h-0`) → Timeline → Planner**

Local mapping:

| Official | Local |
|---|---|
| `ManusComputer` | `ComputerPanel.vue` + `ComputerPanelContent.vue` |
| `ManusComputerHeader` | header block in `ComputerPanelContent.vue` |
| `ManusComputerPanel` | tool view slot + `ComputerInactiveEmpty.vue` |
| `ManusComputerTimeline` | bottom scrub bar in `ComputerPanelContent.vue` |
| `ManusComputerPlanner` | `PlanPanel.vue` (must sit **under** Timeline, not above ChatBox) |

### Header (do / don't)

**Do**

- Title: `{name}'s computer` (`text-[14px] font-[500]`)
- Subtitle: using + divider + action/param (`text-xs`, mono param)
- Right: **Use {product}'s computer** (monitor → confirm → takeover/VNC) + divider + **Close**
- Hide Use-computer when `isShare` / readonly

**Don't**

- “Select an application to use” app switcher (misread of Use-computer)
- Side/Center view toggle unless user explicitly wants dialog mode
- Play/Pause on timeline (official: Prev/Next + slider + Live + floating Jump to live)

### Timeline

- Bar: `h-[45px] … ps-[16px] pe-[8px]`, `border-t border-b`
- Prev/Next: `size-[24px]` only
- Slider: `h-[4px]`, range `--text-blue`, thumb `size-[14px]`
- Live: `size-[6px]` dot + `text-[12px] font-[500]`
- Jump to live: absolute centered above bar when not real-time
- Hover: datetime tooltip above scrub position
- Scrub against **real event timestamps**, not fake tool-index progress

### Planner

- Flat expand/collapse under timeline (`p-[16px]`, progress `current / total`)
- Not a card stacked above the chat input

### Empty panel

- `{name}'s computer is inactive` + centered illustration (~160px)

### Tool content (Terminal / File — easy to get wrong)

- **Panel bg** is `--background-gray-main`, never a white card inside Computer.
- **Terminal**: xterm host `agent-workspace-terminal-panel(-light|-dark)`; light bg `#f8f8f7`, padding `8px 4px 8px 12px`, **mono 14 / lineHeight 1.15** (not system UI 16 — that breaks column layout). See [reference.md](reference.md#terminal-computer--not-chat).
- **File**: tabs Diff / Original / **Modified** (`已修改`); **default = Modified**; Monaco on gray-main, line numbers off. Not the chat “Plain Text” card.
- Full tokens: [reference.md](reference.md#tool-content-panels-inside-computer-panel).

## Done surfaces (do not re-document)

**Library / cards / FilePreviewer chrome** already landed in code (`LibraryPage.vue`, `LibraryFileCard.vue`, `FilePreviewer*`, `ToolViewModeMenu.vue`). Skill is for **未对齐** surfaces and the 直接抄 workflow — not a museum of finished pages. If the user asks to redo one, mine JS/DOM again; do not paste stale skill tokens.

Optional deep dump (only when reopening a regression): [reference.md](reference.md).

## Other surfaces (pointers)

| Surface | Start here |
|---|---|
| Session list / sidebar | `SessionSidebar` |
| Library (done) | `LibraryPage.vue` + `LibraryFileCard.vue` |
| File preview (done unless user reopens) | `FilePreviewer.vue` + `useFilePreviewer` |
| Project detail | `ProjectPage.vue` |
| Search tasks | `SearchDialog.vue` |
| Chat top bar | `ChatPage.vue` header |
| Input | `ChatBox.vue` |
| Take control banner | `TakeControlBanner.vue` |

When starting a **new** surface, repeat the workflow — do not reuse Computer / Library assumptions blindly.

## Project page (canonical)

Official **`/app/project/:projectId`** (`1whdjijd45ufa.js` `bF` / `AX` / `gN` / `AJ` / `bL` / `bz` / `A9`).
Local: `/project/:projectId` → `ProjectPage.vue`. **Hide FilePreviewer**.

| Piece | Official tokens (copy these) |
|---|---|
| Shell | `flex flex-col items-center gap-3 w-full h-full relative bg-[var(--background-gray-main)]` |
| Header `A9`/`uM` | sticky `h-[56px] … ps-[14px] pe-[20px] md:px-[24px]`; Share + More — **skip Share/Leave** |
| Grid | `pt-8 px-[24px] max-w-[768px]` + `md:max-w-[1168px] md:grid-cols-[minmax(390px,768px)_minmax(240px,320px)] md:gap-x-[44px] md:grid-rows-[auto_auto_1fr]` (official `@md:` → local `md:`) |
| Title `AX` | icon `p-[12px] rounded-[12px] bg-fill-tsp-white-main` + `text-xl font-[500]` + “Created by” / “Updated” |
| Composer `gN` | **reuse `ChatBox`** (`scene=project`); submit → createSession + move + `router.push` with `state` like Home |
| Instructions `AJ` | `rounded-[12px] border`; title + **ChevronRight**; empty → outline **Add**; **no Pencil chrome** |
| Tasks `bL` | `mt-[32px] pb-[32px] px-[16px]`; empty `pt-48` + “Create a new task to get started” |
| Task row `bz` | `SessionItem variant="project"`: `py-[12px] gap-[12px] mx-[-8px]` + time + hover ⋯ + bottom hairline |
| Dialog | Instructions `w-[560px] h-[560px]` |
| Sidebar | Row → `/project/:id` + active; chevron expands nested tasks |
| API | `GET/POST/PATCH/DELETE /projects`, pin, session `PATCH …/project` |

### Project — do not invent / classic mistakes

| Mistake | What went wrong |
|---|---|
| Guess from Library shell | Official is **two-column grid** `max-w-[1168px]`, not Library title+toolbar |
| Fake「新建任务」pill | Official `gN` = **same ChatBox** as home (`rounded-[22px]`) |
| Instructions + Pencil | Official `AJ` = title + **ChevronRight** + empty **Add** |
| Sidebar `SessionItem` as Tasks | Official `bz` = taller row + time + hairline (`variant="project"`) |
| Connectors / Skills / Scheduled | No local backend — omit, don’t fake cards |
| Share / Leave / members | Product skip — remove controls only |
| Custom project icon picker | Folder OK |

## Pitfalls

- **没直接抄 / 凭感觉对齐** — user will reject; paste mined `className` trees before wiring.
- **错页套壳** — do not transplant one finished page’s chrome onto another.
- **Truncated dump → invented chrome** — re-mine before coding.
- **Screenshot-only copy** — always mine JS/DOM for the component name.
- **`localStorage` for product state** — favorites / pins / synced prefs must be server APIs.
- **Done surfaces** — Library/cards/FilePreviewer already shipped; do not reopen or re-document unless the user asks.

## Verify checklists

```
直接抄 (any surface):
- [ ] Mined component names + class trees pasted (not vibes)
- [ ] Reused ChatBox / shared pieces where official reuses them
- [ ] No chrome from a different page; product skips = omit only
- [ ] Side-by-side re-check Vue vs JS snippet


Project verify:
- [ ] Grid md:max-w-[1168px] two-col; FilePreviewer hidden
- [ ] Composer = ChatBox; Instructions = ChevronRight (+ Add if empty)
- [ ] Tasks = SessionItem variant=project (bz), empty pt-48 copy
- [ ] Re-check AX/gN/AJ/bL/bz/A9 in 1whdjijd45ufa.js (or current chunk)

```

## Additional resources

- Optional token dump when reopening a regression: [reference.md](reference.md)
- Personal Telegram delivery (not in repo): `~/.cursor/skills/telegram-screenshots/SKILL.md`
