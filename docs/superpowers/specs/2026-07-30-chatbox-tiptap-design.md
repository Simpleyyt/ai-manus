# ChatBox TipTap + Slash Parity (方案 C)

Date: 2026-07-30  
Status: approved for implementation (awaiting written-spec review)  
Surface: `ChatBox` composer (Home / Chat / Project / Claw)

## Goal

把本地 `ChatBox` 从 `<textarea>` 换成与官方同构的 **TipTap** 输入壳，并加上 **仅本地可用** 的 `/` 命令菜单；外层 class 直接抄 official，对外仍输出纯字符串，不改后端消息协议。

## Decisions (locked)

| 项 | 选择 |
|---|---|
| 范围 | **C** — TipTap + slash（不是仅壳 A / 轻量提示 B） |
| `/` 菜单内容 | **B** — 只列本地真有能力（至少「添加本地文件」） |
| 内容模型 | 挖官方后定：**UI 用 TipTap JSON；提交用 `getText()` 纯文本**；不把 `editorContent` 写入后端 |

## Official findings (CDP + `/tmp/manus-js/3-57lzi_niw24.js`)

### Shell (live DOM)

```
flex flex-col rounded-[22px] relative bg-[var(--background-menu-white)] py-3 w-full z-[2] gap-3
shadow-[0px_12px_32px_0px_rgba(0,0,0,0.02)] border border-black/8 dark:border-[var(--border-main)]
focus-within:border focus-within:border-black/20 focus-within:dark:border-[var(--border-dark)]
```

Editor wrap:

```
chat-input-editor overflow-auto ps-4 pe-2 bg-transparent pt-[1px] border-0
focus-visible:ring-0 focus-visible:ring-offset-0 w-full
placeholder:text-[var(--text-disable)] text-[15px] leading-[24px]
min-h-[50px]   /* home */
min-h-[28px]   /* session */
max-h-[216px]
```

Inner: `tiptap ProseMirror` (+ `ProseMirror-focused`).

### Placeholders (zh live)

- Home: `分配一个任务或输入 / 查看更多`（`data-placeholder` on empty `<p>`）
- Session: `向 Manus 发送消息`

### Editor schema (live TipTap)

**Nodes:** `doc`, `paragraph`, `text`, `hardBreak`, `bulletList`, `orderedList`, `listItem`, plus product-only `skillTag`, `mention`, `addonResourceMention`, `canvasMark`, `canvasImage`, `selectExt`, `inputExt`.

**Marks:** `bold`, `italic`, `suggestion`.

**Notable extensions:** `markdownEditingShortcuts`, `placeholder`, `command` / `suggestion` (slash), `undoRedo`.

### Wire / draft model

- Draft dual-write: `{ content: { text, editorContent, files, … } }`
- Agent path uses **plain `text`** (`chatSlice.selectors.textContent`)
- `editor.getText()`：`skillTag` → `/slides …`；**bold/italic 不进入 text**
- Slash 选技能 → 插入 `skillTag` 节点，不是改 API 协议

### Product omit (unchanged constraints)

Desktop chip、Cable/connectors、语音、官方技能/`skillTag`/mention/canvas — **不做**。

## Approach (recommended #1)

1. TipTap 壳 + 基础扩展（paragraph / hardBreak / bold / italic / lists + placeholder + undo）
2. `/` suggestion 仅本地项（「添加本地文件」→ 现有 upload）
3. `v-model` 仍是 `string`，`update:modelValue` ← `editor.getText()`
4. 底栏：`+` 带边框；去掉独立 Paperclip；发送/停止逻辑不变

**Rejected:** #2 本地假 chip 节点（无技能体系）；#3 后端双写 `editorContent`（协议大改）。

## Scope

**In:**

