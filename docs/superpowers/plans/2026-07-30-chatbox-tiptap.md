# ChatBox TipTap + Slash Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `ChatBox` textarea with TipTap, paste official shell/footer tokens, and add a local-only `/` menu (「添加本地文件」), while keeping `modelValue: string` for the existing API.

**Architecture:** Keep `ChatBox.vue` as the single composer. TipTap owns the editor DOM; on every update emit `getText()`. Slash and `+` share one popover panel (official `shadow-menu rounded-xl w-[240px]`). Session pages pass `dense` for `min-h-[28px]`.

**Tech Stack:** Vue 3, TipTap (`@tiptap/vue-3`, `@tiptap/starter-kit`, `@tiptap/extension-placeholder`, `@tiptap/suggestion`), Vitest + `@vue/test-utils`, vue-i18n, Tailwind.

**Spec:** `docs/superpowers/specs/2026-07-30-chatbox-tiptap-design.md`

## Global Constraints

- 直接抄 official class strings below (and any re-dug tokens); do not approximate
- `/` menu = local-only items (v1: `add_local_files` only); no skillTag / Desktop / Cable / voice
- Submit path stays plain string via `editor.getText()`; do not persist `editorContent` to backend
- i18n both `en.ts` + `zh.ts`
- Do **not** commit unless the user explicitly asks
- Verify: `cd frontend && npm run test && npm run type-check && npm run lint`

### Official tokens to paste (already mined)

**Card shell:**

```
flex flex-col rounded-[22px] relative bg-[var(--background-menu-white)] py-3 w-full z-[2] gap-3
shadow-[0px_12px_32px_0px_rgba(0,0,0,0.02)] border border-black/8 dark:border-[var(--border-main)]
focus-within:border focus-within:border-black/20 focus-within:dark:border-[var(--border-dark)]
```

**Editor wrap:**

```
chat-input-editor overflow-auto ps-4 pe-2 bg-transparent pt-[1px] border-0
focus-visible:ring-0 focus-visible:ring-offset-0 w-full
placeholder:text-[var(--text-disable)] text-[15px] leading-[24px]
min-h-[50px]   /* default / home */
min-h-[28px]   /* dense / session */
max-h-[216px]
```

**`+` button:**

```
rounded-full border border-[var(--border-main)] inline-flex items-center justify-center gap-1
clickable cursor-pointer text-xs text-[var(--text-secondary)]
hover:bg-[var(--fill-tsp-white-light)] w-8 h-8 p-0
```

**Popover panel (`+` / `/`):**

```
bg-[var(--background-menu-white)] shadow-menu rounded-xl w-[240px] flex flex-col p-0
backdrop-blur-[40px] overflow-hidden z-[9]
```

Scroll body: `hide-scroll-bar flex-1 min-h-0 max-h-[280px] overflow-y-auto py-1`

**Row item:**

```
clickable mx-1 flex min-h-9 items-center gap-2 rounded-lg px-2 text-sm text-[var(--text-primary)]
```

(Add hover: `hover:bg-[var(--fill-tsp-white-main)]` if live DOM shows it on hover — re-check once; do not invent other chrome.)

**Send (disabled sample):** uses `bg-[var(--Button-black)]` / disabled → `disabled:bg-[var(--fill-tsp-white-dark)]`. Map to existing local `--Button-primary-black` only if `--Button-black` is already themed; prefer paste `--Button-black` if present in `theme.css`, else keep current `--Button-primary-black` and note once.

---

## File structure

| File | Responsibility |
|---|---|
| `frontend/package.json` | TipTap deps |
| `frontend/src/components/ChatBox.vue` | Composer shell + TipTap + `+`/`/` menu + send/stop |
| `frontend/src/components/chatbox/slashSuggestion.ts` | TipTap Suggestion config (trigger `/`, items, command) |
| `frontend/src/components/chatbox/ChatBoxSlashMenu.vue` | Floating menu UI (official panel tokens) |
| `frontend/src/components/__tests__/ChatBox.spec.ts` | Sync, dense class, slash item → upload hook |
| `frontend/src/locales/en.ts` / `zh.ts` | Placeholders + slash labels |
| `frontend/src/pages/ChatPage.vue` | Pass `dense` (+ session placeholder already) |
| `frontend/src/pages/HomePage.vue` / `ProjectPage.vue` / `ClawPage.vue` | Home-height default; update home placeholder key if needed |

---

