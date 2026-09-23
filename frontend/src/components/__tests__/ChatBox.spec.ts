import { describe, it, expect, vi, beforeEach } from 'vitest'
import { nextTick } from 'vue'
import { mount, flushPromises } from '@vue/test-utils'
import { Editor } from '@tiptap/core'
import StarterKit from '@tiptap/starter-kit'
import { createRouter, createWebHistory } from 'vue-router'
import ChatBox from '../ChatBox.vue'
import { i18n } from '../../composables/useI18n'
import { applySlashSelection, type SlashItem } from '../chatbox/slashSuggestion'
import {
  resetSkillsStoreForTests,
  setSkillsStoreForTests,
} from '../../composables/skillsStore'
import {
  resetConnectorsStoreForTests,
  setConnectorsStoreForTests,
} from '../../composables/connectorsStore'
import { useSettingsDialog } from '../../composables/useSettingsDialog'

export const uploadFileMock = vi.fn()

const router = createRouter({
  history: createWebHistory(),
  routes: [{ path: '/', component: { template: '<div />' } }],
})

vi.mock('@/api/skills', () => ({
  fetchSkillsState: vi.fn().mockResolvedValue({ catalog: [], added: [] }),
  addSkills: vi.fn(),
  setSkillEnabled: vi.fn(),
  importSkillFromGitHub: vi.fn(),
  importSkillFromUpload: vi.fn(),
}))

vi.mock('@/api/connectors', () => ({
  fetchConnectors: vi.fn().mockResolvedValue([]),
  createConnector: vi.fn(),
  updateConnector: vi.fn(),
  deleteConnector: vi.fn(),
  importMcpJson: vi.fn(),
  createMcpFromUrl: vi.fn(),
  createFromCatalog: vi.fn(),
  setConnectorEnabled: vi.fn(),
}))

vi.mock('../ChatBoxFiles.vue', () => ({
  default: {
    name: 'ChatBoxFiles',
    props: ['attachments'],
    emits: ['update:attachments'],
    setup(_: unknown, { expose }: { expose: (exposed: Record<string, unknown>) => void }) {
      expose({ isAllUploaded: true, uploadFile: uploadFileMock })
      return {}
    },
    template: '<div data-testid="chatbox-files" />'
  }
}))

