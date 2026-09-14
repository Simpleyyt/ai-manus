# Manus Skills UI Shell Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 直接抄官方 Skills UI 壳：**SettingsDialog → 技能 tab**（已添加的技能 + 创建 ▾ 占位对话框）+ ChatBox `/` skillTag chip；假数据；发送纯文本含 `/{skill-name}`。

**Architecture:** 复用现有 `SettingsDialog`/`SettingsTabs`；新增 `SkillsSettings.vue` + `SkillCard`；**不**做侧栏入口或 `/skills` 路由；`useSkills()` 供设置页与 slash 共用；TipTap `SkillTag` + text serializer。

**Tech Stack:** Vue 3 + TipTap (`@tiptap/vue-3` / `@tiptap/core`) + Vitest + vue-i18n + Tailwind；无后端改动。

**Spec:** `docs/superpowers/specs/2026-08-16-manus-skills-ui-shell-design.md`

## Global Constraints

- 直接抄 official class strings（挖矿后写入 `tmp/skills-ui-mine.md` 再贴）；禁止 approximate
- 纯 UI 壳：无 SKILL.md 运行时、无真 Upload/GitHub/Official/Build、无后端、无 localStorage 产品数据
- 不做 Project 右侧 Skills、不做官方商店独立页
- Slash 保留 `add_local_files`；skill 选中 → skillTag chip；`getText()` → `/{name}`
- i18n 两边：`frontend/src/locales/en.ts` + `zh.ts`；英文 key 用官方文案
- Do **not** commit unless the user explicitly asks
- Verify per task as specified; final: `cd frontend && npm run test && npm run type-check && npm run lint`
- Product skips: Collaborate、Manus 版本切换等既有禁项不变

---

## File structure

| File | Responsibility |
|---|---|
| `tmp/skills-ui-mine.md` | 挖矿笔记（gitignored）；完整 className / DOM |
| `frontend/src/types/skill.ts` | `Skill` / `SkillOwnerType` |
| `frontend/src/mocks/skills.ts` | 假 skill 列表常量 |
| `frontend/src/composables/useSkills.ts` | 只读 list + filterByQuery |
| `frontend/src/composables/__tests__/useSkills.spec.ts` | composable 单测 |
| `frontend/src/components/chatbox/skillTag.ts` | TipTap SkillTag 节点 |
| `frontend/src/components/chatbox/__tests__/skillTag.spec.ts` | serializer / insert |
| `frontend/src/components/chatbox/slashSuggestion.ts` | SlashItem 联合类型 + skill 项 |
| `frontend/src/components/chatbox/ChatBoxSlashMenu.vue` | skill 行 UI（挖后贴） |
| `frontend/src/components/ChatBox.vue` | 注册 SkillTag；buildSlashItems 含 skills |
| `frontend/src/components/__tests__/ChatBox.spec.ts` | slash → chip → getText |
| `frontend/src/components/settings/SkillsSettings.vue` | 设置内「已添加的技能」内容区 |
| `frontend/src/components/skills/SkillCard.vue` | SkillCard 卡片 |
| `frontend/src/components/skills/SkillsCreateMenu.vue` | 创建 ▾ 下拉 |
| `frontend/src/components/skills/SkillsPlaceholderDialog.vue` | 四类占位对话框 |
| `frontend/src/components/settings/SettingsTabs.vue` | 增加 `skills` nav（Features 组） |
| `frontend/src/components/settings/SettingsDialog.vue` | `#skills` slot |
| `frontend/src/composables/useSettingsDialog.ts` | `SettingsTabId` 含 `skills` |
| `frontend/src/locales/en.ts` / `zh.ts` | 文案 |

---

### Task 1: Mine official Skills UI

**Files:**
- Create: `tmp/skills-ui-mine.md` (gitignored; do not commit)

**Interfaces:**
- Consumes: logged-in manus.im Chrome CDP (`9222`) or existing `/tmp/manus-js` bundles
- Produces: `tmp/skills-ui-mine.md` with complete className trees for surfaces below

- [ ] **Step 1: Open official surfaces**

登录态 Chrome（sticky profile）打开：

