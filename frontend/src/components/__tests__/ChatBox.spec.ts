import { describe, it, expect, vi } from 'vitest'
import { nextTick } from 'vue'
import { mount, flushPromises } from '@vue/test-utils'
import { Editor } from '@tiptap/core'
import StarterKit from '@tiptap/starter-kit'
import ChatBox from '../ChatBox.vue'
import { i18n } from '../../composables/useI18n'
import { applySlashSelection, type SlashItem } from '../chatbox/slashSuggestion'

export const uploadFileMock = vi.fn()

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
    expect(menu.text()).toContain('Add local files')

    const row = menu.findAll('button').find((b) => b.text().includes('Add local files'))
    expect(row).toBeTruthy()
    await row!.trigger('click')
    await nextTick()

    expect(uploadFileMock).toHaveBeenCalled()
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
})
