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
| Sidebar | `frontend/src/components/SessionSidebar.vue`, `SessionItem.vue` |
| Search modal | `frontend/src/components/SearchDialog.vue` |
| Library page | `frontend/src/pages/LibraryPage.vue`, `components/LibraryFileCard.vue` |
| Project page | `frontend/src/pages/ProjectPage.vue` |
| File type icons | `frontend/src/components/icons/CodeFileIcon.vue`, `FileIcon.vue` |
| Chat page wire-up | `frontend/src/pages/ChatPage.vue` |
| Share page | `frontend/src/pages/SharePage.vue` |
| Router | `frontend/src/router/index.ts` (`/library`, `/project/:projectId`) |
| Theme tokens | `frontend/src/assets/theme.css` (`--Button-border-secondary`, `--shadow-S`, …) |
| Terminal/File CSS | `frontend/src/assets/global.css` (xterm + `.computer-monaco-panel` + `shadow-menu`) |
| Locales | `frontend/src/locales/en.ts`, `zh.ts` |

## Mining recipe (Python sketch)

```python
s = open("/tmp/manus-js/<chunk>.js").read()
idx = s.find('e.s(["ManusComputerHeader"')
chunk = s[idx - 15000 : idx]
pos = chunk.rfind("h-[56px]")
print(chunk[pos : pos + 2500])
```

Search strings that work well: `Manus is using`, `Jump to live`, `Task progress`, `Use {product}'s computer`, `manus-agent-workspace`, `搜索文件`, `我的收藏`, `manus-home-page-session-content`, `{count} more files`, `md:grid-cols-3`, `md:max-w-[200px]`.

Library mine targets: `function e7(`, `function eW(`, `function eG(`, `function eT(`, `function eR(`, `function eD(`, `ei=R!==` (file vs session mode).

CDP dump checklist for Library:

1. Screenshot of full `/app/library` viewport (**All** + **search/favorites** flat state)
2. Toolbar parent `outerHTML` (全部 → view tabs) — **untruncated**
3. One **grid card** `outerHTML` including header + preview (must include `</svg>` and basename/`.ext`)
4. One **list row** dump (confirm `eD`, not a card)
5. Confirm page title node is `text-lg font-[500] leading-[28px]`, not session `md:text-[16px]`
6. Confirm scroll content has a **single** flex-col wrapper (not toolbar ‖ groups as flex-row siblings)

## Session sidebar (canonical)

Official `<nav>`:

```
bg-[var(--background-nav)] flex flex-col transition-[width,transform] duration-200
h-full border-e border-[var(--border-main)]
width: SESSION_LIST_WIDTH_FOLD 52 | UNFOLD 300
```

| Piece | Official |
|---|---|
| Header | `h-[56px] pe-[10px] ps-[12px]` — logo + **Search** + Collapse |
| Body | `p-[8px] pb-0 gap-px` |
| Nav rows | New Task → Agent → Plugins → Scheduled → Library (+ Claw product) |
| Library icon | `LibraryBig` (not `Library`) |
| New Task shortcut | hover-only `text-[11px] … opacity-0 group-hover:opacity-100` (local ⌘K) |
| Row chrome | `ps-[8px] pe-[2px] h-[36px] gap-[8px] rounded-[10px]` |
| Active row | `bg-[var(--fill-tsp-white-main)]` when route matches (e.g. `/library`) |
| Scroll | `-mx-[8px]`; sticky **Projects** / **Tasks** headers `z-[3]` |
| Tasks filter | size-32 `ListFilter` on header (not chevron-as-label) |
| Footer | fade mask + avatar + Desktop/Bell placeholders |

Local: `SessionSidebar.vue` + `SessionItem.vue`. Skip invite/share-friend banner (product).

Search opens **`SearchDialog`** (modal), not an inline sidebar filter.

## Search dialog (canonical)

Centered modal (not a page):

```
@container/dialog w-[680px] h-[440px] rounded-[20px]
bg-[var(--background-menu-white)] shadow-menu
```

- Placeholder: Search tasks / 搜索任务
- Groups: Today / Yesterday / Past 7 days / …
- Top row can include New Task
- Local: `SearchDialog.vue`; CSS `shadow-menu` in `global.css`