1. Skills 管理页（侧栏 Skills）
2. Skills 页点击 **+ Add** 展开菜单
3. 首页/会话 ChatBox 输入 `/`，展开含 skill 的菜单；选一个 skill 插入 chip

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=9222 \
  --user-data-dir=/tmp/chrome-manus-debug \
  --profile-directory=Default \
  --no-first-run --no-default-browser-check \
  "https://manus.im/app"
```

截图存 `tmp/screenshots/skills-*`（不提交）。

- [ ] **Step 2: Dump DOM + mine JS**

对每个 surface dump **完整** outerHTML / className（禁止截断半截 `var(--`）。在 `/tmp/manus-js` 或下载的 chunk 中：

```bash
rg -n 'skillTag|SkillTag|Add from official|Build with Manus|Skills' /tmp/manus-js/*.js | head -80
```

- [ ] **Step 3: Write mine notes**

创建 `tmp/skills-ui-mine.md`，至少包含这些标题与**完整** class 字符串：

1. Sidebar Skills row
2. SkillsPage shell / header / search / list row or card / empty
3. + Add button + dropdown panel + four menu rows
4. Placeholder dialogs if visible (Upload / GitHub / Official / Build)
5. ChatBox slash skill row (+ divider if any)
6. skillTag chip (outer + inner text classes)

若某对话框打不开，在笔记写明「未挖到 → 实现时用已有 dialog shell + 官方文案，禁止 invent 装饰」。

- [ ] **Step 4: Smoke-check notes**

确认无 `…` 截断 class；每个区块至少一行完整 `class=` / `className:`。

（本 task 无 git commit。）

---

### Task 2: Skill types, mock data, `useSkills`

**Files:**
- Create: `frontend/src/types/skill.ts`
- Create: `frontend/src/mocks/skills.ts`
- Create: `frontend/src/composables/useSkills.ts`
- Create: `frontend/src/composables/__tests__/useSkills.spec.ts`

**Interfaces:**
- Consumes: none
- Produces:
  - `export type SkillOwnerType = 'personal' | 'official'`
  - `export type Skill = { id: string; name: string; description: string; owner_type: SkillOwnerType }`
  - `export const MOCK_SKILLS: Skill[]`（≥3 条；`name` 为 slug，如 `market-research`）
  - `export function useSkills(): { skills: ComputedRef<Skill[]>; filterByQuery: (query: string) => Skill[] }`

- [ ] **Step 1: Write the failing test**

```typescript
// frontend/src/composables/__tests__/useSkills.spec.ts
import { describe, it, expect } from 'vitest'
import { useSkills } from '../useSkills'
import { MOCK_SKILLS } from '../../mocks/skills'

describe('useSkills', () => {
  it('exposes mock skills', () => {
    const { skills } = useSkills()
    expect(skills.value.length).toBeGreaterThanOrEqual(3)
    expect(skills.value[0]).toMatchObject({
      id: expect.any(String),
      name: expect.any(String),
      description: expect.any(String),
      owner_type: expect.stringMatching(/^(personal|official)$/),
    })
  })

  it('filterByQuery matches name and description case-insensitively', () => {
    const { filterByQuery } = useSkills()
    const probe = MOCK_SKILLS[0]
    expect(filterByQuery(probe.name.slice(0, 3).toUpperCase()).some((s) => s.id === probe.id)).toBe(true)
    expect(filterByQuery('___no_such_skill___')).toEqual([])
  })

  it('filterByQuery empty returns all', () => {
    const { filterByQuery } = useSkills()
    expect(filterByQuery('').length).toBe(MOCK_SKILLS.length)
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm run test -- src/composables/__tests__/useSkills.spec.ts`

Expected: FAIL (module not found)

- [ ] **Step 3: Write minimal implementation**

```typescript
// frontend/src/types/skill.ts
export type SkillOwnerType = 'personal' | 'official'

export type Skill = {
  id: string
  name: string
  description: string
  owner_type: SkillOwnerType
}
```

```typescript
// frontend/src/mocks/skills.ts
import type { Skill } from '../types/skill'

export const MOCK_SKILLS: Skill[] = [
  {
    id: 'skill_market_research',
    name: 'market-research',
    description: 'Research markets and competitors into a structured brief',
    owner_type: 'official',
  },
  {
    id: 'skill_slides',
    name: 'slides',
    description: 'Turn an outline into presentation slides',
    owner_type: 'official',
  },
  {
    id: 'skill_data_viz',
    name: 'data-viz',
    description: 'Plot CSV data with clear charts',
    owner_type: 'personal',
  },
]
```

```typescript
// frontend/src/composables/useSkills.ts
import { computed } from 'vue'
import { MOCK_SKILLS } from '../mocks/skills'
import type { Skill } from '../types/skill'

export function useSkills() {
  const skills = computed(() => MOCK_SKILLS)

  const filterByQuery = (query: string): Skill[] => {
    const q = query.trim().toLowerCase()
    if (!q) return MOCK_SKILLS
    return MOCK_SKILLS.filter(
      (s) =>
        s.name.toLowerCase().includes(q) ||
        s.description.toLowerCase().includes(q),
    )
  }

  return { skills, filterByQuery }
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npm run test -- src/composables/__tests__/useSkills.spec.ts`

Expected: PASS

- [ ] **Step 5: Stop — no commit unless user asks**

---

### Task 3: TipTap `SkillTag` node

**Files:**
- Create: `frontend/src/components/chatbox/skillTag.ts`
- Create: `frontend/src/components/chatbox/__tests__/skillTag.spec.ts`

**Interfaces:**
- Consumes: TipTap `Node` from `@tiptap/core`
- Produces:
  - `export const SkillTag` TipTap extension
  - Node name: `'skillTag'`
  - Attrs: `{ skillId: string; name: string }`
  - `renderHTML` / `parseHTML` for chip
  - `renderText` / text serializer so `editor.getText()` includes `/{name}`
  - Command helper: `insertSkillTag({ skillId, name })` via `addCommands` if natural; else document insert JSON for ChatBox

- [ ] **Step 1: Write the failing test**

```typescript
// frontend/src/components/chatbox/__tests__/skillTag.spec.ts
import { describe, it, expect } from 'vitest'
import { Editor } from '@tiptap/core'
import StarterKit from '@tiptap/starter-kit'
import { SkillTag } from '../skillTag'

function makeEditor() {
  return new Editor({
    extensions: [StarterKit, SkillTag],
    content: { type: 'doc', content: [{ type: 'paragraph' }] },
  })
}

describe('SkillTag', () => {
  it('serializes to /{name} in getText', () => {
    const editor = makeEditor()
    editor.commands.setContent({
      type: 'doc',
      content: [
        {
          type: 'paragraph',
          content: [
            {
              type: 'skillTag',
              attrs: { skillId: 'skill_slides', name: 'slides' },
            },
            { type: 'text', text: ' please' },
          ],
        },
      ],
    })
    expect(editor.getText()).toBe('/slides please')
    editor.destroy()
  })

  it('renders a non-editable chip DOM', () => {
    const editor = makeEditor()
    editor.commands.insertContent({
      type: 'skillTag',
      attrs: { skillId: 'skill_slides', name: 'slides' },
    })
    const el = editor.view.dom.querySelector('[data-skill-tag]')
    expect(el).toBeTruthy()
    expect(el!.getAttribute('data-skill-name')).toBe('slides')
    editor.destroy()
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npm run test -- src/components/chatbox/__tests__/skillTag.spec.ts`

Expected: FAIL

- [ ] **Step 3: Write SkillTag extension**

实现要点（class 字符串从 `tmp/skills-ui-mine.md` 的 skillTag 区块粘贴；若挖矿缺失，用最小可测 DOM，后续 Task 6 替换）：

```typescript
// frontend/src/components/chatbox/skillTag.ts
import { Node, mergeAttributes } from '@tiptap/core'

export type SkillTagAttrs = {
  skillId: string
  name: string
}

declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    skillTag: {
      insertSkillTag: (attrs: SkillTagAttrs) => ReturnType
    }
  }
}

export const SkillTag = Node.create({
  name: 'skillTag',
  group: 'inline',
  inline: true,
  atom: true,
  selectable: true,
  draggable: false,

  addAttributes() {
    return {
      skillId: { default: '' },
      name: { default: '' },
    }
  },

  parseHTML() {
    return [{ tag: 'span[data-skill-tag]' }]
  },

  renderHTML({ node, HTMLAttributes }) {
    // PASTE chip classes from tmp/skills-ui-mine.md here
    return [
      'span',
      mergeAttributes(HTMLAttributes, {
        'data-skill-tag': '',
        'data-skill-name': node.attrs.name,
        'data-skill-id': node.attrs.skillId,
        class:
          'skill-tag inline-flex items-center rounded-md px-1.5 text-[13px] bg-[var(--fill-tsp-white-main)] text-[var(--text-primary)]',
        contenteditable: 'false',
      }),
      `/${node.attrs.name}`,
    ]
  },

  renderText({ node }) {
    return `/${node.attrs.name}`
  },

  addCommands() {
    return {
      insertSkillTag:
        (attrs) =>
        ({ commands }) =>
          commands.insertContent({
            type: this.name,
            attrs,
          }),
    }
  },
})
```

若 TipTap 版本里 `getText()` 不走 `renderText`，在测试失败时改为：

```typescript
addProseMirrorPlugins() { /* or */ }
// 或在 ChatBox onUpdate 使用 editor.getText({ textSerializers: { skillTag: (...) => `/${name}` } })
```

以测试绿为准；把最终 serializer 路径写进代码注释一行。

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npm run test -- src/components/chatbox/__tests__/skillTag.spec.ts`

