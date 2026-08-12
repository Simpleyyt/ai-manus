import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import ToolUse from '../ToolUse.vue'
import type { ToolContent } from '../../types/message'
import { TOOL_SHIMMER_MIN_MS } from '../../composables/useToolShimmer'
import en from '../../locales/en'

const i18n = createI18n({
  legacy: false,
  locale: 'en',
  messages: { en },
})

const makeTool = (overrides: Partial<ToolContent> = {}): ToolContent => ({
  tool_call_id: 'tc-1',
  name: 'file',
  function: 'file_write',
  args: { file: '/home/ubuntu/web_game/index.html' },
  status: 'called',
  timestamp: Date.now(),
  ...overrides,
})

describe('ToolUse', () => {
  it('prefers official brief over message.action/param (StandardToolUsed)', () => {
    const wrapper = mount(ToolUse, {
      props: {
        tool: makeTool({ brief: '编写 Python 示例代码' }),
      },
      global: { plugins: [i18n] },
    })
    expect(wrapper.find('.truncate.text-sm').text()).toBe('编写 Python 示例代码')
    expect(wrapper.find('.font-mono').exists()).toBe(false)
  })

  it('falls back to action + mono param when brief is missing', () => {
    const wrapper = mount(ToolUse, {
      props: { tool: makeTool({ brief: null }) },
      global: { plugins: [i18n] },
    })
    expect(wrapper.find('span.text-sm').text()).toContain('Writing file')
    expect(wrapper.find('.font-mono').text()).toBe('web_game/index.html')
  })

  it('applies shimmer-text-secondary on the label while calling', () => {
    const wrapper = mount(ToolUse, {
      props: {
        tool: makeTool({ status: 'calling', brief: '编写 Python 示例代码' }),
      },
      global: { plugins: [i18n] },
    })
    const shimmer = wrapper.find('.shimmer-text-secondary')
    expect(shimmer.exists()).toBe(true)
    expect(shimmer.text()).toBe('编写 Python 示例代码')
    expect(wrapper.find('.group').classes().join('')).not.toContain('text-[var(--text-secondary)]')
  })

  it('keeps shimmer while active even after called', async () => {
    vi.useFakeTimers()
    const tool = makeTool({ status: 'calling', brief: '编写 Python 示例代码' })
    const wrapper = mount(ToolUse, {
      props: { tool, active: true },
      global: { plugins: [i18n] },
    })
    await wrapper.setProps({ tool: { ...tool, status: 'called' }, active: true })
    await vi.advanceTimersByTimeAsync(TOOL_SHIMMER_MIN_MS + 100)
    expect(wrapper.find('.shimmer-text-secondary').exists()).toBe(true)
    await wrapper.setProps({ active: false })
    expect(wrapper.find('.shimmer-text-secondary').exists()).toBe(false)
    vi.useRealTimers()
  })

  it('keeps shimmer briefly after a fast called so the sweep is visible', async () => {
    vi.useFakeTimers()
    const tool = makeTool({ status: 'calling', brief: '编写 Python 示例代码' })
    const wrapper = mount(ToolUse, {
      props: { tool },
      global: { plugins: [i18n] },
    })
    expect(wrapper.find('.shimmer-text-secondary').exists()).toBe(true)

    await wrapper.setProps({ tool: { ...tool, status: 'called' } })
    expect(wrapper.find('.shimmer-text-secondary').exists()).toBe(true)

    await vi.advanceTimersByTimeAsync(TOOL_SHIMMER_MIN_MS + 100)
    expect(wrapper.find('.shimmer-text-secondary').exists()).toBe(false)
    vi.useRealTimers()
  })
})
