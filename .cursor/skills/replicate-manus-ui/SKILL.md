---
name: replicate-manus-ui
description: >-
  Replicate manus.im / manus.ai UI into ai-manus by mining official JS bundles
  and live DOM (Chrome CDP), then mapping classNames and structure onto Vue
  components. Use when aligning SessionSidebar, Library page, Search dialog,
  Computer panel, Chat header, Share popover, or any Manus UI parity work; when
  the user says 对齐官方、复刻、抄源码、manus.im, or asks what is still not aligned.
---

# Replicate Manus UI

Align ai-manus frontend with **logged-in manus.im** by copying structure and Tailwind classNames from official source — not by guessing from screenshots alone.

Respond in **中文** unless the user writes in English.

## Hard rules

1. **Source first** — Prefer official bundle JSX / live DOM class strings over memory or “AI default” layouts.
2. **Do not invent chrome** — If a control is not in the mined Header/Timeline (or the user says it is not on the live site), do not add it. Example: “选择要使用的应用” was a wrong reading of **Use {product}'s computer** (VNC / takeover).
3. **User visual beats stale JS** when they contradict (e.g. no Side/Center view on their session). Note the discrepancy once, then follow the user.
4. **Product constraints for this repo** (unless user overrides):
   - No Collaborate
   - No Manus 1.6 / Chat·Lite mode switcher in chat header
   - i18n: add keys to both `frontend/src/locales/en.ts` and `zh.ts`
5. **Do not commit** unless asked. Do not commit `tmp/` screenshots or scraped bundles.

## Workflow

Copy and track:

```
Manus UI replicate:
- [ ] 1. Capture live DOM / screenshot (logged-in target page)
- [ ] 2. Locate official chunk + component export names
- [ ] 3. Extract className trees (Header / body / footer)
- [ ] 4. Map to local Vue files + gap list
- [ ] 5. Implement shell → chrome → content (in that order)
- [ ] 6. Re-check against source; remove extras the user rejects
```

### 1. Capture live UI

Prefer a **logged-in** session (guest marketing pages lack Computer / sidebar).

**Chrome CDP** (typical local debug profile):

```bash
# Example: Chrome with --remote-debugging-port=9222
# Dump nodes matching computer / sidebar / header / library
# Save under tmp/screenshots/manus-live/ (gitignored)
```

Also save screenshots under `tmp/screenshots/` for visual diff. Never commit binaries.

**Dump quality (mandatory):**

- Do **not** implement from truncated HTML/class strings. Card/toolbar dumps cut mid-`<svg>` or mid-`text-[var(--` are incomplete — re-dump until header, filename row, preview body, and trailing chrome (e.g. `⋯`) are fully present.
- Verify you selected the **right node** (page title `库` ≠ session group title `text-[14px]`).
- Prefer screenshot + full outerHTML of one card + toolbar parent over a shallow class list.

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

### 4. Implement order

1. **Shell** — outer layout, borders, gray background, no fake white cards if official is `border-l` sidebar
2. **Chrome** — header / timeline / planner placement
3. **Behavior** — real data (timeline timestamps, plan steps, takeover), not decorative controls
4. **Content views** — Browser / Terminal / File tool views last

Match **token-level** spacing from source (`gap-[8px]`, `h-[45px]` timeline). Map missing CSS vars:

| Official | Local fallback |
|---|---|
| `--text-blue` | add alias or use `--text-brand` |
| `--text-shining` | add for shimmer |
| `--icon-blue` | `--icon-brand` |

Shimmer pattern (streaming action line):

`animate-shimmer bg-[linear-gradient(110deg,var(--text-tertiary),35%,var(--text-shining),50%,var(--text-tertiary),75%,var(--text-tertiary))] bg-[length:200%_100%] bg-clip-text text-transparent`

### 5. Verify

- Re-read the mined snippet for the component you touched
- Ask: did we add any button/menu not in source or rejected by user?
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

## Library page (canonical)

Official **`/app/library` is a full page**, not a modal (Search is the modal). Local: `/library` → `LibraryPage.vue` + `LibraryFileCard.vue`. Mine from chunk `2930l2ba6yrcn.js`: **`e7` toolbar · `e9` view tabs · `eW`/`eG` groups · `eT` flat · `eR` grid card · `eD` list row · `ey`/`ev` filename/preview**.