Expected: PASS

- [ ] **Step 5: Stop — no commit unless user asks**

---

### Task 4: Wire slash menu + ChatBox to skills

**Files:**
- Modify: `frontend/src/components/chatbox/slashSuggestion.ts`
- Modify: `frontend/src/components/chatbox/ChatBoxSlashMenu.vue`
- Modify: `frontend/src/components/ChatBox.vue`
- Modify: `frontend/src/components/__tests__/ChatBox.spec.ts`

**Interfaces:**
- Consumes: `useSkills().filterByQuery`, `SkillTag`, `Skill`
- Produces:
  - `SlashItem` =
    | `{ id: 'add_local_files'; kind: 'local'; titleKey: string; run: () => void }`
    | `{ id: string; kind: 'skill'; titleKey: string; skillId: string; name: string; description: string; run: () => void }`
  - `buildSlashItems(opts: { runAddLocalFiles: () => void; skills: Skill[]; onInsertSkill: (s: Skill) => void }): SlashItem[]`
  - Slash `command`：local → `run()`；skill → `deleteRange` + `insertSkillTag`

- [ ] **Step 1: Extend failing ChatBox test**

在 `ChatBox.spec.ts` 追加：

```typescript
  it('slash skill inserts chip and getText is /{name}', async () => {
    const wrapper = mount(ChatBox, {
      props: { modelValue: '', rows: 1, isRunning: false, attachments: [] },
      global: { plugins: [i18n] },
      attachTo: document.body,
    })
    await flushPromises()
    await nextTick()

    type EditorLike = {
      commands: {
        setContent: (c: unknown, o?: unknown) => boolean
        insertContent: (c: unknown) => boolean
      }
      chain: () => {
        focus: () => {
          deleteRange: (r: { from: number; to: number }) => {
            insertContent: (c: unknown) => { run: () => boolean }
          }
        }
      }
      getText: (o?: { blockSeparator?: string }) => string
      view: { dom: HTMLElement }
    }
    const exposed = wrapper.vm as unknown as { editor: EditorLike | { value?: EditorLike } }
    const raw = exposed.editor
    const ed = raw && 'commands' in raw ? raw : raw?.value
    expect(ed).toBeTruthy()

    // Prefer exercising public slash path if exposed; else insertSkillTag via command:
    // After wiring, simulate selecting first mock skill via applySlashSelection + skill item.
    const { MOCK_SKILLS } = await import('../../mocks/skills')
    const skill = MOCK_SKILLS[0]
    const item: SlashItem = {
      id: skill.id,
      kind: 'skill',
      titleKey: skill.name,
      skillId: skill.id,
      name: skill.name,
      description: skill.description,
      run: () => {
        ed!.commands.insertContent({
          type: 'skillTag',
          attrs: { skillId: skill.id, name: skill.name },
        })
      },
    }
    applySlashSelection({
      editor: ed as unknown as import('@tiptap/core').Editor,
      range: { from: 1, to: 1 },
      command: null,
      item,
    })
    await flushPromises()
    expect(ed!.getText()).toContain(`/${skill.name}`)
    expect(wrapper.find('[data-skill-tag]').exists()).toBe(true)
  })
```

