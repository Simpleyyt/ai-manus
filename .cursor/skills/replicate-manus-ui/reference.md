# Manus UI replicate — reference

Detailed tokens and file map. Read when implementing Computer or auditing gaps.

## Official Computer shell

```
id: manus-agent-workspace
class: h-full flex flex-col bg-[var(--background-gray-main)]
  sidebar mode: border-l border-[var(--border-main)]
  dialog mode: rounded-[12px] border + heavy multi-layer shadow
children: Header | Panel | Timeline | Planner
```

## Header class tree

```
flex h-[56px] items-center gap-[8px] border-b border-[var(--border-main)] px-[16px] py-[12px]
├─ left: flex min-w-0 flex-1 flex-col justify-center
│  ├─ h2: truncate text-[14px] font-[500] text-[var(--text-primary)]
│  └─ row: flex … gap-[8px] text-[var(--text-tertiary)] text-xs
│     ├─ using title (Translations with <b>)
│     ├─ divider: h-[12px] w-px bg-[var(--border-main)]
│     └─ action + mono param (shimmer when tool streaming)
└─ right: flex shrink-0 items-center gap-[4px]
   ├─ Use computer button !size-[32px] !rounded-[8px]
   ├─ divider: h-[16px] w-px bg-[var(--border-dark)]  (px-[4px] wrapper)
   ├─ Side/Center IconButton (source: when !mobile) — often omitted per product decision
   └─ Close IconButton !size-[32px]
```

Title variants in source: `{name}'s computer` | `Cloud computer` | `Local computer` (special shell ids).

## Timeline class tree

```
mt-auto flex h-[45px] w-full items-center gap-[8px] py-[12px] ps-[16px] pe-[8px] relative
bg-[var(--background-gray-main)] border-t border-b border-[var(--border-main)]
├─ Prev / Next size-[24px] (no Play)
├─ SliderHorizontal h-[4px]
│  track: bg-[var(--fill-tsp-gray-dark)]
│  range: bg-[var(--text-blue)]
│  thumb: size-[14px] border-2 border-[var(--background-menu-white)] bg-[var(--text-blue)]
│  hover child: absolute -top-10 … bg-[var(--text-blue)] datetime
├─ Live: size-[6px] dot + text-[12px] font-[500]
└─ Jump to live (when not live): absolute left-1/2 -translate-x-1/2 bottom: calc(100% + 10px)
   h-10 px-3 rounded-full border + shadow, Play icon + label
```

## Planner class tree

```
button.flex.w-full.flex-col.p-[16px].pe-0.text-start.hover:bg-[var(--fill-tsp-gray-main)]
├─ row: title or current task + "i / n" + chevron
└─ expanded: max-h-[260px] list, gap-[4px], icons size 12
   done → Check success | todo → Clock tertiary | doing → spinner | else → blue diamond
```

## Use-computer confirm copy (keys)

- `Use {product}'s computer`
- `Use application on {product}'s computer`
- `You're about to use {product}'s computer. `
- `When finished, please inform {product} of your changes to help it work effectively.`
- `Use application` / `Cancel`

Confirm → local takeover: `CustomEvent('takeover', { sessionId, active: true })` (same path as Take control).

# Tool content panels (inside Computer Panel)

Official panels have **no** inner title bar — url/path already live in Computer Header.
Panel slot itself is gray canvas: `bg-[var(--background-gray-main)]` (not white).

| Tool | Official notes | Local |
|---|---|---|
| Browser | `px-0 py-0 … h-full` + screenshot/VNC; Take control `bg-menu-white` / `hover:bg-[var(--text-blue)]` | `BrowserToolView.vue` |
| Terminal | see **Terminal** below | `ShellToolView.vue` (`@xterm/xterm` + fit) |
| Search | `px-4 py-3`, favicon + title + snippet | `SearchToolView.vue` |
| File | see **File** below | `FileToolView.vue` + `MonacoEditor` / `MonacoDiffEditor`; backend `old_content` on CALLING |
| Empty | inactive illustration | `ComputerInactiveEmpty.vue` |