### Task 1: TipTap deps + failing ChatBox sync tests

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/src/components/__tests__/ChatBox.spec.ts`
- (Implementation in Task 2)

**Interfaces:**
- Produces (expected public API after Task 2–3):

```ts
props: {
  modelValue: string
  rows: number
  isRunning: boolean
  attachments: FileInfo[]
  hideStopButton?: boolean
  allowSendFilesOnly?: boolean
  placeholder?: string
  dense?: boolean  // session min-h-[28px]
}
emits: 'update:modelValue' | 'update:attachments' | 'submit' | 'stop'
```

- [ ] **Step 1: Install TipTap packages**

```bash
cd frontend && npm install @tiptap/vue-3 @tiptap/starter-kit @tiptap/extension-placeholder @tiptap/suggestion @tiptap/pm
```

Expected: packages appear under `dependencies` in `package.json` / lockfile updated.

- [ ] **Step 2: Write failing tests**

Create `frontend/src/components/__tests__/ChatBox.spec.ts`:

```ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { defineComponent, ref, nextTick } from 'vue'
import { mount, flushPromises } from '@vue/test-utils'
import ChatBox from '../ChatBox.vue'
import { i18n } from '../../composables/useI18n'

vi.mock('../ChatBoxFiles.vue', () => ({
  default: {
    name: 'ChatBoxFiles',
    props: ['attachments'],
    emits: ['update:attachments'],
    setup(_, { expose }) {
      expose({ isAllUploaded: true, uploadFile: vi.fn() })
      return {}
    },
    template: '<div data-testid="chatbox-files" />'
  }
}))

const mountBox = (props: Record<string, unknown> = {}) => {
  const modelValue = ref('')
  const attachments = ref([])
  const Parent = defineComponent({
    components: { ChatBox },
    setup: () => ({ modelValue, attachments, ...props }),
    template: `
      <ChatBox
        v-model="modelValue"
        v-model:attachments="attachments"
        :rows="1"
        :is-running="false"
        :dense="dense"
        :placeholder="placeholder"
        @submit="onSubmit"
      />
    `,
    data: () => ({ dense: props.dense ?? false, placeholder: props.placeholder, onSubmit: props.onSubmit ?? vi.fn() })
  })
  // Prefer simpler mount if Parent data dance is awkward — direct mount is OK:
  return {
    wrapper: mount(ChatBox, {
      props: {
        modelValue: '',
        rows: 1,
        isRunning: false,
        attachments: [],
        dense: Boolean(props.dense),
        placeholder: props.placeholder as string | undefined,
        ...props
      },
      attrs: { onSubmit: props.onSubmit },
      global: { plugins: [i18n] }
    }),
    modelValue,
    attachments
  }
}

describe('ChatBox TipTap', () => {
  it('emits update:modelValue from editor plain text', async () => {
    const wrapper = mount(ChatBox, {
      props: { modelValue: '', rows: 1, isRunning: false, attachments: [] },
      global: { plugins: [i18n] }
    })
    await flushPromises()
    const editorEl = wrapper.find('.ProseMirror')
    expect(editorEl.exists()).toBe(true)
    // Prefer calling exposed editor if available; else dispatch input via tip tap view
    const vm = wrapper.vm as unknown as { editor?: { commands: { insertContent: (s: string) => void } } }
    if (wrapper.vm && 'editor' in (wrapper.vm as object)) {
      // access via defineExpose in implementation
    }
    // Implementation MUST defineExpose({ editor }) for tests OR use:
    await wrapper.find('.ProseMirror').trigger('focus')
    // Fallback: set props modelValue and assert ProseMirror text after watch
    await wrapper.setProps({ modelValue: 'hello tip tap' })
    await flushPromises()
    await nextTick()
    expect(wrapper.find('.ProseMirror').text()).toContain('hello tip tap')
  })

  it('applies dense min-h class on editor wrap', async () => {
    const wrapper = mount(ChatBox, {
      props: { modelValue: '', rows: 1, isRunning: false, attachments: [], dense: true },
      global: { plugins: [i18n] }
    })
    await flushPromises()
    expect(wrapper.find('.chat-input-editor').classes().join(' ')).toContain('min-h-[28px]')
  })

  it('default editor wrap uses min-h-[50px]', async () => {
    const wrapper = mount(ChatBox, {
      props: { modelValue: '', rows: 1, isRunning: false, attachments: [] },
      global: { plugins: [i18n] }
    })
    await flushPromises()
    expect(wrapper.find('.chat-input-editor').classes().join(' ')).toContain('min-h-[50px]')
  })
})
```

Refine the first test during implementation so it fails for the right reason (no `.ProseMirror` yet). Keep assertions on class names exact.

- [ ] **Step 3: Run tests — expect FAIL**

```bash
cd frontend && npm run test -- src/components/__tests__/ChatBox.spec.ts
```

Expected: FAIL (no TipTap / no `.ProseMirror` / no `dense` prop).

---

### Task 2: TipTap editor + shell tokens (no slash yet)

**Files:**
- Modify: `frontend/src/components/ChatBox.vue`
- Modify: `frontend/src/components/__tests__/ChatBox.spec.ts` (tighten sync test if needed)

**Interfaces:**
- Consumes: TipTap packages from Task 1
- Produces: working TipTap `ChatBox` with string `v-model`, official shell, bordered `+`, no Paperclip, `dense` prop

- [ ] **Step 1: Replace textarea with TipTap in `ChatBox.vue`**

Script outline (paste into component; keep existing send/stop/files logic):

```ts
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Placeholder from '@tiptap/extension-placeholder'
import { watch, computed, onBeforeUnmount } from 'vue'