1. `frontend/src/components/ChatBox.vue` — TipTap 替换 textarea；shell / footer token 对齐
2. TipTap 依赖：`@tiptap/vue-3`、`@tiptap/starter-kit`（或等价精简）、`@tiptap/extension-placeholder`；slash 用官方同思路的 Suggestion（`@tiptap/suggestion` + tippy/本地浮层）
3. Slash 菜单 UI：直接抄 official 浮层 class（再挖一轮完整 class 再贴）；首项「添加本地文件」
4. i18n：首页 placeholder 对齐「任务 + `/` 提示」；会话保持「向 Manus 发送消息」类文案（en + zh）
5. Home vs session `min-h`：通过现有 `placeholder` prop 或新增 `variant`/`dense` 区分（Chat 页会话用矮高）
6. 单元测试：至少覆盖 `getText` 同步、`/` 触发菜单、Enter 发送不打断中文 IME（若现有 composable 可测）

**Out:**

- `skillTag` / mention / canvas / 官方技能目录
- Desktop / Cable / 语音
- 后端消息 schema / Mongo 存 `editorContent`
- Claw 专用第二套编辑器（继续复用 `ChatBox`）
- 把富文本渲染进历史气泡（历史仍纯文本）

## Local mapping

| Piece | File / note |
|---|---|
| Composer | `frontend/src/components/ChatBox.vue` |
| Attachments | `ChatBoxFiles.vue` — 保持；slash/「添加本地文件」调用现有 `uploadFile` |
| Consumers | `Home` / `ChatPage` / `ProjectPage` / `ClawPage` — props 尽量兼容；按需传 session 矮高 / placeholder |
| Locales | `frontend/src/locales/en.ts` + `zh.ts` |
| Deps | `frontend/package.json` |

### Public API (keep)

```ts
modelValue: string
attachments: FileInfo[]
rows: number          // may become unused / ignored once TipTap owns height; prefer not break callers
isRunning: boolean
hideStopButton?: boolean
allowSendFilesOnly?: boolean
placeholder?: string
// emits: update:modelValue, update:attachments, submit, stop
```

可选新增：`dense?: boolean`（会话 `min-h-[28px]`）— 若用 placeholder 推断不稳则显式加。

### Slash items (v1)

| id | Label (i18n) | Action |
|---|---|---|
| `add_local_files` | `Add local files` | close menu → `uploadFile()` |

后续本地真有能力再加行；禁止为对齐而放灰项官方技能。

## UI tokens to paste

- Outer card：上表 official shell（本地现 `pt-3 pb-2.5 gap-2 max-h-[300px]` → 改成 `py-3 gap-3` + `max-h-[216px]` 在 editor，不是整卡 300）
- Editor wrap：`chat-input-editor …` 全串
- Footer：`flex gap-1.5 px-3 items-center`；`+` 按钮抄 official 带 border 的圆形（再挖精确 class 后贴）；右侧 Send `Button-primary-black` / Stop 方块保持现有语义
- 删除独立 Paperclip 按钮（入口归 `+` 菜单与 `/`）

## Behavior

- **Enter**：发送（非 shift）；**Shift+Enter**：换行（TipTap hardBreak）
- **IME**：`compositionstart/end` 期间 Enter 不发送（与现逻辑一致）
- **`/`**：仅在行首或空白后触发 suggestion（跟 TipTap suggestion 默认）；选中项执行 action，不把假 skill 文本硬塞进 model（「添加本地文件」只开文件选择）
- **空内容**：`getText().trim()` 为空且无附件 → 禁用发送（现 `sendEnabled`）
- **外部 `modelValue` 清空**：submit 后父组件清空 → editor `setContent('')` / `clearContent`
- **markdown 快捷键**：允许 StarterKit 自带 bold/italic/list 输入手感；提交仍纯文本（官方同款）

## Verification

1. 首页 / 会话：壳、placeholder、`min-h`、focus-within border 与官方截图并排接近
2. `/` 弹出本地菜单；选「添加本地文件」能选文件并进 `attachments`
3. 发送后消息仍是纯字符串；后端 / WS 无回归
4. Home、Chat、Project、Claw 共用 ChatBox 均可输入发送
5. `cd frontend && npm run test && npm run type-check && npm run lint`
6. Telegram：首页+会话 ChatBox 对比图（可选）

## Open dig before code (implementation plan will include)

1. 再挖官方 `/` 浮层完整 `className` + `+` 按钮 border class（直接贴，不近似）
2. 确认 Home vs session 用 prop 还是路由推断 `min-h`