describe('ChatBox TipTap', () => {
  beforeEach(() => {
    // jsdom lacks layout geometry that ProseMirror needs on focus/scrollIntoView
    const emptyRect = {
      x: 0,
      y: 0,
      width: 0,
      height: 0,
      top: 0,
      right: 0,
      bottom: 0,
      left: 0,
      toJSON() {
        return {}
      },
    }
    const rectList = {
      length: 1,
      item: () => emptyRect,
      0: emptyRect,
      [Symbol.iterator]: function* () {
        yield emptyRect
      },
    }
    Element.prototype.getClientRects = () => rectList as unknown as DOMRectList
    Element.prototype.getBoundingClientRect = () => emptyRect as DOMRect
    Object.defineProperty(Text.prototype, 'getClientRects', {
      configurable: true,
      value: () => rectList as unknown as DOMRectList,
    })
    Object.defineProperty(Text.prototype, 'getBoundingClientRect', {
      configurable: true,
      value: () => emptyRect as DOMRect,
    })

    resetSkillsStoreForTests()
    resetConnectorsStoreForTests()
    setConnectorsStoreForTests([
      {
        id: 'c1',
        name: 'Docs MCP',
        server_key: 'docs_mcp',
        transport: 'streamable-http',
        enabled: true,
        source: 'form',
        readonly: false,
        url: 'https://mcp.example.com/mcp',
      },
    ])
    setSkillsStoreForTests({
      catalog: [
        {
          id: 'skill_market_research',
          name: 'market-research',
          description: 'Research markets',
          owner_type: 'official',
        },
      ],
      added: [
        {
          id: 'skill_market_research',
          name: 'market-research',
          description: 'Research markets',
          owner_type: 'official',
          enabled: true,
        },
      ],
    })
    useSettingsDialog().closeSettingsDialog()
  })
  it('emits update:modelValue from editor plain text', async () => {
    const wrapper = mount(ChatBox, {
      props: { modelValue: '', rows: 1, isRunning: false, attachments: [] },
      global: { plugins: [i18n] }
    })
    await flushPromises()
    const editorEl = wrapper.find('.ProseMirror')
    expect(editorEl.exists()).toBe(true)

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

  it('emits multi-paragraph text with single \\n separators', async () => {
    const wrapper = mount(ChatBox, {
      props: { modelValue: '', rows: 1, isRunning: false, attachments: [] },
      global: { plugins: [i18n] }
    })
    await flushPromises()
    await nextTick()

    type EditorLike = {
      commands: { setContent: (c: unknown, o?: unknown) => boolean }
      getText: (o?: { blockSeparator?: string }) => string
    }
    const exposed = wrapper.vm as unknown as { editor: EditorLike | { value?: EditorLike } }
    const raw = exposed.editor
    const ed = raw && 'commands' in raw ? raw : raw?.value
    expect(ed).toBeTruthy()

    // Two paragraphs (Enter while send disabled creates a new block)
    ed!.commands.setContent({
      type: 'doc',
      content: [
        { type: 'paragraph', content: [{ type: 'text', text: 'line one' }] },
        { type: 'paragraph', content: [{ type: 'text', text: 'line two' }] },
      ],
    })
    await flushPromises()
    await nextTick()

    const emitted = wrapper.emitted('update:modelValue')
    expect(emitted).toBeTruthy()
    const last = emitted![emitted!.length - 1][0] as string
    expect(last).toBe('line one\nline two')
    expect(last).not.toContain('\n\n')
  })

  it('plus menu lists Add local files and triggers uploadFile', async () => {
    uploadFileMock.mockClear()
    const wrapper = mount(ChatBox, {
      props: { modelValue: '', rows: 1, isRunning: false, attachments: [] },
      global: { plugins: [i18n] },
      attachTo: document.body,
    })
    await flushPromises()
    await nextTick()

    const plusBtn = wrapper.find('button[aria-haspopup="dialog"]')
    expect(plusBtn.exists()).toBe(true)
    await plusBtn.trigger('click')
    await nextTick()

    const menu = wrapper.find('[data-testid="chatbox-plus-menu"]')
    expect(menu.exists()).toBe(true)
    // Official + shell (not slash rounded-xl w-[240px])
    expect(menu.classes().join(' ')).toContain('rounded-[12px]')
    expect(menu.classes().join(' ')).toContain('p-1')
    expect(menu.text()).toContain('Add local files')
    expect(menu.text()).toContain('Use skills')

    const row = menu.findAll('button').find((b) => b.text().includes('Add local files'))
    expect(row).toBeTruthy()
    expect(row!.classes().join(' ')).toContain('rounded-[8px]')
    expect(row!.classes().join(' ')).toContain('p-2')
    await row!.trigger('click')
    await nextTick()

    expect(uploadFileMock).toHaveBeenCalled()
    wrapper.unmount()
  })

  it('Connect apps button opens official connectors popover', async () => {
    const wrapper = mount(ChatBox, {
      props: { modelValue: '', rows: 1, isRunning: false, attachments: [] },
      global: { plugins: [i18n, router] },
      attachTo: document.body,
    })
    await flushPromises()
    await nextTick()

    const trigger = wrapper.find('[data-testid="chatbox-connect-apps-trigger"]')
    expect(trigger.exists()).toBe(true)
    expect(trigger.classes().join(' ')).toContain('rounded-[100px]')
    expect(trigger.attributes('title')).toBe('Connect apps')
    await trigger.trigger('click')
    await nextTick()
    await flushPromises()

    const panel = document.body.querySelector('[data-testid="chatbox-connectors-panel"]')
    expect(panel).toBeTruthy()
    expect(panel!.textContent).toContain('Docs MCP')
    expect(panel!.textContent).toContain('Add connectors')
    expect(panel!.textContent).toContain('Manage connectors')
    wrapper.unmount()
  })

  it('plus Use skills panel inserts skill chip and supports Add / Manage skills', async () => {
    const wrapper = mount(ChatBox, {
      props: { modelValue: '', rows: 1, isRunning: false, attachments: [] },
      global: { plugins: [i18n, router] },
      attachTo: document.body,
    })
    await flushPromises()
    await nextTick()

    await wrapper.find('button[aria-haspopup="dialog"]').trigger('click')
    await nextTick()

    const useSkills = wrapper.find('[data-testid="chatbox-plus-use-skills"]')
    expect(useSkills.exists()).toBe(true)
    await useSkills.trigger('mouseenter')
    await nextTick()
    await flushPromises()

    const panel = wrapper.find('[data-testid="chatbox-plus-skills-panel"]')
    expect(panel.exists()).toBe(true)
    expect(panel.text()).toContain('market-research')
    expect(panel.text()).toContain('Add skills')
    expect(panel.text()).toContain('Manage skills')

    await wrapper.find('[data-testid="chatbox-plus-skill-skill_market_research"]').trigger('click')
    await flushPromises()
    await nextTick()

    type EditorLike = {
      getText: () => string
      view: { dom: HTMLElement }
    }
    const exposed = wrapper.vm as unknown as { editor: EditorLike | { value?: EditorLike } }
    const raw = exposed.editor
    const ed = raw && 'getText' in raw ? raw : raw?.value
    expect(ed!.getText()).toContain('/market-research')
    expect(ed!.view.dom.querySelector('[data-skill-tag]')).toBeTruthy()

    // Re-open for Manage skills
    await wrapper.find('button[aria-haspopup="dialog"]').trigger('click')
    await nextTick()
    await wrapper.find('[data-testid="chatbox-plus-use-skills"]').trigger('mouseenter')
    await nextTick()
    await wrapper.find('[data-testid="chatbox-plus-manage-skills"]').trigger('click')
    await nextTick()

    const settings = useSettingsDialog()
    expect(settings.isSettingsDialogOpen.value).toBe(true)
    expect(settings.defaultTab.value).toBe('skills')

    // Re-open for Add skills → Upload
    await wrapper.find('button[aria-haspopup="dialog"]').trigger('click')
    await nextTick()
    await wrapper.find('[data-testid="chatbox-plus-use-skills"]').trigger('mouseenter')
    await nextTick()
    await wrapper.find('[data-testid="chatbox-plus-add-skills"]').trigger('mouseenter')
    await nextTick()
    expect(wrapper.find('[data-testid="chatbox-plus-add-skills-menu"]').exists()).toBe(true)
    await wrapper.find('[data-testid="chatbox-plus-add-upload"]').trigger('click')
    await flushPromises()
    await nextTick()

    expect(document.body.querySelector('[data-testid="skills-placeholder-dialog"]')).toBeTruthy()
    expect(document.body.textContent).toContain('Upload skill')
    wrapper.unmount()
  })

  it('slash menu rows prevent mousedown default to keep editor selection', async () => {
    const wrapper = mount(ChatBox, {
      props: { modelValue: '', rows: 1, isRunning: false, attachments: [] },
      global: { plugins: [i18n] },
      attachTo: document.body,
    })
    await flushPromises()
    await nextTick()

    type EditorLike = {
      chain: () => {
        focus: () => {
          insertContent: (c: string) => { run: () => boolean }
        }
      }
    }
    const exposed = wrapper.vm as unknown as { editor: EditorLike | { value?: EditorLike } }
    const raw = exposed.editor
    const ed = raw && 'chain' in raw ? raw : raw?.value
    expect(ed).toBeTruthy()

    ed!.chain().focus().insertContent('/').run()
    await flushPromises()
    await nextTick()
    await flushPromises()

    const menu = wrapper.find('[data-testid="chatbox-slash-menu"]')
    expect(menu.exists()).toBe(true)
    const row = menu.findAll('button').find((b) => b.text().includes('Add local files'))
    expect(row).toBeTruthy()

    const ev = new MouseEvent('mousedown', { bubbles: true, cancelable: true })
    row!.element.dispatchEvent(ev)
    expect(ev.defaultPrevented).toBe(true)
    wrapper.unmount()
  })

  it('applySlashSelection fallback deletes / range when suggestion command is gone', () => {
    const run = vi.fn()
    const item: SlashItem = {
      id: 'add_local_files',
      kind: 'local',
      titleKey: 'Add local files',
      run,
    }
    const editor = new Editor({
      extensions: [StarterKit],
      content: '<p>/</p>',
    })
    const from = 1
    const to = 2 // the "/" character in the paragraph
    expect(editor.getText()).toBe('/')

    // Simulate mouse race: suggestion command cleared, only stored range remains
    applySlashSelection({
      editor,
      range: { from, to },
      command: null,
      item,
    })

    expect(editor.getText()).toBe('')
    expect(run).toHaveBeenCalled()
    editor.destroy()
  })

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
        insertSkillTag: (attrs: { skillId: string; name: string }) => boolean
        setContent: (c: unknown, o?: unknown) => boolean
      }
      getText: (o?: { blockSeparator?: string }) => string
      view: { dom: HTMLElement }
    }
    const exposed = wrapper.vm as unknown as { editor: EditorLike | { value?: EditorLike } }
    const raw = exposed.editor
    const ed = raw && 'commands' in raw ? raw : raw?.value
    expect(ed).toBeTruthy()

    const { MOCK_SKILLS } = await import('../../mocks/skills')
    const skill = MOCK_SKILLS[0]
    ed!.commands.insertSkillTag({ skillId: skill.id, name: skill.name })
    await flushPromises()
    await nextTick()

    expect(ed!.getText()).toBe(`/${skill.name}`)
    expect(ed!.view.dom.querySelector('[data-skill-tag]')).toBeTruthy()
    wrapper.unmount()
  })

  it('seedDraft inserts text around a skill chip', async () => {
    const wrapper = mount(ChatBox, {
      props: { modelValue: '', rows: 1, isRunning: false, attachments: [] },
      global: { plugins: [i18n] },
      attachTo: document.body,
    })
    await flushPromises()
    await nextTick()

    type Exposed = {
      seedDraft: (draft: {
        before: string
        skill: { skillId: string; name: string; description?: string; ownerType?: string }
        after: string
      }) => void
      editor: { getText: () => string; view: { dom: HTMLElement } }
    }
    const vm = wrapper.vm as unknown as Exposed
    vm.seedDraft({
      before: 'Help me create a skill together using ',
      skill: {
        skillId: 'skill_creator',
        name: 'skill-creator',
        description: 'Build a skill',
        ownerType: 'official',
      },
      after: ' to create a skill. First ask me what the skill should do.',
    })
    await flushPromises()
    await nextTick()

    expect(vm.editor.getText()).toContain('/skill-creator')
    expect(vm.editor.getText()).toContain('Help me create a skill together using ')
    expect(vm.editor.view.dom.querySelector('[data-skill-tag]')).toBeTruthy()
    expect(vm.editor.view.dom.querySelector('[data-skill-name]')?.getAttribute('data-skill-name')).toBe(
      '/skill-creator',
    )
    wrapper.unmount()
  })
})