| Piece | Official |
|---|---|
| Shell | `flex size-full min-h-0 flex-col` under sidebar; title **库** `text-lg font-[500] leading-[28px]` in `h-[56px]`; **hide `FilePanel`** on `/library` |
| Scroll | Official wraps **one** `flex min-h-full flex-col` under SimpleBar. Local prefers `overflow-y-auto` — **never** put toolbar + groups as **siblings** under a `flex-row` SimpleBar content (they lay out sideways → 「布局很乱」) |
| Toolbar `e7` | sticky; own `max-w-[1000px] mx-auto` inside `px-5 md:px-6` — **全部** dropdown \| **我的收藏** \| search `md:ms-auto md:max-w-[200px]` \| Grid/List **`e9` 32×32 icon tabs** (not filled pills) |
| Browse mode | **`session`** (All, no query): grouped `eW`/`eG`. **`file`** (type ≠ All **or** favorites **or** search text): flat `eT` — **no** session headers, one `md:grid-cols-3` |
| Groups `eG` | title `md:text-[16px] … font-medium leading-[22px]` + time (`justify-between` in grid); first **3** cards + “{count} more files” |
| Grid `eR` | `rounded-[12px] border-[0.5px] border-dark` + hover `shadow-S`; header `gap-2 px-2 py-[10px]`; **24px** type SVG; filename **`ey` basename+ext inline** single `text-sm` truncate row; preview **`aspect-[16/9]`** + code `scale-[0.8]` on `#F7F7F7` |
| List `eD` | **horizontal rows** (`hover:bg-fill-tsp-white-light`, `border-b`, icon + `text-[14px]`), **not** 1-col grid cards |

Active chrome: type filter → `bg-[var(--fill-blue)] text-[var(--text-blue)]` (only when **not** All); favorites → `bg-[var(--function-warning-tsp)]`. Favorites = session `is_favorite` on `/library/files`. Full tokens: [reference.md](reference.md#library-canonical).

### Library — do not invent / classic mistakes

| Mistake | What went wrong |
|---|---|
| `LibraryDialog` modal | Official is a **route page**; Search is the `680×440` modal |
| Truncated CDP → guess chrome | Mid-SVG dumps invent padding / wrong tabs / fake list |
| Filename two block lines | Official `ey` is **inline** basename + `.ext` |
| List = 1-col cards | Official list is **`eD` rows** |
| Fixed `h-[166px]` preview | Official `aspect-[16/9]` + `scale-[0.8]` |
| Search `flex-1` grow | Official `md:max-w-[200px] md:ms-auto` |
| Always session-group | Search / favorites / type filter → **flat `eT`** |
| SimpleBar multi-child | Content `flex-row` → toolbar left, groups shoved right |
| Leave `FilePanel` open | Chat workspace column steals width on `/library` |
| Blame sparse 3-col for “乱” | 1 file / session → left column only is **correct**; denser when flat mode or multi-file sessions |

## Other surfaces (pointers)

| Surface | Start here |
|---|---|
| Session list / sidebar | `SessionSidebar` (+ related list components) |
| Library | `LibraryPage.vue` + `LibraryFileCard.vue` (route `/library`) |
| Search tasks | `SearchDialog.vue` (centered `680×440` modal — not Library) |
| Chat top bar | `ChatPage.vue` header (`h-[56px]`, Share popover) |
| Input | `ChatBox.vue` |
| Take control banner | `TakeControlBanner.vue` + browser takeover events |

When starting a new surface, repeat the workflow — do not reuse Computer assumptions blindly.

## Pitfalls

- **U in Header ≠ app menu** — it is “Use Manus's computer” (VNC dialog), often with a confirm popover.
- **PlanPanel location** — moving it only in CSS while leaving it in ChatPage breaks parity.
- **White rounded card shell** — official sidebar Computer is gray + `border-l`, not `sm:rounded-[16px]` white card.
- **Terminal white / mono / wrong size** — live uses gray-main + **ui-monospace 14 / 1.15**; system UI 16 causes mid-word wrap.
- **File default Diff / 修改后** — live default is Modified / `已修改`.
- **Chat Plain Text ≠ Computer File** — left-column code card is a different surface.
- **Library ≠ dialog** — full page `/library`; Search is the `680×440` modal.
- **Library SimpleBar / scroll** — one flex-col child only; multi-sibling under flex-row content = sideways mess.
- **Library browse mode** — `file` (flat) vs `session` (grouped); do not always group.
- **Library list ≠ 1-col cards** — copy `eD` rows from source.
- **Truncated dump → invented chrome** — incomplete card/toolbar HTML caused wrong padding, fake list layout, wrong view tabs; re-mine before coding.
- **Wrong mined node** — session group `text-[14px]`/`md:text-[16px]` is not the page title `text-lg`.
- **Screenshot-only copy** — misses hover states, empty states, and exact tokens; always mine JS/DOM for the component name.
- **Over-building** — dialog/center layout, Cloud/Local computer titles, policy error panels: only when source + user priority say so.

## Library verify checklist

```
Library verify:
- [ ] Route /library; FilePanel hidden; no LibraryDialog
- [ ] All → session groups; search/favorites/type → flat 3-col (no group titles)
- [ ] Grid cards aspect-16/9 + inline filename; List = full-width rows (not pushed right)
- [ ] Toolbar max-w-1000; search ≤200px ms-auto; view tabs 32px
- [ ] Re-check e7/eW/eT/eR/eD in 2930l2ba6yrcn.js (or current chunk)
```

## Additional resources

- Component token dump and file map: [reference.md](reference.md)