const props = withDefaults(defineProps<{
  modelValue: string
  rows: number
  isRunning: boolean
  attachments: FileInfo[]
  hideStopButton?: boolean
  allowSendFilesOnly?: boolean
  placeholder?: string
  dense?: boolean
}>(), { placeholder: undefined, dense: false, hideStopButton: false, allowSendFilesOnly: false })

const placeholderText = computed(() => props.placeholder || t('Assign a task or type / to see more'))

const editor = useEditor({
  extensions: [
    StarterKit.configure({
      heading: false,
      codeBlock: false,
      blockquote: false,
      horizontalRule: false,
      // keep bold/italic/lists/hardBreak
    }),
    Placeholder.configure({ placeholder: () => placeholderText.value })
  ],
  content: props.modelValue || '',
  editorProps: {
    attributes: { class: 'tiptap ProseMirror focus:outline-none' },
    handleKeyDown: (_view, event) => {
      if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
        if (sendEnabled.value) {
          event.preventDefault()
          handleSubmit()
          return true
        }
      }
      return false
    }
  },
  onUpdate: ({ editor: ed }) => {
    const text = ed.getText()
    hasTextInput.value = !!text.trim()
    emit('update:modelValue', text)
  }
})

watch(() => props.modelValue, (val) => {
  if (!editor.value) return
  const current = editor.value.getText()
  if (val !== current) {
    editor.value.commands.setContent(val ? val : '', false)
  }
})

watch(placeholderText, () => {
  // Placeholder extension reads function; force view update if needed
  editor.value?.view.dispatch(editor.value.state.tr)
})

onBeforeUnmount(() => editor.value?.destroy())

defineExpose({ editor })
```

Template structure (tokens exact):

```vue
<template>
  <div class="pb-3 relative bg-[var(--background-gray-main)]">
    <div
      class="flex flex-col rounded-[22px] relative bg-[var(--background-menu-white)] py-3 w-full z-[2] gap-3 shadow-[0px_12px_32px_0px_rgba(0,0,0,0.02)] border border-black/8 dark:border-[var(--border-main)] focus-within:border focus-within:border-black/20 focus-within:dark:border-[var(--border-dark)]"
    >
      <ChatBoxFiles ... />
      <div
        class="chat-input-editor overflow-auto ps-4 pe-2 bg-transparent pt-[1px] border-0 focus-visible:ring-0 focus-visible:ring-offset-0 w-full placeholder:text-[var(--text-disable)] text-[15px] leading-[24px] max-h-[216px]"
        :class="dense ? 'min-h-[28px]' : 'min-h-[50px]'"
      >
        <EditorContent :editor="editor" />
      </div>
      <div class="flex gap-1.5 px-3 items-center">
        <!-- + button with official bordered class; menu deferred to Task 3 if needed keep simple plus→upload for green tests -->
        <button type="button" ... official + classes ... @click="showPlusMenu = !showPlusMenu">
          <Plus :size="17" />
        </button>
        <!-- NO standalone Paperclip -->
        <div class="flex gap-1.5 ml-auto items-center">
          <!-- existing send / stop -->
        </div>
      </div>
    </div>
  </div>