（若 `SlashItem` 字段名在实现中微调，测试与实现对齐；`kind: 'skill'` 必须存在。）

- [ ] **Step 2: Run test — expect fail on kind/SkillTag missing**

Run: `cd frontend && npm run test -- src/components/__tests__/ChatBox.spec.ts`

- [ ] **Step 3: Update `slashSuggestion.ts`**

```typescript
import type { Skill } from '../../types/skill'

export type SlashItem =
  | {
      id: 'add_local_files'
      kind: 'local'
      titleKey: string
      run: () => void
    }
  | {
      id: string
      kind: 'skill'
      titleKey: string
      skillId: string
      name: string
      description: string
      run: () => void
    }

export function buildSlashItems(opts: {
  runAddLocalFiles: () => void
  skills: Skill[]
  onInsertSkill: (skill: Skill) => void
}): SlashItem[] {
  const local: SlashItem = {
    id: 'add_local_files',
    kind: 'local',
    titleKey: 'Add local files',
    run: opts.runAddLocalFiles,
  }
  const skillItems: SlashItem[] = opts.skills.map((s) => ({
    id: s.id,
    kind: 'skill' as const,
    titleKey: s.name,
    skillId: s.id,
    name: s.name,
    description: s.description,
    run: () => opts.onInsertSkill(s),
  }))
  return [local, ...skillItems]
}
```

