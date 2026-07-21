---
name: replicate-manus-ui
description: >-
  Replicate manus.im / manus.ai UI into ai-manus by mining official JS bundles
  and live DOM (Chrome CDP), then mapping classNames and structure onto Vue
  components. Use when aligning SessionSidebar, Computer panel, Chat header,
  Share popover, or any Manus UI parity work; when the user says 对齐官方、复刻、
  抄源码、manus.im, or asks what is still not aligned.
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
# Dump nodes matching computer / sidebar / header
# Save under tmp/screenshots/manus-live/ (gitignored)
```

Also save screenshots under `tmp/screenshots/` for visual diff. Never commit binaries.

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

## Other surfaces (pointers)

| Surface | Start here |
|---|---|
| Session list / sidebar | `SessionSidebar` (+ related list components) |
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
- **Screenshot-only copy** — misses hover states, empty states, and exact tokens; always mine JS for the component name.
- **Over-building** — dialog/center layout, Cloud/Local computer titles, policy error panels: only when source + user priority say so.

## Additional resources

- Component token dump and file map: [reference.md](reference.md)
