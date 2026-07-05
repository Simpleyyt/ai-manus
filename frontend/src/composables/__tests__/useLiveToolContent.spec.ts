import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { defineComponent, ref, computed, h, type Ref } from 'vue'
import { mount } from '@vue/test-utils'
import { useLiveToolContent } from '../useLiveToolContent'
import type { ToolContent } from '../../types/message'

const makeToolContent = (overrides: Partial<ToolContent> = {}): ToolContent => ({
  tool_call_id: 'call-1',
  name: 'file',
  function: 'file_write',
  args: { file: '/tmp/a.txt' },
  status: 'called',
  timestamp: 1,
  ...overrides
})

const mountHarness = (options: {
  live: boolean
  load: () => void
  toolContent?: ToolContent
}) => {
  const toolContent = ref(options.toolContent ?? makeToolContent()) as Ref<ToolContent>
  const live = ref(options.live)
  const Harness = defineComponent({
    setup() {
      const targetKey = computed(() => toolContent.value.args.file || '')
      useLiveToolContent({ toolContent, live, targetKey, load: options.load })
      return () => h('div')
    }
  })
  const wrapper = mount(Harness)
  return { wrapper, toolContent, live }
}

describe('useLiveToolContent', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('loads content on mount', () => {
    const load = vi.fn()
    mountHarness({ live: false, load })
    expect(load).toHaveBeenCalledTimes(1)
  })

  it('auto-refreshes every 5 seconds while live', () => {
    const load = vi.fn()
    mountHarness({ live: true, load })
    expect(load).toHaveBeenCalledTimes(1)

    vi.advanceTimersByTime(5000)
    expect(load).toHaveBeenCalledTimes(2)
    vi.advanceTimersByTime(10000)
    expect(load).toHaveBeenCalledTimes(4)
  })

  it('does not auto-refresh when not live', () => {
    const load = vi.fn()
    mountHarness({ live: false, load })
    vi.advanceTimersByTime(60000)
    expect(load).toHaveBeenCalledTimes(1)
  })

  it('starts refreshing when live becomes true and stops when it becomes false', async () => {
    const load = vi.fn()
    const { wrapper, live } = mountHarness({ live: false, load })

    live.value = true
    await wrapper.vm.$nextTick()
    expect(load).toHaveBeenCalledTimes(2) // mount + live watcher

    vi.advanceTimersByTime(5000)
    expect(load).toHaveBeenCalledTimes(3)

    live.value = false
    await wrapper.vm.$nextTick()
    vi.advanceTimersByTime(30000)
    expect(load).toHaveBeenCalledTimes(3)
  })

  it('reloads when tool content is replaced', async () => {
    const load = vi.fn()
    const { wrapper, toolContent } = mountHarness({ live: false, load })

    // Same timestamp: only the tool-content watcher fires
    toolContent.value = makeToolContent({ timestamp: 1 })
    await wrapper.vm.$nextTick()
    expect(load).toHaveBeenCalledTimes(2)

    // New timestamp on the same content object also triggers a reload
    toolContent.value = { ...toolContent.value, timestamp: 2 }
    await wrapper.vm.$nextTick()
    expect(load.mock.calls.length).toBeGreaterThanOrEqual(3)
  })

  it('stops refreshing after unmount', () => {
    const load = vi.fn()
    const { wrapper } = mountHarness({ live: true, load })
    wrapper.unmount()
    vi.advanceTimersByTime(60000)
    expect(load).toHaveBeenCalledTimes(1)
  })
})