更新 `items` filter：skill 也可匹配 `description` / `name`。

更新 `command`：始终 `deleteRange` 后调用 `props.run()`（skill 的 `run` 负责 insert）。

- [ ] **Step 4: Update ChatBoxSlashMenu**

- Props `items` 扩展：可选 `kind`、`description`
- skill 行：从 mine notes 贴 class；显示 `name`（或 `t(titleKey)`）；副标题 description 若官方有则抄
- local 行保持 Paperclip；skill 行图标从 mine 抄（无则用 `Sparkles` / 官方同款 lucide，不 invent 第二套样式）

- [ ] **Step 5: Wire `ChatBox.vue`**

1. `extensions` 加入 `SkillTag`
2. `const { skills, filterByQuery } = useSkills()`
3. `buildSlashItems` 传入 skills；`onInsertSkill` → `editor.chain().focus().insertSkillTag({ skillId, name }).run()`（若 deleteRange 已在 suggestion command 完成，则 `run` 只 insert）
4. `onUpdate` 的 `getText` 若需显式 textSerializers，在此补上以保证含 `/{name}`
5. Suggestion `items` 用 `filterByQuery(query)` 再 `buildSlashItems`（或 build 全量再 filter）

注意：`plainTextToDoc` **不需要** 解析 `/{name}` 回 chip（spec：inbound 纯文本即可）。

- [ ] **Step 6: Fix existing slash tests**

现有 `add_local_files` 测试若因 `SlashItem` 形状变更失败，补上 `kind: 'local'`。

- [ ] **Step 7: Run tests**

Run: `cd frontend && npm run test -- src/components/__tests__/ChatBox.spec.ts src/components/chatbox/__tests__/skillTag.spec.ts`

Expected: PASS

- [ ] **Step 8: Stop — no commit unless user asks**

---

### Task 5: Route, sidebar, SkillsPage list shell

**Files:**
- Modify: `frontend/src/router/index.ts`
- Modify: `frontend/src/components/SessionSidebar.vue`
- Create: `frontend/src/pages/SkillsPage.vue`
- Create: `frontend/src/pages/__tests__/SkillsPage.spec.ts`
- Modify: `frontend/src/locales/en.ts` / `zh.ts`（本 task 至少加 `Skills`、`Search skills`）

**Interfaces:**
- Consumes: `useSkills()`；mine notes § SkillsPage / Sidebar
- Produces: 可导航 `/skills`；列表展示 mock；搜索过滤；行不导航

- [ ] **Step 1: Write SkillsPage smoke test**