## Library (canonical)

Official URL: `https://manus.im/app/library` — **full page**, never a dialog.  
Source chunk (example): `/tmp/manus-js/2930l2ba6yrcn.js` — exports/helpers: `e7` toolbar, `e9` tabs, `eW`/`eG` groups, `eT` flat list, `eR` grid card, `eD` list row, `ey` name, `ev` code preview.

```
#manus-home-page-session-content
  bg-[var(--background-gray-main)]
  └─ flex size-full min-h-0 flex-col bg-gray-main
     ├─ header h-[56px] … ps-[14px] pe-[20px] md:px-[24px]
     │    title: text-lg font-[500] leading-[28px]  → 库 / Library
     └─ scroll (SimpleBar OR overflow-y-auto)
        └─ ONE child: flex min-h-full flex-col   ← critical
           ├─ sticky toolbar wrapper px-5 md:px-6 → e7 (max-w-[1000px])
           └─ body: eW (session) OR eT (file)     ← mode switch
```

**Local wiring:** route `/library` → `LibraryPage.vue` + `LibraryFileCard.vue`; card click opens **`FilePreviewer`**. Sidebar Library → `router.push('/library')` + active row highlight.

### Browse mode (official `ei`)

```
ei = (docType !== All) || isFavorite || searchTrimmed ? "file" : "session"
```

| Mode | When | UI |
|---|---|---|
| `session` | All + empty search + favorites off | `eW` → per-session `eG` (title + time + grid/list) |
| `file` | type filter / 我的收藏 / search text | `eT` flat `md:grid-cols-3` (or list rows) — **no** session headers |

Always grouping in filter/search → sparse one-card-per-group rows that look 「乱」.

### Toolbar (`e7`)

```
flex md:flex-wrap gap-[8px] pb-[12px] md:pb-[20px] items-center
max-w-[1000px] mx-auto w-full
├─ 全部 — h-8 rounded-lg border-[var(--Button-border-secondary)]
│        active only when type ≠ All: bg-[var(--fill-blue)] text-[var(--text-blue)]
├─ 我的收藏 — same border; active: bg-[var(--function-warning-tsp)]
├─ Search — order-first w-full md:order-none md:ms-auto md:min-w-[160px] md:max-w-[200px]
│           h-8 rounded-[8px] … placeholder 搜索文件
└─ e9 Tabs — item h-full w-[32px] min-w-[32px]; LayoutGrid | List icons
```

Theme: `--Button-border-secondary`, `--icon-blue`, `--border-primary` (search focus), `--function-warning-tsp`, `--shadow-S`.

### Groups (`eW` / `eG`) + grid

```
eW: flex flex-col pb-6 px-[20px]  + gap-3 (grid) | gap-[17px] (list)
  └─ max-w-[1000px] mx-auto w-full flex flex-col md:gap-[24px] gap-[12px]
     └─ eG × N
```

| Piece | Token |
|---|---|
| Group title | `md:text-[16px] text-[14px] font-medium leading-[22px]` + hover underline |
| Time | `text-[13px] leading-[18px] text-secondary`; grid header `justify-between gap-[8px]` |
| Grid | `grid gap-3 items-start grid-cols-1 md:grid-cols-3` (~278–325px cols) |
| Cap | show first 3; button `{count} more files` |
| List mode | **`eD` rows** — not 1-col `eR` cards |

### File card `eR` / name `ey` / preview `ev`

```
clickable relative flex flex-col overflow-hidden
rounded-[12px] border-[0.5px] border-[var(--border-dark)]
bg-[var(--background-menu-white)]
hover:shadow-[0_7px_16px_0_var(--shadow-S)]
├─ header: flex items-center gap-2 px-2 py-[10px] border-b border-main
│  ├─ FileIcon 24
│  ├─ flex flex-1 min-w-0 items-center gap-1
│  │  └─ text-sm truncate — ey: basename + .ext INLINE (flex row, not two blocks)
│  │     + optional StarFill when favorite
│  └─ ⋯ menu
└─ preview: aspect-[16/9] overflow-hidden relative
   code: canvas #F7F7F7 (dark #1c1c1c) + p-[12px] + scale-[0.8] origin-top-left
         + pre w-[125%] + bottom fade gradient
```

