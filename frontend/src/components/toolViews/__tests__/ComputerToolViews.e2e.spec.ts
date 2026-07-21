/**
 * Component-level e2e checks for Computer tool views (xterm + file diff tabs).
 */
import { describe, it, expect, afterEach, beforeAll } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { nextTick, defineComponent, h } from 'vue'
import { createI18n } from 'vue-i18n'
import en from '@/locales/en'
import FileToolView from '@/components/toolViews/FileToolView.vue'
import ShellToolView from '@/components/toolViews/ShellToolView.vue'
import type { ToolContent } from '@/types/message'

const i18n = createI18n({
  legacy: false,
  locale: 'en',
  messages: { en },
})

const MonacoStub = defineComponent({
  name: 'MonacoStub',
  props: ['value', 'original', 'modified', 'filename'],
  setup: () => () => h('div', { class: 'monaco-stub' }),
})

beforeAll(() => {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: (query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false,
    }),
  })
  // jsdom lacks ResizeObserver; xterm FitAddon needs it.
  class RO {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
  // @ts-expect-error test polyfill
  global.ResizeObserver = RO
})

function fileTool(partial: Partial<ToolContent> & { content?: any }): ToolContent {
  return {
    timestamp: Date.now(),
    tool_call_id: 'call-1',
    name: 'file',
    function: 'file_write',
    args: { file: '/home/ubuntu/example.txt' },
    status: 'called',
    ...partial,
  }
}

describe('Computer tool views e2e', () => {
  afterEach(() => {
    document.body.innerHTML = ''
  })

  it('FileToolView shows Diff/Original/Modified when old_content exists', async () => {
    const wrapper = mount(FileToolView, {
      global: {
        plugins: [i18n],
        stubs: {
          MonacoEditor: MonacoStub,
          MonacoDiffEditor: MonacoStub,
        },
      },
      props: {
        sessionId: 'sess-1',
        live: false,
        toolContent: fileTool({
          content: {
            content: 'new line\n',
            old_content: 'old line\n',
          },
        }),
      },
    })
    await flushPromises()
    await nextTick()

    const labels = wrapper.findAll('button').map((b) => b.text())
    expect(labels).toContain('Diff')
    expect(labels).toContain('Original')
    expect(labels).toContain('Modified')
    // Official default tab is Modified
    const modified = wrapper.findAll('button').find((b) => b.text() === 'Modified')
    expect(modified?.attributes('data-state')).toBe('on')
  })

  it('FileToolView hides tabs when there is no old_content', async () => {
    const wrapper = mount(FileToolView, {
      global: {
        plugins: [i18n],
        stubs: {
          MonacoEditor: MonacoStub,
          MonacoDiffEditor: MonacoStub,
        },
      },
      props: {
        sessionId: 'sess-1',
        live: false,
        toolContent: fileTool({
          content: { content: 'only new\n' },
        }),
      },
    })
    await flushPromises()
    const tabBar = wrapper.find('.backdrop-blur-3xl')
    expect(tabBar.exists()).toBe(true)
    expect(tabBar.element.parentElement?.classList.contains('hidden')).toBe(true)
  })

  it('ShellToolView mounts xterm host panel', async () => {
    const wrapper = mount(ShellToolView, {
      global: { plugins: [i18n] },
      props: {
        sessionId: 'sess-1',
        live: false,
        toolContent: {
          timestamp: Date.now(),
          tool_call_id: 'shell-1',
          name: 'shell',
          function: 'shell_exec',
          args: { id: 'shell-1' },
          status: 'called',
          content: {
            console: [
              { ps1: 'ubuntu@sandbox:~$', command: 'echo hi', output: 'hi' },
            ],
          },
        },
      },
      attachTo: document.body,
    })
    await flushPromises()
    await nextTick()
    await new Promise((r) => setTimeout(r, 50))

    expect(wrapper.find('.agent-workspace-terminal-panel').exists()).toBe(true)
    wrapper.unmount()
  })
})