```typescript
// frontend/src/pages/__tests__/SkillsPage.spec.ts
import { describe, it, expect } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import SkillsPage from '../SkillsPage.vue'
import { i18n } from '../../composables/useI18n'
import { MOCK_SKILLS } from '../../mocks/skills'

describe('SkillsPage', () => {
  it('renders skill names from mock data', async () => {
    const wrapper = mount(SkillsPage, {
      global: { plugins: [i18n] },
    })
    await flushPromises()
    expect(wrapper.text()).toContain(MOCK_SKILLS[0].name)
    expect(wrapper.find('[data-testid="skills-add-button"]').exists()).toBe(true)
  })

  it('filters list by search query', async () => {
    const wrapper = mount(SkillsPage, {
      global: { plugins: [i18n] },
    })
    await flushPromises()
    const input = wrapper.find('[data-testid="skills-search-input"]')
    await input.setValue('___no_such_skill___')
    expect(wrapper.text()).not.toContain(MOCK_SKILLS[0].name)
  })
})
```

- [ ] **Step 2: Run — expect fail**

Run: `cd frontend && npm run test -- src/pages/__tests__/SkillsPage.spec.ts`

- [ ] **Step 3: Add route**

在 `router/index.ts` 于 `/library` 旁增加：

```typescript
    {
      path: '/skills',
      component: () => import('../pages/MainLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          component: () => import('../pages/SkillsPage.vue'),
          meta: { requiresAuth: true },
        },
      ],
    },
```

- [ ] **Step 4: Sidebar entry**

在 `SessionSidebar.vue` Library 块**下方**插入 Skills 行：class **完整粘贴** mine notes「Sidebar Skills row」；图标用官方同款（挖到的 lucide / svg）；`route.path === '/skills'` 高亮；`router.push('/skills')`。

- [ ] **Step 5: Implement SkillsPage shell**

粘贴 mine notes 的 header / search / list / empty。骨架：

```vue
<template>
  <div data-testid="skills-page" class="/* PASTE shell from mine */">
    <div class="/* PASTE header */">
      <div>{{ t('Skills') }}</div>
      <button type="button" data-testid="skills-add-button" @click="addOpen = !addOpen">
        <!-- + Add — Task 6 接菜单；本步可先只有按钮 -->
        {{ t('Add') }}
      </button>
    </div>
    <input
      data-testid="skills-search-input"
      v-model="query"
      :placeholder="t('Search skills')"
    />
    <div v-if="filtered.length === 0" class="/* PASTE empty */">
      {{ t('No skills yet') }}
    </div>
    <div v-else>
      <div
        v-for="skill in filtered"
        :key="skill.id"
        data-testid="skills-list-item"
        class="/* PASTE row/card */"
      >
        <div>{{ skill.name }}</div>
        <div>{{ skill.description }}</div>
        <span v-if="skill.owner_type === 'official'">{{ t('Official') }}</span>
      </div>
    </div>
  </div>
</template>
```

```typescript
const { filterByQuery } = useSkills()
const query = ref('')
const filtered = computed(() => filterByQuery(query.value))
```

行 **无** `@click` 导航。

- [ ] **Step 6: i18n keys**

`en.ts` / `zh.ts` 增加至少：

- `Skills` / `技能`
- `Search skills` / `搜索技能`
- `No skills yet` / `暂无技能`
- `Add` / `添加`（若官方是 `+ Add`，key 用官方英文）
- `Official` / `官方`

- [ ] **Step 7: Run tests**

Run: `cd frontend && npm run test -- src/pages/__tests__/SkillsPage.spec.ts`

Expected: PASS

- [ ] **Step 8: Stop — no commit unless user asks**

---

### Task 6: + Add menu + placeholder dialogs

**Files:**
- Create: `frontend/src/components/skills/SkillsAddMenu.vue`
- Create: `frontend/src/components/skills/SkillsPlaceholderDialog.vue`
- Modify: `frontend/src/pages/SkillsPage.vue`
- Modify: `frontend/src/pages/__tests__/SkillsPage.spec.ts`
- Modify: `frontend/src/locales/en.ts` / `zh.ts`
- Modify: `frontend/src/components/chatbox/skillTag.ts`（若 Task 3 用了临时 chip class，替换为 mine 最终 token）

**Interfaces:**
- Consumes: mine notes Add menu + dialogs
- Produces: 四项菜单；四项打开占位对话框；Upload/GitHub/Official/Build 提交均为 no-op + 可选 toast `Coming soon`（key 已存在）

- [ ] **Step 1: Extend SkillsPage test**