### List row `eD`

```
clickable group flex … hover:bg-[var(--fill-tsp-white-light)]
md:w-[calc(100%+24px)] md:px-[12px] md:-ms-[12px] rounded-lg
└─ w-full flex … border-b border-main gap-10 py-[12px] md:ps-[8px]
   ├─ icon 24 + text-[14px] leading-[20px] (+ star)
   └─ hover actions / ⋯
```

### Library failure modes (learned)

| Mistake | Why it happened | Fix |
|---|---|---|
| Modal `LibraryDialog` | Assumed Search-like UX | Full page route `/library` |
| Truncated CDP mid-SVG | Coded from incomplete dump | Mine full `eR`/`e7` from JS chunk |
| Two-line filename blocks | Misread `innerText` newlines | Official `ey` inline basename+ext |
| List = 1-col cards | Guessed list mode | Copy `eD` row classes |
| Fixed `h-[166px]` preview | Guessed from card height | `aspect-[16/9]` + `scale-[0.8]` |
| Search `flex-1` on desktop | Guessed toolbar | `md:max-w-[200px] md:ms-auto` |
| Always session-group | Missed `ei` file/session switch | Flat `eT` when filter/search/favorites |
| SimpleBar siblings sideways | Content node is `flex-row` | One `flex-col` child, or drop SimpleBar |
| FilePreviewer always unmounted on `/library` | Avoided width steal | Mount previewer; `hide` on enter; **card click** opens it |
| Named `FilePanel` | Local legacy | Official **`FilePreviewer`** |
| File favorites in `localStorage` | “先本地以后再改” | **Forbidden** — `POST/DELETE /library/files/{id}/favorite` + Mongo `file_favorites` |
| 「布局很乱」= empty columns | 1 file / session in 3-col grid | Expected; use flat mode or richer data |
| Wrong title node | Mined session `text-[14px]` | Page title is `text-lg … leading-[28px]` |

CDP dump checklist:

1. Full `/app/library` screenshot (All + one filtered/search state)
2. Toolbar `outerHTML` untruncated; one `eR` card including `</svg>` + preview
3. Confirm list mode dumps **`eD` row**, not a card
4. Confirm page title vs session group title nodes

## Chat header (brief)

Official bar often: `h-[56px] … py-[12px] ps-[14px] pe-[20px] md:px-[24px] gap-1 border-b … bg-[var(--background-gray-main)]`.

Left product label ~ `text-[16px]/md:text-[18px] font-[500]` — product decision may be plain **Manus** without mode chevron.

## Project (canonical)

**直接抄** from `/tmp/manus-js/1whdjijd45ufa.js`: `bF`, `AX`, `gN(scene=project)`, `AJ`, `bL`, `bz`, `A9`/`uM`.
Official URL: `https://manus.im/app/project/:projectId`.

```
Dragger: flex flex-col items-center gap-3 w-full h-full relative bg-gray-main
  SimpleBar
    A9 sticky h-[56px] — Share + More (local: More only; skip Leave)
    grid pt-8 px-[24px] max-w-[768px]
      + md:max-w-[1168px] md:grid-cols-[minmax(390px,768px)_minmax(240px,320px)] md:gap-x-[44px]
      AX title | gN ChatBox | AJ Instructions (ChevronRight + Add) | bL Tasks (bz rows)
```

| Paste these | Not these |
|---|---|
| `gN` → reuse `ChatBox` | Fake「新建任务」pill / skinny textarea |
| `AJ` ChevronRight + Add | Pencil-as-primary chrome |
| `bz` `py-[12px]` + time + hairline | Sidebar `h-[36px]` `SessionItem` |
| Official two-col grid | Library `h-[56px]` title + single column body |

Do not invent: Connectors/Skills/Scheduled, Share/Leave.

Local: `ProjectPage.vue`, `SessionItem variant="project"`, router `/project/:projectId`, MainLayout hides FilePreviewer.