### Terminal (Computer — not chat)

Host classes: `agent-workspace-terminal-panel` + `-light` / `-dark`.

Measured light theme (do **not** use white `#fff` / VS Code dark defaults):

| Token | Value |
|---|---|
| Background | `--background-gray-main` → `#f8f8f7` |
| Foreground | `--text-primary` → `#34322d` |
| Selection | `#b8d3f8` (light) |
| `.xterm` padding | `8px 4px 8px 12px` |
| Font | **ui-monospace** stack (Menlo/Monaco/…), **14px**, lineHeight **1.15** — NOT system UI / 16px (CDP inherits parent font; xterm options are mono) |
| Options | `customGlyphs: true`, `overviewRuler: { width: 8 }`, `disableStdin`, `cursorInactiveStyle: "none"` |
| Cursor | theme `cursor` / `cursorAccent` = background (invisible) |
| Theme | CSS vars via `tU(el, isDark)` — light maps ANSI; dark returns bg/selection only |
| Selection | `--background-selection` (fallback `#b8d3f8`) |
| Write | `\x1b[?2026h\x1b[2J\x1b[3J\x1b[H` + text + `\x1b[?2026l` (not naive `reset()`) |

CSS hooks live in `frontend/src/assets/global.css` (`.agent-workspace-terminal-panel*`).

### File (Computer Monaco)

Tabs (only when `old_content` present): **Diff / Original / Modified**  
Locale ZH: `差异` / `原始` / **`已修改`** (not `修改后`).

| Rule | Official |
|---|---|
| Default tab | **Modified** (`data-state=on`), not Diff |
| Tab chrome | `flex items-center justify-center px-[16px] py-[8px]` + pill `bg-[var(--tab-fill)]` |
| Editor canvas | `bg-[var(--background-gray-main)]` (theme `vs` + CSS override; not pure white) |
| Line numbers | **off**; ~16px left margin / `lineDecorationsWidth` |
| Diff mode | inline (not side-by-side) when user picks Diff |

Do not confuse with chat **Plain Text** blocks (`rounded-lg border … bg-[var(--fill-tsp-white-light)]` + Copy) — those are message markdown, not Computer File.

## Local file map

| Concern | Path |
|---|---|
| Computer shell | `frontend/src/components/ComputerPanel.vue` |
| Computer content | `frontend/src/components/ComputerPanelContent.vue` |
| Inactive empty | `frontend/src/components/ComputerInactiveEmpty.vue` |
| Planner | `frontend/src/components/PlanPanel.vue` |
| Step icons | `frontend/src/components/PlanStepIcon.vue` |
| Terminal view | `frontend/src/components/toolViews/ShellToolView.vue` |
| File view | `frontend/src/components/toolViews/FileToolView.vue` |
| Monaco | `frontend/src/components/ui/MonacoEditor.vue`, `MonacoDiffEditor.vue` |
| Chat page wire-up | `frontend/src/pages/ChatPage.vue` |
| Share page | `frontend/src/pages/SharePage.vue` |
| Theme tokens | `frontend/src/assets/theme.css` |
| Terminal/File CSS | `frontend/src/assets/global.css` (xterm + `.computer-monaco-panel`) |
| Locales | `frontend/src/locales/en.ts`, `zh.ts` |

## Mining recipe (Python sketch)

```python
s = open("/tmp/manus-js/<chunk>.js").read()
idx = s.find('e.s(["ManusComputerHeader"')
chunk = s[idx - 15000 : idx]
pos = chunk.rfind("h-[56px]")
print(chunk[pos : pos + 2500])
```

Search strings that work well: `Manus is using`, `Jump to live`, `Task progress`, `Use {product}'s computer`, `manus-agent-workspace`.

## Chat header (brief)

Official bar often: `h-[56px] … py-[12px] ps-[14px] pe-[20px] md:px-[24px] gap-1 border-b … bg-[var(--background-gray-main)]`.

Left product label ~ `text-[16px]/md:text-[18px] font-[500]` — product decision may be plain **Manus** without mode chevron.