```typescript
  it('opens Add menu with four official actions', async () => {
    const wrapper = mount(SkillsPage, {
      global: { plugins: [i18n] },
      attachTo: document.body,
    })
    await flushPromises()
    await wrapper.find('[data-testid="skills-add-button"]').trigger('click')
    const menu = wrapper.find('[data-testid="skills-add-menu"]')
    expect(menu.exists()).toBe(true)
    expect(menu.text()).toContain('Build with Manus')
    expect(menu.text()).toContain('Upload a skill')
    expect(menu.text()).toContain('Add from official')
    expect(menu.text()).toContain('Import from GitHub')
  })

  it('opens placeholder dialog when choosing Upload a skill', async () => {
    const wrapper = mount(SkillsPage, {
      global: { plugins: [i18n] },
      attachTo: document.body,
    })
    await flushPromises()
    await wrapper.find('[data-testid="skills-add-button"]').trigger('click')
    await wrapper.find('[data-testid="skills-add-upload"]').trigger('click')
    expect(wrapper.find('[data-testid="skills-placeholder-dialog"]').exists()).toBe(true)
  })
```

（菜单项可见文案用 `t('…')`，测试对英文 locale 断言英文官方 key。）

- [ ] **Step 2: Run — expect fail**

- [ ] **Step 3: Implement `SkillsAddMenu.vue`**

四项 `data-testid`：

- `skills-add-build`
- `skills-add-upload`
- `skills-add-official`
- `skills-add-github`

Panel/row class 从 mine 粘贴。emit `select`：`'build' | 'upload' | 'official' | 'github'`。

- [ ] **Step 4: Implement `SkillsPlaceholderDialog.vue`**

Props：`open`、`variant: 'build' | 'upload' | 'official' | 'github'`。

- 有 mine 的 dialog class → 粘贴
- 无 → 复用项目现有居中 dialog 壳（参考 Settings / confirm dialog），只换标题与正文
- Upload：拖拽区样式能抄则抄；**不**读文件
- GitHub：URL input；提交按钮 → toast / no-op
- Confirm/Close → `emit('close')`
- 主操作按钮 → 显示 `t('Coming soon')` 后 close（或仅 close）

- [ ] **Step 5: Wire SkillsPage**

`skills-add-button` 切换菜单；选中项打开对应 `variant` dialog；点击页外关闭菜单。

- [ ] **Step 6: i18n**

增加官方英文 key（中文翻译）：

- `Build with Manus`
- `Upload a skill`
- `Add from official`
- `Import from GitHub`
- 各占位对话框短说明（可各一条 `… placeholder body`）

- [ ] **Step 7: Replace temporary skillTag chip classes with mined tokens**（若尚未）

- [ ] **Step 8: Run page + chatbox tests**

Run: `cd frontend && npm run test -- src/pages/__tests__/SkillsPage.spec.ts src/components/__tests__/ChatBox.spec.ts src/components/chatbox/__tests__/skillTag.spec.ts src/composables/__tests__/useSkills.spec.ts`

Expected: PASS

- [ ] **Step 9: Full verify**

Run: `cd frontend && npm run test && npm run type-check && npm run lint`

Expected: all green

- [ ] **Step 10: Stop — no commit unless user asks**

---

## Spec coverage (self-review)

| Spec requirement | Task |
|---|---|
| 设置 Skills tab + SkillsSettings | 5 |
| 管理页列表/搜索/空态 | 5 |
| + Add 四项 + 占位对话框 | 6 |
| 假数据 + useSkills，无 localStorage/后端 | 2 |
| ChatBox `/` + skill chip | 3–4 |
| `getText` → `/{name}` | 3–4 |
| 直接抄 / 挖矿 | 1（+ 3/5/6 粘贴） |
| 不做 Project Skills / 商店页 / 运行时 | Global Constraints |
| i18n en+zh | 5–6 |
| 验收 test/type-check/lint | 6 Step 9 |

## Placeholder / type consistency check

- `Skill.name` slug ↔ serializer `/{name}` ↔ slash `titleKey`/`name` 一致
- `SlashItem.kind`：`'local' | 'skill'`
- Dialog `variant` 与 Add menu emit 联合一致：`'build' | 'upload' | 'official' | 'github'`
- 无 TBD；挖矿产物路径固定为 `tmp/skills-ui-mine.md`
