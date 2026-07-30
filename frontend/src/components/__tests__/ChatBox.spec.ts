import { describe, it, expect, vi } from 'vitest'
import { nextTick } from 'vue'
import { mount, flushPromises } from '@vue/test-utils'
import ChatBox from '../ChatBox.vue'
import { i18n } from '../../composables/useI18n'

vi.mock('../ChatBoxFiles.vue', () => ({
  default: {
    name: 'ChatBoxFiles',
    props: ['attachments'],
    emits: ['update:attachments'],
    setup(_: unknown, { expose }: { expose: (exposed: Record<string, unknown>) => void }) {
      expose({ isAllUploaded: true, uploadFile: vi.fn() })
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
})