</template>
```

Remove fixed `height: 46px` textarea styles. Keep `rows` prop in the type for caller compatibility but unused.

- [ ] **Step 2: Add i18n keys used by default placeholder**

`frontend/src/locales/en.ts`:

```ts
'Assign a task or type / to see more': 'Assign a task or type / to see more',
```

`frontend/src/locales/zh.ts`:

```ts
'Assign a task or type / to see more': '分配一个任务或输入 / 查看更多',
```

Keep existing `Send message to Manus` for session (`ChatPage` already passes it). Optionally align zh to `向 Manus 发送消息` if current zh differs — update both locales to match official session copy:

```ts
// en
'Send message to Manus': 'Send message to Manus',
// zh
'Send message to Manus': '向 Manus 发送消息',
```

HomePage: stop relying on old default; either pass nothing (new default) or pass the new key explicitly.

- [ ] **Step 3: Run ChatBox tests — expect PASS for Task 1 assertions**

```bash
cd frontend && npm run test -- src/components/__tests__/ChatBox.spec.ts
```

Expected: PASS for ProseMirror presence, dense/default min-h, modelValue → editor text.

- [ ] **Step 4: type-check**

```bash
cd frontend && npm run type-check
```

Expected: clean.

---

### Task 3: Shared `+` / `/` menu (local item only)

**Files:**
- Create: `frontend/src/components/chatbox/slashSuggestion.ts`
- Create: `frontend/src/components/chatbox/ChatBoxSlashMenu.vue`
- Modify: `frontend/src/components/ChatBox.vue`
- Modify: `frontend/src/components/__tests__/ChatBox.spec.ts`
- Modify: `frontend/src/locales/en.ts`, `zh.ts`

**Interfaces:**
- Consumes: `ChatBox` editor + `uploadFile()` from Task 2
- Produces:

```ts
// slashSuggestion.ts
export type SlashItem = { id: 'add_local_files'; titleKey: string; run: () => void }
export function buildSlashItems(runAddLocalFiles: () => void): SlashItem[]
export function createSlashSuggestion(opts: {
  items: () => SlashItem[]
  onOpenChange?: (open: boolean) => void
}): Extension // or Suggestion config plugged into a thin Extension
```

- [ ] **Step 1: Add failing test for slash / plus menu item**

Append to `ChatBox.spec.ts`:

```ts
it('plus menu lists Add local files and triggers uploadFile', async () => {
  const uploadFile = vi.fn()
  // Remount with ChatBoxFiles mock exposing uploadFile
  // Click + button, assert menu text includes i18n 'Add local files', click row, expect uploadFile called
})
```

Implement by exporting/mocking: the existing mock's `uploadFile` must be shared via `vi.fn()` reference asserted in the test. Adjust Task 1 mock to:

```ts
export const uploadFileMock = vi.fn()
vi.mock('../ChatBoxFiles.vue', () => ({
  default: {
    name: 'ChatBoxFiles',
    setup(_, { expose }) {
      expose({ isAllUploaded: true, uploadFile: uploadFileMock })
      return {}
    },
    template: '<div />'
  }
}))
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
cd frontend && npm run test -- src/components/__tests__/ChatBox.spec.ts
```

- [ ] **Step 3: Implement `ChatBoxSlashMenu.vue`**

```vue
<template>
  <div
    v-show="open"
    class="bg-[var(--background-menu-white)] shadow-menu rounded-xl w-[240px] flex flex-col p-0 backdrop-blur-[40px] overflow-hidden z-[9]"
    :style="positionStyle"
    data-testid="chatbox-slash-menu"
  >
    <div class="hide-scroll-bar flex-1 min-h-0 max-h-[280px] overflow-y-auto py-1">
      <button
        v-for="item in items"
        :key="item.id"
        type="button"
        class="clickable mx-1 flex min-h-9 w-[calc(100%-8px)] items-center gap-2 rounded-lg px-2 text-sm text-[var(--text-primary)] hover:bg-[var(--fill-tsp-white-main)]"
        @click="emit('select', item)"
      >
        <Paperclip :size="16" class="text-[var(--icon-tertiary)]" />
        {{ t(item.titleKey) }}
      </button>
    </div>
  </div>
</template>
```

Props: `open`, `items`, `positionStyle` (for tippy/absolute). For `+` menu, position `absolute bottom-[calc(100%+8px)] left-0` on a relative wrapper (same as current plus menu).

- [ ] **Step 4: Wire `+` menu in `ChatBox.vue` to the shared panel + single item**

Items:

```ts
const localMenuItems = [{ id: 'add_local_files' as const, titleKey: 'Add local files' }]
```

On select → `showPlusMenu=false`; `uploadFile()`.

- [ ] **Step 5: TipTap Suggestion for `/`**

`slashSuggestion.ts` — use `@tiptap/suggestion` with `char: '/'`. On select `add_local_files`: delete the `/` query range, then call `runAddLocalFiles()`. Do **not** insert skillTag text.

Minimal extension pattern:

```ts
import { Extension } from '@tiptap/core'
import Suggestion from '@tiptap/suggestion'

export function SlashCommands(opts: {
  getItems: () => { id: string; titleKey: string }[]
  onStart: (props: unknown) => void
  onUpdate: (props: unknown) => void
  onExit: () => void
  onKeyDown: (props: { event: KeyboardEvent }) => boolean
}) {
  return Extension.create({
    name: 'slashCommands',
    addProseMirrorPlugins() {
      return [
        Suggestion({
          editor: this.editor,
          char: '/',
          items: ({ query }) =>
            opts.getItems().filter((i) =>
              i.id.includes(query.toLowerCase()) || query === ''
            ),
          render: () => ({
            onStart: opts.onStart,
            onUpdate: opts.onUpdate,
            onExit: opts.onExit,
            onKeyDown: opts.onKeyDown
          }),
          command: ({ editor, range, props }) => {
            editor.chain().focus().deleteRange(range).run()
            // ChatBox handles side effect via props.id callback registered in onStart client
          }
        })
      ]
    }
  })
}
```

In `ChatBox.vue`, onStart/onUpdate set menu `open=true` and clientRect → `positionStyle` (`position:fixed; left/top` from `props.clientRect()`). onExit closes. Selecting item runs upload.

If `@tiptap/suggestion` render wiring is awkward in Vue, acceptable fallback (still in this task): detect `/` at start of current textblock via `onUpdate` and show the same panel anchored above the editor — but prefer real Suggestion so Arrow/Enter work.

- [ ] **Step 6: Run tests — expect PASS**

```bash
cd frontend && npm run test -- src/components/__tests__/ChatBox.spec.ts
```

---

### Task 4: Wire consumers (`dense` + placeholders)

**Files:**
- Modify: `frontend/src/pages/ChatPage.vue`
- Modify: `frontend/src/pages/HomePage.vue` (if needed)
- Modify: `frontend/src/pages/ClawPage.vue` (session-like → `dense`)
- Modify: `frontend/src/pages/ProjectPage.vue` (home-height; keep task placeholder or new `/` home key)

- [ ] **Step 1: ChatPage**

```vue
<ChatBox
  ...
  dense
  :placeholder="chatPlaceholder"
/>
```

`chatPlaceholder` stays `t('Send message to Manus')` (zh updated in Task 2).

- [ ] **Step 2: ClawPage**

Pass `dense` (session-style composer). Keep whatever placeholder Claw already uses; if none, use `Send message to Manus` or Claw-specific existing key — do not invent product copy.

- [ ] **Step 3: HomePage / ProjectPage**

Do **not** pass `dense`. Default placeholder becomes 「分配一个任务或输入 / 查看更多」. Project may keep `t('Give Manus a task...')` or switch to the new `/` home string — prefer new home string for parity:

```vue
:placeholder="t('Assign a task or type / to see more')"
```

- [ ] **Step 4: Smoke type-check**

```bash
cd frontend && npm run type-check
```

---

### Task 5: Full verify + visual check

**Files:** none (verification only)

- [ ] **Step 1: Run full frontend gates**

```bash
cd frontend && npm run test && npm run type-check && npm run lint
```

Expected: all green.

- [ ] **Step 2: Manual / Playwright smoke**

1. Home: shell `py-3 gap-3`, placeholder with `/`, `+` has border, no Paperclip
2. Type `/` → menu shows only「添加本地文件」→ file picker
3. Chat session: `dense` min-height, placeholder「向 Manus 发送消息」
4. Submit message → still plain string in UI/network

- [ ] **Step 3 (optional): Telegram compare shots**

If user asks「截图发过来」, capture home+session ChatBox vs official and send via telegram-screenshots skill.

---

## Spec coverage checklist

| Spec item | Task |
|---|---|
| TipTap replace textarea | 2 |
| Official shell / editor / + tokens | 2 |
| `modelValue` = `getText()` | 2 |
| Remove Paperclip | 2 |
| Home vs session min-h (`dense`) | 2 + 4 |
| i18n placeholders | 2 + 4 |
| `/` local-only menu | 3 |
| `+` menu same local item | 3 |
| No skillTag / Desktop / Cable / backend editorContent | constraints (all tasks) |
| Consumers Home/Chat/Project/Claw | 4 |
| test + type-check + lint | 1–3, 5 |

## Placeholder / ambiguity scan

- No TBD left for tokens (mined above)
- Suggestion Vue wiring has an allowed fallback (still Task 3) if tippy-less fixed positioning is used
- `--Button-black` vs `--Button-primary-black`: prefer theme token that already exists; do not invent a third send style
